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
| skoda | Reolink RLC-510A | `10.100.90.11` | H.265 2880×1616 | H.264 640×480 |
| mazda | Reolink RLC-510A | `10.100.90.12` | H.265 2880×1616 | H.264 640×480 |
| sypialnia | Reolink E1 Pro | `10.100.90.14` | H.264 2880×1616 | H.264 896×512 |

### Bind Mounts (pve2 host)

| Host path | LXC path | Purpose |
|-----------|----------|---------|
| `/opt/lxc-data/frigate-data` | `/data` | Frigate configuration + database |
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
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-frigate.yml -l frigate
```

**After config changes** — force container restart (Ansible only restarts when docker-compose.yml changes):

```bash
ssh root@10.100.20.32 "cd /opt/docker-data && docker compose down && docker compose up -d"
```

### Frigate Configuration

Main configuration in `ansible/files/frigate-config.yml.j2`. Camera passwords and MQTT credentials in `ansible/secrets.yml` (gitignored).

**go2rtc stream architecture:**

Each camera has two separate named streams in go2rtc:

- `<name>_main` — full resolution, used for `record` and `stream`
- `<name>_sub` — low resolution, used for `detect` only

This is critical — using a single stream for both roles causes VAAPI context exhaustion and ffmpeg crashes.

**Key settings:**

- go2rtc as RTSP proxy (solves Reolink camera connection limit)
- `ffmpeg.hwaccel_args: []` — hardware decode explicitly disabled (iGPU shared with Jellyfin; auto-detection would cause context exhaustion with 6 simultaneous ffmpeg processes)
- CPU detector (`cpu1`, 3 threads) — no Coral TPU
- `fps: 5` on detect for all cameras (sufficient for object detection, reduces CPU load)
- `shm_size: 512mb` — required for pre_capture buffering with 3 cameras
- MQTT → Mosquitto broker on HA (`10.100.20.100`), user `frigate`
- Event retention: 14 days
- Pre-capture buffer: 25 seconds, post-capture: 10 seconds

**Detection zones (Mazda camera):**

- `parking_til_1`, `parking_til_2` — neighbor's parking spots
- `parking_motocykl` — motorcycle spot
- `parking_mazda` — car spot
- Detected objects in zones: `person`, `cat`, `car`

### MQTT Integration

Frigate sends events to Mosquitto broker (HA add-on) via MQTT. Home Assistant receives these events through the MQTT integration and Frigate HACS integration.

**Components:**

- Mosquitto broker: HA add-on, port 1883, user `frigate`
- MQTT credentials: stored in `ansible/secrets.yml` (`mqtt_username`, `mqtt_password`)
- HA MQTT integration: configured with same `frigate` credentials
- Frigate HACS integration v5.15.3: URL `http://10.100.20.32:5000`

**Result in HA:** 8 devices, 153 entities — server, 3 cameras, 4 Mazda zones as separate devices.

**Troubleshooting MQTT:**

```bash
# Test connectivity from Frigate LXC
mosquitto_pub -h 10.100.20.100 -p 1883 -u frigate -P 'PASSWORD' -t test -m hello -d

# Check Frigate logs for MQTT
ssh root@10.100.20.32 "docker logs frigate 2>&1 | grep -i mqtt | tail -10"
```

### Authentication

Frigate enforces authentication only on port `8971` (HTTPS). Port `5000` is unauthenticated — used by HA integration.

**Config:**

```yaml
auth:
  enabled: true
  trusted_proxies:
    - 10.100.20.24/32    # NPM IP
```

**NPM configuration for `frigate.damianzientek.de`:**

- Forward scheme: `https`
- Forward port: `8971`
- SSL verify: off (Frigate uses self-signed cert)

**Admin password** is stored in `/opt/docker-data/frigate/frigate.db`. Set via UI on first login.

### Known Issues and Solutions

**Issue:** go2rtc doesn't start RTSP (port 8554 unavailable)
**Cause:** Frigate 0.17 creates empty `/config/go2rtc_homekit.yml` which blocks go2rtc
**Solution:** `FRIGATE_DISABLE_HOMEKIT=true` in docker-compose environment — critical, do not remove

**Issue:** ffmpeg crashes with `Failed to sync surface` / `hwdownload failed`
**Cause:** Frigate 0.17 auto-detects VAAPI when `/dev/dri/renderD128` is present, even without explicit config. With split streams (6 ffmpeg processes) this exhausts iGPU contexts.
**Solution:** `ffmpeg: hwaccel_args: []` in config — explicit empty list overrides auto-detection

**Issue:** sypialnia detect errors (`Invalid data found when processing input`)
**Cause:** detect was receiving main stream (2880×1616) instead of substream
**Solution:** Split go2rtc streams into `_main` and `_sub`, assign `detect` role only to `_sub`

