# Backup Scripts — Installation Guide

🌐 Language / Sprache / Język:  
**[🇬🇧 English](#-english)** · [🇩🇪 Deutsch](#-deutsch) · [🇵🇱 Polski](#-polski)

---

# 🇬🇧 English

🌐 Language / Sprache / Język:
[🇬🇧 English](#-english) · [🇩🇪 Deutsch](#-deutsch) · [🇵🇱 Polski](#-polski)

## Table of Contents

- [Architecture](#architecture)
- [Configuration File](#configuration-file-backupconf)
- [proxmox_backup_telegram.sh](#proxmox-pve1--proxmox_backup_telegramsh)
- [proxmox_config_backup_v3.sh](#proxmox-pve1--proxmox_config_backup_v3sh)
- [wyse_backup.sh](#dell-wyse-3040--wyse_backupsh)
- [SSH Key: Wyse → Proxmox](#ssh-key-wyse--proxmox)
- [Cron](#cron)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Architecture

```
Dell Wyse 3040                        Proxmox pve1
──────────────────────────            ──────────────────────────────────────
wyse_backup.sh                        proxmox_backup_telegram.sh
  └─ tar: AGH, Unbound, Docker          └─ vzdump: all LXC + VMs
  └─ rsync → pve1:/mnt/hdd-data/       └─ Telegram report + log file
             backups/dell-wyse/
                                      proxmox_config_backup_v3.sh
                                        └─ tar: /etc/pve, fstab, interfaces,
                                               /usr/local/bin/
                                        └─ tar: /opt/lxc-data/ (bind mounts)
                                        └─ pvesh: vzdump/PBS job monitoring
                                        └─ Telegram report
```

**Responsibilities:**
- `vzdump` / PBS — rootfs snapshots of LXC containers and VMs
- `proxmox_config_backup_v3.sh` — host config + bind mounts (invisible to PBS)
- `wyse_backup.sh` — Dell Wyse backup transferred to Proxmox via rsync

**Why a separate config file?**
Sensitive data (tokens, IPs, SSH credentials) lives in `/etc/homelab/backup.conf` — outside the repository. Scripts load it via `source`. Only `backup.conf.example` with placeholders is committed to the repo.

---

## Configuration File (backup.conf)

### Setup (on each host separately)

```bash
mkdir -p /etc/homelab
cp backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
chown root:root /etc/homelab/backup.conf
nano /etc/homelab/backup.conf
```

### Contents of backup.conf

```bash
TELEGRAM_TOKEN="1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
TELEGRAM_CHAT_ID="987654321"

# Dell Wyse only — Proxmox SERVER_LAN IP (not Management VLAN)
REMOTE_USER="root"
REMOTE_HOST="10.100.20.10"
REMOTE_PATH="/mnt/hdd-data/backups/dell-wyse"
```

> Token: message `@BotFather` on Telegram → `/newbot`
> Chat ID: message `@userinfobot` on Telegram

### .gitignore

```
backup.conf
*.conf
!backup.conf.example
```

---

## Proxmox pve1 — proxmox_backup_telegram.sh

Runs `vzdump` on all LXC containers and VMs, sends a Telegram report with the log file attached.

```bash
cp proxmox_backup_telegram.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox_backup_telegram.sh
bash /usr/local/bin/proxmox_backup_telegram.sh   # test run
```

| Variable | Default | Description |
|---|---|---|
| `STORAGE` | `hdd-storage` | Storage name from `/etc/pve/storage.cfg` |
| `RETENTION` | `7` | Number of backups to keep |
| `LOG_DIR` | `/var/log/proxmox_backup` | Log directory |
| `FREE_LIMIT` | `90` | Alert when disk usage exceeds X% |

---

## Proxmox pve1 — proxmox_config_backup_v3.sh

Backs up host configuration and LXC bind mount data. Monitors PBS/vzdump job results via the Proxmox API and includes them in the Telegram report.

```bash
cp proxmox_config_backup_v3.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox_config_backup_v3.sh
bash /usr/local/bin/proxmox_config_backup_v3.sh  # test run
```

| Variable | Default | Description |
|---|---|---|
| `BACKUP_PATH` | `/mnt/hdd-data/backups/pve-configs` | Archive destination |
| `HOST_RETENTION_DAYS` | `30` | Retention for host_config (small file) |
| `LXC_RETENTION_DAYS` | `7` | Retention for lxc_data (potentially large) |
| `LXC_DATA_SOURCE` | `/opt/lxc-data/` | LXC bind mount directory |

**Dependencies:**
```bash
python3 --version   # pre-installed on every Proxmox
apt install zstd
```

---

## Dell Wyse 3040 — wyse_backup.sh

Packages AGH, Unbound and Docker data, transfers the archive to Proxmox via rsync over SSH.

**Prerequisites:**
```bash
apt install zstd rsync
```

```bash
cp wyse_backup.sh /usr/local/bin/
chmod +x /usr/local/bin/wyse_backup.sh
mkdir -p /etc/homelab
cp backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
nano /etc/homelab/backup.conf
bash /usr/local/bin/wyse_backup.sh   # test run
```

| Variable | Default | Description |
|---|---|---|
| `TMP_DIR` | `/var/tmp/wyse-backup` | Temp directory (eMMC, not RAM) |
| `RETENTION_DAYS` | `7` | Days to keep backups on Proxmox |
| `LOG_DIR` | `/var/log/wyse-backup` | Log directory |
| `SOURCES` | see script | List of directories to archive |

> **Why `/var/tmp` and not `/tmp`?**
> On Debian with systemd, `/tmp` is `tmpfs` (RAM). The Wyse only has 2 GB — a large archive could trigger the OOM killer. `/var/tmp` lives on the eMMC.

---

## SSH Key: Wyse → Proxmox

```bash
# On Dell Wyse
ssh-keygen -t ed25519 -C "wyse-backup" -f /root/.ssh/id_ed25519
# Leave passphrase EMPTY (backup runs unattended)
ssh-copy-id -i /root/.ssh/id_ed25519.pub root@10.100.20.10

# Verify
ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

> Use the SERVER_LAN IP (`10.100.20.10`), not the Management VLAN (`10.100.1.x`).

---

## Cron

### pve1

```cron
# vzdump backup — daily at 02:00
0 2 * * * /usr/local/bin/proxmox_backup_telegram.sh

# Host config + bind mount backup — daily at 03:00 (after vzdump, avoids I/O contention)
0 3 * * * /usr/local/bin/proxmox_config_backup_v3.sh
```

### Dell Wyse

```cron
# Wyse → Proxmox — daily at 04:00
0 4 * * * /usr/local/bin/wyse_backup.sh
```

---

## Verification

```bash
# Logs on pve1
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logs on Dell Wyse
tail -f /var/log/wyse-backup/backup_$(date +%Y-%m-%d).log

# Archives on Proxmox
ls -lh /mnt/hdd-data/backups/pve-configs/
ls -lh /mnt/hdd-data/backups/dell-wyse/

# Verify archive integrity
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve1_$(date +%Y-%m-%d).tar.zst | head -20
```

---

## Troubleshooting

**Telegram not sending messages**
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  --data-urlencode "chat_id=<CHAT_ID>" --data-urlencode "text=test"
```

**wyse_backup.sh: SSH error**
```bash
ssh -v -o BatchMode=yes root@10.100.20.10 "echo OK"
# If key rejected — repeat ssh-copy-id
```

**Disk not mounted**
```bash
mountpoint /mnt/hdd-data && pvesm status
```

---
---

# 🇩🇪 Deutsch

🌐 Language / Sprache / Język:  
[🇬🇧 English](#-english) · **[🇩🇪 Deutsch](#-deutsch)** · [🇵🇱 Polski](#-polski)

## Inhaltsverzeichnis

- [Architektur](#architektur)
- [Konfigurationsdatei](#konfigurationsdatei-backupconf)
- [proxmox_backup_telegram.sh](#proxmox-pve1--proxmox_backup_telegramsh-1)
- [proxmox_config_backup_v3.sh](#proxmox-pve1--proxmox_config_backup_v3sh-1)
- [wyse_backup.sh](#dell-wyse-3040--wyse_backupsh-1)
- [SSH-Schlüssel: Wyse → Proxmox](#ssh-schlüssel-wyse--proxmox)
- [Cron](#cron-1)
- [Überprüfung](#überprüfung)
- [Fehlerbehebung](#fehlerbehebung)

---

## Architektur

```
Dell Wyse 3040                        Proxmox pve1
──────────────────────────            ──────────────────────────────────────
wyse_backup.sh                        proxmox_backup_telegram.sh
  └─ tar: AGH, Unbound, Docker          └─ vzdump: alle LXC + VMs
  └─ rsync → pve1:/mnt/hdd-data/       └─ Telegram-Bericht + Logdatei
             backups/dell-wyse/
                                      proxmox_config_backup_v3.sh
                                        └─ tar: /etc/pve, fstab, interfaces,
                                               /usr/local/bin/
                                        └─ tar: /opt/lxc-data/ (Bind-Mounts)
                                        └─ pvesh: vzdump/PBS-Job-Überwachung
                                        └─ Telegram-Bericht
```

**Aufgabenteilung:**
- `vzdump` / PBS — Rootfs-Snapshots von LXC-Containern und VMs
- `proxmox_config_backup_v3.sh` — Host-Konfiguration + Bind-Mounts (für PBS unsichtbar)
- `wyse_backup.sh` — Dell-Wyse-Backup, übertragen per rsync auf Proxmox

**Warum eine separate Konfigurationsdatei?**
Sensible Daten (Tokens, IPs, SSH-Zugangsdaten) werden in `/etc/homelab/backup.conf` gespeichert — außerhalb des Repositories. Skripte laden diese Datei per `source`. Nur `backup.conf.example` mit Platzhaltern wird ins Repository eingecheckt.

---

## Konfigurationsdatei (backup.conf)

### Einrichtung (auf jedem Host separat)

```bash
mkdir -p /etc/homelab
cp backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
chown root:root /etc/homelab/backup.conf
nano /etc/homelab/backup.conf
```

### Inhalt von backup.conf

```bash
TELEGRAM_TOKEN="1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
TELEGRAM_CHAT_ID="987654321"

# Nur Dell Wyse — Proxmox SERVER_LAN IP (nicht Management VLAN)
REMOTE_USER="root"
REMOTE_HOST="10.100.20.10"
REMOTE_PATH="/mnt/hdd-data/backups/dell-wyse"
```

> Token: `@BotFather` auf Telegram anschreiben → `/newbot`
> Chat ID: `@userinfobot` auf Telegram anschreiben

### .gitignore

```
backup.conf
*.conf
!backup.conf.example
```

---

## Proxmox pve1 — proxmox_backup_telegram.sh {#proxmox-pve1--proxmox_backup_telegramsh-1}

Führt `vzdump` für alle LXC-Container und VMs aus, sendet einen Telegram-Bericht mit Logdatei als Anhang.

```bash
cp proxmox_backup_telegram.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox_backup_telegram.sh
bash /usr/local/bin/proxmox_backup_telegram.sh   # Testlauf
```

| Variable | Standard | Beschreibung |
|---|---|---|
| `STORAGE` | `hdd-storage` | Storage-Name aus `/etc/pve/storage.cfg` |
| `RETENTION` | `7` | Anzahl der aufzubewahrenden Backups |
| `LOG_DIR` | `/var/log/proxmox_backup` | Log-Verzeichnis |
| `FREE_LIMIT` | `90` | Warnung bei Festplattennutzung über X% |

---

## Proxmox pve1 — proxmox_config_backup_v3.sh {#proxmox-pve1--proxmox_config_backup_v3sh-1}

Sichert Host-Konfiguration und LXC-Bind-Mount-Daten. Überwacht PBS/vzdump-Jobs über die Proxmox-API und fügt Ergebnisse in den Telegram-Bericht ein.

```bash
cp proxmox_config_backup_v3.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox_config_backup_v3.sh
bash /usr/local/bin/proxmox_config_backup_v3.sh  # Testlauf
```

| Variable | Standard | Beschreibung |
|---|---|---|
| `BACKUP_PATH` | `/mnt/hdd-data/backups/pve-configs` | Zielverzeichnis für Archive |
| `HOST_RETENTION_DAYS` | `30` | Aufbewahrung host_config (kleine Datei) |
| `LXC_RETENTION_DAYS` | `7` | Aufbewahrung lxc_data (potenziell groß) |
| `LXC_DATA_SOURCE` | `/opt/lxc-data/` | LXC-Bind-Mount-Verzeichnis |

**Abhängigkeiten:**
```bash
python3 --version   # auf jedem Proxmox vorinstalliert
apt install zstd
```

---

## Dell Wyse 3040 — wyse_backup.sh {#dell-wyse-3040--wyse_backupsh-1}

Packt AGH-, Unbound- und Docker-Daten und überträgt das Archiv per rsync über SSH auf Proxmox.

**Voraussetzungen:**
```bash
apt install zstd rsync
```

```bash
cp wyse_backup.sh /usr/local/bin/
chmod +x /usr/local/bin/wyse_backup.sh
mkdir -p /etc/homelab
cp backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
nano /etc/homelab/backup.conf
bash /usr/local/bin/wyse_backup.sh   # Testlauf
```

| Variable | Standard | Beschreibung |
|---|---|---|
| `TMP_DIR` | `/var/tmp/wyse-backup` | Temp-Verzeichnis (eMMC, kein RAM) |
| `RETENTION_DAYS` | `7` | Tage, die Backups auf Proxmox verbleiben |
| `LOG_DIR` | `/var/log/wyse-backup` | Log-Verzeichnis |
| `SOURCES` | siehe Skript | Liste der zu archivierenden Verzeichnisse |

> **Warum `/var/tmp` statt `/tmp`?**
> Unter Debian mit systemd ist `/tmp` als `tmpfs` (RAM) eingehängt. Der Wyse hat nur 2 GB RAM — ein großes Archiv könnte den OOM-Killer auslösen. `/var/tmp` liegt auf der eMMC.

---

## SSH-Schlüssel: Wyse → Proxmox

```bash
# Auf Dell Wyse
ssh-keygen -t ed25519 -C "wyse-backup" -f /root/.ssh/id_ed25519
# Passphrase LEER lassen (Backup läuft unbeaufsichtigt)
ssh-copy-id -i /root/.ssh/id_ed25519.pub root@10.100.20.10

# Überprüfen
ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

> SERVER_LAN-IP verwenden (`10.100.20.10`), nicht das Management VLAN (`10.100.1.x`).

---

## Cron {#cron-1}

### pve1

```cron
# vzdump-Backup — täglich um 02:00
0 2 * * * /usr/local/bin/proxmox_backup_telegram.sh

# Host-Konfiguration + Bind-Mounts — täglich um 03:00 (nach vzdump, kein I/O-Konflikt)
0 3 * * * /usr/local/bin/proxmox_config_backup_v3.sh
```

### Dell Wyse

```cron
# Wyse → Proxmox — täglich um 04:00
0 4 * * * /usr/local/bin/wyse_backup.sh
```

---

## Überprüfung

```bash
# Logs auf pve1
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logs auf Dell Wyse
tail -f /var/log/wyse-backup/backup_$(date +%Y-%m-%d).log

# Archive auf Proxmox
ls -lh /mnt/hdd-data/backups/pve-configs/
ls -lh /mnt/hdd-data/backups/dell-wyse/

# Archivintegrität prüfen
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve1_$(date +%Y-%m-%d).tar.zst | head -20
```

---

## Fehlerbehebung

**Telegram sendet keine Nachrichten**
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  --data-urlencode "chat_id=<CHAT_ID>" --data-urlencode "text=test"
```

**wyse_backup.sh: SSH-Fehler**
```bash
ssh -v -o BatchMode=yes root@10.100.20.10 "echo OK"
# Schlüssel abgelehnt → ssh-copy-id wiederholen
```

**Datenträger nicht eingehängt**
```bash
mountpoint /mnt/hdd-data && pvesm status
```

---
---

# 🇵🇱 Polski

🌐 Language / Sprache / Język:  
[🇬🇧 English](#-english) · [🇩🇪 Deutsch](#-deutsch) · **[🇵🇱 Polski](#-polski)**

## Spis treści

- [Architektura](#architektura)
- [Plik konfiguracyjny](#plik-konfiguracyjny-backupconf)
- [proxmox_backup_telegram.sh](#proxmox-pve1--proxmox_backup_telegramsh-2)
- [proxmox_config_backup_v3.sh](#proxmox-pve1--proxmox_config_backup_v3sh-2)
- [wyse_backup.sh](#dell-wyse-3040--wyse_backupsh-2)
- [Klucz SSH: Wyse → Proxmox](#klucz-ssh-wyse--proxmox)
- [Cron](#cron-2)
- [Weryfikacja](#weryfikacja)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## Architektura

```
Dell Wyse 3040                        Proxmox pve1
──────────────────────────            ──────────────────────────────────────
wyse_backup.sh                        proxmox_backup_telegram.sh
  └─ tar: AGH, Unbound, Docker          └─ vzdump: wszystkie LXC + VM
  └─ rsync → pve1:/mnt/hdd-data/       └─ raport Telegram + plik logu
             backups/dell-wyse/
                                      proxmox_config_backup_v3.sh
                                        └─ tar: /etc/pve, fstab, interfaces,
                                               /usr/local/bin/
                                        └─ tar: /opt/lxc-data/ (bind mounty)
                                        └─ pvesh: monitoring zadań vzdump/PBS
                                        └─ raport Telegram
```

**Podział odpowiedzialności:**
- `vzdump` / PBS — snapshoty rootfs kontenerów LXC i VM
- `proxmox_config_backup_v3.sh` — konfiguracja hosta + bind mounty (niewidoczne dla PBS)
- `wyse_backup.sh` — backup Dell Wyse przesyłany przez rsync na Proxmox

**Dlaczego osobny plik konfiguracyjny?**
Wrażliwe dane (tokeny, IP, dane SSH) żyją w `/etc/homelab/backup.conf` — poza repozytorium. Skrypty wczytują go przez `source`. Do repo trafia tylko `backup.conf.example` z placeholderami.

---

## Plik konfiguracyjny (backup.conf)

### Instalacja (na każdym hoście osobno)

```bash
mkdir -p /etc/homelab
cp backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
chown root:root /etc/homelab/backup.conf
nano /etc/homelab/backup.conf
```

### Zawartość backup.conf

```bash
TELEGRAM_TOKEN="1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"
TELEGRAM_CHAT_ID="987654321"

# Tylko Dell Wyse — IP Proxmoxa z SERVER_LAN (nie Management VLAN)
REMOTE_USER="root"
REMOTE_HOST="10.100.20.10"
REMOTE_PATH="/mnt/hdd-data/backups/dell-wyse"
```

> Token: napisz do `@BotFather` na Telegramie → `/newbot`
> Chat ID: napisz do `@userinfobot` na Telegramie

### .gitignore

```
backup.conf
*.conf
!backup.conf.example
```

---

## Proxmox pve1 — proxmox_backup_telegram.sh {#proxmox-pve1--proxmox_backup_telegramsh-2}

Wykonuje `vzdump` wszystkich kontenerów LXC i VM, wysyła raport na Telegram z plikiem logu jako załącznikiem.

```bash
cp proxmox_backup_telegram.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox_backup_telegram.sh
bash /usr/local/bin/proxmox_backup_telegram.sh   # test ręczny
```

| Zmienna | Domyślna wartość | Opis |
|---|---|---|
| `STORAGE` | `hdd-storage` | Nazwa storage z `/etc/pve/storage.cfg` |
| `RETENTION` | `7` | Liczba backupów do zachowania |
| `LOG_DIR` | `/var/log/proxmox_backup` | Folder logów |
| `FREE_LIMIT` | `90` | Alert gdy użycie dysku > X% |

---

## Proxmox pve1 — proxmox_config_backup_v3.sh {#proxmox-pve1--proxmox_config_backup_v3sh-2}

Backupuje konfigurację hosta i dane bind mountów LXC. Monitoruje wyniki zadań PBS/vzdump przez API Proxmoxa i uwzględnia je w raporcie Telegram.

```bash
cp proxmox_config_backup_v3.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox_config_backup_v3.sh
bash /usr/local/bin/proxmox_config_backup_v3.sh  # test ręczny
```

| Zmienna | Domyślna wartość | Opis |
|---|---|---|
| `BACKUP_PATH` | `/mnt/hdd-data/backups/pve-configs` | Gdzie lądują archiwa |
| `HOST_RETENTION_DAYS` | `30` | Retencja dla host_config (mały plik) |
| `LXC_RETENTION_DAYS` | `7` | Retencja dla lxc_data (może być duże) |
| `LXC_DATA_SOURCE` | `/opt/lxc-data/` | Katalog bind mountów LXC |

**Zależności:**
```bash
python3 --version   # domyślnie na każdym Proxmoxie
apt install zstd
```

---

## Dell Wyse 3040 — wyse_backup.sh {#dell-wyse-3040--wyse_backupsh-2}

Pakuje dane AGH, Unbound i Docker, przesyła archiwum przez rsync/SSH na Proxmox.

**Wymagania wstępne:**
```bash
apt install zstd rsync
```

```bash
cp wyse_backup.sh /usr/local/bin/
chmod +x /usr/local/bin/wyse_backup.sh
mkdir -p /etc/homelab
cp backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
nano /etc/homelab/backup.conf
bash /usr/local/bin/wyse_backup.sh   # test ręczny
```

| Zmienna | Domyślna wartość | Opis |
|---|---|---|
| `TMP_DIR` | `/var/tmp/wyse-backup` | Katalog tymczasowy (eMMC, nie RAM) |
| `RETENTION_DAYS` | `7` | Ile dni trzymać backupy na Proxmoxie |
| `LOG_DIR` | `/var/log/wyse-backup` | Folder logów |
| `SOURCES` | patrz skrypt | Lista katalogów do spakowania |

> **Dlaczego `/var/tmp` zamiast `/tmp`?**
> Na Debianie z systemd `/tmp` to `tmpfs` (RAM). Wyse ma tylko 2 GB — duże archiwum mogłoby wywołać OOM killera. `/var/tmp` jest na eMMC (dysku).

---

## Klucz SSH: Wyse → Proxmox

```bash
# Na Dell Wyse
ssh-keygen -t ed25519 -C "wyse-backup" -f /root/.ssh/id_ed25519
# Passphrase zostaw PUSTE (backup działa bez nadzoru)
ssh-copy-id -i /root/.ssh/id_ed25519.pub root@10.100.20.10

# Weryfikacja
ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

> Użyj IP z SERVER_LAN (`10.100.20.10`), nie z Management VLAN (`10.100.1.x`).

---

## Cron {#cron-2}

### pve1

```cron
# Backup VM/LXC (vzdump) — codziennie o 02:00
0 2 * * * /usr/local/bin/proxmox_backup_telegram.sh

# Backup konfiguracji + bind mountów — codziennie o 03:00 (po vzdump, bez konfliktu I/O)
0 3 * * * /usr/local/bin/proxmox_config_backup_v3.sh
```

### Dell Wyse

```cron
# Backup Wyse → Proxmox — codziennie o 04:00
0 4 * * * /usr/local/bin/wyse_backup.sh
```

---

## Weryfikacja

```bash
# Logi na pve1
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logi na Dell Wyse
tail -f /var/log/wyse-backup/backup_$(date +%Y-%m-%d).log

# Archiwa na Proxmoxie
ls -lh /mnt/hdd-data/backups/pve-configs/
ls -lh /mnt/hdd-data/backups/dell-wyse/

# Weryfikacja archiwum
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve1_$(date +%Y-%m-%d).tar.zst | head -20
```

---

## Rozwiązywanie problemów

**Telegram nie wysyła wiadomości**
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  --data-urlencode "chat_id=<CHAT_ID>" --data-urlencode "text=test"
```

**wyse_backup.sh: błąd SSH**
```bash
ssh -v -o BatchMode=yes root@10.100.20.10 "echo OK"
# Klucz odrzucony → powtórz ssh-copy-id
```

**Dysk nie zamontowany**
```bash
mountpoint /mnt/hdd-data && pvesm status
```