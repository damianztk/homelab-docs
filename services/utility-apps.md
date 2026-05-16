# utility-apps — Docker LXC (pve1, ID 300)

**Language / Sprache / Język:**
[English](#english) | [Deutsch](#deutsch) | [Polski](#polski)

---

## English

### Overview

`utility-apps` is a Debian 13 LXC container on pve1 acting as a Docker host for lightweight user-facing applications. It replaced the former dedicated Kavita LXC (also ID 300) and follows the same Docker-host pattern as `arr-stack` on pve2.

**Node:** pve1 (`10.100.20.10`)
**LXC ID:** 300
**IP:** `10.100.20.30`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 cores | **Disk:** 16 GB (local-lvm)
**Nesting:** enabled (required for Docker)

---

### Services

Two independent Docker Compose projects run inside this LXC.

#### Stack: utility-apps (`/opt/docker-data/docker-compose.yml`)

| Service | Port (host→container) | URL | Notes |
|---------|----------------------|-----|-------|
| Vaultwarden | 8080→80 | https://vault.damianzientek.de | Password manager |
| Kavita | 5000→5000 | https://kavita.damianzientek.de | E-book library (migrated from dedicated LXC) |
| Actual Budget | 5006→5006 | https://budzet.damianzientek.de | Personal finance tracker |
| Ntfy | 8090→80 | https://ntfy.damianzientek.de | Push notifications |
| Homarr | 7575→**3000** | https://homarr.damianzientek.de | Dashboard (container port is 3000, not 7575!) |
| Stirling PDF | 8091→8080 | https://edytor-pdf.damianzientek.de | PDF editor/tools |

#### Stack: wger (`/opt/docker-data/wger-stack/`)

| Service | Port | Notes |
|---------|------|-------|
| wger-nginx | 8100→80 | https://trening.damianzientek.de — serves static files + proxies to Gunicorn |
| wger-web | expose 8000 | Django app (Gunicorn), healthcheck enabled |
| wger-db | expose 5432 | postgres:15 |
| wger-cache | expose 6379 | redis:7 |
| wger-celery-worker | — | `/start-worker` |
| wger-celery-beat | — | `/start-beat` |

---

### Directory Structure

**On host (pve1):**
```
/opt/lxc-data/utility-apps-data/     → bind-mounted to /data inside LXC
/opt/docker-data/utility-apps-data/  → bind-mounted to /opt/docker-data inside LXC
    ├── docker-compose.yml            ← utility-apps stack
    ├── vaultwarden/
    ├── kavita/                       ← migrated from old LXC
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/
    │   └── configs/
    └── wger-stack/                   ← separate Compose project
        ├── docker-compose.yml
        ├── nginx.conf
        ├── postgres-data/
        ├── redis-data/
        └── media/
        (wger-static is a Docker named volume)

/mnt/hdd-data2/kavita/               → bind-mounted to /mnt/kavita-library inside LXC
```

**Bind mounts (`/etc/pve/lxc/300.conf`):**
```
mp0: /opt/lxc-data/utility-apps-data,mp=/data
mp1: /opt/docker-data/utility-apps-data,mp=/opt/docker-data
mp2: /mnt/hdd-data2/kavita,mp=/mnt/kavita-library
```

**Inside LXC:**
```
/data/                        ← LXC working data
/opt/docker-data/
    ├── docker-compose.yml    ← utility-apps stack
    ├── vaultwarden/
    ├── kavita/
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/configs/
    └── wger-stack/           ← wger Compose project
/mnt/kavita-library/          ← book library (beletrystyka, komiksy, ogólne, poradniki)
```

---

### Infrastructure as Code

**Terraform** (`homelab-iac/terraform/lxc/pve1/main.tf`) provisions the LXC container.
**Ansible** (`homelab-iac/ansible/playbooks/`) handles everything inside.

#### Playbooks

| Playbook | Purpose |
|----------|---------|
| `setup-base.yml` | Base packages, timezone, hostname |
| `install-docker.yml` | Docker Engine + Compose plugin |
| `deploy-utility-apps.yml` | Full utility-apps stack (template-based) |
| `deploy-wger.yml` | wger fitness stack |

#### Jinja2 Templates (`ansible/files/`)

| File | Purpose |
|------|---------|
| `utility-apps-compose.yml.j2` | docker-compose.yml for utility-apps stack |
| `wger-compose.yml.j2` | docker-compose.yml for wger stack |
| `nginx-wger.conf` | nginx config for wger (copied by deploy-wger.yml) |

**Secrets:** `ansible/secrets.yml` (gitignored) — contains:
- `vaultwarden_admin_token` — Argon2 PHC hash
- `homarr_secret_key` — 64-char hex (`openssl rand -hex 32`)
- `wger_secret_key` — 64-char hex
- `wger_db_password` — base64 password (`openssl rand -base64 16`)
- `mqtt_*`, `camera_*` — Frigate-related

---

### Deployment

```bash
# 1. Provision LXC (only needed for fresh setup)
cd ~/homelab-iac/terraform/lxc/pve1
terraform apply

# 2. Set bind mounts manually on pve1 host (Terraform bug — see Known Issues)
pct set 300 -mp0 /opt/lxc-data/utility-apps-data,mp=/data
pct set 300 -mp1 /opt/docker-data/utility-apps-data,mp=/opt/docker-data
pct set 300 -mp2 /mnt/hdd-data2/kavita,mp=/mnt/kavita-library
pct stop 300 && pct start 300

# 3. Install Docker
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml

# 4. Deploy utility-apps stack
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-utility-apps.yml

# 5. Deploy wger stack
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-wger.yml
```

**Adding a new service to utility-apps stack:**
1. Add service block to `ansible/files/utility-apps-compose.yml.j2`
2. Add directory name to `loop` in `deploy-utility-apps.yml`
3. Add any secrets to `ansible/secrets.yml`
4. `git add -A && git commit -m "feat: add <service>" && git push`
5. `ansible-playbook -i ... deploy-utility-apps.yml --check`
6. `ansible-playbook -i ... deploy-utility-apps.yml`
7. Add proxy host in NPM (`10.100.20.30:<port>`)

---

### Known Issues & Gotchas

**1. Terraform bind mount HTTP 403**
`bpg/proxmox` provider returns HTTP 403 when setting bind mounts via `mount_point {}` block with a `root@pam` API token. Bind mounts must be set manually via `pct set`. The `mount_point` blocks remain in `main.tf` for documentation purposes.

**2. `$$` escaping in docker-compose.yml**
Values containing `$` (e.g. Argon2 hashes) must use `$$` to prevent Docker variable interpolation. In Jinja2 template:
```yaml
- ADMIN_TOKEN={{ vaultwarden_admin_token | replace('$', '$$') }}
```

**3. Homarr container port is 3000, not 7575**
Host port `7575` maps to container port `3000` (Next.js). Mapping `7575:7575` results in a connection failure.

**4. wger requires nginx sidecar for static files**
`WGER_USE_GUNICORN=True` starts Gunicorn on port 8000 — Gunicorn does not serve static files. A separate nginx container shares the `wger-static` named volume and serves `/static/` and `/media/`. NPM proxies to nginx (port 80), not directly to Gunicorn.

**5. wger admin setup via Django shell**
The `/admin` URL does not exist in wger. Use `/en/user/list` (requires `is_superuser=True`).
```bash
# Set superuser
ssh utility-apps "docker exec wger-web python3 /home/wger/src/manage.py shell -c \
\"from django.contrib.auth.models import User; u = User.objects.get(username='damian'); \
u.is_active = True; u.is_staff = True; u.is_superuser = True; u.save()\""

# Verify email (use update, not get_or_create — the latter won't update existing records)
ssh utility-apps "docker exec wger-web python3 /home/wger/src/manage.py shell -c \
\"from allauth.account.models import EmailAddress; \
EmailAddress.objects.filter(user__username='damian').update(verified=True, primary=True)\""
```
Note: use `python3`, not `python` (not in PATH). Never use `-it` flags in non-interactive SSH exec.

**6. Disk resize without downtime**
```bash
ssh pve1 "pct resize 300 rootfs 16G"
```
Works on a running LXC. Update `size` in `main.tf` afterwards.

**7. Android Private DNS bypasses AdGuard**
Local subdomains (`*.damianzientek.de`) resolve via AdGuard Home wildcard rewrite. Android Private DNS bypasses this — disable it on the phone. Use Tailscale when outside home network.

---

### Design Decisions

- **Docker LXC over individual LXC per service** — consistent with `arr-stack` pattern on pve2; one host to manage, one Compose file per stack, Ansible deploys everything.
- **Jinja2 templates for docker-compose** — single `deploy-utility-apps.yml` manages all services via `utility-apps-compose.yml.j2`. Adding a service = one block in the template + one line in the loop.
- **Separate Compose project for wger** — wger is a multi-container stack (web, db, cache, celery ×2, nginx). Keeping it isolated from the utility-apps stack avoids coupling and simplifies troubleshooting.
- **Debian 13 (Trixie)** — stable since July 2025; consistent with other LXC containers on pve1/pve2.
- **Bind mounts to host** — all persistent data lives outside rootfs. Migrating, snapshotting, or rebuilding the LXC never risks application data.
- **`ansible/secrets.yml` + `.gitignore`** — secrets never committed to repository.

---
---

## Deutsch

### Überblick

`utility-apps` ist ein Debian-13-LXC-Container auf pve1, der als Docker-Host für leichtgewichtige Benutzeranwendungen dient. Er ersetzt den früheren dedizierten Kavita-LXC (ebenfalls ID 300) und folgt demselben Docker-Host-Muster wie `arr-stack` auf pve2.

**Node:** pve1 (`10.100.20.10`)
**LXC-ID:** 300
**IP:** `10.100.20.30`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 Kerne | **Disk:** 16 GB (local-lvm)
**Nesting:** aktiviert (erforderlich für Docker)

---

### Dienste

Zwei unabhängige Docker-Compose-Projekte laufen in diesem LXC.

#### Stack: utility-apps (`/opt/docker-data/docker-compose.yml`)

| Dienst | Port (Host→Container) | URL | Hinweise |
|--------|----------------------|-----|----------|
| Vaultwarden | 8080→80 | https://vault.damianzientek.de | Passwort-Manager |
| Kavita | 5000→5000 | https://kavita.damianzientek.de | E-Book-Bibliothek (migriert) |
| Actual Budget | 5006→5006 | https://budzet.damianzientek.de | Haushaltsbuch |
| Ntfy | 8090→80 | https://ntfy.damianzientek.de | Push-Benachrichtigungen |
| Homarr | 7575→**3000** | https://homarr.damianzientek.de | Dashboard (Container-Port ist 3000!) |
| Stirling PDF | 8091→8080 | https://edytor-pdf.damianzientek.de | PDF-Werkzeuge |

#### Stack: wger (`/opt/docker-data/wger-stack/`)

| Dienst | Port | Hinweise |
|--------|------|----------|
| wger-nginx | 8100→80 | https://trening.damianzientek.de |
| wger-web | expose 8000 | Django (Gunicorn), Healthcheck |
| wger-db | expose 5432 | postgres:15 |
| wger-cache | expose 6379 | redis:7 |
| wger-celery-worker | — | `/start-worker` |
| wger-celery-beat | — | `/start-beat` |

---

### Verzeichnisstruktur

**Auf dem Host (pve1):**
```
/opt/lxc-data/utility-apps-data/     → bind-gemountet nach /data im LXC
/opt/docker-data/utility-apps-data/  → bind-gemountet nach /opt/docker-data im LXC
    ├── docker-compose.yml
    ├── vaultwarden/
    ├── kavita/
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/configs/
    └── wger-stack/
        ├── docker-compose.yml
        ├── nginx.conf
        ├── postgres-data/
        ├── redis-data/
        └── media/

/mnt/hdd-data2/kavita/               → bind-gemountet nach /mnt/kavita-library im LXC
```

---

### Infrastructure as Code

**Terraform** provisioniert den LXC-Container.
**Ansible** übernimmt alles innerhalb des Containers via Jinja2-Templates.

| Playbook | Zweck |
|----------|-------|
| `setup-base.yml` | Basispakete, Zeitzone, Hostname |
| `install-docker.yml` | Docker Engine + Compose-Plugin |
| `deploy-utility-apps.yml` | Gesamter utility-apps-Stack |
| `deploy-wger.yml` | wger-Fitness-Stack |

---

### Bekannte Probleme & Fallstricke

**1. Terraform Bind Mount HTTP 403**
Der `bpg/proxmox`-Provider gibt HTTP 403 zurück. Bind Mounts müssen manuell via `pct set` gesetzt werden.

**2. `$$`-Escaping in docker-compose.yml**
```yaml
- ADMIN_TOKEN={{ vaultwarden_admin_token | replace('$', '$$') }}
```

**3. Homarr Container-Port ist 3000, nicht 7575**
Host-Port `7575` mappt auf Container-Port `3000` (Next.js).

**4. wger benötigt nginx-Sidecar für statische Dateien**
`WGER_USE_GUNICORN=True` startet Gunicorn auf Port 8000 — kein Static-File-Serving. Separater nginx-Container mit geteiltem `wger-static` Volume.

**5. Disk-Erweiterung ohne Downtime**
```bash
ssh pve1 "pct resize 300 rootfs 16G"
```

---

### Designentscheidungen

- **Docker LXC statt einzelner LXC pro Dienst** — konsistent mit `arr-stack`-Muster auf pve2.
- **Jinja2-Templates** — ein Playbook verwaltet alle Dienste; neuer Dienst = ein Block im Template.
- **Separates Compose-Projekt für wger** — Isolation von Multi-Container-Stack.
- **Bind Mounts auf den Host** — alle persistenten Daten außerhalb des Rootfs.
- **`ansible/secrets.yml` + `.gitignore`** — Secrets werden nie committet.

---
---

## Polski

### Opis

`utility-apps` to kontener LXC z Debianem 13 na pve1, pełniący rolę hosta Dockera dla lekkich aplikacji użytkowych. Zastępuje wcześniejszy dedykowany LXC Kavity (również ID 300) i podąża za tym samym wzorcem Docker-host co `arr-stack` na pve2.

**Node:** pve1 (`10.100.20.10`)
**ID LXC:** 300
**IP:** `10.100.20.30`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 rdzenie | **Dysk:** 16 GB (local-lvm)
**Nesting:** włączony (wymagany dla Dockera)

---

### Usługi

W tym LXC działają dwa niezależne projekty Docker Compose.

#### Stack: utility-apps (`/opt/docker-data/docker-compose.yml`)

| Usługa | Port (host→kontener) | URL | Uwagi |
|--------|---------------------|-----|-------|
| Vaultwarden | 8080→80 | https://vault.damianzientek.de | Menedżer haseł |
| Kavita | 5000→5000 | https://kavita.damianzientek.de | Biblioteka e-booków (zmigrowana z osobnego LXC) |
| Actual Budget | 5006→5006 | https://budzet.damianzientek.de | Budżet domowy |
| Ntfy | 8090→80 | https://ntfy.damianzientek.de | Powiadomienia push |
| Homarr | 7575→**3000** | https://homarr.damianzientek.de | Dashboard (port kontenera to 3000, nie 7575!) |
| Stirling PDF | 8091→8080 | https://edytor-pdf.damianzientek.de | Narzędzia PDF |

#### Stack: wger (`/opt/docker-data/wger-stack/`)

| Usługa | Port | Uwagi |
|--------|------|-------|
| wger-nginx | 8100→80 | https://trening.damianzientek.de — serwuje pliki statyczne + proxy do Gunicorn |
| wger-web | expose 8000 | Django (Gunicorn), healthcheck włączony |
| wger-db | expose 5432 | postgres:15 |
| wger-cache | expose 6379 | redis:7 |
| wger-celery-worker | — | `/start-worker` |
| wger-celery-beat | — | `/start-beat` |

---

### Struktura katalogów

**Na hoście (pve1):**
```
/opt/lxc-data/utility-apps-data/     → bind mount do /data w LXC
/opt/docker-data/utility-apps-data/  → bind mount do /opt/docker-data w LXC
    ├── docker-compose.yml            ← stack utility-apps
    ├── vaultwarden/
    ├── kavita/                       ← zmigrowane ze starego LXC
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/
    │   └── configs/
    └── wger-stack/                   ← osobny projekt Compose
        ├── docker-compose.yml
        ├── nginx.conf
        ├── postgres-data/
        ├── redis-data/
        └── media/
        (wger-static jako Docker named volume)

/mnt/hdd-data2/kavita/               → bind mount do /mnt/kavita-library w LXC
```

**Bind mounty (`/etc/pve/lxc/300.conf`):**
```
mp0: /opt/lxc-data/utility-apps-data,mp=/data
mp1: /opt/docker-data/utility-apps-data,mp=/opt/docker-data
mp2: /mnt/hdd-data2/kavita,mp=/mnt/kavita-library
```

**Wewnątrz LXC:**
```
/data/
/opt/docker-data/
    ├── docker-compose.yml
    ├── vaultwarden/
    ├── kavita/
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/configs/
    └── wger-stack/
/mnt/kavita-library/          ← biblioteka książek (beletrystyka, komiksy, ogólne, poradniki)
```

---

### Infrastructure as Code

**Terraform** (`homelab-iac/terraform/lxc/pve1/main.tf`) tworzy kontener LXC.
**Ansible** obsługuje wszystko wewnątrz przez szablony Jinja2.

#### Playbooki

| Playbook | Zadanie |
|----------|---------|
| `setup-base.yml` | Podstawowe pakiety, strefa czasowa, hostname |
| `install-docker.yml` | Docker Engine + plugin Compose |
| `deploy-utility-apps.yml` | Pełny stack utility-apps (oparty na szablonie) |
| `deploy-wger.yml` | Stack wger fitness |

#### Szablony Jinja2 (`ansible/files/`)

| Plik | Zadanie |
|------|---------|
| `utility-apps-compose.yml.j2` | docker-compose.yml dla stacku utility-apps |
| `wger-compose.yml.j2` | docker-compose.yml dla stacku wger |
| `nginx-wger.conf` | konfiguracja nginx dla wger (kopiowana przez deploy-wger.yml) |

**Sekrety:** `ansible/secrets.yml` (gitignore) — zawiera:
- `vaultwarden_admin_token` — hash Argon2 PHC
- `homarr_secret_key` — 64-znakowy hex (`openssl rand -hex 32`)
- `wger_secret_key` — 64-znakowy hex
- `wger_db_password` — hasło base64 (`openssl rand -base64 16`)
- `mqtt_*`, `camera_*` — związane z Frigate

---

### Wdrożenie

```bash
# 1. Utwórz LXC przez Terraform (tylko przy świeżej instalacji)
cd ~/homelab-iac/terraform/lxc/pve1
terraform apply

# 2. Ustaw bind mounty ręcznie na hoście pve1 (bug Terraforma — patrz Znane problemy)
pct set 300 -mp0 /opt/lxc-data/utility-apps-data,mp=/data
pct set 300 -mp1 /opt/docker-data/utility-apps-data,mp=/opt/docker-data
pct set 300 -mp2 /mnt/hdd-data2/kavita,mp=/mnt/kavita-library
pct stop 300 && pct start 300

# 3. Zainstaluj Docker
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml

# 4. Wdróż stack utility-apps
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-utility-apps.yml

# 5. Wdróż stack wger
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-wger.yml
```

**Dodawanie nowego serwisu do stacku utility-apps:**
1. Dodaj blok serwisu do `ansible/files/utility-apps-compose.yml.j2`
2. Dodaj nazwę katalogu do `loop` w `deploy-utility-apps.yml`
3. Dodaj ewentualne sekrety do `ansible/secrets.yml`
4. `git add -A && git commit -m "feat: add <serwis>" && git push`
5. `ansible-playbook -i ... deploy-utility-apps.yml --check`
6. `ansible-playbook -i ... deploy-utility-apps.yml`
7. Dodaj proxy host w NPM (`10.100.20.30:<port>`)

---

### Znane problemy i pułapki

**1. Terraform bind mount HTTP 403**
Provider `bpg/proxmox` zwraca HTTP 403 przy ustawianiu bind mountów przez blok `mount_point {}` z tokenem `root@pam`. Bind mounty muszą być ustawiane ręcznie przez `pct set` po `terraform apply`. Bloki `mount_point` pozostają w `main.tf` dla celów dokumentacyjnych.

**2. Escapowanie `$$` w docker-compose.yml**
Wartości zmiennych środowiskowych zawierające `$` (np. hashe Argon2) muszą używać `$$`, żeby Docker nie interpretował ich jako zmiennych powłoki. W szablonie Jinja2:
```yaml
- ADMIN_TOKEN={{ vaultwarden_admin_token | replace('$', '$$') }}
```

**3. Port kontenera Homarr to 3000, nie 7575**
Port hosta `7575` mapuje na port kontenera **3000** (Next.js). Mapowanie `7575:7575` powoduje błąd połączenia.

**4. wger wymaga nginx sidecar dla plików statycznych**
`WGER_USE_GUNICORN=True` uruchamia Gunicorn na porcie 8000 — Gunicorn nie serwuje plików statycznych. Osobny kontener nginx współdzieli named volume `wger-static` i serwuje `/static/` i `/media/`. NPM proxy do nginx (port 80), nie bezpośrednio do Gunicorn.

**5. Konfiguracja admina wger przez Django shell**
URL `/admin` nie istnieje w wger. Używaj `/en/user/list` (wymaga `is_superuser=True`).
```bash
# Ustaw superusera
ssh utility-apps "docker exec wger-web python3 /home/wger/src/manage.py shell -c \
\"from django.contrib.auth.models import User; u = User.objects.get(username='damian'); \
u.is_active = True; u.is_staff = True; u.is_superuser = True; u.save()\""

# Zweryfikuj e-mail (używaj update, nie get_or_create — to drugie nie aktualizuje istniejących rekordów)
ssh utility-apps "docker exec wger-web python3 /home/wger/src/manage.py shell -c \
\"from allauth.account.models import EmailAddress; \
EmailAddress.objects.filter(user__username='damian').update(verified=True, primary=True)\""
```
Uwaga: używaj `python3`, nie `python` (nie ma w PATH). Nigdy nie używaj flag `-it` przy docker exec przez SSH.

**6. Powiększanie dysku bez przestoju**
```bash
ssh pve1 "pct resize 300 rootfs 16G"
```
Działa na działającym LXC. Zaktualizuj `size` w `main.tf` po operacji.

**7. Android Private DNS omija AdGuard**
Lokalne subdomeny (`*.damianzientek.de`) rozwiązują się przez wildcard rewrite w AdGuard Home. Android Private DNS omija to — wyłącz na telefonie. Poza domem używaj Tailscale.

**8. `docker_compose_v2` w trybie `--check`**
Moduł Ansible może zgłaszać błędy w trybie `--check` których nie ma w rzeczywistości (nie może sprawdzić stanu kontenerów). Reszta tasków (`file`, `template`, `copy`) jest wiarygodna.

---

### Decyzje architektoniczne

- **Docker LXC zamiast osobnych LXC na usługę** — spójność z wzorcem `arr-stack` na pve2; jeden host do zarządzania, Ansible deployuje wszystko.
- **Szablony Jinja2 dla docker-compose** — jeden `deploy-utility-apps.yml` zarządza wszystkimi serwisami przez `utility-apps-compose.yml.j2`. Dodanie serwisu = jeden blok w szablonie + jedna linia w pętli.
- **Osobny projekt Compose dla wger** — wger to wielokontenerowy stack (web, db, cache, celery ×2, nginx). Izolacja od stacku utility-apps upraszcza troubleshooting.
- **Debian 13 (Trixie)** — stabilny od lipca 2025; spójny z innymi kontenerami LXC na pve1/pve2.
- **Bind mounty na host** — wszystkie dane trwałe leżą poza rootfs. Migracja, snapshot lub odbudowa LXC nigdy nie ryzykuje danych aplikacji.
- **`ansible/secrets.yml` + `.gitignore`** — sekrety nigdy nie trafiają do repozytorium.

---

*Ostatnia aktualizacja: 2026-05 | Sesja: utility-apps full stack deployment*