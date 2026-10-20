# STELAB Kiosk. Runtime derived from Jeff Kosowsky / Welizard; see LICENSE.
ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-debian:trixie-2026.10.0
FROM ${BUILD_FROM} AS vtbuild
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev
COPY tty0_override.c /tmp/tty0_override.c
RUN gcc -Wall -shared -fPIC -o /tmp/tty0_override.so /tmp/tty0_override.c -ldl

FROM ${BUILD_FROM}
ARG BUILD_VERSION=0.1.0-rc.3
ARG CHATGPT_VERSION=26.1013.40934
ARG CHATGPT_SHA256=9ab2cbbaf33cebeaa1e06eb5cab78128936f927a0d97bf00e40694e5f31c629b
ENV ADDON_VERSION=${BUILD_VERSION} DISPLAY=:0 \
    S6_SERVICES_GRACETIME=25000 S6_KILL_GRACETIME=15000
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash jq curl ca-certificates util-linux bsdextrautils procps iproute2 patch scrot \
    xserver-xorg-core xserver-xorg-input-libinput libinput-tools udev evtest \
    libgl1-mesa-dri libegl-mesa0 libgles2 libgl1 libdrm2 mesa-utils \
    xdotool x11-utils xinput x11-xserver-utils x11-xkb-utils libxkbcommon0 \
    openbox xterm pcmanfm mousepad dbus-x11 dconf-cli libglib2.0-bin \
    gsettings-desktop-schemas onboard at-spi2-core gir1.2-atspi-2.0 \
    unclutter-xfixes fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
    chromium pulseaudio-utils libasound2-plugins \
    python3 python3-xlib python3-aiohttp python3-venv git bubblewrap x11vnc novnc \
    && rm -rf /var/lib/apt/lists/*
# Pin the official vendor package, architecture and bytes for repeatable builds.
RUN curl -fSL --proto '=https' --tlsv1.2 --retry 3 \
      "https://persistent.oaistatic.com/codex-app-prod/linux/deb/pool/main/c/chatgpt/chatgpt_${CHATGPT_VERSION}_arm64.deb" \
      -o /tmp/chatgpt.deb \
    && echo "${CHATGPT_SHA256}  /tmp/chatgpt.deb" | sha256sum -c - \
    && test "$(dpkg-deb -f /tmp/chatgpt.deb Architecture)" = arm64 \
    && test "$(dpkg-deb -f /tmp/chatgpt.deb Version)" = "${CHATGPT_VERSION}" \
    && apt-get update && apt-get install -y --no-install-recommends /tmp/chatgpt.deb \
    && rm /tmp/chatgpt.deb && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 1000 --user-group --home-dir /config/chatgpt/home \
       --no-create-home --shell /bin/bash stelab-ai
COPY --from=vtbuild /tmp/tty0_override.so /usr/lib/tty0_override.so
COPY xorg.conf.default /etc/X11/xorg.conf.default
COPY translations/ /translations/
COPY browser_profile.py startup_ports.py remote_access.py /
COPY run.sh browser_ctl.py chromium_watchdog.py mouse_touch_inputs.py rest_server.py gesture_commands.json /
COPY s6-run.sh /etc/services.d/stelab/run
COPY kiosk-ui.sh /usr/local/bin/kiosk-ui
COPY stelab-browser.sh /usr/local/bin/stelab-browser
COPY stelab-desktop.sh /usr/local/bin/stelab-desktop
COPY stelab-chatgpt.sh /usr/local/bin/stelab-chatgpt
COPY stelab-ai-session.sh /usr/local/bin/stelab-ai-session
COPY stelab-ai-browser.sh /usr/local/bin/stelab-ai-browser
COPY stelab-ai-browser.desktop /usr/share/applications/stelab-ai-browser.desktop
COPY stelab-ai-mimeapps.list /usr/share/stelab-ai-mimeapps.list
COPY openbox-menu.xml /etc/xdg/openbox/stelab-menu.xml
RUN chmod 755 /etc/services.d/stelab/run /usr/local/bin/stelab-browser /run.sh /usr/local/bin/kiosk-ui /usr/local/bin/stelab-desktop /usr/local/bin/stelab-chatgpt /usr/local/bin/stelab-ai-session /usr/local/bin/stelab-ai-browser \
    && test -x /usr/lib/xorg/Xorg \
    && command -v bashio && command -v xprop && command -v xterm \
    && command -v pcmanfm && command -v mousepad && command -v onboard \
    && command -v chatgpt && command -v bwrap && command -v runuser \
    && python3 -c 'import aiohttp, Xlib' \
    && test -f /usr/share/novnc/vnc.html \
    && test -f /usr/share/novnc/core/rfb.js \
    && test -e /usr/lib/aarch64-linux-gnu/dri/v3d_dri.so \
    && chromium --version \
    && dpkg-query -W chromium libgl1-mesa-dri libegl-mesa0 chatgpt > /etc/stelab-build-packages.txt
LABEL io.hass.name="STELAB Kiosk" \
      io.hass.description="Chromium and lightweight Debian desktop for HAOS" \
      io.hass.type="addon" io.hass.arch="aarch64" \
      io.hass.version="${BUILD_VERSION}" \
      org.opencontainers.image.source="https://github.com/HSTEP/stelab-kiosk"
CMD []
