#!/usr/bin/env python3
"""Set the container's local timezone; never set the host/system clock."""
import os
from pathlib import Path
import tempfile
from zoneinfo import ZoneInfo


def configure(name, etc=Path('/etc'), zones=Path('/usr/share/zoneinfo')):
    ZoneInfo(name)  # Reject unknown names, absolute paths and path traversal.
    target = (zones / name).resolve(strict=True)
    if not target.is_relative_to(zones.resolve()) or not target.is_file():
        raise ValueError('Invalid timezone file')
    descriptor, temporary = tempfile.mkstemp(prefix='.stelab-localtime-', dir=etc)
    os.close(descriptor)
    temporary = Path(temporary)
    try:
        temporary.unlink()
        temporary.symlink_to(target)
        temporary.replace(etc / 'localtime')
    finally:
        temporary.unlink(missing_ok=True)
    (etc / 'timezone').write_text(name + '\n')


def main():
    try:
        name = os.environ.get('TZ') or 'Etc/UTC'
        configure(name)
        print(f'Container local timezone: {name}', flush=True)
    except (OSError, ValueError, KeyError) as error:
        # An immutable /etc mount must not prevent HA's kiosk from starting.
        print(f'Could not configure container timezone ({type(error).__name__}); using TZ environment', flush=True)


if __name__ == '__main__':
    main()
