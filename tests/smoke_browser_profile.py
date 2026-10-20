"""Run only inside the built image: verify real cookies/storage across browser restart."""
import asyncio
import http.server
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
sys.path.insert(0, '/')
from browser_profile import initialize_profile, close_browser
from browser_ctl import ChromiumController

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        if self.path == '/set':
            self.send_header('Set-Cookie', 'STELABPersistence=present; Max-Age=86400; Path=/; SameSite=Lax')
            body = "<html><body>READY<script>localStorage.setItem('STELABStorage','present')</script></body></html>"
        else:
            found = 'STELABPersistence=present' in self.headers.get('Cookie', '')
            body = '<html><body>' + ('PERSISTED' if found else 'MISSING') + '</body></html>'
        self.end_headers()
        self.wfile.write(body.encode())
    def log_message(self, *args):
        pass

async def poll_evaluate(controller, expression, expected, timeout=45):
    end = asyncio.get_running_loop().time() + timeout
    last = 'No result yet'
    while asyncio.get_running_loop().time() < end:
        try:
            result = await controller.evaluate(expression)
            last = repr(result)
            if result.get('result', {}).get('value') == expected:
                return
        except Exception as error:
            last = f'{type(error).__name__}: {error}'
        await asyncio.sleep(0.3)
    raise AssertionError(f'Expected {expected!r}; last DevTools result: {last}')

async def test_browser(profile, port, origin):
    controller = ChromiumController(port=port)
    argv = ['chromium', '--headless=new', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage',
            '--no-first-run', '--password-store=basic', '--remote-debugging-address=127.0.0.1',
            f'--remote-debugging-port={port}', f'--user-data-dir={profile}']
    initialize_profile(profile)
    for page, expected in [('/set', 'READY'), ('/check', 'PERSISTED')]:
        if page == '/check':
            # Startup must preserve Chromium-written profile preferences and key state.
            settings = profile/'Default/Preferences'
            local_state = profile/'Local State'
            before = (settings.read_bytes(), local_state.read_bytes())
            assert not initialize_profile(profile)
            assert (settings.read_bytes(), local_state.read_bytes()) == before
        print(f'Checking browser launch: {page}', flush=True)
        log = tempfile.TemporaryFile(mode='w+t')
        process = subprocess.Popen(argv + [origin + page], stdout=log, stderr=log)
        try:
            await poll_evaluate(controller, 'document.body.innerText.trim()', expected)
            await poll_evaluate(controller, "localStorage.getItem('STELABStorage')", 'present')
            assert await close_browser(profile, port), 'Browser did not close gracefully'
            process.wait(timeout=10)
        except Exception:
            log.seek(0)
            print(log.read()[-5000:], flush=True)
            raise
        finally:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            log.close()
    print('Real Chromium persistence test passed: cookie, localStorage, Preferences and Local State survived restart.')

with tempfile.TemporaryDirectory(prefix='stelab-smoke-') as folder:
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    try:
        asyncio.run(asyncio.wait_for(test_browser(Path(folder), port, f'http://127.0.0.1:{server.server_port}'), timeout=120))
    finally:
        server.shutdown()
