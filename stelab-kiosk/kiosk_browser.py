#!/usr/bin/env python3
"""Launch the kiosk browser as its own user, keeping the existing profile path."""
import grp
import os
from pathlib import Path
import pwd
import stat
import subprocess
import sys

USER = 'stelab-browser'
HOME = Path('/config/chromium-home')
RUNTIME = Path('/run/stelab-browser')


def checked_directory(path):
    if not path.is_absolute() or '..' in path.parts:
        raise ValueError('Expected an absolute directory')
    for part in reversed([path, *path.parents]):
        if part.is_symlink():
            raise ValueError(f'Refusing symbolic link at {part}')
    path.mkdir(parents=True, exist_ok=True, mode=0o700)


def environment():
    env = {'HOME': str(HOME), 'USER': USER, 'LOGNAME': USER,
           'PATH': '/usr/local/bin:/usr/bin:/bin', 'LANG': 'C.UTF-8',
           'TZ': os.environ.get('TZ') or 'Etc/UTC',
           'DISPLAY': os.environ.get('DISPLAY', ':0'),
           'XDG_RUNTIME_DIR': str(RUNTIME),
           'XDG_CONFIG_HOME': str(HOME / '.config'),
           'XDG_CACHE_HOME': str(RUNTIME / 'cache'),
           'XDG_DATA_HOME': str(HOME / '.local/share')}
    # Preserve only the system audio connection, not HA credentials/session bus.
    for name in ('PULSE_SERVER', 'PULSE_COOKIE', 'PULSE_CLIENTCONFIG'):
        if name in os.environ:
            env[name] = os.environ[name]
    return env


def prepare(profile):
    if not profile.is_relative_to('/config') or profile == Path('/config'):
        raise ValueError('Kiosk profile must be below /config')
    account = pwd.getpwnam(USER)
    for path in (HOME, RUNTIME, profile):
        checked_directory(path)
        # Also repair root-created files after a rollback to a legacy image.
        # Never follow symbolic links or change files owned by another user.
        if path.stat().st_uid not in (0, account.pw_uid):
            raise ValueError(f'Unexpected owner of {path}')
        if path == profile or path.stat().st_uid == 0:
            subprocess.run(['chown', '-hR', '-P', '--from=0', f'{account.pw_uid}:{account.pw_gid}', '--', str(path)], check=True)
        if path.stat().st_uid != account.pw_uid:
            raise ValueError(f'Unexpected owner of {path}')
        path.chmod(0o700)
    # Device groups on HAOS can differ from Debian's group numbers.
    for device in Path('/dev/dri').glob('*'):
        info = device.stat()
        if not stat.S_ISCHR(info.st_mode) or (info.st_mode & 0o006) == 0o006:
            continue
        try:
            group = grp.getgrgid(info.st_gid).gr_name
        except KeyError:
            group = f'stelab-dri-{info.st_gid}'
            subprocess.run(['groupadd', '--gid', str(info.st_gid), group], check=True)
        subprocess.run(['usermod', '--append', '--groups', group, USER], check=True)
    subprocess.run(['runuser', '-u', USER, '--', 'env', '-i',
                    *[f'{k}={v}' for k, v in environment().items()],
                    'python3', '/browser_profile.py', 'init', '--profile', str(profile)], check=True)


def main():
    if os.getuid() != 0:
        raise SystemExit('Kiosk launcher must be called by the desktop service')
    if len(sys.argv) == 3 and sys.argv[1] == '--prepare':
        prepare(Path(sys.argv[2]))
        return
    if len(sys.argv) != 1:
        raise SystemExit('Usage: kiosk_browser.py [--prepare /config/profile]')
    argv = Path('/tmp/stelab-browser.argv').read_bytes().rstrip(b'\0').decode().split('\0')
    if not argv or argv[0] not in ('chromium', 'chromium-browser', '/usr/bin/chromium'):
        raise ValueError('Unexpected browser executable')
    if any(arg in ('--no-sandbox', '--disable-setuid-sandbox', '--disable-seccomp-filter-sandbox', '--single-process') for arg in argv):
        raise ValueError('Browser sandbox must stay enabled')
    directory = next(arg.split('=', 1)[1] for arg in argv if arg.startswith('--user-data-dir='))
    prepare(Path(directory))
    subprocess.run(['xhost', '+SI:localuser:' + USER], check=True, stdout=subprocess.DEVNULL)
    os.execvpe('/usr/sbin/runuser', ['runuser', '-u', USER, '--', 'dbus-run-session', '--', *argv], environment())

if __name__ == '__main__':
    main()
