# STELAB Kiosk

A local touchscreen dashboard and lightweight desktop for **Home Assistant OS on Raspberry Pi 5 (64-bit)**. Connect a display directly to the Pi running Home Assistant: Chromium opens your chosen dashboard, while an autohiding taskbar gives access to running applications, a terminal and a file manager.

> **1.0 preparation:** This branch is a release candidate, not yet a tested public release. Use the published version from the default branch until the 1.0 image and installation have been verified.

## Why STELAB Kiosk?

- Fullscreen Chromium dashboard, optional touchscreen keyboard, rotation and reconnect-aware touch mapping.
- A usable Openbox desktop with an autohiding taskbar, browser, terminal and file manager; you can switch between open applications without losing the dashboard.
- Optional official ChatGPT desktop application. It is **not included in the base image** and is downloaded only when explicitly enabled; the dashboard does not wait for the download. You can enable background startup separately. The vendor package is pinned and verified by SHA-256 and architecture.
- Optional remote view of the same desktop through authenticated Home Assistant Ingress; disabled by default.
- Optional display timeout that detects visible, playing HTML video. Hidden/offscreen browser windows are suspended while the display is off to reduce unnecessary rendering.
- Persistent browser login, application home, desktop configuration and an optional custom wallpaper.
- GPU rendering using the existing Pi 5 V3D/Mesa stack was observed on the author's device. Hardware **video decoding** depends on the codec, browser and hardware and is not guaranteed.

This project builds on [WeLizard HAOS-kiosk](https://github.com/WeLizard/HAOS-kiosk), itself derived from [HAOS-kiosk](https://github.com/puterboy/HAOS-kiosk). It is independent of Home Assistant and OpenAI.

## Install

In Home Assistant OS open **Settings → Apps → App Store → ⋮ → Repositories** and add:

```text
https://github.com/HSTEP/stelab-kiosk
```

Install **STELAB Kiosk**, set your dashboard path, stop any other HDMI kiosk, and start the app. To start after a reboot or power interruption, enable **Start on boot** in the app's Info page. Other architectures are not currently supported. A connected keyboard/mouse can be paired through the host's supported Bluetooth setup; Apple-specific or Matter hardware is not required.

## Options

| Setting | Purpose | New-install default |
| --- | --- | --- |
| `ha_url`, `ha_dashboard` | Home Assistant address and dashboard path | local HA, default dashboard |
| `dashboard_fullscreen` | Open the dashboard in fullscreen | on |
| `chatgpt_install` | Download/install official ChatGPT into persistent app storage | off |
| `chatgpt_autostart` | Install if needed and start ChatGPT minimized | off |
| `wallpaper_file` | PNG/JPEG/WebP path in `/share` or `/media` | retain existing/default |
| `screen_timeout` | Seconds of inactivity before display turns off; 0 disables | 0 |
| `video_aware_screen_timeout` | Keep screen on while supported HTML video is visibly playing | on |
| `remote_access` | Remote desktop through HA Ingress | off |

After changing app configuration, restart the app. The pinned ChatGPT download is approximately **535 MB** and needs at least **3 GB free** for installation; its extracted size exceeds 1.7 GB. It is downloaded from the vendor and kept in app storage; a failed download does not stop the dashboard. Signing into the application is separate from your HA account. An existing user's saved `chatgpt_autostart: true` requests the optional installation automatically after upgrading; existing app home/projects are not removed.

To use a wallpaper, put an image in HA's `/share` or `/media` folder, enter its full path (for example `/share/wallpaper.png`) and restart. Leaving the option blank retains the current desktop configuration. This controls the desktop wallpaper, not the background of an individual HA dashboard.

CPU and RAM depend heavily on the dashboard, video, screen state and other open applications. One short Pi 5 test of a visible dashboard measured roughly **7% of total four-core CPU**, but this is not an idle guarantee or a comparison benchmark. Measure on your own configuration; no broadly representative RAM figure is claimed.

## Security and privacy

The app requires direct display/input access, host networking, audio and `SYS_ADMIN` to operate on HAOS. Review `stelab-kiosk/config.yaml` before installing. Chromium uses its sandbox under a dedicated user. ChatGPT, when installed, uses a separate user and persistent home; the launcher clears HA/Supervisor credentials from its inherited environment. Apps running inside the desktop can still access the network and files their user can read; review their own privacy terms and permissions. Remote access is off by default. The configurable legacy LAN VNC and network-exposed REST API require particular care; prefer authenticated HA Ingress.

Back up the app's persistent data, including browser and ChatGPT profiles, projects and desktop settings. Never post credentials, personal URLs or private data in public logs or screenshots.

## Feedback and development

[Report a bug or request a feature](https://github.com/HSTEP/stelab-kiosk/issues/new/choose), or [share your experience in Discussions](https://github.com/HSTEP/stelab-kiosk/discussions). Please include versions and hardware details, and remove passwords, tokens, personal URLs and IP addresses from logs. [Source and verification notes](SOURCE.md) · [Detailed technical documentation](stelab-kiosk/DOCS.md) · [Changelog](stelab-kiosk/CHANGELOG.md).

The source is GPL-2.0; upstream copyright and licence notices are retained. The optional vendor application is distributed separately under its own terms.
