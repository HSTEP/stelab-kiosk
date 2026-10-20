# Publikování — až po výslovném svolení HSTEP

Zdrojový repozitář a obrazy `0.1.0-rc.2` i `0.1.0-rc.3` jsou se svolením HSTEP veřejné.
Publikace prošla; anonymně ověřen manifest ARM64 a přístup ke všem vrstvám.
Na HA dosud nebylo nic měněno. Následující postup slouží pro další vydání.

1. Vytvořit veřejný GitHub repozitář `HSTEP/stelab-kiosk`, default branch `main`.
   Nahrát celý obsah tohoto repozitáře včetně `.github/workflows` a GPL licence.
   Přístup musí být přes přihlášený GitHub nebo uživatelem nastavené nástroje;
   hesla a osobní tokeny se neposílají do chatu ani nezapisují do zdrojů.
2. Spustit pouze workflow **Check and build STELAB Kiosk**. Opravit případné chyby
   sestavení před vydáním. Oprava buildu ani průchod CI nepotvrzuje Pi 5 hardware.
3. V GitHub Settings → Environments vytvořit `release`. Pokud účet podporuje
   required reviewers, přidat schválení HSTEP. Samotný název environmentu schválení
   nevynucuje. Workflow je každopádně pouze ručně spouštěné se slovem `PUBLISH`.
4. Po svolení publikovat testovací GHCR obraz workflow **Publish STELAB Kiosk to
   GHCR** z větve main nebo přípravné release/* větve. Používá repozitářový GITHUB_TOKEN, oprávnění packages:write
   pouze v release jobu, bez osobního tokenu.
5. U GHCR balíčku `stelab-kiosk-aarch64` nastavit veřejnou viditelnost a přístup
   z tohoto repozitáře. Viditelnost zdrojového repozitáře sama nezaručuje veřejnost
   balíčku. Ověřit anonymní stažení přes prázdnou konfiguraci Dockeru:

   ```bash
   docker --config /tmp/stelab-anonymous-pull pull ghcr.io/hstep/stelab-kiosk-aarch64:0.1.0-rc.3
   ```

   Použít novou prázdnou složku. Až úspěšný anonymní pull potvrzuje použitelnost
   veřejného obrazu pro Home Assistant bez přihlášení k GHCR.
6. Teprve poté přidat repozitář do HA a provést postup přepnutí a testy v README.
   První veřejná verze je experimentální release candidate, nikoliv stabilní 1.0.

Cílový obraz: `ghcr.io/hstep/stelab-kiosk-aarch64:0.1.0-rc.3`.
`image` v manifestu obsahuje placeholder `{arch}`, který Supervisor nahradí za
`aarch64`; `version` je přesný tag. Před publikací obrazu nelze tuto konfiguraci
instalovat jako GHCR doplněk. Manifest v repozitáři tedy může být do prvního
vydání viditelný, ale ještě nemusí být instalovatelný.

Pro další vydání vždy zvýšit VERSION a verzi config.yaml, aktualizovat changelog,
sestavit, publikovat nový tag a ověřit anonymní pull. Již vydané tagy nepřepisovat.
Workflow se pokus o přepsání dostupného tagu snaží odmítnout; skutečná neměnnost
vyžaduje dodržet proces také mimo workflow. Při velkých změnách publikovat obraz
z přípravné větve jiným procesem a manifest hlavní větve aktualizovat až poté.

Ověření na Raspberry Pi je nutné zejména při změně Debianu, Mesa, Chromia, Xorgu,
udev nebo VT knihovny. Aktualizace neprovádět uvnitř běžícího kontejneru.


Při přípravě aktualizace použít release/* větev. Nejprve sestavit a otestovat,
pak publikovat obraz z této větve a ověřit dostupnost. Až následně přenést
odpovídající manifest do main, aby HA nenabízelo verzi bez dostupného obrazu.
Vydávací workflow před push také spustí test cookies ve skutečném Chromiu.