**Issue:** Missing pre-capture (recording starts when object already in frame)
**Cause:** SHM too small (256mb) for 3-camera buffering, or detect on main stream causing buffer overflow
**Solution:** `shm_size: 512mb` + detect on substream only. Also increase `pre_capture` to 25s.

**Issue:** MQTT `Not authorized` despite correct credentials
**Cause:** Mosquitto add-on user list not saved/applied correctly
**Solution:** Remove and re-add user in Mosquitto add-on config, restart add-on, verify with `mosquitto_pub -d`

**Issue:** Disk resize via `terraform apply` destroys LXC (destroy+recreate)
**Solution:** Use `pct resize` directly on Proxmox

### Network

- VLAN 90 (IoT) → VLAN 20 (SERVER): FortiGate rule `Frigate_to_Cams`
- Access: SERVER_LAN (Frigate IP `10.100.20.32`) → cameras (VLAN90), RTSP port
- Recordings excluded from rsync (`--exclude='frigate/'` in rsync-hdd-backup.sh on pve2)

### Home Assistant Integration

- Frigate integration via HACS (v5.15.3)
- Frigate URL in HA: `http://10.100.20.32:5000`, SSL disabled
- MQTT: Mosquitto broker as HA Add-on, user `frigate`
- 8 devices visible: Frigate server + 3 cameras + 4 Mazda parking zones
- HA can use zone data in automations: "person detected in parking_mazda"

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
| skoda | Reolink RLC-510A | `10.100.90.11` | H.265 2880×1616 | H.264 640×480 |
| mazda | Reolink RLC-510A | `10.100.90.12` | H.265 2880×1616 | H.264 640×480 |
| sypialnia | Reolink E1 Pro | `10.100.90.14` | H.264 2880×1616 | H.264 896×512 |

### Bind Mounts (pve2 Host)

| Host-Pfad | LXC-Pfad | Zweck |
|-----------|----------|-------|
| `/opt/lxc-data/frigate-data` | `/data` | Frigate-Konfiguration + Datenbank |
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
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-frigate.yml -l frigate
```

**Nach Konfigurationsänderungen** — Container-Neustart erzwingen:

```bash
ssh root@10.100.20.32 "cd /opt/docker-data && docker compose down && docker compose up -d"
```

### Frigate-Konfiguration

Hauptkonfiguration in `ansible/files/frigate-config.yml.j2`. Kamerapasswörter und MQTT-Zugangsdaten in `ansible/secrets.yml` (gitignored).

**go2rtc Stream-Architektur:**

Jede Kamera hat zwei separate benannte Streams in go2rtc:

- `<name>_main` — volle Auflösung, für `record` und `stream`
- `<name>_sub` — niedrige Auflösung, nur für `detect`

Dies ist kritisch — ein einzelner Stream für beide Rollen führt zu VAAPI-Kontexterschöpfung und ffmpeg-Abstürzen.

**Wichtige Einstellungen:**

- go2rtc als RTSP-Proxy (löst das Verbindungslimit der Reolink-Kameras)
- `ffmpeg.hwaccel_args: []` — Hardware-Dekodierung explizit deaktiviert (iGPU wird mit Jellyfin geteilt)
- CPU-Detektor (`cpu1`, 3 Threads) — kein Coral TPU
- `fps: 5` für detect bei allen Kameras
- `shm_size: 512mb` — erforderlich für Pre-Capture-Pufferung mit 3 Kameras
- MQTT → Mosquitto-Broker auf HA (`10.100.20.100`), Benutzer `frigate`
- Event-Aufbewahrung: 14 Tage
- Pre-Capture-Puffer: 25 Sekunden, Post-Capture: 10 Sekunden

**Erkennungszonen (Mazda-Kamera):**

- `parking_til_1`, `parking_til_2` — Parkplätze des Nachbarn
- `parking_motocykl` — Motorradstellplatz
- `parking_mazda` — Autostellplatz
- Erkannte Objekte in Zonen: `person`, `cat`, `car`

### MQTT-Integration

**Komponenten:**

- Mosquitto-Broker: HA Add-on, Port 1883, Benutzer `frigate`
- MQTT-Zugangsdaten: in `ansible/secrets.yml` (`mqtt_username`, `mqtt_password`)
- HA MQTT-Integration: mit denselben `frigate`-Zugangsdaten konfiguriert
- Frigate HACS-Integration v5.15.3: URL `http://10.100.20.32:5000`

**Ergebnis in HA:** 8 Geräte, 153 Entitäten — Server, 3 Kameras, 4 Mazda-Zonen als separate Geräte.

### Authentifizierung

Frigate erzwingt Authentifizierung nur auf Port `8971` (HTTPS). Port `5000` ist nicht authentifiziert — wird von der HA-Integration verwendet.

**Konfiguration:**

