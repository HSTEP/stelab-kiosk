# STELAB Kiosk

Lehký Debian desktop pro místní HDMI displej Home Assistant OS na Raspberry Pi 5:
Chromium s dashboardem, Openbox, terminál xterm, správce souborů PCManFM a editor
Mousepad. Vychází ze zaslané funkční kopie Welizard Browser Custom
`1.3.1-welizard.8-local1`, nikoliv z nahrazení runtime dnešním upstreamem.

**Stav: 0.1.0-rc.3 — připravená aktualizace se vzdálenou plochou, dosud nevydaná.**
Poslední vydaná verze je 0.1.0-rc.2. Její test Chromia zachoval cookies,
localStorage, Preferences a Local State přes dvě spuštění. Nová verze vyžaduje
sestavení a test vzdálené plochy na ARM64 před publikací.

## Oprava restartu v 0.1.0-rc.2

Verze opravuje reset Preferences a mazání části dat webů při
startu. Profil zůstává v `/config/chromium-profile`, včetně Local State a cookies.
Před vypnutím Xorgu dostane Chromium čas řádně ukončit a zapsat data.
Kontrola portů zohledňuje TCP TIME_WAIT; skutečný druhý kiosk zůstává blokovaný.
AT-SPI typelib pro Onboard je součástí obrazu. GPU parametry se nemění.

Po aktualizaci bude případně potřeba přihlásit se na Google/YouTube jednou znovu;
následně ověřit zavření/otevření Chromia, restart doplňku i zachování přihlášení.
Přihlášení k webům není zapnutí proprietární synchronizace Google Chrome.
Při běžném prohlížení webů je vhodné `browser_refresh: 0`, aby se po deseti
minutách nepřerušovalo sledování YouTube (v zaslané konfiguraci bylo 600).

## Přidání do Home Assistantu

V obchodě s doplňky otevři **⋮ → Repozitáře** a přidej:

```text
https://github.com/HSTEP/stelab-kiosk
```

Nainstaluj **STELAB Kiosk**, zatím ho nespouštěj. Ponech automatický start a
watchdog vypnuté, přenes konfiguraci z původního doplňku. Před spuštěním nového
vždy zastav původní kiosk. Podrobný postup a návrat jsou níže.
Pokud experimentální doplněk není vidět, zkontroluj pokročilý režim profilu a
obnov katalog doplňků. Původní `local_welizard_browser` neodinstalovávej.

## Co je připraveno

- Debian 13 Trixie; ověřen zveřejněný HA base tag `trixie-2026.10.0`.
- Chromium a Mesa se při sestavení berou z repozitářů Debianu včetně security.
  Výsledné verze se zapisují do `/etc/stelab-build-packages.txt`.
- Zachovány původní parametry `--use-gl=angle`, `--use-angle=default`,
  GPU rasterizace, DRI3 modesetting, PulseAudio, gesta a watchdog pro přihlášení.
  Není vynucen SwiftShader ani vypnuté GPU. Skutečný renderer se musí otestovat.
- Samostatný slug `stelab_kiosk`, pouze ARM64, experimentální doplněk, ruční start.
- Přístup k databázi udev hostitele jen pro čtení; párování Bluetooth dál v HAOS.
- Debian Xorg používá VT kompatibilní knihovnu z Welizard upstreamu jen pro proces
  Xorg. Neprovádí se původní remount `/dev` ani mazání `/dev/tty0`.
- Před startem kontroluje dostupnost REST a Chromium DevTools portů. To pomáhá
  odhalit spuštěný původní kiosk, ale není to univerzální zámek displeje.

## STELAB Remote přes přihlášení Home Assistantu

Verze 0.1.0-rc.3 přidává noVNC přes vestavěný **Ingress**. Ovládá stejnou
obrazovku `:0`, která je připojená přes HDMI. Používá existující přihlášení do
Home Assistantu a existující adresu HA, takže není potřeba další doména, VPN,
Cloudflare Access ani aktivace jeho tarifu.

Po vydání, aktualizaci a ověření zálohy:

1. V konfiguraci STELAB Kiosku zapni **Remote desktop through Home Assistant**
   (`remote_access: true`), ulož a restartuj pouze STELAB Kiosk.
2. Starou volbu `vnc_server` ponech prázdnou. Webová plocha ji nepotřebuje;
   neprázdná hodnota by navíc zapnula původní VNC na LAN portu 5900.
3. Na stránce doplňku vyber **Open Web UI**. Pro pohodlné otevírání zapni
   **Show in sidebar**; položka se jmenuje **STELAB Remote**.
