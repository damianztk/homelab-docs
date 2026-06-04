# AdGuard Home Sync — Instalacja i konfiguracja | Installation and Configuration | Installation und Konfiguration

> 🇵🇱 [Polski](#-polski) | 🇬🇧 [English](#-english) | 🇩🇪 [Deutsch](#-deutsch)

---

# 🇵🇱 Polski

> **Środowisko:** Proxmox VE 9, LXC Debian 13, architektura amd64  
> **Cel:** Synchronizacja konfiguracji z głównej instancji AGH (DELL Wyse 3040) do repliki (LXC na Node 1)

## Spis treści

1. [Pobieranie binarki](#1-pobieranie-binarki)
2. [Instalacja](#2-instalacja)
3. [Konfiguracja](#3-konfiguracja)
4. [Usługa systemd](#4-usługa-systemd)
5. [Uruchomienie](#5-uruchomienie)
6. [Typowe błędy](#6-typowe-błędy)

## 1. Pobieranie binarki

Sprawdź aktualną wersję:

```bash
curl -s https://api.github.com/repos/bakito/adguardhome-sync/releases/latest | grep tag_name
```

Pobierz binarkę — **ważne:** nazwa pliku zawiera numer wersji:

```bash
wget https://github.com/bakito/adguardhome-sync/releases/download/v0.9.0/adguardhome-sync_0.9.0_linux_amd64.tar.gz
```

> ⚠️ **Częsty błąd:** Stara nazwa bez wersji (`adguardhome-sync_linux_amd64.tar.gz`) zwróci błąd `404 Not Found`. Zawsze używaj formatu `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz`.

## 2. Instalacja

```bash
tar -xzf adguardhome-sync_0.9.0_linux_amd64.tar.gz
chmod +x adguardhome-sync
mv adguardhome-sync /usr/local/bin/

# Sprawdź instalację:
adguardhome-sync --version
```

## 3. Konfiguracja

```bash
mkdir -p /etc/adguardhome-sync
nano /etc/adguardhome-sync/config.yaml
```

```yaml
cron: "*/10 * * * *"  # synchronizacja co 10 minut
runOnStart: true

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

> 💡 Domyślny port panelu AGH to `:3000`. Hasła ze znakami specjalnymi umieść w cudzysłowie: `password: "haslo!123"`.

## 4. Usługa systemd

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

## 5. Uruchomienie

```bash
systemctl daemon-reload
systemctl enable adguardhome-sync
systemctl start adguardhome-sync

# Status:
systemctl status adguardhome-sync

# Logi na żywo:
journalctl -u adguardhome-sync -f
```

## 6. Typowe błędy

| Problem | Przyczyna | Rozwiązanie |
|---|---|---|
| `404 Not Found` przy wget | Brak numeru wersji w nazwie pliku | Użyj `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz` |
| Brak połączenia z origin | Port zablokowany na firewallu | Odblokuj port `3000` między LXC a Wyse |
| Synchronizacja nie działa | Złe dane logowania | Sprawdź login/hasło w panelu AGH |

---

# 🇬🇧 English

> 🇵🇱 [Polski](#-polski) | 🇬🇧 [English](#-english) | 🇩🇪 [Deutsch](#-deutsch)

---

> **Environment:** Proxmox VE 9, LXC Debian 13, amd64  
> **Goal:** Synchronize AGH configuration from the primary instance (DELL Wyse 3040) to the replica (LXC on Node 1)

## Table of Contents

1. [Downloading the binary](#1-downloading-the-binary)
2. [Installation](#2-installation)
3. [Configuration](#3-configuration)
4. [Systemd service](#4-systemd-service)
5. [Starting the service](#5-starting-the-service)
6. [Common issues](#6-common-issues)

## 1. Downloading the binary

Check the latest version:

```bash
curl -s https://api.github.com/repos/bakito/adguardhome-sync/releases/latest | grep tag_name
```

Download the binary — **important:** the filename includes the version number:

```bash
wget https://github.com/bakito/adguardhome-sync/releases/download/v0.9.0/adguardhome-sync_0.9.0_linux_amd64.tar.gz
```

> ⚠️ **Common mistake:** The old filename without version (`adguardhome-sync_linux_amd64.tar.gz`) will return `404 Not Found`. Always use the format `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz`.

## 2. Installation

```bash
tar -xzf adguardhome-sync_0.9.0_linux_amd64.tar.gz
chmod +x adguardhome-sync
mv adguardhome-sync /usr/local/bin/

# Verify:
adguardhome-sync --version
```

## 3. Configuration

```bash
mkdir -p /etc/adguardhome-sync
nano /etc/adguardhome-sync/config.yaml
```

```yaml
cron: "*/10 * * * *"  # sync every 10 minutes
runOnStart: true

origin:
  url: http://10.100.30.X:3000   # primary AGH — DELL Wyse 3040
  username: admin
  password: your_password

replicas:
  - url: http://10.100.20.Y:3000  # replica AGH — LXC on Node 1
    username: admin
    password: your_password

sync:
  filters: true
  rewrites: true
  services: true
  clients: true
  generalSettings: true
  queryLogConfig: true
  statsConfig: true
```

> 💡 Default AGH panel port is `:3000`. Wrap passwords with special characters in quotes: `password: "pass!123"`.

## 4. Systemd service

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

## 5. Starting the service

```bash
systemctl daemon-reload
systemctl enable adguardhome-sync
systemctl start adguardhome-sync

# Status:
systemctl status adguardhome-sync

# Live logs:
journalctl -u adguardhome-sync -f
```

## 6. Common issues

| Problem | Cause | Solution |
|---|---|---|
| `404 Not Found` on wget | Missing version number in filename | Use `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz` |
| Cannot reach origin | Firewall blocking the port | Allow port `3000` between LXC and Wyse |
| Sync not working | Wrong credentials | Verify login/password in AGH panel |

---

# 🇩🇪 Deutsch

> 🇵🇱 [Polski](#-polski) | 🇬🇧 [English](#-english) | 🇩🇪 [Deutsch](#-deutsch)

---

> **Umgebung:** Proxmox VE 9, LXC Debian 13, amd64  
> **Ziel:** AGH-Konfiguration von der primären Instanz (DELL Wyse 3040) zur Replik (LXC auf Node 1) synchronisieren

## Inhaltsverzeichnis

1. [Binary herunterladen](#1-binary-herunterladen)
2. [Installation](#2-installation-1)
3. [Konfiguration](#3-konfiguration-1)
4. [Systemd-Dienst](#4-systemd-dienst)
5. [Dienst starten](#5-dienst-starten)
6. [Häufige Fehler](#6-häufige-fehler)

## 1. Binary herunterladen

Aktuelle Version prüfen:

```bash
curl -s https://api.github.com/repos/bakito/adguardhome-sync/releases/latest | grep tag_name
```

Binary herunterladen — **wichtig:** der Dateiname enthält die Versionsnummer:

```bash
wget https://github.com/bakito/adguardhome-sync/releases/download/v0.9.0/adguardhome-sync_0.9.0_linux_amd64.tar.gz
```

> ⚠️ **Häufiger Fehler:** Der alte Dateiname ohne Version (`adguardhome-sync_linux_amd64.tar.gz`) gibt `404 Not Found` zurück. Immer das Format `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz` verwenden.

## 2. Installation

```bash
tar -xzf adguardhome-sync_0.9.0_linux_amd64.tar.gz
chmod +x adguardhome-sync
mv adguardhome-sync /usr/local/bin/

# Überprüfen:
adguardhome-sync --version
```

## 3. Konfiguration

```bash
mkdir -p /etc/adguardhome-sync
nano /etc/adguardhome-sync/config.yaml
```

```yaml
cron: "*/10 * * * *"  # Synchronisation alle 10 Minuten
runOnStart: true

origin:
  url: http://10.100.30.X:3000   # primäre AGH-Instanz — DELL Wyse 3040
  username: admin
  password: dein_passwort

replicas:
  - url: http://10.100.20.Y:3000  # AGH-Replik — LXC auf Node 1
    username: admin
    password: dein_passwort

sync:
  filters: true
  rewrites: true
  services: true
  clients: true
  generalSettings: true
  queryLogConfig: true
  statsConfig: true
```

> 💡 Standard-Port des AGH-Panels ist `:3000`. Passwörter mit Sonderzeichen in Anführungszeichen setzen: `password: "pass!123"`.

## 4. Systemd-Dienst

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

## 5. Dienst starten

```bash
systemctl daemon-reload
systemctl enable adguardhome-sync
systemctl start adguardhome-sync

# Status:
systemctl status adguardhome-sync

# Live-Logs:
journalctl -u adguardhome-sync -f
```

## 6. Häufige Fehler

| Problem | Ursache | Lösung |
|---|---|---|
| `404 Not Found` bei wget | Fehlende Versionsnummer im Dateinamen | `adguardhome-sync_X.Y.Z_linux_amd64.tar.gz` verwenden |
| Keine Verbindung zur Origin | Firewall blockiert den Port | Port `3000` zwischen LXC und Wyse freigeben |
| Synchronisation funktioniert nicht | Falsche Anmeldedaten | Login/Passwort im AGH-Panel prüfen |

---

*Dokumentacja / Documentation / Dokumentation — kwiecień / April 2026*