#!/usr/bin/env python3
"""Keep the autohide edge reachable over Openbox fullscreen, without polling."""
import os
import select
import signal
import subprocess
import time
from Xlib import X, display, error


def find_panel(d, root, pid):
    clients = root.get_full_property(d.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
    for identifier in clients.value if clients is not None else []:
        window = d.create_resource_object('window', int(identifier))
        try:
            value = window.get_full_property(d.intern_atom('_NET_WM_PID'), X.AnyPropertyType)
            kinds = window.get_full_property(d.intern_atom('_NET_WM_WINDOW_TYPE'), X.AnyPropertyType)
            if (value is not None and int(value.value[0]) == pid and kinds is not None
                    and d.intern_atom('_NET_WM_WINDOW_TYPE_DOCK') in kinds.value):
                return window
        except error.BadWindow:
            pass
    return None


def make_overlay(d, root, panel):
    position = root.translate_coords(panel, 0, 0)
    panel.unmap()
    d.sync()
    # Give Openbox its UnmapNotify before remapping as an unmanaged dock.
    deadline = time.monotonic() + 2
    atom = d.intern_atom('_NET_CLIENT_LIST')
    while time.monotonic() < deadline:
        clients = root.get_full_property(atom, X.AnyPropertyType)
        if ((clients is None or panel.id not in clients.value)
                and panel.query_tree().parent.id == root.id):
            break
        time.sleep(.02)
    if panel.query_tree().parent.id != root.id:
        raise RuntimeError('Window manager did not release taskbar')
    panel.change_attributes(override_redirect=True)
    panel.reparent(root, position.x, position.y)
    panel.map()
    panel.configure(stack_mode=X.Above)
    d.sync()


def property_changed(root, atom, snapshots):
    """Openbox can announce an unchanged stack in response to a raise."""
    value = root.get_full_property(atom, X.AnyPropertyType)
    value = tuple(value.value) if value is not None else None
    changed = atom not in snapshots or snapshots[atom] != value
    snapshots[atom] = value
    return changed


def raise_if_covered(root, panel):
    # Raising an already-top window can itself provoke another WM notification.
    for window in reversed(root.query_tree().children):
        try:
            if window.get_attributes().map_state == X.IsViewable:
                if window.id != panel.id:
                    panel.configure(stack_mode=X.Above)
                    return True
                return False
        except error.BadWindow:
            continue
    return False


def main():
    app = subprocess.Popen(['tint2', '-c', '/config/desktop/tint2rc'])
    d = None
    pidfd = None
    def stop(_signum, _frame):
        raise SystemExit(0)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        d = display.Display()
        root = d.screen().root
        root.change_attributes(event_mask=X.PropertyChangeMask)
        deadline = time.monotonic() + 15
        panel = None
        while app.poll() is None and time.monotonic() < deadline:
            panel = find_panel(d, root, app.pid)
            if panel is not None:
                break
            select.select([d.fileno()], [], [], .1)
            while d.pending_events():
                d.next_event()
        if panel is None:
            raise RuntimeError('Taskbar window did not appear')
        make_overlay(d, root, panel)
        snapshots = {}
        watched = {d.intern_atom(name) for name in (
            '_NET_ACTIVE_WINDOW', '_NET_CLIENT_LIST_STACKING', '_NET_CURRENT_DESKTOP', '_NET_CLIENT_LIST')}
        for atom in watched:
            property_changed(root, atom, snapshots)
        try:
            pidfd = os.pidfd_open(app.pid)
        except (AttributeError, OSError):
            pass
        print('Autohide taskbar ready over fullscreen', flush=True)
        while app.poll() is None:
            # pidfd wakes on process exit; X11 wakes on a window event. The
            # fallback timer is used only on kernels without pidfd support.
            if not d.pending_events():
                select.select([d.fileno()] + ([pidfd] if pidfd is not None else []),
                              [], [], None if pidfd is not None else 5)
            changed_atoms = set()
            while d.pending_events():
                event = d.next_event()
                if event.type == X.PropertyNotify and event.atom in watched:
                    changed_atoms.add(event.atom)
            if changed_atoms:
                # Startup/output changes can re-manage or recreate tint2's
                # window. Repair the boundary once, rather than fighting WM.
                try:
                    unmanaged = panel.get_attributes().override_redirect
                except error.BadWindow:
                    panel = find_panel(d, root, app.pid)
                    unmanaged = False
                if panel is None:
                    continue
                if not unmanaged:
                    make_overlay(d, root, panel)
                changed = [property_changed(root, atom, snapshots) for atom in changed_atoms]
                if any(changed):
                    raise_if_covered(root, panel)
                    d.flush()
    finally:
        if pidfd is not None:
            os.close(pidfd)
        if app.poll() is None:
            app.terminate()
            try:
                app.wait(timeout=5)
            except subprocess.TimeoutExpired:
                app.kill(); app.wait()
        if d:
            d.close()


if __name__ == '__main__':
    main()
