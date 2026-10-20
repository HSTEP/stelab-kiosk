"""Run only in a disposable candidate container with Xvfb installed, not on HA."""
import asyncio
import importlib.util
import ipaddress
import os
from pathlib import Path
import struct
import subprocess
import time

from aiohttp.test_utils import TestClient, TestServer

spec = importlib.util.spec_from_file_location('remote_access', '/remote_access.py')
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)


async def main():
    assert str(remote.SUPERVISOR_IP) == '172.30.32.2'
    # Production has no flag/env override for the trusted peer. Change it only
    # inside this disposable smoke test to simulate the Supervisor connection.
    remote.SUPERVISOR_IP = ipaddress.ip_address('127.0.0.1')
    app = remote.create_app(True)
    async with TestClient(TestServer(app)) as client:
        response = await client.get('/')
        assert response.status == 200 and 'noVNC' in await response.text()
        for path in ('/core/rfb.js', '/app/ui.js', '/vendor/pako/lib/zlib/inflate.js'):
            response = await client.get(path)
            assert response.status == 200, path
        response = await client.get('/mandatory.json')
        assert (await response.json())['resize'] == 'scale'
        port = app[remote.STATE]['vnc_port']
        listeners = []
        for table in ('/proc/net/tcp', '/proc/net/tcp6'):
            for line in Path(table).read_text().splitlines()[1:]:
                fields = line.split()
                address, hexport = fields[1].split(':')
                if int(hexport, 16) == port and fields[3] == '0A':
                    listeners.append(address)
        assert listeners == ['0100007F'], listeners  # IPv4 loopback only
        async with client.ws_connect('/websockify', protocols=('binary',)) as ws:
            buffer = bytearray()

            async def read_exact(size):
                while len(buffer) < size:
                    buffer.extend(await ws.receive_bytes(timeout=5))
                data = bytes(buffer[:size])
                del buffer[:size]
                return data

            assert (await read_exact(12)).startswith(b'RFB ')
            await ws.send_bytes(b'RFB 003.008\n')
            count = (await read_exact(1))[0]
            security_types = await read_exact(count)
            assert 1 in security_types
            await ws.send_bytes(b'\x01')
            assert await read_exact(4) == b'\x00\x00\x00\x00'
            await ws.send_bytes(b'\x01')  # Shared desktop
            info = await read_exact(24)
            width, height = struct.unpack('>HH', info[:4])
            assert (width, height) == (320, 240), (width, height)
            name = await read_exact(struct.unpack('>I', info[20:24])[0])
            assert b'STELAB Remote' in name
            await ws.send_bytes(struct.pack('>BBHH', 5, 0, 42, 51))  # Pointer move
            for _ in range(30):
                location = subprocess.check_output(['xdotool', 'getmouselocation', '--shell'], text=True)
                if 'X=42\nY=51\n' in location:
                    break
                await asyncio.sleep(.1)
            else:
                raise AssertionError(location)
        process = app[remote.STATE]['process']
    assert process.returncode is not None
    print('PASS: packaged noVNC assets, loopback-only x11vnc, real RFB handshake, pointer input, cleanup')


if __name__ == '__main__':
    # This process/container has no host devices and never starts /run.sh.
    os.environ['DISPLAY'] = ':0'
    xvfb = subprocess.Popen(['Xvfb', ':0', '-screen', '0', '320x240x24', '-nolisten', 'tcp'])
    try:
        for _ in range(50):
            if subprocess.run(['xdpyinfo'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(.1)
        else:
            raise RuntimeError('Xvfb did not start')
        asyncio.run(main())
    finally:
        xvfb.terminate()
        xvfb.wait(timeout=5)
