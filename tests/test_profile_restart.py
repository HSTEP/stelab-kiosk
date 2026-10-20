import asyncio
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import AsyncMock, patch

ADDON = Path(__file__).resolve().parents[1] / 'stelab-kiosk'
def load(name):
    spec = importlib.util.spec_from_file_location(name, ADDON / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
profile = load('browser_profile')
ports = load('startup_ports')

class ProfileTests(unittest.TestCase):
    def test_existing_profile_and_auth_files_remain_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            data = {
                'Default/Preferences': b'{"profile":{"name":"My profile"},"browser":{"custom":true}}\n',
                'Local State': b'{"os_crypt":{"encrypted_key":"test-key"}}',
                'Default/Network/Cookies': b'test cookie database',
                'Default/Local Storage/leveldb/test.ldb': b'test local storage',
                'Default/Service Worker/test': b'test service worker',
                'Default/Bookmarks': b'test bookmarks',
            }
            for name, content in data.items():
                target = root / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(content)
            self.assertFalse(profile.initialize_profile(root))
            self.assertFalse(profile.initialize_profile(root))
            for name, content in data.items():
                self.assertEqual((root/name).read_bytes(), content, name)

    def test_new_profile_is_seeded_once_and_keeps_later_edits(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertTrue(profile.initialize_profile(root))
            settings = root/'Default/Preferences'
            custom = json.loads(settings.read_text())
            custom['homepage'] = 'https://example.com/'
            settings.write_text(json.dumps(custom))
            self.assertFalse(profile.initialize_profile(root))
            self.assertEqual(json.loads(settings.read_text()), custom)

    def test_unreadable_preferences_are_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/'Default').mkdir()
            settings = root/'Default/Preferences'
            settings.write_bytes(b'not valid json')
            self.assertFalse(profile.initialize_profile(root))
            self.assertEqual(settings.read_bytes(), b'not valid json')

    def test_only_browser_with_our_profile_and_port_is_owned(self):
        argv = ['/usr/lib/chromium/chromium', '--user-data-dir=/config/chromium-profile', '--remote-debugging-port=9222']
        self.assertTrue(profile.matching_browser(argv, Path('/config/chromium-profile'), 9222))
        self.assertFalse(profile.matching_browser(argv, Path('/other-profile'), 9222))
        self.assertFalse(profile.matching_browser(argv, Path('/config/chromium-profile'), 9223))
        self.assertFalse(profile.matching_browser(argv + ['--type=renderer'], Path('/config/chromium-profile'), 9222))

class ShutdownTests(unittest.IsolatedAsyncioTestCase):
    async def test_unowned_debug_port_is_never_closed(self):
        with patch.object(profile, 'browser_pids', return_value=[]), patch.object(profile, 'request_browser_close', new_callable=AsyncMock) as close:
            self.assertTrue(await profile.close_browser(Path('/test'), 9222))
            close.assert_not_called()

    async def test_clean_exit_does_not_send_signals(self):
        with patch.object(profile, 'browser_pids', return_value=[123]), patch.object(profile, 'request_browser_close', new_callable=AsyncMock) as close, patch.object(profile, 'wait_for_exit', new_callable=AsyncMock, return_value=True), patch.object(profile.os, 'kill') as kill:
            self.assertTrue(await profile.close_browser(Path('/test'), 9222))
            close.assert_awaited_once_with(9222)
            kill.assert_not_called()

    async def test_stuck_owned_browser_gets_term_after_grace_period(self):
        with patch.object(profile, 'browser_pids', return_value=[123]), patch.object(profile, 'request_browser_close', new_callable=AsyncMock), patch.object(profile, 'wait_for_exit', new_callable=AsyncMock, side_effect=[False, True]), patch.object(profile.os, 'kill') as kill:
            self.assertTrue(await profile.close_browser(Path('/test'), 9222))
            kill.assert_called_once_with(123, profile.signal.SIGTERM)

class PortTests(unittest.TestCase):
    def test_real_listener_is_rejected_even_with_reuseaddr(self):
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('127.0.0.1', 0))
            server.listen()
            self.assertEqual(ports.check_ports([server.getsockname()[1]], timeout=0), [server.getsockname()[1]])

    def test_stopped_listener_with_time_wait_does_not_block_restart(self):
        with socket.socket() as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(('127.0.0.1', 0))
            port = server.getsockname()[1]
            server.listen()
            with socket.create_connection(('127.0.0.1', port)) as client:
                accepted, _ = server.accept()
                accepted.close()
                self.assertEqual(client.recv(1), b'')
        self.assertEqual(ports.check_ports([port], timeout=0), [])

if __name__ == '__main__': unittest.main()
