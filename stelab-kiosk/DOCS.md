# STELAB Kiosk — documentation

## Installation and startup

This app targets Home Assistant OS on Raspberry Pi 5, 64-bit. Stop other apps that use the same HDMI display before starting STELAB Kiosk. Set `ha_url` and `ha_dashboard` as needed. The Chromium profile and desktop configuration are stored in app data and retained across ordinary app upgrades. Enable **Start on boot** in the app Info page if you want automatic startup following a host restart.

`dashboard_fullscreen` controls fullscreen at startup. The desktop's Dashboard launcher brings the browser forward; Web opens a regular browser window. The autohiding taskbar appears when the pointer reaches the bottom edge. Touchscreen mapping can be adjusted with `map_touch_inputs`, `output_number`, and `rotate_display`.

## Optional ChatGPT application

New installations default to `chatgpt_install: false` and `chatgpt_autostart: false`; the basic image does not contain the large application. Enable `chatgpt_install` to download the pinned official ARM64 package, or enable `chatgpt_autostart` to install it if necessary and launch it minimized. Restart the app after changing settings. The first download is approximately 535 MB; allow at least 3 GB of free space for download and extraction. A failed download leaves the dashboard available and is reported in the app log. The installer checks the package's SHA-256, architecture and version before activation; it does not execute the package's maintainer scripts.

The app runs as a separate non-root user with a cleared environment and persistent home in `/config/chatgpt/home`; its login and projects are not removed by app upgrades. The runtime is stored under `/config/stelab-chatgpt-runtime`. Updating to a newer vendor package requires a future STELAB Kiosk release. ChatGPT and its online features require a working internet connection and are subject to the vendor's terms.

## Wallpaper

Put a PNG, JPEG or WebP file under Home Assistant's `/share` or `/media`, set `wallpaper_file` to its full path, and restart the app. An empty option keeps the current desktop wallpaper. An invalid path leaves the current wallpaper unchanged and prints a message in the log. This does not alter any dashboard's background.

## Display and remote access

`screen_timeout: 0` keeps the screen on. When a timeout is configured, `video_aware_screen_timeout` can keep the display awake for visible, advancing HTML video; manual display-off requests retain priority. The timeout is not a guarantee for every streaming website or embedded player.

`remote_access` is off by default. When enabled, it exposes the same desktop through authenticated HA Ingress, not a separate desktop session. The older `vnc_server` setting exposes a separate LAN service and should be protected; `-` disables its password. REST is bound to loopback by default. Exposing it to the network or weakening its authentication has security consequences.

The app requires direct hardware access, host networking and `SYS_ADMIN`; review the manifest and install only if you trust it. Bluetooth peripherals are paired by the host's supported mechanism, not by a built-in Matter or Apple-specific pairing flow.

## Troubleshooting and reporting

- Inspect the app log for an unavailable display/input device, invalid wallpaper or failed optional installation.
- For browser GPU rendering, check `chrome://gpu`; a working V3D renderer does **not** prove every video codec is hardware decoded.
- Back up the app data before troubleshooting. Avoid posting passwords, tokens, private URLs or personal information in logs or screenshots.
- Report reproducible problems and hardware details through GitHub Issues; general experiences are welcome in GitHub Discussions.

Hardware support and CPU/RAM use vary by display, dashboard, drivers and running applications. See the root README for measured examples and the current tested scope.
