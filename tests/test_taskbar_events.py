"""Regression: duplicate WM notifications must not cause endless X11 raises."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock
from Xlib import X

spec = importlib.util.spec_from_file_location('taskbar_events', Path(__file__).resolve().parents[1]/'stelab-kiosk/taskbar_session.py')
taskbar = importlib.util.module_from_spec(spec);spec.loader.exec_module(taskbar)

class TaskbarEvents(unittest.TestCase):
    def test_duplicate_stacking_notifications_are_ignored(self):
        root = Mock(); root.get_full_property.return_value = SimpleNamespace(value=[11,22,33])
        snapshots = {}
        self.assertTrue(taskbar.property_changed(root, 99, snapshots))
        for _ in range(1000):
            self.assertFalse(taskbar.property_changed(root, 99, snapshots))
        root.get_full_property.return_value = SimpleNamespace(value=[22,11,33])
        self.assertTrue(taskbar.property_changed(root, 99, snapshots))

    def test_topmost_panel_is_not_raised_again(self):
        root = Mock(); panel = Mock(); panel.id = 33
        panel.get_attributes.return_value = SimpleNamespace(map_state=X.IsViewable)
        root.query_tree.return_value = SimpleNamespace(children=[Mock(),panel])
        self.assertFalse(taskbar.raise_if_covered(root,panel))
        panel.configure.assert_not_called()

    def test_covered_panel_is_raised_once(self):
        root = Mock(); panel = Mock(); panel.id = 33
        other = Mock(); other.id = 44
        other.get_attributes.return_value = SimpleNamespace(map_state=X.IsViewable)
        root.query_tree.return_value = SimpleNamespace(children=[panel,other])
        self.assertTrue(taskbar.raise_if_covered(root,panel))
        panel.configure.assert_called_once_with(stack_mode=X.Above)
