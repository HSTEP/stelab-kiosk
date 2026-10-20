# STELAB Kiosk — 0.1.0-rc.3 (kandidát)

Experimentální Debian desktop pro Raspberry Pi 5 a HAOS: Chromium, Openbox,
terminál xterm, správce souborů PCManFM a editor Mousepad.

Zachovává základ dodané lokální kopie Welizard Browser. ARM64 sestavení a test zachování cookies
mezi dvěma spuštěními Chromia prošly. Uživatel potvrdil funkční displej, zvuk, dotyk a Bluetooth; GPU report potvrdil V3D.

⌘↓ zobrazí lištu Chromia, ⌘↑ ji skryje. ⌘Enter otevře terminál, ⌘E správce souborů,
⌘D se vrátí k prohlížeči. Skripty: /config/scripts, dokumenty: /config/files.

Nově připraveno: STELAB Remote přes přihlášení HA (Ingress + noVNC).
Vzdálené ovládání je standardně vypnuté, zapíná se volbou remote_access.
Potom se otevírá přes Open Web UI / boční panel STELAB Remote.
Není potřeba Cloudflare Access ani další subdoména.
Kandidát vyžaduje ARM64 sestavení a test skutečné vzdálené relace před vydáním.

Před spuštěním zastavit všechny ostatní kiosky a vypnout jejich start i watchdog.
Původní local_welizard_browser ponechat jako zálohu. Pro návrat nejprve zastavit
STELAB, teprve potom spustit zálohu. Nikdy nespouštět oba současně.

Podrobný postup a omezení: https://github.com/HSTEP/stelab-kiosk
