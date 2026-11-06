import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('installer', Path(__file__).resolve().parents[1] / 'stelab-kiosk/chatgpt_install.py')
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class Response(io.BytesIO):
    pass


class OptionalInstall(unittest.TestCase):
    def test_verified_download_is_extracted_and_activated(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = b'verified test package'
            def extract(command, check):
                launcher = Path(command[-1])/'usr/lib/chatgpt/codex-launcher'
                launcher.parent.mkdir(parents=True)
                launcher.write_text('test application')
            with patch.object(installer, 'ROOT', root), patch.object(installer, 'check_directory'), \
                 patch.object(installer, 'SHA256', hashlib.sha256(payload).hexdigest()), \
                 patch.object(installer.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 4_000_000_000})()), \
                 patch.object(installer.urllib.request, 'urlopen', return_value=Response(payload)), \
                 patch.object(installer.subprocess, 'check_output', side_effect=['arm64', installer.VERSION]), \
                 patch.object(installer.subprocess, 'run', side_effect=extract):
                installer.install()
            self.assertEqual((root/'current/usr/lib/chatgpt/codex-launcher').read_text(), 'test application')

    def test_checksum_failure_never_publishes_runtime(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(installer, 'ROOT', root), patch.object(installer, 'check_directory'), \
                 patch.object(installer.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 4_000_000_000})()), \
                 patch.object(installer.urllib.request, 'urlopen', return_value=Response(b'wrong bytes')):
                with self.assertRaisesRegex(RuntimeError, 'checksum'):
                    installer.install()
            self.assertFalse((root/'current').exists())

    def test_existing_package_does_not_download_or_touch_user_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            launcher = root/installer.VERSION/'usr/lib/chatgpt/codex-launcher'
            launcher.parent.mkdir(parents=True)
            launcher.write_text('existing')
            with patch.object(installer, 'ROOT', root), patch.object(installer, 'check_directory'), \
                 patch.object(installer.urllib.request, 'urlopen') as download:
                installer.install()
            download.assert_not_called()
            self.assertEqual((root/'current').resolve(), root/installer.VERSION)
            self.assertEqual(launcher.read_text(), 'existing')

    def test_low_disk_refuses_download(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(installer, 'ROOT', root), patch.object(installer, 'check_directory'), \
                 patch.object(installer.shutil, 'disk_usage', return_value=type('Disk', (), {'free': 1})()), \
                 patch.object(installer.urllib.request, 'urlopen') as download:
                with self.assertRaisesRegex(RuntimeError, 'free storage'):
                    installer.install()
            download.assert_not_called()


if __name__ == '__main__':
    unittest.main()
