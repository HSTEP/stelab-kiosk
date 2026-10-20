# Kandidát 0.1.0-rc.5 — Chromium sandbox

Dosud nezveřejněn. Kompletní obraz nové verze ještě nebyl sestaven.
Běžící uživatelský doplněk ani jeho profily nebyly změněny.

Ověřeno přímo na uživatelově HAOS / Raspberry Pi v dočasném kontejneru
odvozeném z rc.4, bez host zařízení, host sítě nebo uživatelských dat:

- Instalovány pouze chromium-sandbox a Xvfb; žádný stávající balíček se neupgradoval.
- Stejný rootem vytvořený testovací profil převeden na UID1001.
- Skutečné cookies a localStorage zachované při převodu i následném restartu.
- Stránka chrome://sandbox potvrdila aktivní sandbox a adekvátní izolaci.
- Skutečný proces Chromia běžel jako UID1001 bez --no-sandbox.
- Chromium se ve všech třech fázích korektně ukončilo před Xvfb.
- Opraveno rozpoznání procesu: Chromium pod D-Bus přepisuje argv[0] na celý
  procesový titulek, což předchozí detekce hlavního procesu nerozpoznala.
- Ověřena oprava vlastnictví souboru po simulovaném návratu na starší root verzi.
- Lokálně prošlo všech 25 testů a validace syntaxe/metadata.

Zachována cesta /config/chromium-profile a dosavadní parametry GPU.
ChatGPT ponechává samostatný UID1000 a svůj nezměněný domov.
Nový domov prohlížeče: /config/chromium-home, UID1001.
Přidávají se skupiny pouze podle skutečných DRM zařízení; PulseAudio připojení
se předává čistému prostředí bez HA hesel a Supervisor tokenů.

Před vydáním zbývá úplné ARM64 sestavení se všemi integračními testy.
Po vydání je nutné na fyzickém displeji zkontrolovat V3D, zvuk a ovládání.
Testovací cookie není ověřením přihlášení ke skutečnému účtu Google; server může
relaci odvolat nezávisle na zachování profilu.

Historická ověření:

# Ověření vydání 0.1.0-rc.4 — 2026-10-20

Runtime commit: `3fe1353`. Native ARM64 publish workflow:
https://github.com/HSTEP/stelab-kiosk/actions/runs/39457252498

- Source syntax and all 23 unit tests passed.
- Native ARM64 image built on ubuntu-24.04-arm.
- Real Chromium cookie/localStorage persistence test passed.
- Real noVNC/RFB handshake, pointer input and loopback-listener test passed.
- Official ChatGPT window, UID1000, clean environment and persistent home test passed.
- Real PCManFM desktop displayed a nonblank wallpaper under Xvfb/Openbox.
- Seven launchers created; show/restore desktop with wmctrl succeeded.
- Repeated initialization preserved modified launcher, wallpaper and opaque
  Chromium/ChatGPT auth-file sentinels byte-for-byte in the test container.
- Actual Google/ChatGPT account sessions were not used in CI. A server may
  expire a login independently of preserving the local profile.
- No original kiosk or second hardware Xorg was started. Actual Pi display and
  mouse/touch activation of desktop icons require acceptance after updating.

The first test run (eef22ba) built successfully and passed the existing tests,
but its desktop probe incorrectly searched only root children after Openbox
reparented windows. The passing revision uses _NET_CLIENT_LIST. Nothing from
that failed run was published.

Historical rc.3 verification follows:

# Ověření vydání 0.1.0-rc.3 — 2026-10-20

- Lokální kontrola zdrojů a 23 testů prošly. Sedm nových kontrol ověřilo
  odmítnutí cizí TCP adresy i s podvrženými ingress/user/IP hlavičkami, vypnutý
  stav, statické soubory, odmítnutí symlinku mimo assets a binární přenos.
- Nativní ARM64 testovací sestavení prošlo:
  https://github.com/HSTEP/stelab-kiosk/actions/runs/39445548335
- Vydávací sestavení finálního runtime commitu 37ab4d9 prošlo a publikovalo obraz:
  https://github.com/HSTEP/stelab-kiosk/actions/runs/39446283466
- Oba testy použily skutečné Chromium a ověřily cookie/localStorage/Preferences/
  Local State přes restart. GPU hardware tento headless test neověřuje.
- Jednorázový kontejner s Xvfb ověřil skutečný x11vnc RFB handshake, výhradně
  loopback bind s vypnutým IPv6, WebSocket přenos, pohyb myši a ukončení serveru.
  Xvfb není součástí zveřejněného obrazu. Kiosk /run.sh se v CI nespouštěl.
- Oficiální ChatGPT ARM64 26.1013.40934 otevřel viditelné okno. Test ověřil UID
  1000, nepřítomnost HA_PASSWORD/SUPERVISOR_TOKEN v prostředí a nepoužití
  --no-sandbox. Závěrečný test navíc ověřil, že root příprava nesleduje symlink
  uvnitř AI domova, a zachování uživatelových souborů přes opakovanou přípravu.
- Balíček aplikace má ověřená vendor metadata a SHA-256. Omezení agentových
  příkazů, přihlášení a zachování skutečné přihlášené relace vyžadují zařízení.
- Anonymně ověřen manifest/config a čtení prvního bajtu ze všech 20 vrstev.
  Viz REGISTRY-VERIFICATION.json. Komprimované vrstvy mají celkem 1 243 477 043 B.
  Nejde o úplný Docker pull ani o spuštění obrazu na Pi.
- Digest: sha256:73f92dec5a6913340fe230b34c8a81ccc5af5e03fd9884183fe8a98ef4b567b2
- Dodaný GPU report na zařízení potvrdil ANGLE/Broadcom V3D 7.1.10.2 a Mesa
  25.0.7, GPU crash count 0. Parametry GPU se v rc.3 nemění.
- Neprovedeno: reálný HA Ingress/Cloudflare průchod a ovládání HDMI plochy,
  přihlášení ChatGPT, agentův shell sandbox na HAOS a restart s tímto přihlášením.
- Na běžícím HA ani v Cloudflare nebylo při přípravě a vydání nic změněno.

Historické ověření rc.2 (registry report: REGISTRY-VERIFICATION-rc.2.json):

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
