#!/bin/sh
# Run the optional interactive launcher under a PTY on unattended starts.
set -eu

export STELAB_AGY_LAUNCHER="${1:?Missing Antigravity launcher}"
umask 077
pty_input=$(mktemp -d)
trap 'rm -f "$pty_input/input"; rmdir "$pty_input"' EXIT

# Keep stdin open without a long-lived feeder process.
mkfifo "$pty_input/input"
exec 3<>"$pty_input/input"
script -qefc 'exec "$STELAB_AGY_LAUNCHER" --continue' /dev/null <&3 >/dev/null
