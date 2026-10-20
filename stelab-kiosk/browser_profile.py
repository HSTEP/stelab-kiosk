"""Initialize Chromium once and close its own browser before stopping Xorg."""
from __future__ import annotations
import argparse
import asyncio
import json
import os
from pathlib import Path
import signal
import shlex
from urllib.parse import urlparse

DEFAULT_PREFERENCES = {
    'autofill': {'enabled': False},
    'browser': {'check_default_browser': False, 'has_seen_welcome_page': True},
    'credentials_enable_service': False,
    'distribution': {'skip_first_run_ui': True},
    'profile': {'default_content_setting_values': {'notifications': 2}, 'password_manager_enabled': False},
    'sync_promo': {'show_on_first_run_allowed': False},
    'translate': {'enabled': False},
}

def initialize_profile(profile: Path) -> bool:
    """Never replace an existing Preferences file, even if it is malformed."""
    default = profile / 'Default'
    default.mkdir(parents=True, exist_ok=True, mode=0o700)
    preferences = default / 'Preferences'
    try:
        with preferences.open('x', encoding='utf-8') as output:
            json.dump(DEFAULT_PREFERENCES, output, indent=2)
            output.write('\n')
        preferences.chmod(0o600)
        return True
    except FileExistsError:
        return False


def matching_browser(argv: list[str], profile: Path, port: int) -> bool:
    if not argv or Path(argv[0]).name not in {'chromium', 'chromium-browser'}:
        return False
    # Child renderers must be left to their browser during a graceful close.
    if any(arg.startswith('--type=') or arg == '--type' for arg in argv):
        return False
    def option(name: str) -> str | None:
        for i, arg in enumerate(argv):
            if arg.startswith(name + '='):
                return arg.split('=', 1)[1]
            if arg == name and i + 1 < len(argv):
                return argv[i + 1]
        return None
    directory = option('--user-data-dir')
    return bool(directory and os.path.abspath(directory) == os.path.abspath(profile)
                and option('--remote-debugging-port') == str(port))


def process_argv(raw: bytes) -> list[str]:
    argv = raw.rstrip(b'\0').decode().split('\0')
    # Chromium may rewrite argv[0] to the complete process title under D-Bus.
    # Decode only known executable prefixes; never evaluate a shell command.
    if len(argv) == 1 and argv[0].startswith(('/usr/lib/chromium/chromium ', '/usr/bin/chromium ')):
        return shlex.split(argv[0])
    return argv


def browser_pids(profile: Path, port: int) -> list[int]:
    found = []
    for process in Path('/proc').glob('[0-9]*'):
        try:
            argv = process_argv(process.joinpath('cmdline').read_bytes())
            if matching_browser(argv, profile, port):
                found.append(int(process.name))
        except (OSError, UnicodeError, ValueError):
            continue
    return found


def is_alive(pid: int) -> bool:
    try:
        # Treat a terminated, unreaped browser as done; do not wait on a zombie.
        status = Path(f'/proc/{pid}/stat').read_text().rsplit(')', 1)[1].split()[0]
        return status != 'Z'
    except (OSError, IndexError):
        return False


async def request_browser_close(port: int) -> None:
    from aiohttp import ClientSession, ClientTimeout
    async with ClientSession(timeout=ClientTimeout(total=3)) as session:
        async with session.get(f'http://127.0.0.1:{port}/json/version') as response:
            response.raise_for_status()
            endpoint = (await response.json())['webSocketDebuggerUrl']
        parsed = urlparse(endpoint)
        if parsed.scheme != 'ws' or parsed.hostname not in {'127.0.0.1', 'localhost'} or parsed.port != port:
            raise ValueError('Unexpected DevTools endpoint')
        async with session.ws_connect(endpoint) as websocket:
            await websocket.send_json({'id': 1, 'method': 'Browser.close'})
            # Delivery is not proof of shutdown; the caller waits for the process.
            try:
                await asyncio.wait_for(websocket.receive(), timeout=1)
            except (TimeoutError, ConnectionError):
                pass


async def wait_for_exit(pids: list[int], seconds: float) -> bool:
    end = asyncio.get_running_loop().time() + seconds
    while any(is_alive(pid) for pid in pids):
        if asyncio.get_running_loop().time() >= end:
            return False
        await asyncio.sleep(0.1)
    return True


async def close_browser(profile: Path, port: int, grace: float = 8, term_grace: float = 4) -> bool:
    # /proc is container-local. Never close another kiosk just because its port is open.
    pids = browser_pids(profile, port)
    if not pids:
        return True
    try:
        await request_browser_close(port)
    except Exception as error:
        print(f'Graceful DevTools close unavailable ({type(error).__name__}); using SIGTERM.', flush=True)
    if await wait_for_exit(pids, grace):
        print('Chromium exited before Xorg shutdown.', flush=True)
        return True
    for pid in pids:
        # Recheck ownership before signalling: do not act on a recycled PID.
        if pid in browser_pids(profile, port):
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    return await wait_for_exit(pids, term_grace)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['init', 'close'])
    parser.add_argument('--profile', type=Path, required=True)
    parser.add_argument('--port', type=int, default=9222)
    args = parser.parse_args()
    if args.action == 'init':
        created = initialize_profile(args.profile)
        print('New Chromium preferences initialized.' if created else 'Existing Chromium preferences preserved.')
    elif not asyncio.run(close_browser(args.profile, args.port)):
        print('Chromium did not finish saving before the shutdown deadline.', flush=True)
        raise SystemExit(1)

if __name__ == '__main__':
    main()
