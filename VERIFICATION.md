# Ověření kandidáta 0.1.0-rc.3 — 2026-10-20

- Lokální kontrola zdrojů prošla.
- 23 lokálních testů prošlo: původních 16 a sedm nových kontrol brány.
- Ověřeno odmítnutí cizí TCP adresy na HTTP i WebSocket cestách, i s podvrženými
  ingress/user/IP hlavičkami; vypnutý stav, statické soubory, odmítnutí symlinku
  mimo složku assets a obousměrný přenos binárních dat přes testovací TCP server.
- Produkční povolená adresa nemá přepínač ani proměnnou pro obejití ochrany.
- Nové CI kroky připravují jednorázový kontejner bez HA zařízení, přidají pouze
  do něj Xvfb a ověří skutečný x11vnc RFB handshake, loopback bind i pohyb myši.
  Tyto kroky zatím NEBYLY spuštěné. Xvfb není součástí vydávaného obrazu.
- Neprovedeno: ARM64 sestavení této verze, reálný HA Ingress/Cloudflare průchod,
  noVNC v prohlížeči, start/stop na Pi a reálná vzdálená relace.
- Na běžícím HA ani v Cloudflare nebylo při této přípravě nic změněno.
- Dodaný GPU report na zařízení potvrdil ANGLE/Broadcom V3D 7.1.10.2 a Mesa
  25.0.7, GPU crash count 0. GPU parametry se v rc.3 nemění.

# Ověření opravy 0.1.0-rc.2 — 2026-10-20

- 16 testů prošlo lokálně i na GitHubu: uchování profilu, idempotentní inicializace,
  omezení ukončování na vlastní browser/profil/port, fullscreen a porty TIME_WAIT.
- Nativní ARM64 build a test skutečného Chromia prošly:
  https://github.com/HSTEP/stelab-kiosk/actions/runs/39418146659
- Skutečné Chromium během testu zachovalo persistentní cookie a localStorage
  mezi dvěma spuštěními. Startup zachoval jeho Preferences a Local State.
  Browser.close ukončil proces před zastavením testovacího prostředí.
- Vydávací workflow tento test zopakovalo před push obrazu a prošlo:
  https://github.com/HSTEP/stelab-kiosk/actions/runs/39418628719
- Anonymně ověřen ARM64 manifest, config a čtení ze všech 14 vrstev obrazu.
  Viz REGISTRY-VERIFICATION.json. Nejedná se o úplný Docker pull ani start na Pi.
- Změna řízení S6 a konkrétní Google/YouTube přihlášení vyžadují ještě kontrolu
  po aktualizaci na zařízení uživatele. GPU parametry se nezměnily; přiložený
  log rc.1 s chybou prvního EGL pokusu sám o sobě nepotvrzuje použitý renderer.

Původní ověření rc.1 následuje jako historický záznam.

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
- Úplný Docker pull a spuštění obrazu na hardware.
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

Zdrojový repozitář i obraz jsou nyní veřejné. Publikace #1 prošla:
https://github.com/HSTEP/stelab-kiosk/actions/runs/39408626834
Manifest ARM64 a čtení jednoho bajtu z každé z 12 vrstev ověřeny anonymním
registry tokenem, bez uložených uživatelských přihlašovacích údajů.
Digest indexu: sha256:33ded578d2ee9b1e2fbf69816967bc4a7f1de5369553874c4c0214c75491fe90.
Podrobnosti v REGISTRY-VERIFICATION.json. Nejde o úplný Docker pull ani hardware test.
