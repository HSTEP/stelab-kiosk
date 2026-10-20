#!/bin/sh
set -eu
# Open only fixed tools. No evaluation of arbitrary command strings.
case "${1:-}" in
    terminal)
        cd /config/scripts
        exec env -u HA_PASSWORD -u HA_USERNAME -u SUPERVISOR_TOKEN -u HASSIO_TOKEN -u REST_BEARER_TOKEN -u VNC_SERVER xterm -T 'STELAB Terminal' -fa 'DejaVu Sans Mono' -fs 13 -e bash --noprofile
        ;;
    files) exec env -u HA_PASSWORD -u SUPERVISOR_TOKEN pcmanfm /config/files ;;
    editor) exec env -u HA_PASSWORD -u SUPERVISOR_TOKEN mousepad ;;
    shared) exec env -u HA_PASSWORD -u SUPERVISOR_TOKEN pcmanfm /share ;;
    dashboard)
        window=$(xdotool search --onlyvisible --class '^chromium$' 2>/dev/null | tail -n 1) || window=""
        if [ -n "$window" ]; then exec xdotool windowactivate --sync "$window"; fi
        exec /usr/local/bin/stelab-browser
        ;;
    *) echo 'Usage: stelab-desktop terminal|files|editor|shared|dashboard' >&2; exit 2 ;;
esac
