# Backup Scripts — Installation Guide

🌐 Language / Sprache / Język: 
[🇬🇧 English](#-english) · [🇩🇪 Deutsch](#-deutsch) · [🇵🇱 Polski](#-polski)

---

# 🇬🇧 English

🌐 Language / Sprache / Język:  
**[🇬🇧 English](#-english)** · [🇩🇪 Deutsch](#-deutsch) · [🇵🇱 Polski](#-polski)

## Table of Contents

- [Architecture](#architecture)
- [Configuration File](#configuration-file-backupconf)
- [proxmox-config-backup-and-pbs-check.sh](#proxmox-pve1--pve2--proxmox-config-backup-and-pbs-checksh)
- [wyse-backup.sh](#dell-wyse-3040--wyse-backupsh)
- [SSH Keys](#ssh-keys)
- [Cron](#cron)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## Architecture

```
Dell Wyse 3040                        Proxmox pve1 + pve2
──────────────────────────            ──────────────────────────────────────
wyse-backup.sh                        PBS (Proxmox Backup Server, LXC 900)
  └─ tar: AGH, Unbound, Docker         └─ incremental snapshots: all LXC + VMs
  └─ rsync → pve1:/mnt/hdd-data/       └─ deduplication, retention via datastore
             backups/dell-wyse/        └─ schedule: 03:30 daily (PVE Datacenter → Backup)

                                      proxmox-config-backup-and-pbs-check.sh
                                        └─ auto-detects node (pve1 or pve2)
                                        └─ tar: /etc/pve, fstab, interfaces,
                                               /usr/local/bin/
                                        └─ tar: /opt/lxc-data/ (bind mounts)
                                        └─ tar: /opt/docker-data/ (Docker stacks)
                                        └─ pve2: rsync archives to pve1 via SSH
                                        └─ pvesh: vzdump/PBS job monitoring
                                        └─ Telegram report
```

**Responsibilities:**
- **PBS** — incremental, deduplicated rootfs snapshots of all LXC containers and VMs
- `proxmox-config-backup-and-pbs-check.sh` — host config + bind mounts + Docker data (invisible to PBS)
- `wyse-backup.sh` — Dell Wyse backup transferred to Proxmox via rsync

> **Note:** `proxmox-full-backup-telegram.sh` (vzdump script) is no longer used — PBS replaced it.
> The script remains in the repository for reference but is not deployed or scheduled.

**Why a separate config file?**
Sensitive data (tokens, IPs, SSH credentials) lives in `/etc/homelab/backup.conf` — outside the repository. Scripts load it via `source`. Only `backup.conf.example` with placeholders is committed to the repo.

**Backup storage layout:**
```
/mnt/hdd-data/backups/        ← pve1, hdd-data-1tb-p1
├── pbs-store/                ← PBS datastore (LXC/VM snapshots)
├── pve-configs/              ← config backup archives (pve1 + pve2)
└── dell-wyse/                ← Wyse backup archives
```

---

## Configuration File (backup.conf)

### Setup (each host separately)

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
# Comment out on pve1 and pve2 (not used by the Proxmox script)
# REMOTE_USER="root"
# REMOTE_HOST="10.100.20.10"
# REMOTE_PATH="/mnt/hdd-data/backups/dell-wyse"
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

## Proxmox pve1 + pve2 — proxmox-config-backup-and-pbs-check.sh

Backs up host configuration, LXC bind mount data and Docker stack data. Automatically detects which node it runs on (`pve1` or `pve2`) and adjusts behavior accordingly. Monitors PBS/vzdump job results via the Proxmox API and includes them in the Telegram report.

**pve1:** archives saved directly to `/mnt/hdd-data/backups/pve-configs/`  
**pve2:** archives created in `/tmp`, then transferred to pve1 via rsync, local files cleaned up

### Installation (both nodes)

```bash
# Clone repo (first time only)
apt install git -y
git clone https://gitea.damianzientek.de/damian/scripts.git ~/scripts

# Deploy
cp ~/scripts/proxmox/proxmox-config-backup-and-pbs-check.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox-config-backup-and-pbs-check.sh

# Config file
mkdir -p /etc/homelab
cp ~/scripts/backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
chown root:root /etc/homelab/backup.conf
nano /etc/homelab/backup.conf

# Test run
/usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### Updates

```bash
cd ~/scripts && git pull
cp proxmox/proxmox-config-backup-and-pbs-check.sh /usr/local/bin/
```

### Variables

| Variable | Default | Description |
|---|---|---|
| `BACKUP_PATH` | pve1: `/mnt/hdd-data/backups/pve-configs` / pve2: `/tmp/pve2-config-backup` | Archive destination (auto-set by node detection) |
| `HOST_RETENTION_DAYS` | `30` | Retention for host_config archives |
| `LXC_RETENTION_DAYS` | `7` | Retention for lxc_data and docker_data archives |
| `LXC_DATA_SOURCE` | `/opt/lxc-data/` | LXC bind mount directory |
| `DOCKER_DATA_SOURCE` | `/opt/docker-data/` | Docker stack data directory |
| `REMOTE_HOST` | `10.100.20.10` | pve2 only — target host for rsync transfer |
| `REMOTE_PATH` | `/mnt/hdd-data/backups/pve-configs` | pve2 only — target path on pve1 |

**Dependencies:**
```bash
python3 --version   # pre-installed on every Proxmox
apt install zstd    # usually pre-installed
```

---

## Dell Wyse 3040 — wyse-backup.sh

Packages AGH, Unbound and Docker data, transfers the archive to Proxmox via rsync over SSH.

**Prerequisites:**
```bash
apt install zstd rsync
```

```bash
# Clone repo (first time only)
git clone https://gitea.damianzientek.de/damian/scripts.git ~/scripts

# Deploy
sudo cp ~/scripts/dell-wyse/wyse-backup.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/wyse-backup.sh

# Config file
sudo mkdir -p /etc/homelab
sudo cp ~/scripts/backup.conf.example /etc/homelab/backup.conf
sudo chmod 600 /etc/homelab/backup.conf
sudo chown root:root /etc/homelab/backup.conf
sudo nano /etc/homelab/backup.conf

# Test run
sudo /usr/local/bin/wyse-backup.sh
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

## SSH Keys

### Wyse → pve1

Required for `wyse-backup.sh` — rsync transfer runs as root.

```bash
# On Dell Wyse (as root)
ssh-keyscan -H 10.100.20.10 | tee /root/.ssh/known_hosts
# Key should already exist at /root/.ssh/id_ed25519
# If not: ssh-keygen -t ed25519 -C "wyse-backup" -f /root/.ssh/id_ed25519
# Then: ssh-copy-id -i /root/.ssh/id_ed25519.pub root@10.100.20.10

# Verify
sudo ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

> Use the SERVER_LAN IP (`10.100.20.10`), not the Management VLAN (`10.100.1.x`).

### pve2 → pve1

Required for `proxmox-config-backup-and-pbs-check.sh` on pve2 — rsync transfer and remote retention.

```bash
# On pve2 — key should already exist at /root/.ssh/id_ed25519
# If not: ssh-keygen -t ed25519 -C "pve2-backup" -f /root/.ssh/id_ed25519
#         ssh-copy-id -i /root/.ssh/id_ed25519.pub root@10.100.20.10

# Add pve1 to known_hosts
ssh-keyscan -H 10.100.20.10 >> /root/.ssh/known_hosts

# Verify
ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

---

## Cron

### pve1

```cron
# Host config + bind mount + Docker backup — daily at 04:30
30 4 * * * /usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### pve2

```cron
# Host config + bind mount + Docker backup + rsync to pve1 — daily at 04:45
45 4 * * * /usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### Dell Wyse

```cron
# Wyse → Proxmox — daily at 04:00
0 4 * * * /usr/local/bin/wyse-backup.sh
```

### Full schedule overview

| Time | Host | Job |
|------|------|-----|
| 03:30 | pve1 + pve2 | **PBS backup** (all LXC + VMs) — configured in PVE Datacenter → Backup |
| 04:00 | Dell Wyse | wyse-backup.sh → rsync to pve1 |
| 04:30 | pve1 | proxmox-config-backup-and-pbs-check.sh |
| 04:45 | pve2 | proxmox-config-backup-and-pbs-check.sh → rsync to pve1 |

---

## Verification

```bash
# Logs on pve1
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logs on pve2
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logs on Dell Wyse
tail -f /var/log/wyse-backup/backup_$(date +%Y-%m-%d).log

# Archives on pve1
ls -lh /mnt/hdd-data/backups/pve-configs/
ls -lh /mnt/hdd-data/backups/dell-wyse/

# Verify archive integrity
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve1_$(date +%Y-%m-%d).tar.zst | head -20
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve2_$(date +%Y-%m-%d).tar.zst | head -20
```

---

## Troubleshooting

**Telegram not sending messages**
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  --data-urlencode "chat_id=<CHAT_ID>" --data-urlencode "text=test"
```

**SSH error (Wyse or pve2)**
```bash
ssh -v -o BatchMode=yes root@10.100.20.10 "echo OK"
# Host key verification failed → ssh-keyscan -H 10.100.20.10 >> /root/.ssh/known_hosts
# Key rejected → repeat ssh-copy-id
```

**Disk not mounted (pve1)**
```bash
mountpoint /mnt/hdd-data && pvesm status
```

**PBS monitoring shows no tasks**
```bash
pvesh get /nodes/pve1/tasks --typefilter vzdump --limit 5 --output-format json
# PBS jobs appear as type "vzdump" in PVE task history
```

---
---

# 🇩🇪 Deutsch

🌐 Language / Sprache / Język:  
[🇬🇧 English](#-english) · **[🇩🇪 Deutsch](#-deutsch)** · [🇵🇱 Polski](#-polski)

## Inhaltsverzeichnis

- [Architektur](#architektur)
- [Konfigurationsdatei](#konfigurationsdatei-backupconf)
- [proxmox-config-backup-and-pbs-check.sh](#proxmox-pve1--pve2--proxmox-config-backup-and-pbs-checksh-1)
- [wyse-backup.sh](#dell-wyse-3040--wyse-backupsh-1)
- [SSH-Schlüssel](#ssh-schlüssel)
- [Cron](#cron-1)
- [Überprüfung](#überprüfung)
- [Fehlerbehebung](#fehlerbehebung)

---

## Architektur

```
Dell Wyse 3040                        Proxmox pve1 + pve2
──────────────────────────            ──────────────────────────────────────
wyse-backup.sh                        PBS (Proxmox Backup Server, LXC 900)
  └─ tar: AGH, Unbound, Docker         └─ inkrementelle Snapshots: alle LXC + VMs
  └─ rsync → pve1:/mnt/hdd-data/       └─ Deduplizierung, Retention via Datastore
             backups/dell-wyse/        └─ Zeitplan: 03:30 täglich (PVE Datacenter → Backup)

                                      proxmox-config-backup-and-pbs-check.sh
                                        └─ erkennt Node automatisch (pve1 oder pve2)
                                        └─ tar: /etc/pve, fstab, interfaces,
                                               /usr/local/bin/
                                        └─ tar: /opt/lxc-data/ (Bind-Mounts)
                                        └─ tar: /opt/docker-data/ (Docker-Stacks)
                                        └─ pve2: rsync Archive zu pve1 via SSH
                                        └─ pvesh: vzdump/PBS Job-Monitoring
                                        └─ Telegram-Bericht
```

**Zuständigkeiten:**
- **PBS** — inkrementelle, deduplizierte rootfs-Snapshots aller LXC-Container und VMs
- `proxmox-config-backup-and-pbs-check.sh` — Host-Konfiguration + Bind-Mounts + Docker-Daten (für PBS unsichtbar)
- `wyse-backup.sh` — Dell Wyse Backup, übertragen via rsync auf Proxmox

> **Hinweis:** `proxmox-full-backup-telegram.sh` (vzdump-Skript) wird nicht mehr verwendet — PBS hat es ersetzt.
> Das Skript verbleibt im Repository zur Referenz, wird aber nicht deployed oder geplant.

**Backup-Storage-Layout:**
```
/mnt/hdd-data/backups/        ← pve1, hdd-data-1tb-p1
├── pbs-store/                ← PBS Datastore (LXC/VM Snapshots)
├── pve-configs/              ← Konfigurations-Backup-Archive (pve1 + pve2)
└── dell-wyse/                ← Wyse Backup-Archive
```

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
# Auf pve1 und pve2 auskommentieren (vom Proxmox-Skript nicht verwendet)
# REMOTE_USER="root"
# REMOTE_HOST="10.100.20.10"
# REMOTE_PATH="/mnt/hdd-data/backups/dell-wyse"
```

> Token: Nachricht an `@BotFather` auf Telegram → `/newbot`
> Chat ID: Nachricht an `@userinfobot` auf Telegram

### .gitignore

```
backup.conf
*.conf
!backup.conf.example
```

---

## Proxmox pve1 + pve2 — proxmox-config-backup-and-pbs-check.sh

Sichert Host-Konfiguration, LXC-Bind-Mount-Daten und Docker-Stack-Daten. Erkennt automatisch auf welchem Node es läuft (`pve1` oder `pve2`) und passt das Verhalten entsprechend an. Überwacht PBS/vzdump-Jobergebnisse über die Proxmox-API und fügt sie in den Telegram-Bericht ein.

**pve1:** Archive direkt in `/mnt/hdd-data/backups/pve-configs/` gespeichert  
**pve2:** Archive in `/tmp` erstellt, dann via rsync zu pve1 übertragen, lokale Dateien bereinigt

### Installation (beide Nodes)

```bash
# Repo klonen (nur beim ersten Mal)
apt install git -y
git clone https://gitea.damianzientek.de/damian/scripts.git ~/scripts

# Deployment
cp ~/scripts/proxmox/proxmox-config-backup-and-pbs-check.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox-config-backup-and-pbs-check.sh

# Konfigurationsdatei
mkdir -p /etc/homelab
cp ~/scripts/backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
chown root:root /etc/homelab/backup.conf
nano /etc/homelab/backup.conf

# Testlauf
/usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### Updates

```bash
cd ~/scripts && git pull
cp proxmox/proxmox-config-backup-and-pbs-check.sh /usr/local/bin/
```

### Variablen

| Variable | Standard | Beschreibung |
|---|---|---|
| `BACKUP_PATH` | pve1: `/mnt/hdd-data/backups/pve-configs` / pve2: `/tmp/pve2-config-backup` | Archivziel (automatisch durch Node-Erkennung gesetzt) |
| `HOST_RETENTION_DAYS` | `30` | Aufbewahrung für host_config-Archive |
| `LXC_RETENTION_DAYS` | `7` | Aufbewahrung für lxc_data- und docker_data-Archive |
| `LXC_DATA_SOURCE` | `/opt/lxc-data/` | LXC Bind-Mount-Verzeichnis |
| `DOCKER_DATA_SOURCE` | `/opt/docker-data/` | Docker-Stack-Datenverzeichnis |
| `REMOTE_HOST` | `10.100.20.10` | Nur pve2 — Zielhost für rsync-Transfer |
| `REMOTE_PATH` | `/mnt/hdd-data/backups/pve-configs` | Nur pve2 — Zielpfad auf pve1 |

**Abhängigkeiten:**
```bash
python3 --version   # auf jedem Proxmox vorinstalliert
apt install zstd    # meist vorinstalliert
```

---

## Dell Wyse 3040 — wyse-backup.sh

Packt AGH-, Unbound- und Docker-Daten, überträgt das Archiv via rsync über SSH auf Proxmox.

**Voraussetzungen:**
```bash
apt install zstd rsync
```

```bash
# Repo klonen (nur beim ersten Mal)
git clone https://gitea.damianzientek.de/damian/scripts.git ~/scripts

# Deployment
sudo cp ~/scripts/dell-wyse/wyse-backup.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/wyse-backup.sh

# Konfigurationsdatei
sudo mkdir -p /etc/homelab
sudo cp ~/scripts/backup.conf.example /etc/homelab/backup.conf
sudo chmod 600 /etc/homelab/backup.conf
sudo chown root:root /etc/homelab/backup.conf
sudo nano /etc/homelab/backup.conf

# Testlauf
sudo /usr/local/bin/wyse-backup.sh
```

| Variable | Standard | Beschreibung |
|---|---|---|
| `TMP_DIR` | `/var/tmp/wyse-backup` | Temp-Verzeichnis (eMMC, nicht RAM) |
| `RETENTION_DAYS` | `7` | Tage zur Aufbewahrung von Backups auf Proxmox |
| `LOG_DIR` | `/var/log/wyse-backup` | Log-Verzeichnis |
| `SOURCES` | siehe Skript | Liste der zu archivierenden Verzeichnisse |

> **Warum `/var/tmp` statt `/tmp`?**
> Unter Debian mit systemd ist `/tmp` ein `tmpfs` (RAM). Der Wyse hat nur 2 GB — ein großes Archiv könnte den OOM-Killer auslösen. `/var/tmp` liegt auf dem eMMC.

---

## SSH-Schlüssel

### Wyse → pve1

Erforderlich für `wyse-backup.sh` — rsync-Transfer läuft als root.

```bash
# Auf Dell Wyse (als root)
ssh-keyscan -H 10.100.20.10 | tee /root/.ssh/known_hosts
# Schlüssel sollte bereits unter /root/.ssh/id_ed25519 vorhanden sein
# Falls nicht: ssh-keygen -t ed25519 -C "wyse-backup" -f /root/.ssh/id_ed25519
# Dann: ssh-copy-id -i /root/.ssh/id_ed25519.pub root@10.100.20.10

# Verifizierung
sudo ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

> SERVER_LAN IP verwenden (`10.100.20.10`), nicht das Management VLAN (`10.100.1.x`).

### pve2 → pve1

Erforderlich für `proxmox-config-backup-and-pbs-check.sh` auf pve2 — rsync-Transfer und Remote-Retention.

```bash
# Auf pve2 — Schlüssel sollte bereits unter /root/.ssh/id_ed25519 vorhanden sein
# pve1 zu known_hosts hinzufügen
ssh-keyscan -H 10.100.20.10 >> /root/.ssh/known_hosts

# Verifizierung
ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

---

## Cron

### pve1

```cron
# Host-Konfig + Bind-Mount + Docker-Backup — täglich um 04:30
30 4 * * * /usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### pve2

```cron
# Host-Konfig + Bind-Mount + Docker-Backup + rsync zu pve1 — täglich um 04:45
45 4 * * * /usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### Dell Wyse

```cron
# Wyse → Proxmox — täglich um 04:00
0 4 * * * /usr/local/bin/wyse-backup.sh
```

### Zeitplanübersicht

| Uhrzeit | Host | Job |
|---------|------|-----|
| 03:30 | pve1 + pve2 | **PBS-Backup** (alle LXC + VMs) — konfiguriert in PVE Datacenter → Backup |
| 04:00 | Dell Wyse | wyse-backup.sh → rsync zu pve1 |
| 04:30 | pve1 | proxmox-config-backup-and-pbs-check.sh |
| 04:45 | pve2 | proxmox-config-backup-and-pbs-check.sh → rsync zu pve1 |

---

## Überprüfung

```bash
# Logs auf pve1
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logs auf pve2
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logs auf Dell Wyse
tail -f /var/log/wyse-backup/backup_$(date +%Y-%m-%d).log

# Archive auf pve1
ls -lh /mnt/hdd-data/backups/pve-configs/
ls -lh /mnt/hdd-data/backups/dell-wyse/

# Archivintegrität prüfen
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve1_$(date +%Y-%m-%d).tar.zst | head -20
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve2_$(date +%Y-%m-%d).tar.zst | head -20
```

---

## Fehlerbehebung

**Telegram sendet keine Nachrichten**
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  --data-urlencode "chat_id=<CHAT_ID>" --data-urlencode "text=test"
```

**SSH-Fehler (Wyse oder pve2)**
```bash
ssh -v -o BatchMode=yes root@10.100.20.10 "echo OK"
# Host key verification failed → ssh-keyscan -H 10.100.20.10 >> /root/.ssh/known_hosts
# Schlüssel abgelehnt → ssh-copy-id wiederholen
```

**Datenträger nicht eingehängt (pve1)**
```bash
mountpoint /mnt/hdd-data && pvesm status
```

**PBS-Monitoring zeigt keine Aufgaben**
```bash
pvesh get /nodes/pve1/tasks --typefilter vzdump --limit 5 --output-format json
# PBS-Jobs erscheinen als Typ "vzdump" in der PVE-Aufgabenhistorie
```

---
---

# 🇵🇱 Polski

🌐 Language / Sprache / Język:  
[🇬🇧 English](#-english) · [🇩🇪 Deutsch](#-deutsch) · **[🇵🇱 Polski](#-polski)**

## Spis treści

- [Architektura](#architektura)
- [Plik konfiguracyjny](#plik-konfiguracyjny-backupconf)
- [proxmox-config-backup-and-pbs-check.sh](#proxmox-pve1--pve2--proxmox-config-backup-and-pbs-checksh-2)
- [wyse-backup.sh](#dell-wyse-3040--wyse-backupsh-2)
- [Klucze SSH](#klucze-ssh)
- [Cron](#cron-2)
- [Weryfikacja](#weryfikacja)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)

---

## Architektura

```
Dell Wyse 3040                        Proxmox pve1 + pve2
──────────────────────────            ──────────────────────────────────────
wyse-backup.sh                        PBS (Proxmox Backup Server, LXC 900)
  └─ tar: AGH, Unbound, Docker         └─ inkrementalne snapshoty: wszystkie LXC + VM
  └─ rsync → pve1:/mnt/hdd-data/       └─ deduplikacja, retencja przez datastore
             backups/dell-wyse/        └─ harmonogram: 03:30 codziennie (PVE Datacenter → Backup)

                                      proxmox-config-backup-and-pbs-check.sh
                                        └─ automatycznie wykrywa node (pve1 lub pve2)
                                        └─ tar: /etc/pve, fstab, interfaces,
                                               /usr/local/bin/
                                        └─ tar: /opt/lxc-data/ (bind mounty)
                                        └─ tar: /opt/docker-data/ (stacki Docker)
                                        └─ pve2: rsync archiwów na pve1 przez SSH
                                        └─ pvesh: monitoring zadań vzdump/PBS
                                        └─ raport Telegram
```

**Podział odpowiedzialności:**
- **PBS** — inkrementalne, deduplikowane snapshoty rootfs wszystkich kontenerów LXC i VM
- `proxmox-config-backup-and-pbs-check.sh` — konfiguracja hosta + bind mounty + dane Docker (niewidoczne dla PBS)
- `wyse-backup.sh` — backup Dell Wyse przesyłany przez rsync na Proxmox

> **Uwaga:** `proxmox-full-backup-telegram.sh` (skrypt vzdump) nie jest już używany — PBS go zastąpił.
> Skrypt pozostaje w repozytorium jako punkt odniesienia, ale nie jest wdrożony ani zaplanowany w cronie.

**Layout storage dla backupów:**
```
/mnt/hdd-data/backups/        ← pve1, hdd-data-1tb-p1
├── pbs-store/                ← PBS datastore (snapshoty LXC/VM)
├── pve-configs/              ← archiwa config backup (pve1 + pve2)
└── dell-wyse/                ← archiwa backup Wyse
```

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
# Na pve1 i pve2 zahashować (skrypt Proxmoxa tych zmiennych nie używa)
# REMOTE_USER="root"
# REMOTE_HOST="10.100.20.10"
# REMOTE_PATH="/mnt/hdd-data/backups/dell-wyse"
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

## Proxmox pve1 + pve2 — proxmox-config-backup-and-pbs-check.sh

Backupuje konfigurację hosta, dane bind mountów LXC i dane stacków Docker. Automatycznie wykrywa na którym nodzie jest uruchomiony (`pve1` lub `pve2`) i dostosowuje działanie. Monitoruje wyniki zadań PBS/vzdump przez API Proxmoxa i uwzględnia je w raporcie Telegram.

**pve1:** archiwa zapisywane bezpośrednio do `/mnt/hdd-data/backups/pve-configs/`  
**pve2:** archiwa tworzone w `/tmp`, następnie przesyłane rsync na pve1, lokalne pliki sprzątane

### Instalacja (oba nody)

```bash
# Klonowanie repo (tylko za pierwszym razem)
apt install git -y
git clone https://gitea.damianzientek.de/damian/scripts.git ~/scripts

# Wdrożenie
cp ~/scripts/proxmox/proxmox-config-backup-and-pbs-check.sh /usr/local/bin/
chmod +x /usr/local/bin/proxmox-config-backup-and-pbs-check.sh

# Plik konfiguracyjny
mkdir -p /etc/homelab
cp ~/scripts/backup.conf.example /etc/homelab/backup.conf
chmod 600 /etc/homelab/backup.conf
chown root:root /etc/homelab/backup.conf
nano /etc/homelab/backup.conf

# Test ręczny
/usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### Aktualizacje

```bash
cd ~/scripts && git pull
cp proxmox/proxmox-config-backup-and-pbs-check.sh /usr/local/bin/
```

### Zmienne

| Zmienna | Domyślna wartość | Opis |
|---|---|---|
| `BACKUP_PATH` | pve1: `/mnt/hdd-data/backups/pve-configs` / pve2: `/tmp/pve2-config-backup` | Cel archiwów (ustawiany automatycznie przez detekcję noda) |
| `HOST_RETENTION_DAYS` | `30` | Retencja dla archiwów host_config |
| `LXC_RETENTION_DAYS` | `7` | Retencja dla archiwów lxc_data i docker_data |
| `LXC_DATA_SOURCE` | `/opt/lxc-data/` | Katalog bind mountów LXC |
| `DOCKER_DATA_SOURCE` | `/opt/docker-data/` | Katalog danych stacków Docker |
| `REMOTE_HOST` | `10.100.20.10` | Tylko pve2 — host docelowy dla transferu rsync |
| `REMOTE_PATH` | `/mnt/hdd-data/backups/pve-configs` | Tylko pve2 — ścieżka docelowa na pve1 |

**Zależności:**
```bash
python3 --version   # domyślnie na każdym Proxmoxie
apt install zstd    # zazwyczaj już zainstalowane
```

---

## Dell Wyse 3040 — wyse-backup.sh

Pakuje dane AGH, Unbound i Docker, przesyła archiwum przez rsync/SSH na Proxmox.

**Wymagania wstępne:**
```bash
apt install zstd rsync
```

```bash
# Klonowanie repo (tylko za pierwszym razem)
git clone https://gitea.damianzientek.de/damian/scripts.git ~/scripts

# Wdrożenie
sudo cp ~/scripts/dell-wyse/wyse-backup.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/wyse-backup.sh

# Plik konfiguracyjny
sudo mkdir -p /etc/homelab
sudo cp ~/scripts/backup.conf.example /etc/homelab/backup.conf
sudo chmod 600 /etc/homelab/backup.conf
sudo chown root:root /etc/homelab/backup.conf
sudo nano /etc/homelab/backup.conf

# Test ręczny
sudo /usr/local/bin/wyse-backup.sh
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

## Klucze SSH

### Wyse → pve1

Wymagany dla `wyse-backup.sh` — transfer rsync działa jako root.

```bash
# Na Dell Wyse (jako root)
ssh-keyscan -H 10.100.20.10 | tee /root/.ssh/known_hosts
# Klucz powinien już istnieć w /root/.ssh/id_ed25519
# Jeśli nie: ssh-keygen -t ed25519 -C "wyse-backup" -f /root/.ssh/id_ed25519
# Następnie: ssh-copy-id -i /root/.ssh/id_ed25519.pub root@10.100.20.10

# Weryfikacja
sudo ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

> Użyj IP z SERVER_LAN (`10.100.20.10`), nie z Management VLAN (`10.100.1.x`).

### pve2 → pve1

Wymagany dla `proxmox-config-backup-and-pbs-check.sh` na pve2 — transfer rsync i zdalna retencja.

```bash
# Na pve2 — klucz powinien już istnieć w /root/.ssh/id_ed25519
# Dodaj pve1 do known_hosts
ssh-keyscan -H 10.100.20.10 >> /root/.ssh/known_hosts

# Weryfikacja
ssh -o BatchMode=yes root@10.100.20.10 "echo OK"
```

---

## Cron

### pve1

```cron
# Backup konfiguracji + bind mountów + Docker — codziennie o 04:30
30 4 * * * /usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### pve2

```cron
# Backup konfiguracji + bind mountów + Docker + rsync na pve1 — codziennie o 04:45
45 4 * * * /usr/local/bin/proxmox-config-backup-and-pbs-check.sh
```

### Dell Wyse

```cron
# Backup Wyse → Proxmox — codziennie o 04:00
0 4 * * * /usr/local/bin/wyse-backup.sh
```

### Pełny harmonogram

| Godzina | Host | Zadanie |
|---------|------|---------|
| 03:30 | pve1 + pve2 | **PBS backup** (wszystkie LXC + VM) — skonfigurowany w PVE Datacenter → Backup |
| 04:00 | Dell Wyse | wyse-backup.sh → rsync na pve1 |
| 04:30 | pve1 | proxmox-config-backup-and-pbs-check.sh |
| 04:45 | pve2 | proxmox-config-backup-and-pbs-check.sh → rsync na pve1 |

---

## Weryfikacja

```bash
# Logi na pve1
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logi na pve2
tail -f /var/log/proxmox_backup/config_backup_$(date +%Y-%m-%d).log

# Logi na Dell Wyse
tail -f /var/log/wyse-backup/backup_$(date +%Y-%m-%d).log

# Archiwa na pve1
ls -lh /mnt/hdd-data/backups/pve-configs/
ls -lh /mnt/hdd-data/backups/dell-wyse/

# Weryfikacja archiwum
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve1_$(date +%Y-%m-%d).tar.zst | head -20
tar -I zstd -tf /mnt/hdd-data/backups/pve-configs/host_config_pve2_$(date +%Y-%m-%d).tar.zst | head -20
```

---

## Rozwiązywanie problemów

**Telegram nie wysyła wiadomości**
```bash
curl -s -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  --data-urlencode "chat_id=<CHAT_ID>" --data-urlencode "text=test"
```

**Błąd SSH (Wyse lub pve2)**
```bash
ssh -v -o BatchMode=yes root@10.100.20.10 "echo OK"
# Host key verification failed → ssh-keyscan -H 10.100.20.10 >> /root/.ssh/known_hosts
# Klucz odrzucony → powtórz ssh-copy-id
```

**Dysk nie zamontowany (pve1)**
```bash
mountpoint /mnt/hdd-data && pvesm status
```

**PBS monitoring nie pokazuje zadań**
```bash
pvesh get /nodes/pve1/tasks --typefilter vzdump --limit 5 --output-format json
# Zadania PBS pojawiają się jako typ "vzdump" w historii zadań PVE
```