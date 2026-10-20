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
- Docker/Buildx sestavení (Docker není v tomto prostředí dostupný).
- Spuštění GitHub Actions a ověření reálného pull obrazu (repo nebylo zveřejněno).
- Test knihovny VT na Linuxu, start Xorgu, přihlášení, V3D renderer Chromia,
  HDMI audio, dotyk, reconnect Bluetooth, desktop a restart na Raspberry Pi 5.
- Formální validace kompletního manifestu Home Assistant Supervisorem.

Výsledek je připravený zdrojový release candidate, nikoliv ověřený instalační obraz.
