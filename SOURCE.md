# Source provenance

Runtime imported from the supplied welizard-browser.tar.gz (version
1.3.1-welizard.8-local1). Original copyright headers preserved.
Original run.sh SHA256: 3b85291d7f742d21216588d07686820bc4ae1f2fbbc0d34d7247e7bb2490f9bb.

VT compatibility library and GPLv2 license copied from WeLizard/HAOS-kiosk,
commit 308d0df858e9bff6b7a8dcf64f3c42008ab57a52, retrieved 2026-10-20.
https://github.com/WeLizard/HAOS-kiosk
Original project: https://github.com/puterboy/HAOS-kiosk (Jeff Kosowsky).

STELAB modifications 2026-10-20: Debian 13 build, desktop tools/menu,
manual boot, ARM64-only manifest, host udev mapping, Xorg-only VT preload
instead of deleting device nodes, startup port conflict check, targeted
fullscreen shortcuts, persistent script/file directories, build/release workflow.

The VT library is experimental on Pi 5 and unchanged from upstream. Native
VT mode is available for diagnosis. Neither is verified here on hardware.

0.1.0-rc.2: preserve profile startup data; S6 service plus owned-browser graceful
shutdown; restart-aware port preflight; Onboard AT-SPI typelib; native ARM64
builds and real Chromium persistence test. Original GPU flags retained.

## ChatGPT desktop package in rc.3

Official OpenAI ARM64 Debian package, version 26.1013.40934. Downloaded directly
from the vendor during image build, pinned SHA-256
`9ab2cbbaf33cebeaa1e06eb5cab78128936f927a0d97bf00e40694e5f31c629b`.
Vendor package contents and included copyright/license notices are preserved;
the application is a separate component, not relicensed as kiosk source.
Source URL: https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_26.1013.40934_arm64.deb
Setup documentation: https://learn.chatgpt.com/docs/linux/linux-app

## 0.1.0-rc.6
Image-owned idle/video controller, touchscreen startup readiness and hotplug mapping,
and the HA navigation/theme reload correction developed against the running Pi 5.
Original imported hashes above remain provenance, not current-file checksums.