4. Přes stejný odkaz a přihlášení HA se připoj i mimo domov. Ověř to například
   přes mobilní data. Konkrétní URL spravuje HA; `/remote` se samo nevytváří.
5. Klikání a psaní mění skutečnou místní plochu. Boční panel noVNC nabízí
   klávesnici, další modifikační klávesy, schránku a režim pouze pro prohlížení.
   Pro zkratky Super/Command lze použít tlačítko Windows v panelu noVNC, když
   je prohlížeč na Macu zachytává. Odpojení relace neukončuje aplikace na ploše.
6. Pro vypnutí změň `remote_access: false`, ulož a restartuj doplněk.

Přístup je ve výchozím nastavení vypnutý; nová položka je nastavena jako panel
pro správce HA. Připojený uživatel ovládá také terminál a přihlášené weby kiosku.
Nesdílej svou přihlášenou relaci ani tokenovanou ingress URL.

Webový server přijímá pouze TCP spojení ze Supervisoru `172.30.32.2`.
Nedůvěřuje hlavičkám `X-Forwarded-For` ani `X-Remote-User-Id` jako náhradě
za ověření zdrojové adresy. U host network používá port přidělený Supervisorem.
VNC backend poslouchá pouze na IPv4 loopbacku, IPv6 je vypnuté a je oddělený
od volitelného starého LAN VNC. Samotná lokální VNC větev nepoužívá heslo;
hranici vzdáleného přístupu tvoří HA Ingress. Procesy se stejnými lokálními
oprávněními na hostiteli nejsou touto konfigurací izolované.

Nepřidávej Cloudflare trasu přímo na interní webový ani VNC port. HTTPS zajišťuje
existující spojení do HA. noVNC neposílá zvuk z HDMI a není náhradou streamování
YouTube. Připojení přes skutečný HA Ingress/Cloudflare a zařízení vyžaduje test.

## Ovládání desktopu

| Klávesy | Akce |
|---|---|
| ⌘↓ | Zobrazit lištu a záložky Chromia |
| ⌘↑ | Skrýt lištu návratem do fullscreenu |
| ⌘Enter | Otevřít terminál |
| ⌘E | Otevřít správce souborů |
| ⌘D | Přepnout na okno prohlížeče; po zavření ho znovu otevřít |
| Ctrl+Alt+Shift+← / → | Přepnout mezi okny |
| Ctrl+Alt+O | Přepnout obrazovkovou klávesnici |

⌘ znamená klávesu Super/Command na Apple klávesnici. Zkratky musí být ověřeny na
konkrétní Magic Keyboard. Menu nástrojů je dostupné pravým kliknutím na volnou
plochu Openboxu. Není potřeba zavírat dashboard, abys otevřel terminál.

Skripty ukládej do `/config/scripts`, dokumenty do `/config/files`. Jde o trvalou
konfiguraci tohoto doplňku, nikoli složku konfigurace Home Assistant Core.
Terminál začíná ve složce skriptů. `/share` je dostupné pro přenos souborů například
přes Samba share. Pro návrat k dashboardu použij ⌘D, potom případně ⌘↑.

Bash a Python 3 jsou součástí obrazu. Skripty se samy při startu nespouštějí.
Další systémové balíčky a závislosti Pythonu přidej do Dockerfile a vydej novou
verzi. Ruční instalace v běžícím kontejneru se při aktualizaci ztratí.

Desktop a Chromium běží se stejnými právy jako převzatý kiosk: root v kontejneru,
Chromium s `--no-sandbox`. Terminál je pro důvěryhodného místního uživatele a má
přístup k datům i oprávněním doplňku. Nejde o samostatný Debian systém na hostiteli.
Vzdálený přístup zůstává vypnutý, dokud jej uživatel nezapne volbou `remote_access`.

## První sestavení bez publikování

Po schváleném vytvoření repozitáře `HSTEP/stelab-kiosk` otevři GitHub → Actions →
**Check and build STELAB Kiosk** → Run workflow. Workflow kontroluje zdroje,
testuje fullscreen a sestaví ARM64 obraz bez cache na nativním ARM64 serveru a ověří restart skutečného Chromia. **Nepublikuje nic do GHCR.**
Výsledek ukládá jako krátkodobý artifact. Nemůže ověřit skutečný HDMI displej/GPU.

Alternativně lze sestavit lokálně s Docker Buildx:

```bash
docker buildx build --platform linux/arm64 \
  --build-arg BUILD_VERSION=0.1.0-rc.3 \
  --tag stelab-kiosk:0.1.0-rc.3 --load ./stelab-kiosk
```

Lokální kontroly nevyžadují Docker:

```bash
python3 scripts/validate.py
python3 -m pip install aiohttp
python3 -m unittest discover -s tests -v
```

