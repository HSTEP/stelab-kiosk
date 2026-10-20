# STELAB Kiosk

Lehký Debian desktop pro místní HDMI displej Home Assistant OS na Raspberry Pi 5:
Chromium s dashboardem, Openbox, terminál xterm, správce souborů PCManFM a editor
Mousepad. Vychází ze zaslané funkční kopie Welizard Browser Custom
`1.3.1-welizard.8-local1`, nikoliv z nahrazení runtime dnešním upstreamem.

**Stav: 0.1.0-rc.1, první ARM64 sestavení úspěšné.** Zdrojové kontroly a sedm
testů fullscreen prošly také na GitHubu. [První build](https://github.com/HSTEP/stelab-kiosk/actions/runs/39407259124)
sestavil Chromium 155.0.8059.79 na Debianu 13 a ověřil přítomnost knihovny V3D.
Zdrojové soubory jsou veřejné; obraz dosud není publikovaný v GHCR.
Hardware Raspberry Pi 5 — skutečná akcelerace, HDMI zvuk, touch a Bluetooth —
zatím otestovaný není. Na Home Assistantu nebyla provedena žádná změna.

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
Žádný webový terminál ani nový vzdálený přístup není zapnutý.

## První sestavení bez publikování

Po schváleném vytvoření repozitáře `HSTEP/stelab-kiosk` otevři GitHub → Actions →
**Check and build STELAB Kiosk** → Run workflow. Workflow kontroluje zdroje,
testuje fullscreen a sestaví ARM64 obraz bez cache. **Nepublikuje nic do GHCR.**
Výsledek ukládá jako krátkodobý artifact. Nemůže ověřit skutečný HDMI displej/GPU.

Alternativně lze sestavit lokálně s Docker Buildx:

```bash
docker buildx build --platform linux/arm64 \
  --build-arg BUILD_VERSION=0.1.0-rc.1 \
  --tag stelab-kiosk:0.1.0-rc.1 --load ./stelab-kiosk
```

Lokální kontroly nevyžadují Docker:

```bash
python3 scripts/validate.py
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

Publikování je popsané v [PUBLISHING.md](PUBLISHING.md). Ruční workflow
**Publish STELAB Kiosk to GHCR** vyžaduje zadat `PUBLISH` a používá prostředí
`release`. Nevydává se automaticky při push ani podle časovače.

Zvýšení verze v `VERSION` a `stelab-kiosk/config.yaml` + nový build + odpovídající
GHCR tag umožní HA nabídnout aktualizaci. Aktualizuje se celý doplněk, včetně
Chromia a systémových knihoven. Chromium se neaktualizuje přes své menu.
Pravidelná údržba stále vyžaduje nové sestavení a vydání; samotný GitHub repozitář
není automatický aktualizační systém. Změny nejprve testovat, potom vydávat.

Zdrojový původ a licence: [SOURCE.md](SOURCE.md), [LICENSE](LICENSE).

## Ověřené veřejné podklady

- [Debian release branches](https://www.debian.org/releases/)
- [HA Debian ARM64 base a zveřejněné tagy](https://github.com/home-assistant/docker-base/pkgs/container/aarch64-base-debian)
- [Chromium pro Debian Trixie včetně ARM64](https://packages.debian.org/trixie/chromium)
- [Konfigurace doplňků HA](https://contributors.home-assistant.io/apps/reference/configuration/)
- [Welizard upstream](https://github.com/WeLizard/HAOS-kiosk)
