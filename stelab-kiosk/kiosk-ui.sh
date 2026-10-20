#!/bin/sh
# Local fullscreen shortcuts, with the original F11 behavior.
set -eu
mode="${1:-}"
case "$mode" in show|hide) ;; *) echo "Usage: kiosk-ui show|hide" >&2; exit 2 ;; esac
window=$(xdotool getactivewindow 2>/dev/null) || window=""
if [ -z "$window" ] || ! xprop -id "$window" WM_CLASS 2>/dev/null | grep -qi '"chromium'; then
    window=$(xdotool search --onlyvisible --class '^chromium$' 2>/dev/null | tail -n 1) || window=""
fi
[ -n "$window" ] || { echo "No Chromium window" >&2; exit 1; }
state=$(xprop -id "$window" _NET_WM_STATE)
xdotool windowactivate --sync "$window"
case "$mode" in
    show) if echo "$state" | grep -q '_NET_WM_STATE_FULLSCREEN'; then xdotool key --clearmodifiers F11; fi ;;
    hide) if ! echo "$state" | grep -q '_NET_WM_STATE_FULLSCREEN'; then xdotool key --clearmodifiers F11; fi ;;
esac