```yaml
auth:
  enabled: true
  trusted_proxies:
    - 10.100.20.24/32    # NPM IP
```

**NPM-Konfiguration für `frigate.damianzientek.de`:**

- Forward scheme: `https`
- Forward port: `8971`
- SSL verify: off (Frigate verwendet selbstsigniertes Zertifikat)

**Admin-Passwort** wird in `/opt/docker-data/frigate/frigate.db` gespeichert. Beim ersten Login über die UI festlegen.

### Bekannte Probleme und Lösungen

**Problem:** go2rtc startet RTSP nicht (Port 8554 nicht verfügbar)
**Ursache:** Frigate 0.17 erstellt leere `/config/go2rtc_homekit.yml`, die go2rtc blockiert
**Lösung:** `FRIGATE_DISABLE_HOMEKIT=true` in docker-compose — kritisch, nicht entfernen

**Problem:** ffmpeg-Abstürze mit `Failed to sync surface`
**Ursache:** Frigate erkennt VAAPI automatisch; mit 6 ffmpeg-Prozessen werden iGPU-Kontexte erschöpft
**Lösung:** `ffmpeg: hwaccel_args: []` in der Konfiguration

**Problem:** MQTT `Not authorized` trotz korrekter Zugangsdaten
**Ursache:** Mosquitto Add-on speichert Benutzerliste nicht korrekt
**Lösung:** Benutzer löschen und neu anlegen, Add-on neu starten, mit `mosquitto_pub -d` verifizieren

**Problem:** Festplattengrößenänderung über `terraform apply` zerstört LXC
**Lösung:** `pct resize` direkt auf Proxmox verwenden

### Netzwerk

- VLAN 90 (IoT) → VLAN 20 (SERVER): FortiGate-Regel `Frigate_to_Cams`
- Zugriff: SERVER_LAN (Frigate IP `10.100.20.32`) → Kameras (VLAN90), RTSP-Port
- Aufnahmen von rsync ausgeschlossen (`--exclude='frigate/'` in rsync-hdd-backup.sh auf pve2)

### Home Assistant Integration

- Frigate-Integration über HACS (v5.15.3)
- Frigate URL in HA: `http://10.100.20.32:5000`, SSL deaktiviert
- MQTT: Mosquitto-Broker als HA Add-on, Benutzer `frigate`
- 8 Geräte sichtbar: Frigate-Server + 3 Kameras + 4 Mazda-Parkzonen

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
| skoda | Reolink RLC-510A | `10.100.90.11` | H.265 2880×1616 | H.264 640×480 |
| mazda | Reolink RLC-510A | `10.100.90.12` | H.265 2880×1616 | H.264 640×480 |
| sypialnia | Reolink E1 Pro | `10.100.90.14` | H.264 2880×1616 | H.264 896×512 |

### Bind Mounty (pve2 host)

| Ścieżka hosta | Ścieżka w LXC | Przeznaczenie |
|---------------|---------------|---------------|
| `/opt/lxc-data/frigate-data` | `/data` | Konfiguracja Frigate + baza danych |
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
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-frigate.yml -l frigate
```

**Po zmianach w configu** — wymuś restart kontenera (Ansible restartuje tylko gdy zmienia się docker-compose.yml):

```bash
ssh root@10.100.20.32 "cd /opt/docker-data && docker compose down && docker compose up -d"
```

### Konfiguracja Frigate

Główna konfiguracja w `ansible/files/frigate-config.yml.j2`. Hasła kamer i credentials MQTT w `ansible/secrets.yml` (gitignored).

**Architektura streamów go2rtc:**

Każda kamera ma dwa osobne strumienie w go2rtc:

- `<nazwa>_main` — pełna rozdzielczość, dla `record` i `stream`
- `<nazwa>_sub` — niska rozdzielczość, wyłącznie dla `detect`

To jest krytyczne — użycie jednego strumienia dla obu ról powoduje wyczerpanie kontekstów VAAPI i crashe ffmpeg.

**Kluczowe ustawienia:**

- go2rtc jako RTSP proxy (rozwiązuje limit połączeń kamer Reolink)
- `ffmpeg.hwaccel_args: []` — hardware decode jawnie wyłączony (iGPU współdzielone z Jellyfinem; auto-detekcja przy 6 procesach ffmpeg wyczerpuje konteksty iGPU)
- Detektor CPU (`cpu1`, 3 wątki) — brak Coral TPU
- `fps: 5` dla detect na każdej kamerze (wystarczające do detekcji, odciąża CPU)
- `shm_size: 512mb` — wymagane do buforowania pre_capture przy 3 kamerach
- MQTT → Mosquitto broker na HA (`10.100.20.100`), user `frigate`
- Retencja eventów: 14 dni
- Pre-capture buffer: 25 sekund, post-capture: 10 sekund

**Strefy detekcji (kamera Mazda):**

- `parking_til_1`, `parking_til_2` — miejsca parkingowe sąsiada
- `parking_motocykl` — miejsce motocykla
- `parking_mazda` — miejsce samochodu
- Wykrywane obiekty w strefach: `person`, `cat`, `car`

### Integracja MQTT

Frigate wysyła zdarzenia do Mosquitto brokera (HA add-on) przez MQTT. Home Assistant odbiera te zdarzenia przez integrację MQTT i integrację Frigate (HACS).

**Komponenty:**

- Mosquitto broker: HA add-on, port 1883, user `frigate`
- Credentials MQTT: w `ansible/secrets.yml` (`mqtt_username`, `mqtt_password`)
- Integracja MQTT w HA: skonfigurowana z tymi samymi credentials `frigate`
- Integracja Frigate HACS v5.15.3: URL `http://10.100.20.32:5000`

