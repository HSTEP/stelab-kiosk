#!/bin/bash
set -eu
# This fixed launcher is the only root step. Never pass kiosk credentials or
# Supervisor tokens to the AI app or its command-running children.
AI_HOME=/config/chatgpt/home
AI_RUNTIME=/run/stelab-ai
test "$(id -u)" = 0
# Keep the parent root-owned: the AI user cannot replace home with a symlink.
for path in /config/chatgpt "$AI_HOME" "$AI_RUNTIME"; do
    if [ -L "$path" ]; then
        echo "Refusing symbolic link at AI home/runtime boundary" >&2
        exit 1
    fi
done
install -d -m 711 -o root -g root /config/chatgpt
install -d -m 700 -o stelab-ai -g stelab-ai "$AI_HOME" "$AI_RUNTIME"
if [ "${1:-}" = '--prepare' ]; then
    exit 0
fi
if [ "$#" -ne 0 ]; then
    echo 'Usage: stelab-chatgpt' >&2
    exit 2
fi
# Allow this local X11 user only; never grant access to all hosts/users.
xhost +SI:localuser:stelab-ai >/dev/null
exec runuser -u stelab-ai -- env -i \
    HOME="$AI_HOME" USER=stelab-ai LOGNAME=stelab-ai \
    PATH=/usr/local/bin:/usr/bin:/bin \
    DISPLAY=:0 XDG_RUNTIME_DIR="$AI_RUNTIME" \
    XDG_CONFIG_HOME="$AI_HOME/.config" XDG_CACHE_HOME="$AI_HOME/.cache" \
    XDG_DATA_HOME="$AI_HOME/.local/share" \
    TZ="${TZ:-Etc/UTC}" \
    LANG=C.UTF-8 BROWSER=/usr/local/bin/stelab-ai-browser \
    /usr/local/bin/stelab-ai-session
