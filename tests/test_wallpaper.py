import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('desktop', Path(__file__).resolve().parents[1]/'stelab-kiosk/desktop_session.py')
desktop = importlib.util.module_from_spec(spec)
spec.loader.exec_module(desktop)

class Wallpaper(unittest.TestCase):
    def test_select_image_without_changing_other_preferences(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);share=root/'share';share.mkdir();image=share/'wall.jpg';image.write_bytes(b'jpeg')
            config=root/'desktop.conf';config.write_text('[*]\nwallpaper=old\nshow_trash=0\n')
            desktop.apply_wallpaper(str(image),config,[share])
            self.assertEqual(config.read_text(),f'[*]\nwallpaper={image}\nshow_trash=0\n')
    def test_reject_path_outside_share_even_through_symlink(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);share=root/'share';share.mkdir();image=root/'secret.png';image.write_text('x')
            (share/'link.png').symlink_to(image);config=root/'desktop.conf';config.write_text('wallpaper=old\n')
            with self.assertRaises(ValueError):desktop.apply_wallpaper(str(share/'link.png'),config,[share])
            self.assertEqual(config.read_text(),'wallpaper=old\n')

if __name__ == '__main__': unittest.main()
