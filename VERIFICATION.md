# Ověření 2026-10-20

Prošlo:
- Parsování všech dodaných a upravených Python souborů se syntaxí Python 3.13.
- bash -n pro start, desktop, zkratky a opětovné otevření prohlížeče.
- Konzistence VERSION/config.yaml/build.yaml/Dockerfile a všech lokálních COPY.
- Parsování YAML manifestů, překladů a obou GitHub Actions workflow.
- Parsování XML menu a vložených Openbox keybinds; bez duplicit v nových zkratkách.
- Sedm testů fullscreen rozhodování s náhradami X11 příkazů: show/hide v obou
  stavech, terminál jako aktivní okno, chybějící Chromium, neplatný příkaz.
- Porovnání se vstupním archivem: pole BROWSER_FLAGS, xorg.conf.default a blok
  volby PulseAudio sinku zachovány beze změny.
- Zveřejněný HA ARM64 Debian base tag trixie-2026.10.0 ověřen v GHCR webu.

Neprovedeno:
- Publikování GHCR obrazu a ověření anonymního pull.
- Test knihovny VT na Linuxu, start Xorgu, přihlášení, V3D renderer Chromia,
  HDMI audio, dotyk, reconnect Bluetooth, desktop a restart na Raspberry Pi 5.
- Formální validace kompletního manifestu Home Assistant Supervisorem.

GitHub Actions build #1 dokončen úspěšně za 7m 25s dne 2026-10-20.
URL: https://github.com/HSTEP/stelab-kiosk/actions/runs/39407259124
Sestavený runtime commit: fd25a26049b012f380885f49093bc0481ea4fe80.
Chromium: 155.0.8059.79, Debian GNU/Linux 13 (trixie).
Přítomnost /usr/lib/aarch64-linux-gnu/dri/v3d_dri.so ověřena během sestavení.
Artifact stelab-kiosk-arm64-0.1.0-rc.1 má přibližně 448 MB (uchování 7 dní).
Tím není potvrzeno spuštění na Raspberry Pi ani hardwarová akcelerace.

Zdrojový repozitář je veřejný. GHCR a hardware acceptance zatím neproběhly.
