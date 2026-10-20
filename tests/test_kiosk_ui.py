"""Exercise fullscreen decisions with fake X11 tools, including desktop focus."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'stelab-kiosk/kiosk-ui.sh'

class FullscreenTests(unittest.TestCase):
    def invoke(self, mode, fullscreen=False, active='chromium', present=True):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            (folder/'xdotool').write_text('''#!/bin/sh
printf '%s\\n' "$*" >> "$CALL_LOG"
case "$1" in
 getactivewindow) echo 101 ;;
 search) [ "$PRESENT" = 1 ] && echo 202 || exit 1 ;;
esac
exit 0
''')
            (folder/'xprop').write_text('''#!/bin/sh
case "$3" in
 WM_CLASS) printf 'WM_CLASS = "%s"\\n' "$ACTIVE" ;;
 _NET_WM_STATE) if [ "$FULLSCREEN" = 1 ]; then echo '_NET_WM_STATE_FULLSCREEN'; else echo '_NET_WM_STATE ='; fi ;;
esac
''')
            for name in ['xdotool', 'xprop']: (folder/name).chmod(0o755)
            env = dict(os.environ, PATH=str(folder)+os.pathsep+os.environ['PATH'], CALL_LOG=str(folder/'calls'), FULLSCREEN=str(int(fullscreen)), ACTIVE=active, PRESENT=str(int(present)))
            result = subprocess.run(['sh', str(SCRIPT), mode], env=env, capture_output=True, text=True)
            calls = (folder/'calls').read_text() if (folder/'calls').exists() else ''
            return result.returncode, calls

    def test_show_leaves_visible_toolbar_alone(self):
        code, calls = self.invoke('show')
        self.assertEqual(code, 0)
        self.assertNotIn('key --clearmodifiers F11', calls)

    def test_hide_leaves_fullscreen_alone(self):
        code, calls = self.invoke('hide', fullscreen=True)
        self.assertEqual(code, 0)
        self.assertNotIn('key --clearmodifiers F11', calls)

    def test_show_exits_fullscreen(self):
        code, calls = self.invoke('show', fullscreen=True)
        self.assertEqual(code, 0)
        self.assertIn('key --clearmodifiers F11', calls)

    def test_hide_enters_fullscreen(self):
        code, calls = self.invoke('hide')
        self.assertEqual(code, 0)
        self.assertIn('key --clearmodifiers F11', calls)

    def test_terminal_focus_selects_chromium_before_f11(self):
        code, calls = self.invoke('hide', active='XTerm')
        self.assertEqual(code, 0)
        self.assertIn('windowactivate --sync 202', calls)
        self.assertLess(calls.index('windowactivate --sync 202'), calls.index('key --clearmodifiers F11'))

    def test_no_browser_does_not_send_f11_to_terminal(self):
        code, calls = self.invoke('hide', active='XTerm', present=False)
        self.assertNotEqual(code, 0)
        self.assertNotIn('key --clearmodifiers F11', calls)

    def test_bad_mode_does_not_control_any_window(self):
        code, calls = self.invoke('toggle')
        self.assertEqual(code, 2)
        self.assertEqual(calls, '')

if __name__ == '__main__': unittest.main()
