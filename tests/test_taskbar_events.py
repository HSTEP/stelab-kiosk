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

    def test_destroyed_panel_during_delayed_unmap_does_not_crash(self):
        root = Mock(); d = Mock(); panel = Mock()
        bad_window = taskbar.error.BadWindow.__new__(taskbar.error.BadWindow)
        panel.get_attributes.side_effect = bad_window
        with unittest.mock.patch.object(taskbar, 'find_panel', return_value=None) as lookup:
            self.assertIsNone(taskbar.recover_unmapped(d, root, panel, 123))
            lookup.assert_called_once_with(d, root, 123)

    def test_unmapped_panel_is_mapped_and_raised(self):
        root = Mock(); d = Mock(); panel = Mock()
        panel.get_attributes.return_value = SimpleNamespace(map_state=X.IsUnmapped)
        self.assertIs(taskbar.recover_unmapped(d, root, panel, 123),panel)
        panel.map.assert_called_once_with()
        panel.configure.assert_called_once_with(stack_mode=X.Above)
        d.flush.assert_called_once_with()
