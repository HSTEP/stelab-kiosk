"""Check the official ARM64 desktop app under Xvfb without signing in."""
import os
from pathlib import Path
import signal
import subprocess
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
        processes = []
        for directory in Path('/proc').iterdir():
            if not directory.name.isdecimal():
                continue
            try:
                argv = (directory/'cmdline').read_bytes().split(b'\0')
                if not argv or argv[0] != b'/usr/lib/chatgpt/ChatGPT':
                    continue
                status = (directory/'status').read_text()
                uid = next(line for line in status.splitlines() if line.startswith('Uid:')).split()[1]
                assert uid == '1000', status
                env = (directory/'environ').read_bytes()
                assert b'SUPERVISOR_TOKEN=' not in env and b'HA_PASSWORD=' not in env
                assert b'--no-sandbox' not in argv
                processes.append(directory.name)
            except FileNotFoundError:
                continue
        assert processes, 'No official ChatGPT process found'
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
