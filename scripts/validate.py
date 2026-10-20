#!/usr/bin/env python3
"""Validate release consistency and source syntax without starting any kiosk."""
import ast
import json
from pathlib import Path
import re
import shlex
import subprocess
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
addon = root / 'stelab-kiosk'
config = json.loads((addon / 'config.yaml').read_text())
build = json.loads((addon / 'build.yaml').read_text())
version = (root / 'VERSION').read_text().strip()
assert re.fullmatch(r'\d+\.\d+\.\d+(?:-rc\.\d+)?', version)
assert config['version'] == version
assert config['slug'] == 'stelab_kiosk'
assert config['boot'] == 'manual'
assert config['arch'] == ['aarch64']
assert config['audio'] and config['udev']
assert config['ingress'] and config['ingress_port'] == 0
assert config['panel_admin'] and not config['options']['remote_access']
assert config['image'] == 'ghcr.io/hstep/stelab-kiosk-{arch}'
assert 'config:rw' not in config['map']
assert not config['options']['ha_password']
assert not config['options']['rest_bearer_token']
assert config['options']['rest_ip'] == '127.0.0.1'
assert config['options']['browser_engine'] == 'chromium'
assert set(config['options']) <= set(config['schema'])
base = build['build_from']['aarch64']
dockerfile = (addon / 'Dockerfile').read_text()
assert f'ARG BUILD_FROM={base}' in dockerfile
assert f'ARG BUILD_VERSION={version}' in dockerfile
for line in dockerfile.splitlines():
    if line.startswith('COPY ') and '--from=' not in line:
        for source in shlex.split(line)[1:-1]:
            assert (addon / source).exists(), source
for source in addon.glob('*.py'):
    ast.parse(source.read_text(), filename=str(source), feature_version=(3, 13))
for source in addon.glob('*.sh'):
    subprocess.run(['bash', '-n', str(source)], check=True)
ET.parse(addon / 'openbox-menu.xml')
run = (addon / 'run.sh').read_text()
keybinds = re.search(r"cat <<'EOF' > /tmp/new_keybinds.xml\n(.*?)\nEOF", run, re.S).group(1)
keyboard = ET.fromstring('<keyboard>' + keybinds + '</keyboard>')
keys = [node.attrib['key'] for node in keyboard]
assert len(keys) == len(set(keys))
assert {'W-Down', 'W-Up', 'W-Return', 'W-e', 'W-d'} <= set(keys)
assert '--start-fullscreen' in run and '\n                --kiosk\n' not in run
assert '--disable-gpu\n' not in run and '--use-angle=swiftshader' not in run
assert 'rm -f /dev/tty0' not in run and 'remount,rw /dev' not in run
# Schema keys added by STELAB are explained to the HA UI.
assert 'xorg_vt_mode:' in (addon / 'translations/en.yaml').read_text()
print(f'Source validation passed: {version}. This does not replace a container build or Pi 5 tests.')
