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
