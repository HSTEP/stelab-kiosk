#!/usr/bin/env python3
"""Launch the AI app once at boot, leaving its first window minimized."""
import subprocess
import time

WINDOW_CLASS = '([Cc]hat[Gg][Pp][Tt]|[Cc]odex)'


def minimize_initial_window(app, timeout=90):
    """Stop after the first mapped app window; never touch later user windows."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if app.poll() is not None:
            print('ChatGPT autostart: launcher exited before a window appeared', flush=True)
            return False
        result = subprocess.run(
            ['xdotool', 'search', '--onlyvisible', '--class', WINDOW_CLASS],
            capture_output=True, text=True, timeout=5)
        windows = [line for line in result.stdout.splitlines() if line.isdecimal()]
        if windows:
            # Iconify rather than keeping an always-below rule: the user can
            # activate the app normally later, without fighting the dashboard.
            for window in windows:
                subprocess.run(['xdotool', 'windowminimize', window],
                               check=True, timeout=5)
            print('ChatGPT ready in background', flush=True)
            return True
        time.sleep(.25)
    print('ChatGPT autostart: window timeout; dashboard is unaffected', flush=True)
    return False


def start():
    # The fixed launcher drops privileges and scrubs credentials, as on manual
    # launch. A failure here must not stop or restart the dashboard.
    app = subprocess.Popen(['/usr/local/bin/stelab-chatgpt'], start_new_session=True)
    try:
        minimize_initial_window(app)
    except (OSError, subprocess.SubprocessError) as error:
        print(f'ChatGPT autostart: {type(error).__name__}; dashboard is unaffected', flush=True)
    return app


if __name__ == '__main__':
    start()
