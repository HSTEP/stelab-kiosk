import asyncio
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from aiohttp import WSServerHandshakeError
from aiohttp.test_utils import TestClient, TestServer

ADDON = Path(__file__).resolve().parents[1] / 'stelab-kiosk'
spec = importlib.util.spec_from_file_location('remote_access', ADDON/'remote_access.py')
remote = importlib.util.module_from_spec(spec)
spec.loader.exec_module(remote)


class PeerTests(unittest.TestCase):
    def test_only_supervisor_transport_peer_is_trusted(self):
        self.assertTrue(remote.trusted_peer('172.30.32.2'))
        self.assertTrue(remote.trusted_peer('::ffff:172.30.32.2'))
        for peer in (None, '', '127.0.0.1', '::1', '172.30.32.3', '192.168.1.2', '172.30.32.2.evil'):
            self.assertFalse(remote.trusted_peer(peer), peer)


class GatewayTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)/'assets'
        self.root.mkdir()
        (self.root/'vnc.html').write_text('<html>packaged noVNC</html>')
        (self.root/'core').mkdir()
        (self.root/'core/rfb.js').write_text('// packaged module')
        self.app = remote.create_app(False, self.root)
        self.client = TestClient(TestServer(self.app))
        await self.client.start_server()

    async def asyncTearDown(self):
        await self.client.close()
        self.temp.cleanup()

    async def test_spoofed_headers_cannot_bypass_http_or_ws(self):
        headers = {'X-Forwarded-For': '172.30.32.2', 'X-Real-IP': '172.30.32.2',
                   'X-Remote-User-Id': 'admin', 'X-Ingress-Path': '/api/hassio_ingress/fake'}
        for path in ('/', '/vnc.html', '/mandatory.json', '/core/rfb.js', '/websockify'):
            response = await self.client.get(path, headers=headers)
            self.assertEqual(response.status, 403, path)
        with self.assertRaises(WSServerHandshakeError) as error:
            await self.client.ws_connect('/websockify', headers=headers)
        self.assertEqual(error.exception.status, 403)

    async def test_disabled_mode_never_connects_to_vnc(self):
        with patch.object(remote, 'trusted_peer', return_value=True):
            for path in ('/', '/vnc.html', '/websockify'):
                response = await self.client.get(path)
                self.assertEqual(response.status, 503)
        self.assertIsNone(self.app[remote.STATE]['process'])

    async def test_relative_redirect_assets_and_fixed_target_settings(self):
        self.app[remote.STATE]['enabled'] = True
        with patch.object(remote, 'trusted_peer', return_value=True):
            response = await self.client.get('/', allow_redirects=False)
            self.assertEqual(response.status, 302)
            self.assertTrue(response.headers['Location'].startswith('vnc.html?'))
            response = await self.client.get('/mandatory.json')
            settings = await response.json()
            self.assertEqual(settings['host'], '')
            self.assertEqual(settings['path'], 'websockify')
            self.assertEqual(settings['resize'], 'scale')
            response = await self.client.get('/core/rfb.js')
            self.assertEqual(response.status, 200)
            self.assertEqual(response.headers['Cache-Control'], 'no-store')

    async def test_symlinks_cannot_serve_profile_or_other_files(self):
        secret = Path(self.temp.name)/'secret'
        secret.write_text('not a public asset')
        (self.root/'leak').symlink_to(secret)
        self.app[remote.STATE]['enabled'] = True
        with patch.object(remote, 'trusted_peer', return_value=True):
            response = await self.client.get('/leak')
            self.assertEqual(response.status, 404)

    async def test_binary_bridge_roundtrip_and_disconnect_cleanup(self):
        async def vnc(reader, writer):
            try:
                writer.write(b'RFB 003.008\n')
                await writer.drain()
                writer.write(await reader.readexactly(12))
                await writer.drain()
            finally:
                writer.close()
                await writer.wait_closed()

        server = await asyncio.start_server(vnc, '127.0.0.1', 0)
        state = self.app[remote.STATE]
        state.update(enabled=True, process=SimpleNamespace(returncode=None),
                     vnc_port=server.sockets[0].getsockname()[1])
        try:
            with patch.object(remote, 'trusted_peer', return_value=True):
                ws = await self.client.ws_connect('/websockify?host=evil&port=1', protocols=('binary',))
                self.assertEqual(await ws.receive_bytes(timeout=2), b'RFB 003.008\n')
                await ws.send_bytes(b'RFB 003.008\n')
                self.assertEqual(await ws.receive_bytes(timeout=2), b'RFB 003.008\n')
                await ws.close()
            await self.client.close()
            self.assertEqual(state['sessions'], set())
        finally:
            server.close()
            await server.wait_closed()

    async def test_dead_owned_vnc_is_not_replaced_by_arbitrary_listener(self):
        self.app[remote.STATE].update(enabled=True, process=SimpleNamespace(returncode=1), vnc_port=15900)
        with patch.object(remote, 'trusted_peer', return_value=True):
            response = await self.client.get('/websockify')
            self.assertEqual(response.status, 503)


if __name__ == '__main__':
    unittest.main()
