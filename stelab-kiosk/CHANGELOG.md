# 0.1.0-rc.2

- Preserve existing Chromium Preferences, Local State, cookies, site storage,
  service workers and bookmarks. Initialize a new profile only once.
- Request graceful Browser.close before stopping Xorg, with bounded SIGTERM
  fallback restricted to the current container's browser/profile/debug port.
- Allow TCP TIME_WAIT after restart without bypassing a real port conflict.
- Include the missing AT-SPI Python typelib for Onboard; remove the unused
  Debian menu reference. Existing graphics/input/audio settings are retained.
- Test real persistent cookies and localStorage across two Chromium launches
  inside the built ARM64 image before an image is uploaded or published.

Google website login must still be verified on the user's device after updating.
This does not enable proprietary Google Chrome Sync in Chromium.

# 0.1.0-rc.1

First experimental STELAB release candidate, based on the supplied functioning
Welizard Browser Custom 1.3.1-welizard.8-local1 source.

- Debian 13 Trixie, ARM64, Chromium and Mesa from supported Debian repositories.
- Openbox desktop with xterm, PCManFM, Mousepad and persistent script/file folders.
- Preserve local Chromium GPU flags, DRI3 modesetting and PulseAudio path.
- Preserve Command+Down/Up and add desktop shortcuts; target Chromium when a
  terminal has focus, leaving already correct fullscreen state unchanged.
- Mount host udev data read-only; use Welizard Debian Xorg-only VT preload
  instead of remounting /dev and deleting tty nodes.
- Manual start by default, conflict checks on the old kiosk's common ports.
- Test-build and manual GHCR workflows. No scheduled automatic releases.

Container build and Raspberry Pi 5 hardware acceptance are pending.
