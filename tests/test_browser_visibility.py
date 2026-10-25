import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

spec=importlib.util.spec_from_file_location('browser_visibility',Path(__file__).resolve().parents[1]/'stelab-kiosk/browser_visibility.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class Visibility(unittest.TestCase):
    def saver(self):
        s=m.BrowserWindowSaver.__new__(m.BrowserWindowSaver)
        s.d=Mock();s.root=Mock();s.root.get_full_property.return_value=SimpleNamespace(value=[99])
        s.hidden=[];s.focus=None;s.previous_on=None;s.windows=Mock(return_value=[101]);s.command=Mock()
        return s
    def test_off_hides_once_and_on_restores_prior_focus(self):
        s=self.saver();s.sync(False);s.sync(False)
        s.command.assert_called_once_with('windowminimize',101)
        s.sync(True)
        self.assertEqual([c.args for c in s.command.call_args_list],[('windowminimize',101),('windowmap','--sync',101),('windowactivate','--sync',99)])
        self.assertEqual(s.hidden,[])
    def test_empty_window_list_does_not_change_user_focus(self):
        s=self.saver();s.windows.return_value=[];s.sync(False);s.sync(True)
        s.command.assert_not_called()
    def test_close_restores_only_windows_hidden_by_controller(self):
        s=self.saver();s.sync(False);s.close()
        self.assertEqual(s.hidden,[]);s.d.close.assert_called_once()
