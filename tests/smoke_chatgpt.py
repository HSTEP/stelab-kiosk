"""Check the official ARM64 desktop app under Xvfb without signing in."""
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time


def wait_for(check, timeout=45):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = check()
        if value:
            return value
        time.sleep(.25)
    raise AssertionError('Timed out waiting for ChatGPT desktop')


if __name__ == '__main__':
    os.environ['DISPLAY'] = ':0'
    xvfb = subprocess.Popen(['Xvfb', ':0', '-screen', '0', '1024x768x24', '-nolisten', 'tcp'])
    app = None
    try:
        wait_for(lambda: subprocess.run(['xdpyinfo'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0)
        subprocess.run(['/usr/local/bin/stelab-chatgpt', '--prepare'], check=True)
        home = Path('/config/chatgpt/home')
        # The root preparation intentionally never descends into user paths.
        assert home.parent.stat().st_uid == 0
        assert home.parent.stat().st_mode & 0o022 == 0
        with tempfile.TemporaryDirectory() as guard:
            config_link = home/'.config'
            config_link.symlink_to(guard, target_is_directory=True)
            subprocess.run(['/usr/local/bin/stelab-chatgpt', '--prepare'], check=True)
            assert Path(guard).stat().st_uid == 0, 'Root preparation followed a user-controlled symlink'
            config_link.unlink()
        subprocess.run(['runuser', '-u', 'stelab-ai', '--', 'mkdir', '-p', str(home/'projects')], check=True)
        marker = home/'projects/persistence-check.txt'
        marker.write_text('do not replace existing work')
        subprocess.run(['/usr/local/bin/stelab-chatgpt', '--prepare'], check=True)
        assert marker.read_text() == 'do not replace existing work'
        assert home.stat().st_uid == 1000 and home.stat().st_mode & 0o777 == 0o700
        environment = dict(os.environ, SUPERVISOR_TOKEN='test-secret-not-real', HA_PASSWORD='test-secret-not-real')
        app = subprocess.Popen(['/usr/local/bin/stelab-chatgpt'], env=environment, start_new_session=True)

        def window_ready():
            if app.poll() is not None:
                raise AssertionError('ChatGPT exited:\n' + (home/'chatgpt.log').read_text()[-6000:])
            result = subprocess.run(['xdotool', 'search', '--onlyvisible', '--class', '([Cc]hat[Gg][Pp][Tt]|[Cc]odex)'],
                                    capture_output=True, text=True)
            return result.stdout.strip()

        wait_for(window_ready, timeout=60)
        # Electron can replace argv[0] with its application title. Inspect the
        # executable as the owning user (root in a Docker container need not
        # have CAP_SYS_PTRACE for reading another UID's /proc entries).
        inspect = r"""
import json
from pathlib import Path
records = []
for directory in Path('/proc').iterdir():
    if not directory.name.isdecimal():
        continue
    try:
        executable = (directory/'exe').readlink()
        if str(executable) != '/usr/lib/chatgpt/ChatGPT':
            continue
        argv = (directory/'cmdline').read_bytes().split(b'\0')
        env = (directory/'environ').read_bytes()
        uid = next(line for line in (directory/'status').read_text().splitlines() if line.startswith('Uid:')).split()[1]
        records.append({'uid': uid, 'no_sandbox': b'--no-sandbox' in argv,
                        'has_secrets': b'SUPERVISOR_TOKEN=' in env or b'HA_PASSWORD=' in env})
    except (FileNotFoundError, PermissionError):
        continue
print(json.dumps(records))
"""
        processes = json.loads(subprocess.check_output(
            ['runuser', '-u', 'stelab-ai', '--', 'python3', '-c', inspect], text=True))
        assert processes, 'No official ChatGPT process found via /proc/exe'
        assert all(p['uid'] == '1000' and not p['has_secrets'] and not p['no_sandbox'] for p in processes), processes
        print('PASS: official ChatGPT window, non-root UID, clean environment, persistent home, sandbox not disabled')
    finally:
        if app and app.poll() is None:
            os.killpg(app.pid, signal.SIGTERM)
            try:
                app.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(app.pid, signal.SIGKILL)
                app.wait()
        xvfb.terminate()
        xvfb.wait(timeout=5)
