#!/bin/bash
set -eu
# This fixed launcher is the only root step. Never pass kiosk credentials or
# Supervisor tokens to the AI app or its command-running children.
AI_HOME=/config/chatgpt/home
AI_RUNTIME=/run/stelab-ai
install -d -m 700 -o stelab-ai -g stelab-ai /config/chatgpt "$AI_HOME" "$AI_RUNTIME"
install -d -m 700 -o stelab-ai -g stelab-ai "$AI_HOME/projects" "$AI_HOME/.config" "$AI_HOME/.cache" "$AI_HOME/.local/share"
if [ ! -f "$AI_HOME/.config/mimeapps.list" ]; then
    install -m 600 -o stelab-ai -g stelab-ai /usr/share/stelab-ai-mimeapps.list "$AI_HOME/.config/mimeapps.list"
fi
if [ "${1:-}" = '--prepare' ]; then
    exit 0
fi
if [ "$#" -ne 0 ]; then
    echo 'Usage: stelab-chatgpt' >&2
    exit 2
fi
# Allow this local X11 user only; never grant access to all hosts/users.
xhost +SI:localuser:stelab-ai >/dev/null
cd "$AI_HOME/projects"
exec runuser -u stelab-ai -- env -i \
    HOME="$AI_HOME" USER=stelab-ai LOGNAME=stelab-ai \
    PATH=/usr/local/bin:/usr/bin:/bin \
    DISPLAY=:0 XDG_RUNTIME_DIR="$AI_RUNTIME" \
    XDG_CONFIG_HOME="$AI_HOME/.config" XDG_CACHE_HOME="$AI_HOME/.cache" \
    XDG_DATA_HOME="$AI_HOME/.local/share" \
    LANG=C.UTF-8 BROWSER=/usr/local/bin/stelab-ai-browser \
    dbus-run-session -- chatgpt --ozone-platform=x11 \
    >> "$AI_HOME/chatgpt.log" 2>&1
