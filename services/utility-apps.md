# utility-apps — Docker LXC (pve1, ID 300)

**Language / Sprache / Język:**
[English](#english) | [Deutsch](#deutsch) | [Polski](#polski)

---

## English

### Overview

`utility-apps` is a Debian 13 LXC container on pve1 acting as a Docker host for lightweight user-facing applications. It replaced the former dedicated Kavita LXC (also ID 300).

**Node:** pve1 (`10.x.x.x`)
**LXC ID:** 300
**IP:** `10.x.x.x`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 cores | **Disk:** 16 GB (local-lvm)
**Nesting:** enabled (required for Docker)

---

### Services

Two independent Docker Compose projects run inside this LXC.

#### Stack: utility-apps (`/opt/docker-data/docker-compose.yml`)

| Service | Port (host→container) | Notes |
| ------- | --------------------- | ----- |
| Vaultwarden | 8080→80 | Password manager |
| Kavita | 5000→5000 | E-book library (migrated from dedicated LXC) |
| Actual Budget | 5006→5006 | Personal finance tracker |
| Ntfy | 8090→80 | Push notifications |
| Homarr | 7575→**3000** | Dashboard (container port is 3000, not 7575!) |
| Stirling PDF | 8091→8080 | PDF editor/tools |
| scanservjs | 8093→8080 | Network scan UI for Canon PIXMA MX925 (SANE/BJNP over network, see [dedicated doc](./scanservjs-canon-mx925-network-scan.md)) |

#### Stack: wger (`/opt/docker-data/wger-stack/`)

| Service | Port | Notes |
| ------- | ---- | ----- |
| wger-nginx | 8100→80 | serves static files + proxies to Gunicorn |
| wger-web | expose 8000 | Django app (Gunicorn), healthcheck enabled |
| wger-db | expose 5432 | postgres:15 |
| wger-cache | expose 6379 | redis:7 |
| wger-celery-worker | — | `/start-worker` |
| wger-celery-beat | — | `/start-beat` |

---

### Directory Structure

**On host (pve1):**

```text
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
    ├── scanservjs/
    │   └── config/                   ← config.local.js overrides go here
    └── wger-stack/                   ← separate Compose project
        ├── docker-compose.yml
        ├── nginx.conf
        ├── postgres-data/
        ├── redis-data/
        └── media/
        (wger-static is a Docker named volume)

/mnt/hdd-data2/kavita/               → bind-mounted to /mnt/kavita-library inside LXC
/mnt/hdd-data2/scans/                → bind-mounted to /mnt/scans inside LXC
                                        (also NFS-exported to pve2 for paperless-ngx, see
                                        the NFS bridge doc)
```

**Bind mounts (`/etc/pve/lxc/300.conf`):**

```text
mp0: /opt/lxc-data/utility-apps-data,mp=/data
mp1: /opt/docker-data/utility-apps-data,mp=/opt/docker-data
mp2: /mnt/hdd-data2/kavita,mp=/mnt/kavita-library
mp3: /mnt/hdd-data2/scans,mp=/mnt/scans
```

**Inside LXC:**

```text
/data/                        ← LXC working data
/opt/docker-data/
    ├── docker-compose.yml    ← utility-apps stack
    ├── vaultwarden/
    ├── kavita/
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/configs/
    ├── scanservjs/config/
    └── wger-stack/           ← wger Compose project
/mnt/kavita-library/          ← book library (beletrystyka, komiksy, ogólne, poradniki)
/mnt/scans/                   ← scanservjs output, NFS-exported to pve2
```

---

### Infrastructure as Code

**Terraform** provisions the LXC container.
**Ansible** handles everything inside.

#### Playbooks

| Playbook | Purpose |
| -------- | ------- |
| `setup-base.yml` | Base packages, timezone, hostname |
| `install-docker.yml` | Docker Engine + Compose plugin |
| `deploy-utility-apps.yml` | Full utility-apps stack (template-based) |
| `deploy-wger.yml` | wger fitness stack |

#### Jinja2 Templates (`ansible/files/`)

| File | Purpose |
| ---- | ------- |
| `utility-apps-compose.yml.j2` | docker-compose.yml for utility-apps stack |
| `wger-compose.yml.j2` | docker-compose.yml for wger stack |
| `nginx-wger.conf` | nginx config for wger (copied by deploy-wger.yml) |

**Secrets:** `ansible/secrets.yml` — contains Vaultwarden, Homarr, wger and Frigate-related secrets. Encrypted with Vault.

---

### Deployment

```bash
# 1. Provision LXC (only needed for fresh setup)
cd terraform/lxc/pve1
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
  1. Add directory name to `loop` in `deploy-utility-apps.yml`
  1. Add any secrets to `ansible/secrets.yml`
  1. `git add -A && git commit -m "feat: add <service>" && git push`
  1. `ansible-playbook -i ... deploy-utility-apps.yml --check`
  1. `ansible-playbook -i ... deploy-utility-apps.yml`
  1. Add proxy host in NPM (`10.x.x.x:<port>`)

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
Local subdomains resolve via AdGuard Home wildcard rewrite. Android Private DNS bypasses this — disable it on the phone. Use Tailscale when outside home network.

**8. scanservjs output path differs from official documentation**
The official docs (docs/02-docker.md) list `/var/lib/scanservjs/output` as the volume
mount target. In the `sbs20/scanservjs:latest` image, the actual path the app writes
to is **`/usr/lib/scanservjs/data/output`**. Mounting the documented path silently
fails at scan time (`EACCES: open 'data/output/scan...'` — a relative path, a sign the
app fell back to its own working directory). Verified with
`docker exec scanservjs find / -name '~tmp-scan*'`. Full compose snippet:

```yaml
volumes:
  - /mnt/scans:/usr/lib/scanservjs/data/output
  - ./scanservjs/config:/etc/scanservjs
```

**9. Canon MX925 network scanning requires BJNP, not eSCL, and TCP+UDP on the firewall**
See the dedicated document [`scanservjs-canon-mx925-network-scan.md`](./scanservjs-canon-mx925-network-scan.md)
for the full case: why eSCL doesn't work on this printer, why the FortiGate service
object needed both TCP *and* UDP 8610–8614 (BJNP discovery uses UDP), and why ADF
Duplex scans are noticeably slower over the network than single-sided scans.

**10. Bind mount ownership after adding `mp3` (scans)**
scanservjs runs as UID 103 inside its container; in this unprivileged LXC that maps to
host UID `100103`. The `/mnt/hdd-data2/scans` directory needed
`chown 100103:100000` before writes succeeded — a plain `chown root:root` (which
happened to work for Kavita, see below) was not sufficient here because the two
services run as different container UIDs. See
[`lxc-unprivileged-uid-mapping.md`](./lxc-unprivileged-uid-mapping.md) for the general
mechanism. As a side effect of debugging this, an unrelated, previously unnoticed bug
in Kavita was also found and fixed: its library directory (`/mnt/hdd-data2/kavita`)
was owned by host UID `0` instead of `100000` (the UID Kavita's root process maps to),
which let books appear in the UI (world-readable) but failed on open/download
(`500` error) until ownership was corrected to `100000:100000`.

---

### Design Decisions

- **Docker LXC over individual LXC per service** — one host to manage, one Compose file per stack, Ansible deploys everything.
- **Jinja2 templates for docker-compose** — single `deploy-utility-apps.yml` manages all services via `utility-apps-compose.yml.j2`. Adding a service = one block in the template + one line in the loop.
- **Separate Compose project for wger** — wger is a multi-container stack (web, db, cache, celery ×2, nginx). Keeping it isolated from the utility-apps stack avoids coupling and simplifies troubleshooting.
- **Debian 13 (Trixie)** — stable since July 2025; consistent with other LXC containers on pve1/pve2.
- **Bind mounts to host** — all persistent data lives outside rootfs. Migrating, snapshotting, or rebuilding the LXC never risks application data.

---
---

## Deutsch

### Überblick

`utility-apps` ist ein Debian-13-LXC-Container auf pve1, der als Docker-Host für leichtgewichtige Benutzeranwendungen dient. Er ersetzt den früheren dedizierten Kavita-LXC (ebenfalls ID 300).

**Node:** pve1 (`10.x.x.x`)
**LXC-ID:** 300
**IP:** `10.x.x.x`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 Kerne | **Disk:** 16 GB (local-lvm)
**Nesting:** aktiviert (erforderlich für Docker)

---

### Dienste

Zwei unabhängige Docker-Compose-Projekte laufen in diesem LXC.

#### Stack: utility-apps (`/opt/docker-data/docker-compose.yml`)

| Dienst | Port (Host→Container) | Hinweise |
| ------ | --------------------- | -------- |
| Vaultwarden | 8080→80 | Passwort-Manager |
| Kavita | 5000→5000 | E-Book-Bibliothek (migriert) |
| Actual Budget | 5006→5006 | Haushaltsbuch |
| Ntfy | 8090→80 | Push-Benachrichtigungen |
| Homarr | 7575→**3000** | Dashboard (Container-Port ist 3000!) |
| Stirling PDF | 8091→8080 | PDF-Werkzeuge |
| scanservjs | 8093→8080 | Netzwerk-Scan-UI für Canon PIXMA MX925 (SANE/BJNP, siehe eigenes Dokument) |

#### Stack: wger (`/opt/docker-data/wger-stack/`)

| Dienst | Port | Hinweise |
| ------ | ---- | -------- |
| wger-nginx | 8100→80 | - |
| wger-web | expose 8000 | Django (Gunicorn), Healthcheck |
| wger-db | expose 5432 | postgres:15 |
| wger-cache | expose 6379 | redis:7 |
| wger-celery-worker | — | `/start-worker` |
| wger-celery-beat | — | `/start-beat` |

---

### Verzeichnisstruktur

**Auf dem Host (pve1):**

```text
/opt/lxc-data/utility-apps-data/     → bind-gemountet nach /data im LXC
/opt/docker-data/utility-apps-data/  → bind-gemountet nach /opt/docker-data im LXC
    ├── docker-compose.yml
    ├── vaultwarden/
    ├── kavita/
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/configs/
    ├── scanservjs/config/
    └── wger-stack/
        ├── docker-compose.yml
        ├── nginx.conf
        ├── postgres-data/
        ├── redis-data/
        └── media/

/mnt/hdd-data2/kavita/               → bind-gemountet nach /mnt/kavita-library im LXC
/mnt/hdd-data2/scans/                → bind-gemountet nach /mnt/scans im LXC (auch NFS-Export nach pve2)
```

---

### Infrastructure as Code

**Terraform** provisioniert den LXC-Container.
**Ansible** übernimmt alles innerhalb des Containers via Jinja2-Templates.

| Playbook | Zweck |
| -------- | ----- |
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

**6. scanservjs — abweichender Volume-Pfad und UID-Mapping**
Der Docker-Volume-Pfad für Scan-Ausgaben weicht von der offiziellen Doku ab
(`/usr/lib/scanservjs/data/output` statt `/var/lib/scanservjs/output`), und der
Host-Ordner benötigt korrektes `chown` entsprechend dem UID-Mapping des
unprivilegierten LXC. Details in den eigenen Dokumenten
(`scanservjs-canon-mx925-network-scan.md`, `lxc-unprivileged-uid-mapping.md`).

---

### Designentscheidungen

- **Docker LXC statt einzelner LXC pro Dienst** — konsistent mit `arr-stack`-Muster auf pve2.
- **Jinja2-Templates** — ein Playbook verwaltet alle Dienste; neuer Dienst = ein Block im Template.
- **Separates Compose-Projekt für wger** — Isolation von Multi-Container-Stack.
- **Bind Mounts auf den Host** — alle persistenten Daten außerhalb des Rootfs.

---
---

## Polski

### Opis

`utility-apps` to kontener LXC z Debianem 13 na pve1, pełniący rolę hosta Dockera dla lekkich aplikacji użytkowych. Zastępuje wcześniejszy dedykowany LXC Kavity (również ID 300).

**Node:** pve1 (`10.x.x.x`)
**ID LXC:** 300
**IP:** `10.x.x.x`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 rdzenie | **Dysk:** 16 GB (local-lvm)
**Nesting:** włączony (wymagany dla Dockera)

---

### Usługi

W tym LXC działają dwa niezależne projekty Docker Compose.

#### Stack: utility-apps (`/opt/docker-data/docker-compose.yml`)

| Usługa | Port (host→kontener) | Uwagi |
| ------ | -------------------- | ----- |
| Vaultwarden | 8080→80 | Menedżer haseł |
| Kavita | 5000→5000 | Biblioteka e-booków (zmigrowana z osobnego LXC) |
| Actual Budget | 5006→5006 | Budżet domowy |
| Ntfy | 8090→80 | Powiadomienia push |
| Homarr | 7575→**3000** | Dashboard (port kontenera to 3000, nie 7575!) |
| Stirling PDF | 8091→8080 | Narzędzia PDF |
| scanservjs | 8093→8080 | UI do skanowania sieciowego dla Canon PIXMA MX925 (SANE/BJNP przez sieć, patrz [osobny dokument](./scanservjs-canon-mx925-network-scan.md)) |

#### Stack: wger (`/opt/docker-data/wger-stack/`)

| Usługa | Port | Uwagi |
| ------ | ---- | ----- |
| wger-nginx | 8100→80 | serwuje pliki statyczne + proxy do Gunicorn |
| wger-web | expose 8000 | Django (Gunicorn), healthcheck włączony |
| wger-db | expose 5432 | postgres:15 |
| wger-cache | expose 6379 | redis:7 |
| wger-celery-worker | — | `/start-worker` |
| wger-celery-beat | — | `/start-beat` |

---

### Struktura katalogów

**Na hoście (pve1):**

```text
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
    ├── scanservjs/
    │   └── config/                   ← nadpisania config.local.js
    └── wger-stack/                   ← osobny projekt Compose
        ├── docker-compose.yml
        ├── nginx.conf
        ├── postgres-data/
        ├── redis-data/
        └── media/
        (wger-static jako Docker named volume)

/mnt/hdd-data2/kavita/               → bind mount do /mnt/kavita-library w LXC
/mnt/hdd-data2/scans/                → bind mount do /mnt/scans w LXC
                                        (dodatkowo eksportowane przez NFS na pve2
                                        pod paperless-ngx, patrz dokument o moście NFS)
```

**Bind mounty (`/etc/pve/lxc/300.conf`):**

```textx
mp0: /opt/lxc-data/utility-apps-data,mp=/data
mp1: /opt/docker-data/utility-apps-data,mp=/opt/docker-data
mp2: /mnt/hdd-data2/kavita,mp=/mnt/kavita-library
mp3: /mnt/hdd-data2/scans,mp=/mnt/scans
```

**Wewnątrz LXC:**

```text
/data/
/opt/docker-data/
    ├── docker-compose.yml
    ├── vaultwarden/
    ├── kavita/
    ├── actual-budget/
    ├── ntfy/
    ├── homarr/
    ├── stirling-pdf/configs/
    ├── scanservjs/config/
    └── wger-stack/
/mnt/kavita-library/          ← biblioteka książek (beletrystyka, komiksy, ogólne, poradniki)
/mnt/scans/                   ← output scanservjs, eksportowane przez NFS na pve2
```

---

### Infrastructure as Code

**Terraform** (`terraform/lxc/pve1/main.tf`) tworzy kontener LXC.
**Ansible** obsługuje wszystko wewnątrz przez szablony Jinja2.

#### Playbooki

| Playbook | Zadanie |
| -------- | ------- |
| `setup-base.yml` | Podstawowe pakiety, strefa czasowa, hostname |
| `install-docker.yml` | Docker Engine + plugin Compose |
| `deploy-utility-apps.yml` | Pełny stack utility-apps (oparty na szablonie) |
| `deploy-wger.yml` | Stack wger fitness |

#### Szablony Jinja2 (`ansible/files/`)

| Plik | Zadanie |
| ---- | ------- |
| `utility-apps-compose.yml.j2` | docker-compose.yml dla stacku utility-apps |
| `wger-compose.yml.j2` | docker-compose.yml dla stacku wger |
| `nginx-wger.conf` | konfiguracja nginx dla wger (kopiowana przez deploy-wger.yml) |

**Sekrety:** `ansible/secrets.yml` - Zawiera sekrety związane z Vaultwarden, Homarr, wger ​​i Frigate. Zaszyfrowane za pomocą Vault.

---

### Wdrożenie

```bash
# 1. Utwórz LXC przez Terraform (tylko przy świeżej instalacji)
cd terraform/lxc/pve1
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
  1. Dodaj nazwę katalogu do `loop` w `deploy-utility-apps.yml`
  1. Dodaj ewentualne sekrety do `ansible/secrets.yml`
  1. `git add -A && git commit -m "feat: add <serwis>" && git push`
  1. `ansible-playbook -i ... deploy-utility-apps.yml --check`
  1. `ansible-playbook -i ... deploy-utility-apps.yml`
  1. Dodaj proxy host w NPM (`10.x.x.x:<port>`)

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

**9. Ścieżka output scanservjs inna niż w oficjalnej dokumentacji**
Oficjalna dokumentacja (docs/02-docker.md) podaje `/var/lib/scanservjs/output` jako
ścieżkę do zamapowania. W obrazie `sbs20/scanservjs:latest` faktyczna ścieżka zapisu
to **`/usr/lib/scanservjs/data/output`**. Zamontowanie ścieżki z dokumentacji cicho
zawodzi w momencie skanowania (`EACCES: open 'data/output/scan...'` — ścieżka
relatywna, sygnał że aplikacja pisze do własnego katalogu roboczego). Zweryfikowane
przez `docker exec scanservjs find / -name '~tmp-scan*'`. Poprawny fragment compose:

```yaml
volumes:
  - /mnt/scans:/usr/lib/scanservjs/data/output
  - ./scanservjs/config:/etc/scanservjs
```

**10. Skanowanie sieciowe Canon MX925 wymaga BJNP (nie eSCL) i TCP+UDP na firewallu**
Pełny opis w osobnym dokumencie
[`scanservjs-canon-mx925-network-scan.md`](./scanservjs-canon-mx925-network-scan.md):
dlaczego eSCL nie działa na tej drukarce, dlaczego serwis na FortiGate potrzebował
zarówno TCP, jak i UDP na 8610–8614 (discovery BJNP korzysta z UDP), i dlaczego
skanowanie ADF Duplex przez sieć jest zauważalnie wolniejsze niż jednostronne.

**11. Właściciel bind mounta po dodaniu `mp3` (scans)**
scanservjs działa jako UID 103 wewnątrz kontenera; w tym nieuprzywilejowanym LXC
mapuje się to na UID hosta `100103`. Katalog `/mnt/hdd-data2/scans` wymagał
`chown 100103:100000`, zanim zapis zaczął działać — samo `chown root:root` (które
zadziałało dla Kavity, patrz niżej) tu nie wystarczyło, bo obie usługi działają jako
różne UID w kontenerze. Ogólny mechanizm opisany w
[`lxc-unprivileged-uid-mapping.md`](./lxc-unprivileged-uid-mapping.md). Przy okazji
debugowania tego problemu znaleziono i naprawiono niezależny, wcześniej niezauważony
bug w Kavicie: jej katalog biblioteki (`/mnt/hdd-data2/kavita`) należał do UID hosta
`0` zamiast `100000` (UID na jaki mapuje się proces root Kavity), co pozwalało
książkom pojawiać się w UI (odczyt dla wszystkich), ale otwieranie/pobieranie kończyło
się błędem `500` — do czasu poprawienia właściciela na `100000:100000`.

---

### Decyzje architektoniczne

- **Docker LXC zamiast osobnych LXC na usługę** — spójność z wzorcem `arr-stack` na pve2; jeden host do zarządzania, Ansible deployuje wszystko.
- **Szablony Jinja2 dla docker-compose** — jeden `deploy-utility-apps.yml` zarządza wszystkimi serwisami przez `utility-apps-compose.yml.j2`. Dodanie serwisu = jeden blok w szablonie + jedna linia w pętli.
- **Osobny projekt Compose dla wger** — wger to wielokontenerowy stack (web, db, cache, celery ×2, nginx). Izolacja od stacku utility-apps upraszcza troubleshooting.
- **Debian 13 (Trixie)** — stabilny od lipca 2025; spójny z innymi kontenerami LXC na pve1/pve2.
- **Bind mounty na host** — wszystkie dane trwałe leżą poza rootfs. Migracja, snapshot lub odbudowa LXC nigdy nie ryzykuje danych aplikacji.
- **`ansible/secrets.yml` + `.gitignore`** — sekrety nigdy nie trafiają do repozytorium.

---

*Ostatnia aktualizacja: 2026-07-28 | Sesja: scanservjs (Canon MX925 network scan) + NFS bridge do pve2 + naprawa UID/Kavita*
