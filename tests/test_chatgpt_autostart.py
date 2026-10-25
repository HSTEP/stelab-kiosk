"""Exercise bounded startup without controlling any real desktop."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ADDON = Path(__file__).resolve().parents[1] / 'stelab-kiosk'
spec = importlib.util.spec_from_file_location('chatgpt_autostart', ADDON/'chatgpt_autostart.py')
auto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto)


class BackgroundStartup(unittest.TestCase):
    def test_late_window_is_minimized_once_without_raising_browser(self):
        app = Mock(); app.poll.return_value = None
        with patch.object(auto.subprocess, 'run', side_effect=[
            SimpleNamespace(stdout=''), SimpleNamespace(stdout='123\n'),
            SimpleNamespace(returncode=0)]) as run, patch.object(auto.time, 'sleep'):
            self.assertTrue(auto.minimize_initial_window(app))
        self.assertEqual(run.call_args_list[-1].args[0], ['xdotool','windowminimize','123'])
        self.assertEqual(run.call_count, 3)

    def test_failed_app_does_not_touch_other_windows(self):
        app = Mock(); app.poll.return_value = 1
        with patch.object(auto.subprocess, 'run') as run:
            self.assertFalse(auto.minimize_initial_window(app))
        run.assert_not_called()

    def test_timeout_is_bounded_and_does_not_kill_browser(self):
        app = Mock(); app.poll.return_value = None
        with patch.object(auto.time, 'monotonic', side_effect=[0, 91]), patch.object(auto.subprocess,'run') as run:
            self.assertFalse(auto.minimize_initial_window(app))
        run.assert_not_called()

    def test_launch_uses_the_fixed_privilege_dropping_launcher(self):
        with patch.object(auto.subprocess,'Popen') as launch, patch.object(auto,'minimize_initial_window') as minimize:
            auto.start()
        self.assertEqual(launch.call_args.args[0], ['/usr/local/bin/stelab-chatgpt'])
        minimize.assert_called_once_with(launch.return_value)

    def test_only_boot_path_launches_ai(self):
        run = (ADDON/'run.sh').read_text()
        self.assertEqual(run.count('python3 -u /chatgpt_autostart.py &'), 1)
        self.assertLess(run.index('/chatgpt_autostart.py &'), run.index('    BROWSER_STARTED=true'))
        self.assertNotIn('chatgpt_autostart', (ADDON/'stelab-desktop.sh').read_text())

if __name__ == '__main__':
    unittest.main()
