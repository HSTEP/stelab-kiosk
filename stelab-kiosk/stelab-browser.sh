#!/bin/sh
set -eu
# The root desktop reads its reviewed argv, then drops to the kiosk user.
exec python3 /kiosk_browser.py