## První instalace do HA a návrat k záloze

1. Zálohuj HA a ponech `local_welizard_browser` i jeho zdrojovou složku beze změny.
2. Teprve po úspěšném sestavení a zveřejnění GHCR obrazu přidej repozitář
   `https://github.com/HSTEP/stelab-kiosk` do obchodu s doplňky.
3. Nainstaluj STELAB Kiosk, zatím jej nespouštěj. Automatický start i watchdog
   ponech vypnuté. Přenes nastavení z lokálního Welizardu včetně přihlášení,
   dashboardu, rozložení kláves a displeje. Nový profil prohlížeče vznikne odděleně.
   Starý profil nemaž ani nepřesouvej. Výchozí browser refresh je nyní 0.
4. Zastav `local_welizard_browser` a vypni jeho automatický start i watchdog.
   Ověř, že neběží ani jiný kiosk. Teprve potom spusť STELAB Kiosk.
5. Proveď testy z tabulky níže. Nový doplněk nesmí být považován za náhradu,
   dokud neprojde hardwarem. Automatický start povol pouze u vybrané verze.

**Návrat:** nejprve zastav STELAB a vypni jeho automatický start/watchdog,
potom spusť `local_welizard_browser`. Nikdy nespouštěj oba kiosky současně.
Není třeba odinstalovat ani jednu verzi nebo restartovat celé HA.

| Kontrola na Raspberry Pi 5 | Očekávaný výsledek |
|---|---|
| Dashboard a další weby | Funkční přihlášení, plynulé zobrazení, přetrvání session po restartu |
| `chrome://gpu` a `glxinfo -B` v terminálu | V3D/Mesa renderer a akcelerace; žádný llvmpipe/SwiftShader |
| HDMI audio | Zvuk z Chromia přes výchozí sink HAOS; ověřit hlasitost a mute |
| Touch | Klikání, scroll, gesta, rotace a obrazovková klávesnice |
| Magic Keyboard/Mouse | Psaní, české rozložení, klikání a scroll, odpojení/znovupřipojení |
| Zkratky | ⌘↓/⌘↑ opakovaně; také s aktivním terminálem; návrat do dashboardu |
| Desktop | Terminál, soubory, editor; Bash/Python skript a uložení po restartu |
| Restart hostitele | Automaticky běží pouze jeden kiosk |

Výpis `glxinfo` sám nepotvrzuje akceleraci Chromia ani hardwarové dekódování videa;
zkontroluj také jeho `chrome://gpu`. V3D grafika a dekódování videa jsou různé věci.

Pokud Xorg na Debianu nenastartuje, nejprve ulož jeho logy a vrať se k záloze.
Volba `xorg_vt_mode: native` je připravena pro řízenou diagnostiku; vyžaduje
ověření oprávnění VT zařízení. Není zárukou opravy a nemá se zapínat naslepo.
Zařízení vstupu event0–event25 a DRM mapování zůstala z lokální kopie; při změně
číslování zařízení je nutné mapování zkontrolovat.

## Vydávání a aktualizace

Publikování je popsané v [PUBLISHING.md](https://github.com/HSTEP/stelab-kiosk/blob/main/PUBLISHING.md). Ruční workflow
**Publish STELAB Kiosk to GHCR** vyžaduje zadat `PUBLISH` a používá prostředí
`release`. Nevydává se automaticky při push ani podle časovače.

Zvýšení verze v `VERSION` a `stelab-kiosk/config.yaml` + nový build + odpovídající
GHCR tag umožní HA nabídnout aktualizaci. Aktualizuje se celý doplněk, včetně
Chromia a systémových knihoven. Chromium se neaktualizuje přes své menu.
Pravidelná údržba stále vyžaduje nové sestavení a vydání; samotný GitHub repozitář
není automatický aktualizační systém. Změny nejprve testovat, potom vydávat.

Zdrojový původ a licence: [SOURCE.md](https://github.com/HSTEP/stelab-kiosk/blob/main/SOURCE.md), [LICENSE](https://github.com/HSTEP/stelab-kiosk/blob/main/LICENSE).

## Ověřené veřejné podklady

- [Debian release branches](https://www.debian.org/releases/)
- [HA Debian ARM64 base a zveřejněné tagy](https://github.com/home-assistant/docker-base/pkgs/container/aarch64-base-debian)
- [Chromium pro Debian Trixie včetně ARM64](https://packages.debian.org/trixie/chromium)
- [Konfigurace doplňků HA](https://contributors.home-assistant.io/apps/reference/configuration/)
- [Welizard upstream](https://github.com/WeLizard/HAOS-kiosk)
