# Release procedure

The repository is public. Prepare each release in a `release/*` branch, review all changes and scan the complete candidate for credentials and private user data before pushing. Never put profiles, Home Assistant configuration or tokens into the repository or an image.

1. Update `VERSION`, `stelab-kiosk/config.yaml`, Dockerfile build version and changelog together. Run source validation and the unit tests.
2. Dispatch the ARM64 **Check and build STELAB Kiosk** workflow for the candidate branch. It must build the image and run the Chromium, remote, desktop and optional ChatGPT installation smoke tests.
3. Test the candidate on real Pi 5 hardware, including clean install, upgrade from the previous version, profile and project persistence, fullscreen options, touch, audio, suspend/wake, remote access, optional application installation and custom wallpaper.
4. Publish a new immutable version using the manually dispatched GHCR release workflow. Verify an anonymous ARM64 pull. Do not overwrite an existing tag.
5. Only after the image is available, update the default branch manifest and release notes so Home Assistant cannot offer a version without an image. Describe measured CPU and memory only with their workload and methodology.
6. If a real donation URL is supplied by the owner, review it and add it before the public release; never invent an account or URL.

Third-party HAOS apps are added through **Settings → Apps → repositories**. The Home Assistant 2026.11 Marketplace catalog handles integrations, cards and similar extensions, not HAOS app repositories.
