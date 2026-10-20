# STELAB Kiosk. Runtime derived from Jeff Kosowsky / Welizard; see LICENSE.
ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-debian:trixie-2026.10.0
FROM ${BUILD_FROM} AS vtbuild
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev
COPY tty0_override.c /tmp/tty0_override.c
RUN gcc -Wall -shared -fPIC -o /tmp/tty0_override.so /tmp/tty0_override.c -ldl

FROM ${BUILD_FROM}
ARG BUILD_VERSION=0.1.0-rc.1
ENV ADDON_VERSION=${BUILD_VERSION} DISPLAY=:0
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash jq curl ca-certificates util-linux bsdextrautils procps iproute2 patch scrot \
    xserver-xorg-core xserver-xorg-input-libinput libinput-tools udev evtest \
    libgl1-mesa-dri libegl-mesa0 libgles2 libgl1 libdrm2 mesa-utils \
    xdotool x11-utils xinput x11-xserver-utils x11-xkb-utils libxkbcommon0 \
    openbox xterm pcmanfm mousepad dbus-x11 dconf-cli libglib2.0-bin \
    gsettings-desktop-schemas onboard at-spi2-core \
    unclutter-xfixes fonts-dejavu-core fonts-noto-core fonts-noto-color-emoji \
    chromium pulseaudio-utils libasound2-plugins \
    python3 python3-xlib python3-aiohttp x11vnc \
    && rm -rf /var/lib/apt/lists/*
COPY --from=vtbuild /tmp/tty0_override.so /usr/lib/tty0_override.so
COPY xorg.conf.default /etc/X11/xorg.conf.default
COPY translations/ /translations/
COPY run.sh browser_ctl.py chromium_watchdog.py mouse_touch_inputs.py rest_server.py gesture_commands.json /
COPY kiosk-ui.sh /usr/local/bin/kiosk-ui
COPY stelab-browser.sh /usr/local/bin/stelab-browser
COPY stelab-desktop.sh /usr/local/bin/stelab-desktop
COPY openbox-menu.xml /etc/xdg/openbox/stelab-menu.xml
RUN chmod 755 /usr/local/bin/stelab-browser /run.sh /usr/local/bin/kiosk-ui /usr/local/bin/stelab-desktop \
    && test -x /usr/lib/xorg/Xorg \
    && command -v bashio && command -v xprop && command -v xterm \
    && command -v pcmanfm && command -v mousepad && command -v onboard \
    && python3 -c 'import aiohttp, Xlib' \
    && test -e /usr/lib/aarch64-linux-gnu/dri/v3d_dri.so \
    && chromium --version \
    && dpkg-query -W chromium libgl1-mesa-dri libegl-mesa0 > /etc/stelab-build-packages.txt
LABEL io.hass.name="STELAB Kiosk" \
      io.hass.description="Chromium and lightweight Debian desktop for HAOS" \
      io.hass.type="addon" io.hass.arch="aarch64" \
      io.hass.version="${BUILD_VERSION}" \
      org.opencontainers.image.source="https://github.com/HSTEP/stelab-kiosk"
CMD ["/run.sh"]
