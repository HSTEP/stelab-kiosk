#!/bin/sh
set -eu
# Authentication opens in this user's browser, not the root kiosk profile.
exec chromium --ozone-platform=x11 --user-data-dir="$HOME/.config/auth-browser" "$@"
