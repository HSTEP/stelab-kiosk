# STELAB Kiosk

Lehký Debian desktop pro místní HDMI displej Home Assistant OS na Raspberry Pi 5:
Chromium s dashboardem, Openbox, terminál xterm, správce souborů PCManFM a editor
Mousepad. Vychází ze zaslané funkční kopie Welizard Browser Custom
`1.3.1-welizard.8-local1`, nikoliv z nahrazení runtime dnešním upstreamem.

**Stav: 0.1.0-rc.5 — Chromium pod samostatným uživatelem se zapnutým sandboxem.**
[ARM64 testovací sestavení](https://github.com/HSTEP/stelab-kiosk/actions/runs/39463303726)
a [vydávací sestavení](https://github.com/HSTEP/stelab-kiosk/actions/runs/39446283466)
prošla. Před publikací bylo ověřeno zachování profilu Chromia, skutečné VNC
spojení a pohyb myši i otevření oficiálního ChatGPT okna pod běžným uživatelem
bez HA tajemství v jeho prostředí. Obraz je anonymně dostupný z GHCR.

Průchod přes skutečný HA Ingress / Cloudflare a přihlášení ChatGPT s následným
restartem je ještě nutné ověřit na zařízení. Příprava vydání neměnila běžící HA.

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

## Chromium sandbox (rc.5)

Kiosk prohlížeč má vlastní UID1001 a zapnutý sandbox; původní parametr
`--no-sandbox` se nepoužívá. Při prvním startu se zachová obsah stávajícího
`/config/chromium-profile` a převede se vlastnictví souborů. Profil se nekopíruje
ani nemaže. Nový domov `/config/chromium-home` je trvalý, cache je v `/run`.
Přepínač pro vypnutí sandboxu není dostupný jako nastavení ani automatická záloha.

Aktivní sandbox a převod testovacího profilu byly ověřeny na HAOS v izolovaném
kontejneru i v kompletním ARM64 sestavení. Fyzický displej, V3D a zvuk je
potřeba zkontrolovat po aktualizaci na zařízení.
Chromium stále nenabízí plnohodnotnou Google Chrome Sync; zachovávání webových
přihlášení je oddělené od přihlášení profilu prohlížeče pro synchronizaci.

## Plocha, ikony a trvalé změny (rc.4)

`⌘M` zobrazí/skryje plochu bez zavírání oken. Ikony otevírá jedno kliknutí.
Ikona **Web** aktivuje existující Chromium a zobrazí lištu, aby bylo možné napsat
adresu. **Dashboard** aktivuje prohlížeč; zachovává současnou otevřenou stránku.
Pravé tlačítko na ploše dál otevírá menu Openboxu.

Výchozí pozadí je statické PNG. PCManFM, který už doplněk obsahuje, spravuje
pozadí i ikony; nejde o další prohlížeč ani animované pozadí.

- `/config/desktop/wallpaper.png`: vlastní pozadí.
- `/config/desktop/home/Desktop`: zástupci `.desktop`.
- `/config/desktop/home/.config/pcmanfm/stelab`: nastavení a pozice ikon.
- `/config/chatgpt/home/projects`: projekty samostatného AI uživatele.

Výchozí soubory se zakládají pouze, pokud chybí. Stejný adresář `/config` musí
být zachován a zahrnut do zálohy doplňku. Odinstalace či ztráta dat nejsou aktualizace.
Programy přidané ručně přes `apt`, změny v `/usr`, `/etc` nebo `/root` patří do
sestavení obrazu, jinak mohou při aktualizaci zmizet. Pouhé uložení skriptu do
`/config` nezajistí jeho automatické spuštění; spuštění musí obsahovat doplněk.

ChatGPT/Codex může upravovat projekt ve svém trvalém domově. Nemá `sudo`,
root oprávnění ani přístup k profilu kioskového Chromia nebo HA heslům. Může připravit
změnu klonu tohoto repozitáře; instalace systémové změny dál vyžaduje novou
ověřenou verzi doplňku. Linux preview zatím nepodporuje Computer Use, tedy
obecné ovládání oken klikáním. Lokální spouštění agentů v HAOS kontejneru musí
být ověřeno na zařízení, samotný start aplikace to nedokazuje.

Doplněk sdílí CPU a RAM hostitele s HA a ostatními službami. V jeho konfiguraci
není vlastní limit paměti/CPU; přidělování řeší plánovač Linuxu a případné limity
Dockeru. Výpočet modelu probíhá ve službě OpenAI, ale prohlížeč, aplikace,
terminál a spuštěné skripty spotřebovávají prostředky Raspberry Pi.

## STELAB Remote přes přihlášení Home Assistantu

Verze 0.1.0-rc.3 přidává noVNC přes vestavěný **Ingress**. Ovládá stejnou
obrazovku `:0`, která je připojená přes HDMI. Používá existující přihlášení do
Home Assistantu a existující adresu HA, takže není potřeba další doména, VPN,
Cloudflare Access ani aktivace jeho tarifu.

Po aktualizaci doplňku a ověření zálohy:

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

## ChatGPT a Codex na desktopu

Součástí rc.3 je oficiální linuxová aplikace ChatGPT pro ARM64, verze
`26.1013.40934`. Balíček se bere přímo od OpenAI a ověřuje se jeho SHA-256.
Otevři ji **⌘G** nebo přes pravé tlačítko na ploše → **ChatGPT / Codex**.
Nespouští se automaticky při startu. Přihlas se vlastním účtem ChatGPT;
žádné heslo ani API klíč se nevkládá do konfigurace doplňku.

Aplikace běží jako uživatel `stelab-ai` (nikoli root), bez proměnných obsahujících
HA heslo nebo token Supervisoru. Domov a nastavení jsou trvale v
`/config/chatgpt/home`, projekty ukládej do `/config/chatgpt/home/projects`.
Přihlašovací prohlížeč má oddělený profil; nepoužívá profil dashboardu.
Přihlášení a obnovení relace po restartu vyžadují zkoušku na zařízení.

K dispozici je Git, Python/venv, Node.js (závislost noVNC) a bubblewrap.
Výchozí omezení a schvalování Codexu nevypínej. Funkčnost jeho sandboxu závisí
i na jádře a nastavení HAOS; pokud hlásí chybu, neposouvej úlohu do režimu bez
omezení. Linuxová aplikace je preview a podle dokumentace OpenAI zatím nemá
Computer Use. Práce s projekty a příkazy je jiná funkce než ovládání celé plochy.

Samostatný uživatel není samostatný virtuální počítač: sdílí X11 plochu,
síť a část souborového systému kiosku. Pro nedůvěryhodné projekty a nehlídané
agenty s širokými právy používej samostatné prostředí. Desktopová aplikace zabírá
přibližně 1,6 GB rozbalená; potřebuje také RAM navíc vedle Chromia a HA.
Aktualizace aplikace se vydává s novým sestavením doplňku. Ruční apt upgrade
uvnitř běžícího kontejneru se při výměně obrazu nezachová.

Oficiální podklady: [Linux / ARM64](https://learn.chatgpt.com/docs/linux/linux-app),
[omezení příkazů](https://learn.chatgpt.com/docs/sandboxing).

## Ovládání desktopu

| Klávesy | Akce |
|---|---|
| ⌘↓ | Zobrazit lištu a záložky Chromia |
| ⌘↑ | Skrýt lištu návratem do fullscreenu |
| ⌘Enter | Otevřít terminál |
| ⌘E | Otevřít správce souborů |
| ⌘G | Otevřít ChatGPT / Codex |
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

Xorg a správa plochy běží jako root v kontejneru. Chromium běží jako UID1001
se sandboxem; ChatGPT má samostatný UID1000. Sdílený X11 desktop není úplnou
izolací aplikací. Terminál je pro důvěryhodného místního uživatele a má
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
  --build-arg BUILD_VERSION=0.1.0-rc.5 \
  --tag stelab-kiosk:0.1.0-rc.5 --load ./stelab-kiosk
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
