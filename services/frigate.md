# Frigate NVR — Configuration and Setup | Konfiguration und Einrichtung | Konfiguracja i Setup

---

## Navigation | Navigation | Nawigacja

[🇬🇧 English](#en) | [🇩🇪 Deutsch](#de) | [🇵🇱 Polski](#pl)

---

<a name="en"></a>
## 🇬🇧 English

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Description

Frigate is a self-hosted NVR (Network Video Recorder) running in a Docker container on LXC 320 (pve2). The system handles three Reolink cameras, detects objects (people, cars, cats) and integrates with Home Assistant via MQTT.

### Infrastructure

| Parameter | Value |
|-----------|-------|
| Host | pve2 (`10.100.20.11`) |
| LXC ID | 320 |
| IP | `10.100.20.32` |
| Web UI | `http://10.100.20.32:5000` / `https://frigate.damianzientek.de` |
| go2rtc API | `http://10.100.20.32:1984` |

### Cameras

| Name | Model | IP | Main stream | Substream |
|------|-------|-----|------------|-----------|
| skoda | Reolink RLC-510A | `10.100.90.11` | H.265 | H.264 |
| mazda | Reolink RLC-510A | `10.100.90.12` | H.265 | H.264 |
| sypialnia | Reolink E1 Pro | `10.100.90.14` | H.264 | H.264 |

### Bind Mounts (pve2 host)

| Host path | LXC path | Purpose |
|-----------|----------|---------|
| `/opt/lxc-data/frigate-data` | `/data` | Frigate configuration |
| `/mnt/hdd-data/frigate` | `/media` | Recordings (Toshiba HDD) |
| `/opt/docker-data/frigate-data` | `/opt/docker-data` | Docker data |

### IaC Management

**Terraform** (create/destroy LXC):
```bash
cd ~/homelab-iac/terraform/lxc/pve2
terraform plan
terraform apply
```

**After every terraform apply** — bind mounts and passthrough manually on pve2:
```bash
pct stop 320
pct set 320 --mp0 /opt/lxc-data/frigate-data,mp=/data
pct set 320 --mp1 /mnt/hdd-data/frigate,mp=/media
pct set 320 --mp2 /opt/docker-data/frigate-data,mp=/opt/docker-data
pct set 320 --dev0 /dev/dri/renderD128
chown -R 100000:100000 /opt/lxc-data/frigate-data
chown -R 100000:100000 /mnt/hdd-data/frigate
chown -R 100000:100000 /opt/docker-data/frigate-data
pct start 320
```

**Ansible** (configuration and deployment):
```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l frigate
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l frigate
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-frigate.yml -l frigate
```

### Frigate Configuration

Main configuration in `ansible/files/frigate-config.yml.j2`. Camera passwords in `ansible/secrets.yml` (gitignored).

**Key settings:**
- go2rtc as RTSP proxy (solves Reolink camera connection limit)
- Intel QSV hardware decode via `/dev/dri/renderD128`
- MQTT → Mosquitto broker on HA (`10.100.20.100`)
- Event retention: 14 days
- Pre/post capture buffer: 10 seconds

**Detection zones (Mazda camera):**
- `parking_til_1`, `parking_til_2` — neighbor's parking spots
- `parking_motocykl` — motorcycle spot
- `parking_mazda` — car spot
- Detected objects in zones: `person`, `cat`

### Known Issues and Solutions

**Issue:** go2rtc doesn't start RTSP (port 8554 unavailable)
**Cause:** Frigate 0.17 creates an empty `/config/go2rtc_homekit.yml` which blocks go2rtc
**Solution:** `FRIGATE_DISABLE_HOMEKIT=true` in docker-compose environment

**Issue:** Camera offline after password change
**Solution:** Update `camera_X_password` in `secrets.yml` and run `deploy-frigate.yml`

**Issue:** Disk resize via `terraform apply` destroys LXC (destroy+recreate)
**Solution:** Use `pct resize` directly on Proxmox

### Network

- VLAN 90 (IoT) → VLAN 20 (SERVER): FortiGate rule `Frigate_to_Cams`
- Access: SERVER_LAN (Frigate IP) → cameras (VLAN90), RTSP port
- Recordings excluded from rsync (`--exclude='frigate/'` in `/usr/local/bin/rsync-hdd-backup.sh`)

### Home Assistant Integration

- Frigate integration via HACS (v5.15.3)
- MQTT: Mosquitto broker as HA Add-on
- Frigate URL in HA: `http://10.100.20.32:5000`

---

<a name="de"></a>
## 🇩🇪 Deutsch

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Beschreibung

Frigate ist ein self-hosted NVR (Network Video Recorder), der in einem Docker-Container auf LXC 320 (pve2) läuft. Das System verwaltet drei Reolink-Kameras, erkennt Objekte (Personen, Autos, Katzen) und integriert sich über MQTT mit Home Assistant.

### Infrastruktur

| Parameter | Wert |
|-----------|------|
| Host | pve2 (`10.100.20.11`) |
| LXC ID | 320 |
| IP | `10.100.20.32` |
| Web UI | `http://10.100.20.32:5000` / `https://frigate.damianzientek.de` |
| go2rtc API | `http://10.100.20.32:1984` |

### Kameras

| Name | Modell | IP | Hauptstream | Substream |
|------|--------|-----|------------|-----------|
| skoda | Reolink RLC-510A | `10.100.90.11` | H.265 | H.264 |
| mazda | Reolink RLC-510A | `10.100.90.12` | H.265 | H.264 |
| sypialnia | Reolink E1 Pro | `10.100.90.14` | H.264 | H.264 |

### Bind Mounts (pve2 Host)

| Host-Pfad | LXC-Pfad | Zweck |
|-----------|----------|-------|
| `/opt/lxc-data/frigate-data` | `/data` | Frigate-Konfiguration |
| `/mnt/hdd-data/frigate` | `/media` | Aufnahmen (Toshiba HDD) |
| `/opt/docker-data/frigate-data` | `/opt/docker-data` | Docker-Daten |

### IaC-Verwaltung

**Terraform** (LXC erstellen/löschen):
```bash
cd ~/homelab-iac/terraform/lxc/pve2
terraform plan
terraform apply
```

**Nach jedem terraform apply** — Bind Mounts und Passthrough manuell auf pve2:
```bash
pct stop 320
pct set 320 --mp0 /opt/lxc-data/frigate-data,mp=/data
pct set 320 --mp1 /mnt/hdd-data/frigate,mp=/media
pct set 320 --mp2 /opt/docker-data/frigate-data,mp=/opt/docker-data
pct set 320 --dev0 /dev/dri/renderD128
chown -R 100000:100000 /opt/lxc-data/frigate-data
chown -R 100000:100000 /mnt/hdd-data/frigate
chown -R 100000:100000 /opt/docker-data/frigate-data
pct start 320
```

**Ansible** (Konfiguration und Deployment):
```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l frigate
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l frigate
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-frigate.yml -l frigate
```

### Frigate-Konfiguration

Hauptkonfiguration in `ansible/files/frigate-config.yml.j2`. Kamerapasswörter in `ansible/secrets.yml` (gitignored).

**Wichtige Einstellungen:**
- go2rtc als RTSP-Proxy (löst das Verbindungslimit der Reolink-Kameras)
- Intel QSV Hardware-Dekodierung über `/dev/dri/renderD128`
- MQTT → Mosquitto-Broker auf HA (`10.100.20.100`)
- Event-Aufbewahrung: 14 Tage
- Pre/Post-Capture-Puffer: 10 Sekunden

**Erkennungszonen (Mazda-Kamera):**
- `parking_til_1`, `parking_til_2` — Parkplätze des Nachbarn
- `parking_motocykl` — Motorradstellplatz
- `parking_mazda` — Autostellplatz
- Erkannte Objekte in Zonen: `person`, `cat`

### Bekannte Probleme und Lösungen

**Problem:** go2rtc startet RTSP nicht (Port 8554 nicht verfügbar)
**Ursache:** Frigate 0.17 erstellt eine leere `/config/go2rtc_homekit.yml`, die go2rtc blockiert
**Lösung:** `FRIGATE_DISABLE_HOMEKIT=true` in der docker-compose-Umgebung

**Problem:** Kamera offline nach Passwortänderung
**Lösung:** `camera_X_password` in `secrets.yml` aktualisieren und `deploy-frigate.yml` ausführen

**Problem:** Festplattengrößenänderung über `terraform apply` zerstört LXC (destroy+recreate)
**Lösung:** `pct resize` direkt auf Proxmox verwenden

### Netzwerk

- VLAN 90 (IoT) → VLAN 20 (SERVER): FortiGate-Regel `Frigate_to_Cams`
- Zugriff: SERVER_LAN (Frigate IP) → Kameras (VLAN90), RTSP-Port
- Aufnahmen von rsync ausgeschlossen (`--exclude='frigate/'` in `/usr/local/bin/rsync-hdd-backup.sh`)

### Home Assistant Integration

- Frigate-Integration über HACS (v5.15.3)
- MQTT: Mosquitto-Broker als HA Add-on
- Frigate URL in HA: `http://10.100.20.32:5000`

---

<a name="pl"></a>
## 🇵🇱 Polski

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Opis

Frigate to self-hosted NVR (Network Video Recorder) działający w kontenerze Docker na LXC 320 (pve2). System obsługuje trzy kamery Reolink, wykrywa obiekty (osoby, samochody, koty) i integruje się z Home Assistant przez MQTT.

### Infrastruktura

| Parametr | Wartość |
|----------|---------|
| Host | pve2 (`10.100.20.11`) |
| LXC ID | 320 |
| IP | `10.100.20.32` |
| Web UI | `http://10.100.20.32:5000` / `https://frigate.damianzientek.de` |
| go2rtc API | `http://10.100.20.32:1984` |

### Kamery

| Nazwa | Model | IP | Strumień główny | Substream |
|-------|-------|-----|----------------|-----------|
| skoda | Reolink RLC-510A | `10.100.90.11` | H.265 | H.264 |
| mazda | Reolink RLC-510A | `10.100.90.12` | H.265 | H.264 |
| sypialnia | Reolink E1 Pro | `10.100.90.14` | H.264 | H.264 |

### Bind Mounty (pve2 host)

| Ścieżka hosta | Ścieżka w LXC | Przeznaczenie |
|---------------|---------------|---------------|
| `/opt/lxc-data/frigate-data` | `/data` | Konfiguracja Frigate |
| `/mnt/hdd-data/frigate` | `/media` | Nagrania (Toshiba HDD) |
| `/opt/docker-data/frigate-data` | `/opt/docker-data` | Dane Docker |

### Zarządzanie IaC

**Terraform** (tworzenie/usuwanie LXC):
```bash
cd ~/homelab-iac/terraform/lxc/pve2
terraform plan
terraform apply
```

**Po każdym terraform apply** — bind mounty i passthrough ręcznie na pve2:
```bash
pct stop 320
pct set 320 --mp0 /opt/lxc-data/frigate-data,mp=/data
pct set 320 --mp1 /mnt/hdd-data/frigate,mp=/media
pct set 320 --mp2 /opt/docker-data/frigate-data,mp=/opt/docker-data
pct set 320 --dev0 /dev/dri/renderD128
chown -R 100000:100000 /opt/lxc-data/frigate-data
chown -R 100000:100000 /mnt/hdd-data/frigate
chown -R 100000:100000 /opt/docker-data/frigate-data
pct start 320
```

**Ansible** (konfiguracja i deploy):
```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l frigate
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l frigate
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-frigate.yml -l frigate
```

### Konfiguracja Frigate

Główna konfiguracja w `ansible/files/frigate-config.yml.j2`. Hasła kamer w `ansible/secrets.yml` (gitignored).

**Kluczowe ustawienia:**
- go2rtc jako RTSP proxy (rozwiązuje limit połączeń kamer Reolink)
- Intel QSV hardware decode przez `/dev/dri/renderD128`
- MQTT → Mosquitto broker na HA (`10.100.20.100`)
- Retencja eventów: 14 dni
- Pre/post capture buffer: 10 sekund

**Strefy detekcji (kamera Mazda):**
- `parking_til_1`, `parking_til_2` — miejsca parkingowe sąsiada
- `parking_motocykl` — miejsce motocykla
- `parking_mazda` — miejsce samochodu
- Wykrywane obiekty w strefach: `person`, `cat`

### Znane problemy i rozwiązania

**Problem:** go2rtc nie startuje RTSP (port 8554 niedostępny)
**Przyczyna:** Frigate 0.17 tworzy pusty `/config/go2rtc_homekit.yml` który blokuje go2rtc
**Rozwiązanie:** `FRIGATE_DISABLE_HOMEKIT=true` w environment docker-compose

**Problem:** Kamera offline po zmianie hasła
**Rozwiązanie:** Zaktualizować `camera_X_password` w `secrets.yml` i odpalić `deploy-frigate.yml`

**Problem:** Resize dysku przez `terraform apply` niszczy LXC (destroy+recreate)
**Rozwiązanie:** Używać `pct resize` bezpośrednio na Proxmox

### Sieć

- VLAN 90 (IoT) → VLAN 20 (SERVER): reguła FortiGate `Frigate_to_Cams`
- Dostęp: SERVER_LAN (Frigate IP) → kamery (VLAN90), port RTSP
- Nagrania wykluczone z rsync (`--exclude='frigate/'` w `/usr/local/bin/rsync-hdd-backup.sh`)

### Integracja Home Assistant

- Integracja Frigate przez HACS (v5.15.3)
- MQTT: Mosquitto broker jako Add-on w HA
- Frigate URL w HA: `http://10.100.20.32:5000`