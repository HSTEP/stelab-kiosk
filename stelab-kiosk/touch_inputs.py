#!/usr/bin/env python3
"""Wait for readable evdev touch nodes; map late/reconnected touch devices."""
import argparse
import logging
import os
from pathlib import Path
import re
import subprocess
import time

LOG = logging.getLogger('touch_inputs')

def touch_nodes(sysroot=Path('/sys/class/input'), udev=Path('/run/udev/data')):
    nodes = []
    for event in sysroot.glob('event*'):
        try:
            dev = (event/'dev').read_text().strip()
            props = (udev/('c'+dev)).read_text().splitlines()
            if 'E:ID_INPUT_TOUCHSCREEN=1' in props or 'E:ID_INPUT_TABLET=1' in props:
                nodes.append('/dev/input/'+event.name)
        except OSError:
            continue
    return sorted(nodes)

def readable(node):
    try:
        fd = os.open(node, os.O_RDONLY | os.O_NONBLOCK)
        os.close(fd)
        return True
    except OSError:
        return False

def wait_ready(timeout=20, settle=3, scan=touch_nodes, can_read=readable,
               clock=time.monotonic, sleep=time.sleep):
    deadline = clock()+timeout
    previous = None
    stable_since = clock()
    while True:
        nodes = scan()
        signature = tuple((n,can_read(n)) for n in nodes)
        now = clock()
        if signature != previous:
            previous, stable_since = signature, now
        if nodes and all(ok for _,ok in signature) and now-stable_since >= settle:
            LOG.info('Touch input ready: %s', ', '.join(nodes))
            return True
        if now >= deadline:
            LOG.warning('Touch startup wait ended; nodes=%s. Late devices will still be mapped. '
                        'Unreadable nodes require checking Supervisor hardware access.', signature)
            return False
        sleep(min(.5, deadline-now))

def command(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=5).stdout

def touch_ids(text):
    """Use XInput TouchClass capabilities, not a vendor's device name."""
    devices=[]
    current=None
    for line in text.splitlines():
        match=re.search(r'\bid=(\d+)\b.*\[slave\s+pointer',line)
        if match:current=match.group(1)
        elif re.search(r'\bid=\d+',line):current=None
        if current and 'Touch mode: direct' in line:
            devices.append(current)
            current=None
    return devices

def reconcile(output, mapped, run=command):
    text=run('xinput','--list','--long')
    current=set()
    for device in touch_ids(text):
        props=run('xinput','list-props',device)
        node=re.search(r'Device Node[^:]*:\s*"([^"]+)"',props)
        identity=(device,node.group(1) if node else '')
        current.add(identity)
        enabled=re.search(r'Device Enabled[^:]*:\s*(\d+)',props)
        if enabled and enabled.group(1)=='0':
            run('xinput','enable',device)
        if identity not in mapped or (enabled and enabled.group(1)=='0'):
            # Only remember success; retry failed mapping on the next pass.
            run('xinput','map-to-output',device,output)
            mapped.add(identity)
            LOG.info('Mapped touch device %s (%s) to %s',*identity,output)
    mapped.intersection_update(current)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('mode',choices=['wait','watch'])
    parser.add_argument('--output')
    args=parser.parse_args()
    if args.mode=='wait':
        wait_ready()
        return
    if not args.output:parser.error('watch requires --output')
    mapped=set()
    last_error=-float('inf')
    while True:
        try:reconcile(args.output,mapped)
        except (OSError,subprocess.SubprocessError) as err:
            if time.monotonic()-last_error>60:
                LOG.warning('Touch mapping retry: %s',type(err).__name__)
                last_error=time.monotonic()
        time.sleep(5)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO,format='[touch_inputs] %(message)s')
    main()
