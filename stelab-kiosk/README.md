# STELAB Kiosk — 0.1.0-rc.1

Experimentální Debian desktop pro Raspberry Pi 5 a HAOS: Chromium, Openbox,
terminál xterm, správce souborů PCManFM a editor Mousepad.

Zachovává základ dodané lokální kopie Welizard Browser. První ARM64 sestavení
prošlo. Praktické ověření GPU, HDMI zvuku, dotyku a Bluetooth ještě následuje.

⌘↓ zobrazí lištu Chromia, ⌘↑ ji skryje. ⌘Enter otevře terminál, ⌘E správce souborů,
⌘D se vrátí k prohlížeči. Skripty: /config/scripts, dokumenty: /config/files.

Před spuštěním zastavit všechny ostatní kiosky a vypnout jejich start i watchdog.
Původní local_welizard_browser ponechat jako zálohu. Pro návrat nejprve zastavit
STELAB, teprve potom spustit zálohu. Nikdy nespouštět oba současně.

Podrobný postup a omezení: https://github.com/HSTEP/stelab-kiosk
