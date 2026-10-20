"""Same-screen noVNC through HA Ingress; never trust forwarded client headers."""
import argparse
import asyncio
from contextlib import suppress
import ipaddress
from pathlib import Path

from aiohttp import web, WSMsgType

SUPERVISOR_IP = ipaddress.ip_address('172.30.32.2')
STATE = web.AppKey('remote_state', dict)


def trusted_peer(peer):
    try:
        address = ipaddress.ip_address(peer)
        if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
            address = address.ipv4_mapped
        return address == SUPERVISOR_IP
    except (ValueError, TypeError):
        return False


@web.middleware
async def ingress_only(request, handler):
    # remote is the TCP peer, not X-Forwarded-For, X-Real-IP or a user header.
    if not trusted_peer(request.remote):
        raise web.HTTPForbidden(text='Home Assistant Ingress only')
    if not request.app[STATE]['enabled']:
        return web.Response(text='STELAB Remote je vypnuté. V konfiguraci doplňku zapněte remote_access a restartujte doplněk.',
                            content_type='text/plain', status=503)
    response = await handler(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


async def index(request):
    # Relative location and WS path retain HA's per-session ingress prefix.
    return web.Response(status=302, headers={
        'Location': 'vnc.html?autoconnect=true&resize=scale&path=websockify'})


async def settings(request):
    # noVNC stores settings per origin; prevent a previous app's host/port or
    # resize preference from connecting elsewhere or resizing the HDMI screen.
    return web.json_response({'host': '', 'port': 0, 'path': 'websockify',
                              'resize': 'scale', 'shared': True})


async def websocket(request):
    state = request.app[STATE]
    process = state.get('process')
    if process is None or process.returncode is not None or not state.get('vnc_port'):
        raise web.HTTPServiceUnavailable(text='Vzdálená plocha není připravena.')
    if len(state['sessions']) >= 4:
        raise web.HTTPTooManyRequests(text='Nejvýše čtyři vzdálená spojení.')
    ws = web.WebSocketResponse(protocols=('binary',), heartbeat=30,
                               max_msg_size=4 * 1024 * 1024, compress=False)
    state['sessions'].add(ws)
    writer = None
    tasks = []
    try:
        # Target is chosen by our own x11vnc child, never by a URL parameter.
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection('127.0.0.1', state['vnc_port']), timeout=5)
        await ws.prepare(request)

        async def from_vnc():
            while data := await reader.read(65536):
                await ws.send_bytes(data)

        async def to_vnc():
            async for message in ws:
                if message.type == WSMsgType.BINARY:
                    writer.write(message.data)
                    await writer.drain()
                elif message.type == WSMsgType.TEXT:
                    await ws.close(code=1003, message=b'Binary VNC frames only')
                    break
                else:
                    break

        tasks = [asyncio.create_task(from_vnc()), asyncio.create_task(to_vnc())]
        done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    except (OSError, TimeoutError):
        if not ws.prepared:
            raise web.HTTPServiceUnavailable(text='Vzdálená plocha není dostupná.')
    finally:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        if writer:
            writer.close()
            with suppress(OSError):
                await writer.wait_closed()
        if ws.prepared:
            await ws.close()
        state['sessions'].discard(ws)
    return ws


async def vnc_lifecycle(app):
    state = app[STATE]
    process = None
    try:
        if state['enabled']:
            # -no6 is essential: -listen only controls IPv4 in x11vnc.
            # No public VNC listener and no saved password for ingress mode.
            process = await asyncio.create_subprocess_exec(
                'x11vnc', '-norc', '-display', ':0', '-listen', '127.0.0.1',
                '-no6', '-autoport', '15900', '-forever', '-shared', '-nopw',
                '-noremote', '-nocmds', '-quiet', '-desktop', 'STELAB Remote',
                stdout=asyncio.subprocess.PIPE)
            state['process'] = process
            # PORT is emitted only after x11vnc has actually started listening.
            async with asyncio.timeout(20):
                while line := await process.stdout.readline():
                    if line.startswith(b'PORT='):
                        port = int(line.strip().split(b'=', 1)[1])
                        if not 1024 <= port <= 65535:
                            raise RuntimeError('Invalid x11vnc port')
                        state['vnc_port'] = port
                        break
                else:
                    raise RuntimeError('x11vnc exited before becoming ready')
        yield
    finally:
        if process and process.returncode is None:
            process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=3)
            except TimeoutError:
                process.kill()
                await process.wait()


async def shutdown(app):
    await asyncio.gather(*(ws.close(code=1001, message=b'Kiosk stopping')
                           for ws in tuple(app[STATE]['sessions'])))


def create_app(enabled=False, static_root=Path('/usr/share/novnc')):
    app = web.Application(middlewares=[ingress_only])
    app[STATE] = {'enabled': enabled, 'process': None, 'sessions': set()}
    app.cleanup_ctx.append(vnc_lifecycle)
    app.on_shutdown.append(shutdown)
    app.router.add_get('/', index)
    app.router.add_get('/mandatory.json', settings)
    app.router.add_get('/websockify', websocket)
    # Do not follow arbitrary links outside the packaged, public noVNC assets.
    app.router.add_static('/', static_root, show_index=False, follow_symlinks=False)
    return app


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, required=True)
    parser.add_argument('--enabled', action='store_true')
    args = parser.parse_args()
    if not 62000 <= args.port <= 65500:
        parser.error('Expected a Supervisor-assigned ingress port')
    web.run_app(create_app(args.enabled), host='0.0.0.0', port=args.port,
                access_log=None, shutdown_timeout=3)
