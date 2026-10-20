# STELAB Kiosk — 0.1.0-rc.4

**Lokální kandidát; dosud nezveřejněn ani otestován na Pi.**

Zelenomodrá plocha STELAB a ikony se zobrazí přes ⌘M. Jedno kliknutí otevírá
Dashboard, Web, ChatGPT, Soubory, Terminál, Sdílené soubory a Textový editor.
Vlastní pozadí `/config/desktop/wallpaper.png`, nastavení a ikony v
`/config/desktop/home` se při dalších startech nepřepisují.

Experimentální Debian desktop pro Raspberry Pi 5 a HAOS: Chromium, Openbox,
terminál xterm, správce souborů PCManFM a editor Mousepad.

Zachovává základ dodané lokální kopie Welizard Browser. ARM64 sestavení a test zachování cookies
mezi dvěma spuštěními Chromia prošly. Uživatel potvrdil funkční displej, zvuk, dotyk a Bluetooth; GPU report potvrdil V3D.

⌘↓ zobrazí lištu Chromia, ⌘↑ ji skryje. ⌘Enter otevře terminál, ⌘E správce souborů,
⌘D se vrátí k prohlížeči. ⌘G otevře ChatGPT / Codex. Skripty: /config/scripts, dokumenty: /config/files.

Nově připraveno: STELAB Remote přes přihlášení HA (Ingress + noVNC).
Vzdálené ovládání je standardně vypnuté, zapíná se volbou remote_access.
Potom se otevírá přes Open Web UI / boční panel STELAB Remote.
Není potřeba Cloudflare Access ani další subdoména.
Součástí je oficiální ChatGPT ARM64 aplikace, spouštěná ručně jako samostatný
uživatel. Projekty a přihlášení mají trvalý domov /config/chatgpt/home.
ARM64 sestavení a integrační testy prošly. Připojení přes skutečný HA Ingress
a přihlášení ChatGPT je ještě potřeba ověřit na zařízení.

Před spuštěním zastavit všechny ostatní kiosky a vypnout jejich start i watchdog.
Původní local_welizard_browser ponechat jako zálohu. Pro návrat nejprve zastavit
STELAB, teprve potom spustit zálohu. Nikdy nespouštět oba současně.

Podrobný postup a omezení: https://github.com/HSTEP/stelab-kiosk
