"""Exercise the real PCManFM desktop only in a disposable Xvfb container."""
import importlib.util
import os
from pathlib import Path
import subprocess
import time
from Xlib import X, display


def wait_for(check, message):
    for _ in range(100):
        if check():
            return
        time.sleep(.1)
    raise AssertionError(message)


def main():
    os.environ['DISPLAY'] = ':0'
    xvfb = subprocess.Popen(['Xvfb', ':0', '-screen', '0', '1536x1024x24', '-nolisten', 'tcp'])
    desktop = None
    wm = None
    try:
        wait_for(lambda: subprocess.run(['xdpyinfo'], stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL).returncode == 0, 'Xvfb failed')
        wm = subprocess.Popen(['openbox'])
        subprocess.run(['python3', '/desktop_session.py', 'prepare'], check=True)
        state = Path('/config/desktop')
        home = state / 'home'
        spec = importlib.util.spec_from_file_location('desktop', '/desktop_session.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert len(list((home / 'Desktop').glob('*.desktop'))) == 7
        # User customizations and opaque login files must survive initialization.
        custom = home / 'Desktop/05-terminal.desktop'
        custom.write_text(custom.read_text() + '# user customization\n')
        credentials = [Path('/config/chromium-profile/Default/Cookies'),
                       Path('/config/chatgpt/home/.codex/auth.json')]
        for p in credentials:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b'opaque persistent auth sentinel\x00')
        taskbar = state / 'tint2rc'
        taskbar.write_text(taskbar.read_text() + '\n# user taskbar customization\n')
        before = {p: p.read_bytes() for p in [custom, taskbar, state / 'wallpaper.png', *credentials]}
        subprocess.run(['python3', '/desktop_session.py', 'prepare'], check=True)
        assert all(p.read_bytes() == data for p, data in before.items())
        desktop = subprocess.Popen(['python3', '/desktop_session.py', 'run'])
        d = display.Display()
        root = d.screen().root
        prop = d.intern_atom('_NET_WM_WINDOW_TYPE')
        kind = d.intern_atom('_NET_WM_WINDOW_TYPE_DESKTOP')
        found = []
        def find_desktop():
            clients = root.get_full_property(d.intern_atom('_NET_CLIENT_LIST'), X.AnyPropertyType)
            windows = ([d.create_resource_object('window', int(w)) for w in clients.value]
                       if clients is not None else root.query_tree().children)
            for w in windows:
                value = w.get_full_property(prop, X.AnyPropertyType)
                if value is not None and kind in value.value and w.get_attributes().map_state == X.IsViewable:
                    found[:] = [w]
                    return True
            return False
        wait_for(find_desktop, 'PCManFM did not create a visible desktop window')
        window = found[0]
        def wallpaper_drawn():
            # Right-side sample includes the green/blue circuit wallpaper, not icons.
            image = window.get_image(900, 250, 400, 400, X.ZPixmap, 0xffffffff)
            return image is not None and len(set(image.data)) > 32
        wait_for(wallpaper_drawn, 'Desktop remained blank instead of drawing wallpaper')
        subprocess.run(['wmctrl', '-k', 'on'], check=True)
        wait_for(lambda: root.get_full_property(d.intern_atom('_NET_SHOWING_DESKTOP'), X.AnyPropertyType).value[0] == 1,
                 'Openbox did not reveal desktop')
        subprocess.run(['wmctrl', '-k', 'off'], check=True)
        wait_for(lambda: root.get_full_property(d.intern_atom('_NET_SHOWING_DESKTOP'), X.AnyPropertyType).value[0] == 0,
                 'Openbox did not restore applications')
        d.close()
        print('PASS: real PCManFM desktop, rendered wallpaper, seven launchers, show/restore desktop, preserved customizations and opaque auth files')
    finally:
        if desktop is not None and desktop.poll() is None:
            subprocess.run(['pkill', '-TERM', '-x', 'pcmanfm'], check=False)
            desktop.wait(timeout=10)
        if wm is not None:
            wm.terminate()
            wm.wait(timeout=5)
        xvfb.terminate()
        xvfb.wait(timeout=5)

if __name__ == '__main__':
    main()
