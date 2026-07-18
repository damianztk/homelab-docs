# n8n — Automation Platform

<!-- Navigation -->
[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

---

<a name="english"></a>
## 🇬🇧 English

[🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

### Overview

n8n is a self-hosted workflow automation platform. In this homelab it serves as a universal automation layer for:
- Blog pipeline: Gitea → AI ghostwriter → Telegram review → translation → deploy
- Contact form handling: webhook → analysis → Telegram notification
- Future: CI/CD triggers, monitoring integrations, homelab event automation

**LXC:** 201 | **IP:** `10.x.x.x` | **Node:** pve1 | **URL:** `n8n.damianzientek.de`

### Architecture

```
n8n LXC (201)
├── Docker: n8nio/n8n          → port 5678 (UI + API)
└── Docker: n8nio/runners      → task runner sidecar (JS/Python sandbox)

Host bind mounts (pve1):
├── /opt/lxc-data/n8n-data     → /data         (LXC-level)
└── /opt/docker-data/n8n-data  → /opt/docker-data (Docker data)

n8n data: /opt/docker-data/n8n-data/n8n/  (→ /home/node/.n8n inside container)
```

### Prerequisites

- Debian 13 LXC template available on pve1
- `homelab-iac` repo cloned in WSL
- Ansible `community.docker` collection installed
- Telegram bot token available (for testing)

### Deployment

#### 1. Prepare host directories (on pve1)

```bash
mkdir -p /opt/lxc-data/n8n-data
mkdir -p /opt/docker-data/n8n-data
chown 100000:100000 /opt/docker-data/n8n-data
# Note: chown 100000 because unprivileged LXC remaps root (UID 0 inside LXC = UID 100000 on host)
# /opt/lxc-data/n8n-data does NOT need chown — it's LXC-level, not used by Docker directly
```

#### 2. Add secrets (WSL, secrets.yml)

```bash
openssl rand -hex 32  # → n8n_encryption_key
openssl rand -hex 32  # → n8n_runners_auth_token
```

Add to `ansible/secrets.yml`:
```yaml
n8n_encryption_key: "<generated>"
n8n_runners_auth_token: "<generated>"
```

⚠️ **Critical:** `n8n_encryption_key` must never change after first run — all saved credentials become unreadable if it does.

#### 3. Terraform (WSL)

```bash
cd terraform/lxc/pve1
terraform plan
terraform apply
```

#### 4. Set bind mounts (on pve1)

```bash
pct set 201 --mp0 /opt/lxc-data/n8n-data,mp=/data
pct set 201 --mp1 /opt/docker-data/n8n-data,mp=/opt/docker-data
pct reboot 201
```

#### 5. Ansible playbooks (WSL)

```bash
# Accept SSH fingerprint first
ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts

ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l n8n
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l n8n
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-n8n.yml -l n8n
```

#### 6. NPM reverse proxy

Forward: `n8n.damianzientek.de` → `http://10.x.x.x:5678`

Options: Force SSL ✓ | HTTP/2 ✓ | Websockets ✓

#### 7. First-run setup

Open `https://n8n.damianzientek.de` → create owner account → complete onboarding → activate community license (Settings → License).

### Troubleshooting

#### `Permission denied` on `/opt/docker-data/n8n`

The bind mount directory on the host has wrong ownership. Inside unprivileged LXC, UID mapping is:
- LXC `root` (UID 0) = host UID `100000`

Fix on pve1:
```bash
chown 100000:100000 /opt/docker-data/n8n-data
```
Then reboot LXC and rerun the playbook.

#### `mount_point` Terraform error: "bind is only allowed for root@pam"

Known bug in `bpg/proxmox` provider — bind mounts cannot be set via Terraform with API token auth. Do not include `mount_point` blocks in `main.tf`. Always set bind mounts via `pct set` after `terraform apply`. Add `mount_point` to `lifecycle.ignore_changes`.

#### `n8nio/n8n-runner:latest: not found`

The runner image is not available on `docker.n8n.io`. Use Docker Hub instead:
```yaml
n8n-runner:
  image: n8nio/runners:latest  # correct
  # NOT: docker.n8n.io/n8nio/n8n-runner:latest
```

#### `502 Bad Gateway` from NPM

n8n port was bound to `127.0.0.1:5678` — NPM cannot reach it from outside the LXC. Change compose to:
```yaml
ports:
  - "5678:5678"
```

#### `Host key verification failed` (Ansible)

SSH fingerprint not yet accepted. Run:
```bash
ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts
# or: ssh root@10.x.x.x  (accept manually)
```

---

<a name="deutsch"></a>
## 🇩🇪 Deutsch

[🇬🇧 English](#english) | [🇵🇱 Polski](#polski)

### Übersicht

n8n ist eine selbst gehostete Workflow-Automatisierungsplattform. Im Homelab dient sie als universelle Automatisierungsschicht für:
- Blog-Pipeline: Gitea → KI-Ghostwriter → Telegram-Review → Übersetzung → Deploy
- Kontaktformular: Webhook → Analyse → Telegram-Benachrichtigung
- Zukünftig: CI/CD-Trigger, Monitoring-Integrationen, Homelab-Event-Automatisierung

**LXC:** 201 | **IP:** `10.x.x.x` | **Node:** pve1 | **URL:** `n8n.damianzientek.de`

### Architektur

```
n8n LXC (201)
├── Docker: n8nio/n8n          → Port 5678 (UI + API)
└── Docker: n8nio/runners      → Task-Runner-Sidecar (JS/Python-Sandbox)

Host-Bind-Mounts (pve1):
├── /opt/lxc-data/n8n-data     → /data         (LXC-Ebene)
└── /opt/docker-data/n8n-data  → /opt/docker-data (Docker-Daten)

n8n-Daten: /opt/docker-data/n8n-data/n8n/  (→ /home/node/.n8n im Container)
```

### Voraussetzungen

- Debian-13-LXC-Template auf pve1 verfügbar
- `homelab-iac`-Repo in WSL geklont
- Ansible-Kollektion `community.docker` installiert
- Telegram-Bot-Token vorhanden (zum Testen)

### Deployment

#### 1. Host-Verzeichnisse vorbereiten (auf pve1)

```bash
mkdir -p /opt/lxc-data/n8n-data
mkdir -p /opt/docker-data/n8n-data
chown 100000:100000 /opt/docker-data/n8n-data
# Hinweis: chown 100000, weil unprivilegiertes LXC UIDs remappt (root im LXC = UID 100000 auf Host)
```

#### 2. Secrets hinzufügen (WSL, secrets.yml)

```bash
openssl rand -hex 32  # → n8n_encryption_key
openssl rand -hex 32  # → n8n_runners_auth_token
```

In `ansible/secrets.yml` eintragen:
```yaml
n8n_encryption_key: "<generiert>"
n8n_runners_auth_token: "<generiert>"
```

⚠️ **Wichtig:** `n8n_encryption_key` darf nach dem ersten Start niemals geändert werden — alle gespeicherten Credentials werden sonst unlesbar.

#### 3. Terraform (WSL)

```bash
cd terraform/lxc/pve1
terraform plan
terraform apply
```

#### 4. Bind-Mounts setzen (auf pve1)

```bash
pct set 201 --mp0 /opt/lxc-data/n8n-data,mp=/data
pct set 201 --mp1 /opt/docker-data/n8n-data,mp=/opt/docker-data
pct reboot 201
```

#### 5. Ansible-Playbooks (WSL)

```bash
# SSH-Fingerprint zuerst akzeptieren
ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts

ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l n8n
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l n8n
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-n8n.yml -l n8n
```

#### 6. NPM Reverse Proxy

Weiterleitung: `n8n.damianzientek.de` → `http://10.x.x.x:5678`

Optionen: Force SSL ✓ | HTTP/2 ✓ | Websockets ✓

#### 7. Ersteinrichtung

`https://n8n.damianzientek.de` öffnen → Owner-Account erstellen → Onboarding abschließen → Community-Lizenz aktivieren (Einstellungen → Lizenz).

### Fehlerbehebung

#### `Permission denied` bei `/opt/docker-data/n8n`

Das Bind-Mount-Verzeichnis auf dem Host hat falsche Eigentümerschaft. In einem unprivilegierten LXC gilt:
- LXC `root` (UID 0) = Host-UID `100000`

Lösung auf pve1:
```bash
chown 100000:100000 /opt/docker-data/n8n-data
```
Danach LXC neu starten und Playbook erneut ausführen.

#### `mount_point` Terraform-Fehler: „bind is only allowed for root@pam"

Bekannter Bug im `bpg/proxmox`-Provider — Bind-Mounts können mit API-Token-Authentifizierung nicht über Terraform gesetzt werden. Keine `mount_point`-Blöcke in `main.tf` verwenden. Bind-Mounts immer nach `terraform apply` über `pct set` setzen. `mount_point` zu `lifecycle.ignore_changes` hinzufügen.

#### `n8nio/n8n-runner:latest: not found`

Das Runner-Image ist auf `docker.n8n.io` nicht verfügbar. Stattdessen Docker Hub verwenden:
```yaml
n8n-runner:
  image: n8nio/runners:latest  # korrekt
  # NICHT: docker.n8n.io/n8nio/n8n-runner:latest
```

#### `502 Bad Gateway` von NPM

n8n-Port war an `127.0.0.1:5678` gebunden — NPM kann von außerhalb des LXC nicht darauf zugreifen. Compose ändern:
```yaml
ports:
  - "5678:5678"
```

#### `Host key verification failed` (Ansible)

SSH-Fingerprint noch nicht akzeptiert:
```bash
ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts
```

---

<a name="polski"></a>
## 🇵🇱 Polski

[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch)

### Przegląd

n8n to samodzielnie hostowana platforma automatyzacji workflow. W homelabie pełni rolę uniwersalnej warstwy automatyzacji dla:
- Pipeline blogowy: Gitea → ghostwriter AI → recenzja Telegram → tłumaczenie → deploy
- Obsługa formularza kontaktowego: webhook → analiza → powiadomienie Telegram
- W przyszłości: triggery CI/CD, integracje monitoringu, automatyzacja zdarzeń homelabowych

**LXC:** 201 | **IP:** `10.x.x.x` | **Node:** pve1 | **URL:** `n8n.damianzientek.de`

### Architektura

```
n8n LXC (201)
├── Docker: n8nio/n8n          → port 5678 (UI + API)
└── Docker: n8nio/runners      → task runner sidecar (sandbox JS/Python)

Bind mounty na hoście (pve1):
├── /opt/lxc-data/n8n-data     → /data         (poziom LXC)
└── /opt/docker-data/n8n-data  → /opt/docker-data (dane Docker)

Dane n8n: /opt/docker-data/n8n-data/n8n/  (→ /home/node/.n8n w kontenerze)
```

### Wymagania wstępne

- Szablon Debian 13 LXC dostępny na pve1
- Repo `homelab-iac` sklonowane w WSL
- Kolekcja Ansible `community.docker` zainstalowana
- Token bota Telegram dostępny (do testów)

### Wdrożenie

#### 1. Przygotowanie katalogów na hoście (na pve1)

```bash
mkdir -p /opt/lxc-data/n8n-data
mkdir -p /opt/docker-data/n8n-data
chown 100000:100000 /opt/docker-data/n8n-data
# Uwaga: chown 100000, bo nieuprzywilejowany LXC remapuje UIDs (root w LXC = UID 100000 na hoście)
# /opt/lxc-data/n8n-data NIE wymaga chown — to poziom LXC, nie używany bezpośrednio przez Docker
```

#### 2. Dodanie sekretów (WSL, secrets.yml)

```bash
openssl rand -hex 32  # → n8n_encryption_key
openssl rand -hex 32  # → n8n_runners_auth_token
```

Dodać do `ansible/secrets.yml`:
```yaml
n8n_encryption_key: "<wygenerowany>"
n8n_runners_auth_token: "<wygenerowany>"
```

⚠️ **Krytyczne:** `n8n_encryption_key` nigdy nie może być zmieniony po pierwszym uruchomieniu — wszystkie zapisane credentials stają się nieodczytywalne.

#### 3. Terraform (WSL)

```bash
cd terraform/lxc/pve1
terraform plan
terraform apply
```

#### 4. Ustawienie bind mountów (na pve1)

```bash
pct set 201 --mp0 /opt/lxc-data/n8n-data,mp=/data
pct set 201 --mp1 /opt/docker-data/n8n-data,mp=/opt/docker-data
pct reboot 201
```

#### 5. Playbooki Ansible (WSL)

```bash
# Najpierw zaakceptować fingerprint SSH
ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts

ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l n8n
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l n8n
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-n8n.yml -l n8n
```

#### 6. Reverse proxy NPM

Przekierowanie: `n8n.damianzientek.de` → `http://10.x.x.x:5678`

Opcje: Force SSL ✓ | HTTP/2 ✓ | Websockets ✓

#### 7. Pierwsze uruchomienie

Otworzyć `https://n8n.damianzientek.de` → utworzyć konto właściciela → zakończyć onboarding → aktywować licencję community (Ustawienia → Licencja).

### Rozwiązywanie problemów

#### `Permission denied` przy `/opt/docker-data/n8n`

Katalog bind mountu na hoście ma nieprawidłowego właściciela. W nieuprzywilejowanym LXC mapowanie UID wygląda następująco:
- `root` w LXC (UID 0) = UID `100000` na hoście

Rozwiązanie na pve1:
```bash
chown 100000:100000 /opt/docker-data/n8n-data
```
Następnie zrestartować LXC i ponownie uruchomić playbook.

#### Błąd Terraform `mount_point`: „bind is only allowed for root@pam"

Znany bug providera `bpg/proxmox` — bind mounty nie mogą być ustawiane przez Terraform z tokenem API. Nie używać bloków `mount_point` w `main.tf`. Bind mounty zawsze ustawiać przez `pct set` po `terraform apply`. Dodać `mount_point` do `lifecycle.ignore_changes`.

#### `n8nio/n8n-runner:latest: not found`

Image runnera nie jest dostępny na `docker.n8n.io`. Użyć Docker Hub:
```yaml
n8n-runner:
  image: n8nio/runners:latest  # poprawnie
  # NIE: docker.n8n.io/n8nio/n8n-runner:latest
```

#### `502 Bad Gateway` z NPM

Port n8n był zbindowany na `127.0.0.1:5678` — NPM nie może do niego dotrzeć spoza LXC. Zmienić w compose:
```yaml
ports:
  - "5678:5678"
```

#### `Host key verification failed` (Ansible)

Fingerprint SSH nie został jeszcze zaakceptowany:
```bash
ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts
```
