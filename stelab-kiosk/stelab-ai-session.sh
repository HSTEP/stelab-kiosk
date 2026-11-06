#!/bin/sh
set -eu
test "$(id -u)" = 1000
umask 077
# All operations below untrusted user home paths run as that user, never root.
mkdir -p "$HOME/projects" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"
if [ ! -e "$XDG_CONFIG_HOME/mimeapps.list" ]; then
    cp /usr/share/stelab-ai-mimeapps.list "$XDG_CONFIG_HOME/mimeapps.list"
fi
cd "$HOME/projects"
APP=/config/stelab-chatgpt-runtime/current/usr/lib/chatgpt/codex-launcher
if [ ! -x "$APP" ]; then
    echo 'ChatGPT is not installed; enable the optional installation in app settings.' >&2
    exit 1
fi
exec dbus-run-session -- "$APP" --ozone-platform=x11 >> "$HOME/chatgpt.log" 2>&1
