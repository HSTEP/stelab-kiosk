"""Real legacy-to-sandboxed Chromium profile migration in a disposable container."""
import asyncio
import http.server
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
sys.path.insert(0, '/')
from browser_profile import initialize_profile, close_browser, browser_pids, process_argv
from browser_ctl import ChromiumController

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        if self.path == '/set':
            self.send_header('Set-Cookie', 'STELABAuth=preserved; Max-Age=86400; Path=/; SameSite=Lax')
            body = "<script>localStorage.setItem('STELABMigration','preserved')</script>READY"
        else:
            body = 'PRESERVED' if 'STELABAuth=preserved' in self.headers.get('Cookie', '') else 'MISSING'
        self.end_headers()
        self.wfile.write(body.encode())
    def log_message(self, *args):
        pass

async def evaluate(controller, expression, expected):
    for _ in range(100):
        try:
            value = await controller.evaluate(expression)
            if value.get('result', {}).get('value') == expected:
                return
        except Exception:
            pass
        await asyncio.sleep(.2)
    raise AssertionError(f'Browser did not return expected test value: {expected!r}')

async def test(origin):
    profile = Path('/config/chromium-profile')
    initialize_profile(profile)
    argv = ['chromium', '--no-first-run', '--password-store=basic',
            '--remote-debugging-address=127.0.0.1', '--remote-debugging-port=9222',
            f'--user-data-dir={profile}', '--ozone-platform=x11',
            '--use-gl=angle', '--use-angle=default']
    controller = ChromiumController(port=9222)
    for phase in ('legacy', 'migrated', 'restart'):
        if phase == 'restart':
            rollback_marker = profile / 'Default/LegacyRootMarker'
            rollback_marker.write_bytes(b'keep after legacy rollback')
            rollback_marker.chmod(0o600)
        log = open(f'/tmp/stelab-{phase}.log', 'w+')
        if phase == 'legacy':
            # Simulate rc.4, then migrate the SAME root-owned profile.
            command = [*argv, '--no-sandbox', origin + '/set']
        else:
            binary = [*argv, origin + '/check']
            Path('/tmp/stelab-browser.argv').write_bytes(b'\0'.join(x.encode() for x in binary) + b'\0')
            Path('/tmp/stelab-browser.argv').chmod(0o600)
            command = ['python3', '/kiosk_browser.py']
        process = subprocess.Popen(command, stdout=log, stderr=log)
        try:
            await evaluate(controller, 'document.body.innerText.trim()', 'READY' if phase == 'legacy' else 'PRESERVED')
            await evaluate(controller, "localStorage.getItem('STELABMigration')", 'preserved')
            if phase != 'legacy':
                matches = browser_pids(profile, 9222)
                assert matches, 'No real non-root browser found'
                for pid in matches:
                    p = Path(f'/proc/{pid}')
                    args = process_argv(p.joinpath('cmdline').read_bytes())
                    assert '--no-sandbox' not in args
                    uid = next(x for x in p.joinpath('status').read_text().splitlines() if x.startswith('Uid:')).split()[1]
                    assert uid == '1001', uid
                # Chromium's own diagnostic must report active renderer isolation.
                async def show_sandbox(page, target):
                    return await page.call('Page.navigate', {'url': 'chrome://sandbox'})
                await controller._with_page(show_sandbox)
                for _ in range(50):
                    result = await controller.evaluate('document.body.innerText')
                    text = result.get('result', {}).get('value', '')
                    if 'Seccomp' in text:
                        break
                    await asyncio.sleep(.1)
                assert 'Seccomp' in text and 'Yes' in text, text
                assert 'adequately sandboxed' in text, text
            if phase == 'restart':
                assert rollback_marker.read_bytes() == b'keep after legacy rollback'
                assert rollback_marker.stat().st_uid == 1001
            assert await close_browser(profile, 9222), 'Graceful close failed'
            process.wait(timeout=10)
            assert process.returncode == 0, process.returncode
        except Exception:
            log.seek(0)
            print(log.read()[-5000:], flush=True)
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=10)
            log.close()
    print('PASS: legacy root cookie/localStorage survived UID1001 migration and restart; real Chromium sandbox active; no --no-sandbox')

if __name__ == '__main__':
    os.environ['DISPLAY'] = ':0'
    xvfb = subprocess.Popen(['Xvfb', ':0', '-screen', '0', '1024x768x24', '-nolisten', 'tcp'])
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        for _ in range(50):
            if subprocess.run(['xdpyinfo'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
                break
            time.sleep(.1)
        asyncio.run(asyncio.wait_for(test(f'http://127.0.0.1:{server.server_port}'), timeout=120))
    finally:
        server.shutdown()
        xvfb.terminate()
        xvfb.wait(timeout=5)
