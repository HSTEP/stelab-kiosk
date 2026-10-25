#!/usr/bin/env python3
"""Stop hidden-screen rendering by minimizing only this kiosk's browser windows."""
import logging
from pathlib import Path
import pwd
import subprocess
from Xlib import X, display, error

LOG = logging.getLogger('display_idle')


class BrowserWindowSaver:
    def __init__(self, user_id=None, connection=None):
        self.user_id = pwd.getpwnam('stelab-browser').pw_uid if user_id is None else user_id
        self.d = connection or display.Display()
        self.root = self.d.screen().root
        self.hidden = []
        self.focus = None
        self.previous_on = None

    def windows(self):
        clients = self.root.get_full_property(self.d.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
        for identifier in clients.value if clients is not None else []:
            w = self.d.create_resource_object('window', int(identifier))
            try:
                classes = w.get_wm_class() or ()
                pid = w.get_full_property(self.d.intern_atom('_NET_WM_PID'), X.AnyPropertyType)
                if (any(c.lower() == 'chromium' for c in classes) and pid is not None
                        and Path(f'/proc/{int(pid.value[0])}').stat().st_uid == self.user_id
                        and w.get_attributes().map_state == X.IsViewable):
                    yield w.id
            except (error.BadWindow, OSError):
                continue

    @staticmethod
    def command(*args):
        subprocess.run(['xdotool', *map(str, args)], check=True,
                       timeout=3, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def sync(self, on):
        if self.previous_on == on:
            return
        if on:
            self.restore()
        else:
            active = self.root.get_full_property(self.d.intern_atom('_NET_ACTIVE_WINDOW'), X.AnyPropertyType)
            self.focus = int(active.value[0]) if active is not None and active.value[0] else None
            for identifier in self.windows():
                # Record first, so cleanup can restore even a partial operation.
                self.hidden.append(identifier)
                self.command('windowminimize', identifier)
            if self.hidden:
                LOG.info('Display off: suspended rendering of %s kiosk window(s)', len(self.hidden))
        self.previous_on = on

    def restore(self):
        restored = False
        for identifier in self.hidden:
            try:
                self.command('windowmap', '--sync', identifier)
                restored = True
            except (subprocess.SubprocessError, OSError):
                pass  # A browser window may have been closed while asleep.
        self.hidden = []
        if restored and self.focus:
            try:
                self.command('windowactivate', '--sync', self.focus)
            except (subprocess.SubprocessError, OSError):
                pass
        self.focus = None

    def close(self):
        self.restore()
        self.d.close()
