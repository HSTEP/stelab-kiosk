#!/usr/bin/env python3
"""Persistent PCManFM desktop, seeded once and launched without HA credentials."""
import os
from pathlib import Path
import shutil
import sys

STATE = Path('/config/desktop')
ASSETS = Path('/usr/share/stelab-desktop')
LAUNCHERS = [
    ('01-dashboard', 'Dashboard', '/usr/local/bin/stelab-desktop dashboard', 'chromium'),
    ('02-web', 'Web', '/usr/local/bin/stelab-desktop web', 'chromium'),
    ('03-chatgpt', 'ChatGPT', '/usr/local/bin/stelab-chatgpt', '/usr/share/pixmaps/chatgpt.png'),
    ('04-files', 'Soubory', '/usr/local/bin/stelab-desktop files', 'system-file-manager'),
    ('05-terminal', 'Terminál', '/usr/local/bin/stelab-desktop terminal', 'utilities-terminal'),
    ('06-shared', 'Sdílené soubory', '/usr/local/bin/stelab-desktop shared', 'folder-remote'),
    ('07-editor', 'Textový editor', '/usr/local/bin/stelab-desktop editor', 'accessories-text-editor'),
]

def seed(path, content, mode=0o600):
    """Exclusive creation preserves user edits, including deliberate empty files."""
    try:
        with path.open('x') as f:
            f.write(content)
        path.chmod(mode)
    except FileExistsError:
        pass

def prepare():
    home = STATE / 'home'
    for directory in (STATE, home):
        if directory.is_symlink():
            raise RuntimeError(f'Refusing symbolic link: {directory}')
        directory.mkdir(mode=0o700, exist_ok=True)
        directory.chmod(0o700)
    desktop = home / 'Desktop'
    profile = home / '.config/pcmanfm/stelab'
    desktop.mkdir(exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    wallpaper = STATE / 'wallpaper.png'
    if not wallpaper.exists():
        # The directory is root-only; never overwrite a chosen wallpaper.
        shutil.copyfile(ASSETS / 'wallpaper.png', wallpaper)
    seed(home / '.config/user-dirs.dirs', f'XDG_DESKTOP_DIR="{desktop}"\n')
    seed(profile / 'desktop-items-0.conf', f'''[*]
wallpaper_mode=crop
wallpaper_common=1
wallpaper={wallpaper}
desktop_bg=#061421
desktop_fg=#e6fff8
desktop_shadow=#000000
desktop_font=DejaVu Sans 12
show_wm_menu=1
show_documents=0
show_trash=0
show_mounts=0
''')
    # Touch and mouse both open launchers with one click.
    libfm = home / '.config/libfm'
    libfm.mkdir(exist_ok=True)
    seed(libfm / 'libfm.conf', '[config]\nsingle_click=1\n')
    for slug, label, command, icon in LAUNCHERS:
        seed(desktop / f'{slug}.desktop', f'''[Desktop Entry]
Type=Application
Name={label}
Exec={command}
Icon={icon}
Terminal=false
StartupNotify=false
''', 0o700)
    applications = home / '.local/share/applications'
    applications.mkdir(parents=True, exist_ok=True)
    for slug, short in [('01-dashboard', 'dashboard'), ('02-web', 'web'), ('03-chatgpt', 'chatgpt')]:
        seed(applications / f'stelab-{short}.desktop', (desktop / f'{slug}.desktop').read_text(), 0o700)
    seed(STATE / 'tint2rc', (ASSETS / 'tint2rc').read_text())
    return home

def main():
    if len(sys.argv) != 2 or sys.argv[1] not in ('prepare', 'run', 'panel'):
        raise SystemExit('Usage: desktop_session.py prepare|run|panel')
    home = prepare()
    if sys.argv[1] == 'prepare':
        return
    env = {key: value for key, value in os.environ.items() if key not in {
        'HA_PASSWORD', 'HA_USERNAME', 'SUPERVISOR_TOKEN', 'HASSIO_TOKEN',
        'REST_BEARER_TOKEN', 'VNC_SERVER', 'DBUS_SESSION_BUS_ADDRESS',
    }}
    env.update(HOME=str(home), XDG_CONFIG_HOME=str(home / '.config'),
               XDG_CACHE_HOME=str(home / '.cache'),
               XDG_DATA_HOME=str(home / '.local/share'), LANG='C.UTF-8')
    if sys.argv[1] == 'panel':
        os.execvpe('tint2', ['tint2', '-c', str(STATE / 'tint2rc')], env)
    os.execvpe('dbus-run-session', ['dbus-run-session', '--', 'pcmanfm',
                                 '--desktop', '--profile=stelab'], env)

if __name__ == '__main__':
    main()
