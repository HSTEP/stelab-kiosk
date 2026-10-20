#!/bin/bash
set -eu
# Null-delimited argv avoids shell evaluation of URLs and browser settings.
mapfile -d '' -t browser_argv < /tmp/stelab-browser.argv
[ "${#browser_argv[@]}" -gt 1 ] || exit 1
unset HA_PASSWORD HA_USERNAME SUPERVISOR_TOKEN HASSIO_TOKEN REST_BEARER_TOKEN VNC_SERVER
exec "${browser_argv[@]}"
