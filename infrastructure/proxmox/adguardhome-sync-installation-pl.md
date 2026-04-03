# AdGuard Home Sync — Instalacja i konfiguracja

> **Środowisko:** Proxmox VE 9, LXC Debian 13, architektura amd64  
> **Cel:** Synchronizacja konfiguracji z głównej instancji AGH (DELL Wyse 3040) do repliki (LXC na Node 1)

---

## Spis treści

1. [Pobieranie binarki](#1-pobieranie-binarki)
2. [Instalacja](#2-instalacja)
3. [Konfiguracja](#3-konfiguracja)
4. [Usługa systemd](#4-usługa-systemd)
5. [Uruchomienie](#5-uruchomienie)
6. [Wskazówki i pułapki](#wskazówki-i-pułapki)

---

## 1. Pobieranie binarki

Najpierw sprawdź aktualną wersję na GitHubie:

```bash
curl -s https://api.github.com/repos/bakito/adguardhome-sync/releases/latest | grep tag_name
```

Następnie pobierz binarkę — **ważne:** nazwa pliku zawiera numer wersji:

```bash
wget https://github.com/bakito/adguardhome-sync/releases/download/v0.9.0/adguardhome-sync_0.9.0_linux_amd64.tar.gz
```

> ⚠️ **Częsty błąd:** Stara nazwa pliku bez wersji (`adguardhome-sync_linux_amd64.tar.gz`) nie istnieje w nowszych wydaniach i zwróci błąd `404 Not Found`. Zawsze używaj formatu `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz`.

---

## 2. Instalacja

Wypakuj archiwum, nadaj uprawnienia wykonywania i przenieś binarkę do `/usr/local/bin/`:

```bash
tar -xzf adguardhome-sync_0.9.0_linux_amd64.tar.gz
chmod +x adguardhome-sync
mv adguardhome-sync /usr/local/bin/
```

Sprawdź czy instalacja przebiegła poprawnie:

```bash
adguardhome-sync --version
```

---

## 3. Konfiguracja

Utwórz katalog i plik konfiguracyjny:

```bash
mkdir -p /etc/adguardhome-sync
nano /etc/adguardhome-sync/config.yaml
```

Przykładowa konfiguracja — dostosuj adresy IP i dane logowania:

```yaml
cron: "*/10 * * * *"  # synchronizacja co 10 minut
runOnStart: true       # uruchom synchronizację od razu po starcie usługi

origin:
  url: http://10.100.30.X:3000   # główna instancja AGH — DELL Wyse 3040
  username: admin
  password: twoje_haslo

replicas:
  - url: http://10.100.20.Y:3000  # replika AGH — LXC na Node 1
    username: admin
    password: twoje_haslo

sync:
  filters: true
  rewrites: true
  services: true
  clients: true
  generalSettings: true
  queryLogConfig: true
  statsConfig: true
```

> 💡 **Wskazówka:** Domyślny port panelu AdGuard Home to `:3000`. Jeśli zmieniłeś port w ustawieniach AGH, zaktualizuj URL-e odpowiednio.

> ⚠️ **Hasła ze znakami specjalnymi** (np. `!`, `#`, `@`) umieść w cudzysłowie: `password: "twoje!haslo"`.

---

## 4. Usługa systemd

Utwórz plik jednostki systemd, żeby adguardhome-sync uruchamiał się automatycznie wraz z systemem:

```bash
nano /etc/systemd/system/adguardhome-sync.service
```

```ini
[Unit]
Description=AdGuard Home Sync
After=network.target

[Service]
ExecStart=/usr/local/bin/adguardhome-sync run --config /etc/adguardhome-sync/config.yaml
Restart=on-failure
RestartSec=10s
User=root

[Install]
WantedBy=multi-user.target
```

---

## 5. Uruchomienie

Przeładuj konfigurację systemd, włącz autostart i uruchom usługę:

```bash
systemctl daemon-reload
systemctl enable adguardhome-sync
systemctl start adguardhome-sync
```

Sprawdź status usługi:

```bash
systemctl status adguardhome-sync
```

Podgląd logów na żywo:

```bash
journalctl -u adguardhome-sync -f
```

---

## Wskazówki i pułapki

| Problem | Przyczyna | Rozwiązanie |
|---|---|---|
| `404 Not Found` przy wget | Zła nazwa pliku (brak wersji w nazwie) | Użyj formatu `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz` |
| Brak połączenia z AGH origin | Port zablokowany na firewallu | Odblokuj port `3000` między LXC a Wyse 3040 |
| Synchronizacja nie działa | Złe dane logowania w config.yaml | Sprawdź login/hasło w panelu AGH |

---

*Dokumentacja wygenerowana na podstawie instalacji przeprowadzonej w marcu 2026.*