**Efekt w HA:** 8 urządzeń, 153 encje — serwer, 3 kamery, 4 strefy Mazda jako osobne urządzenia.

**Diagnostyka MQTT:**

```bash
# Test połączenia z LXC Frigate
mosquitto_pub -h 10.100.20.100 -p 1883 -u frigate -P 'HASLO' -t test -m hello -d

# Logi MQTT w Frigate
ssh root@10.100.20.32 "docker logs frigate 2>&1 | grep -i mqtt | tail -10"
```

### Autentykacja

Frigate wymusza autentykację tylko na porcie `8971` (HTTPS). Port `5000` jest nieuwierzytelniony — używany przez integrację HA.

**Config:**

```yaml
auth:
  enabled: true
  trusted_proxies:
    - 10.100.20.24/32    # IP NPM
```

**Konfiguracja NPM dla `frigate.damianzientek.de`:**

- Forward scheme: `https`
- Forward port: `8971`
- SSL verify: off (Frigate używa self-signed cert)

**Hasło admina** przechowywane w `/opt/docker-data/frigate/frigate.db`. Ustawiane przez UI przy pierwszym logowaniu.

### Znane problemy i rozwiązania

**Problem:** go2rtc nie startuje RTSP (port 8554 niedostępny)
**Przyczyna:** Frigate 0.17 tworzy pusty `/config/go2rtc_homekit.yml` który blokuje go2rtc
**Rozwiązanie:** `FRIGATE_DISABLE_HOMEKIT=true` w environment docker-compose — krytyczne, nie usuwać

**Problem:** Crashe ffmpeg z błędem `Failed to sync surface` / `hwdownload failed`
**Przyczyna:** Frigate 0.17 automatycznie wykrywa VAAPI gdy widzi `/dev/dri/renderD128`, nawet bez wpisu w configu. Przy split streamach (6 procesów ffmpeg) wyczerpuje konteksty iGPU.
**Rozwiązanie:** `ffmpeg: hwaccel_args: []` w configu — pusta lista nadpisuje auto-detekcję

**Problem:** Błędy detect kamery sypialnia (`Invalid data found when processing input`)
**Przyczyna:** detect dostawał main stream (2880×1616) zamiast substream
**Rozwiązanie:** Split streamów go2rtc na `_main` i `_sub`, rola `detect` tylko na `_sub`

**Problem:** Brak momentu przyjazdu/odjazdu auta w nagraniach
**Przyczyna:** Pre-capture za krótki (10s), lub brak `car` w obiektach strefy
**Rozwiązanie:** `pre_capture: 25` + dodanie `car` do `objects` w strefach Mazda

**Problem:** MQTT `Not authorized` mimo poprawnych credentials
**Przyczyna:** Lista użytkowników Mosquitto add-on nie jest poprawnie zapisywana
**Rozwiązanie:** Usunąć i ponownie dodać usera, zrestartować add-on, zweryfikować przez `mosquitto_pub -d`

**Problem:** Resize dysku przez `terraform apply` niszczy LXC (destroy+recreate)
**Rozwiązanie:** Używać `pct resize` bezpośrednio na Proxmox

### Sieć

- VLAN 90 (IoT) → VLAN 20 (SERVER): reguła FortiGate `Frigate_to_Cams`
- Dostęp: SERVER_LAN (Frigate IP `10.100.20.32`) → kamery (VLAN90), port RTSP
- Nagrania wykluczone z rsync (`--exclude='frigate/'` w rsync-hdd-backup.sh na pve2)

### Integracja Home Assistant

- Integracja Frigate przez HACS (v5.15.3)
- Frigate URL w HA: `http://10.100.20.32:5000`, SSL odznaczony
- MQTT: Mosquitto broker jako Add-on w HA, user `frigate`
- 8 urządzeń widocznych: serwer Frigate + 3 kamery + 4 strefy parkingowe Mazda
- HA może używać danych stref w automatyzacjach: "wykryto osobę w strefie parking_mazda"
