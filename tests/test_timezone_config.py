import importlib.util
from pathlib import Path
import tempfile
import unittest

ADDON = Path(__file__).resolve().parents[1] / 'stelab-kiosk'
spec = importlib.util.spec_from_file_location('timezone_config', ADDON/'timezone_config.py')
timezone = importlib.util.module_from_spec(spec)
spec.loader.exec_module(timezone)


class LocalTimezone(unittest.TestCase):
    def test_sets_container_files_only(self):
        with tempfile.TemporaryDirectory() as folder:
            etc = Path(folder)
            (etc/'localtime').symlink_to('/usr/share/zoneinfo/Etc/UTC')
            timezone.configure('Europe/Prague', etc=etc)
            self.assertEqual((etc/'localtime').resolve(), Path('/usr/share/zoneinfo/Europe/Prague'))
            self.assertEqual((etc/'timezone').read_text(), 'Europe/Prague\n')
            self.assertEqual(sorted(p.name for p in etc.iterdir()), ['localtime','timezone'])

    def test_invalid_zone_cannot_replace_files(self):
        for name in ['/etc/passwd','../etc/passwd','not-a-timezone']:
            with tempfile.TemporaryDirectory() as folder:
                etc = Path(folder)
                (etc/'timezone').write_text('original')
                with self.assertRaises((ValueError,KeyError)):
                    timezone.configure(name, etc=etc)
                self.assertEqual((etc/'timezone').read_text(), 'original')
                self.assertFalse((etc/'localtime').exists())
