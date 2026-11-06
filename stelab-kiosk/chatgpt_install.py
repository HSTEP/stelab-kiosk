#!/usr/bin/env python3
"""Install the pinned official package on request, without blocking the kiosk."""
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import urllib.request

VERSION = '26.1029.61003'
SHA256 = '4719adfb33fe68e7becdb8169cea5945a297ebb7e3aa9966de7c2a945242bc2b'
URL = ('https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/'
       f'chatgpt/chatgpt_{VERSION}_arm64.deb')
ROOT = Path('/config/stelab-chatgpt-runtime')


def check_directory(root):
    if root.is_symlink():
        raise RuntimeError('Refusing a symlinked application directory')
    root.mkdir(mode=0o755, parents=True, exist_ok=True)
    if root.stat().st_uid != 0 or root.stat().st_mode & 0o022:
        raise RuntimeError('Application directory must be root-owned and not writable by other users')


def install():
    check_directory(ROOT)
    version_dir = ROOT / VERSION
    launcher = version_dir / 'usr/lib/chatgpt/codex-launcher'
    with (ROOT / '.install.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not launcher.is_file():
            if shutil.disk_usage(ROOT).free < 3_000_000_000:
                raise RuntimeError('At least 3 GB of free storage is needed for installation')
            with tempfile.TemporaryDirectory(prefix='.install-', dir=ROOT) as folder:
                temp = Path(folder)
                archive = temp / 'chatgpt.deb'
                digest = hashlib.sha256()
                # The vendor CDN rejects Python's default user agent.
                request = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0 STELAB-Kiosk/1.0'})
                with urllib.request.urlopen(request, timeout=60) as response, archive.open('wb') as out:
                    while True:
                        block = response.read(1024 * 1024)
                        if not block:
                            break
                        digest.update(block)
                        out.write(block)
                if digest.hexdigest() != SHA256:
                    raise RuntimeError('Official package checksum mismatch')
                for field, expected in [('Architecture', 'arm64'), ('Version', VERSION)]:
                    value = subprocess.check_output(['dpkg-deb', '-f', str(archive), field], text=True).strip()
                    if value != expected:
                        raise RuntimeError(f'Unexpected package {field}')
                unpacked = temp / 'unpacked'
                unpacked.mkdir(mode=0o755)
                subprocess.run(['dpkg-deb', '-x', str(archive), str(unpacked)], check=True)
                if not (unpacked / 'usr/lib/chatgpt/codex-launcher').is_file():
                    raise RuntimeError('Expected application launcher not found')
                if version_dir.exists():
                    raise RuntimeError('Incomplete version directory exists; manual inspection required')
                os.rename(unpacked, version_dir)
        link = ROOT / 'current'
        next_link = ROOT / '.current-new'
        next_link.unlink(missing_ok=True)
        next_link.symlink_to(VERSION, target_is_directory=True)
        os.replace(next_link, link)
    print(f'Official ChatGPT {VERSION} is ready', flush=True)


if __name__ == '__main__':
    try:
        install()
    except Exception as error:
        print(f'ChatGPT optional installation failed: {error}', file=sys.stderr, flush=True)
        sys.exit(1)
