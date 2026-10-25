# 0.1.0-rc.8

- Fix high CPU caused by repeated Openbox stacking notifications and taskbar raises.
- Ignore unchanged window properties and never raise an already-topmost taskbar.
- Wait for full window-manager release and recover if the taskbar is re-managed
  or recreated after display/startup changes.
- Retain the rc.7 timezone fix, background ChatGPT, profiles and autohiding taskbar.

# 0.1.0-rc.7

- Preserve Supervisor's TZ in the isolated ChatGPT and Chromium environments,
  including child tools. No system clock changes; DST follows the HA timezone.
- Configure container /etc/localtime from Supervisor TZ for apps that discard TZ;
  never adjust the host clock.
- Add a lightweight autohiding bottom taskbar with minimized apps, fixed launchers
  and a local clock; retain its user configuration across updates.
- Start ChatGPT once per add-on boot and minimize its initial window, leaving
  the configured fullscreen HA dashboard in front. Optional chatgpt_autostart
  defaults to true; browser restarts do not relaunch the AI app.
- Update the pinned official ARM64 ChatGPT package to 26.1021.22027, verified
  against the signed OpenAI package index and SHA256 during image build.
- Rebuild Chromium and Debian dependencies from current Trixie/security packages.
- Preserve persistent profiles, user files, dashboard URL, GPU and sandbox settings.

# 0.1.0-rc.6

- Ship video-aware display idle control in the image: configurable screen_timeout,
  visible advancing HTML video detection, pause/stop grace period and manual-off priority.
- Wait for touchscreen evdev readiness before Xorg probes devices, and retry mapping
  late/reconnected direct-touch devices by capabilities rather than product names.
- Keep hardware permissions unchanged; report unreadable evdev nodes instead of
  requesting full device access. Physical cold-start acceptance is still required.
- Preserve HA navigation/theme settings without repeated reloads on route changes.

# 0.1.0-rc.5

- Run kiosk Chromium as dedicated UID1001 with its native sandbox enabled.
- Install Debian chromium-sandbox and remove the legacy --no-sandbox flag.
- Preserve /config/chromium-profile while migrating ownership; keep GPU argv.
- Keep a separate persistent browser home and a credential-free environment.
- Retain mapped DRM device access and system PulseAudio connection.
- Recognize Chromium's rewritten process title so graceful shutdown flushes
  cookies before the display is stopped. Do not select child renderers.
- Add a real root-to-user cookie/localStorage migration and sandbox test.
- Native ARM64 image build and all integration tests passed before publication;
  the same migration/sandbox test also passed directly on HAOS in isolation.

# 0.1.0-rc.4

- Add a static green/cyan STELAB wallpaper and a PCManFM desktop with launchers
  for Dashboard, Web, ChatGPT, Files, Terminal, Shared files and Text editor.
- Add Command+M and an Openbox menu item to reveal/hide the desktop while
  preserving all running application windows and existing shortcuts.
- Seed desktop settings, icon files/positions and wallpaper in /config/desktop
  only when missing; keep user changes over restarts and image updates.
- Use the existing PCManFM, a private D-Bus session and a credential-scrubbed
  environment. Keep AI app permissions and Chromium GPU/profile settings intact.
- Native ARM64 build and real Xvfb desktop test passed, including wallpaper,
  desktop show/restore and preservation of user files. Pi hardware acceptance
  remains required after updating.

# 0.1.0-rc.3

- Add optional same-screen noVNC through Home Assistant Ingress / STELAB Remote.
- Keep remote control disabled by default; admin sidebar panel, Supervisor-only
  HTTP/WebSocket gateway, loopback-only private x11vnc with IPv6 disabled.
- Preserve the HA ingress path with relative assets and WebSocket URLs; force
  local scaling so reconnecting does not resize the physical HDMI display.
- Add gateway rejection/bridge tests and a disposable Xvfb + real RFB handshake
  and pointer input test before publishing. No new Cloudflare subscription.
- Add pinned official ChatGPT ARM64 app, a non-root desktop launcher, persistent
  AI home/projects, clean credential-free process environment and Command+G.
- Verify the actual ChatGPT window under Xvfb before publishing.
- Keep Chromium profile persistence, GPU flags and the original backup intact.

# 0.1.0-rc.2

- Preserve existing Chromium Preferences, Local State, cookies, site storage,
  service workers and bookmarks. Initialize a new profile only once.
- Run the kiosk as an S6 service so shutdown precedes the container-wide kill.
- Request graceful Browser.close before stopping Xorg, with bounded SIGTERM
  fallback restricted to the current container's browser/profile/debug port.
- Allow TCP TIME_WAIT after restart without bypassing a real port conflict.
- Include the missing AT-SPI Python typelib for Onboard; remove the unused
  Debian menu reference. Existing graphics/input/audio settings are retained.
- Build and test directly on a native ARM64 GitHub runner.
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
