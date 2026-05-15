# utility-apps — Docker LXC (pve1, ID 300)

**Language / Sprache / Język:**
[English](#english) | [Deutsch](#deutsch) | [Polski](#polski)

---

## English

### Overview

`utility-apps` is a Debian 13 LXC container on pve1 acting as a Docker host for lightweight user-facing applications. It replaces the former dedicated Kavita LXC (also ID 300) and follows the same Docker-host pattern as `arr-stack` on pve2.

**Node:** pve1 (`10.100.20.10`)
**LXC ID:** 300
**IP:** `10.100.20.30`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 cores | **Disk:** 16 GB (local-lvm)
**Nesting:** enabled (required for Docker)

---

### Services

| Service      | Port  | URL                              | Status |
|-------------|-------|----------------------------------|--------|
| Vaultwarden | 8080  | https://vault.damianzientek.de   | ✅     |
| Kavita      | 5000  | https://kavita.damianzientek.de  | 🔜 migration pending |
| Actual Budget | 5006 | https://budget.damianzientek.de | 🔜 planned |
| Ntfy        | 80    | https://ntfy.damianzientek.de    | 🔜 planned |

---

### Directory Structure

**On host (pve1):**
```
/opt/lxc-data/utility-apps-data/     → bind-mounted to /data inside LXC
/opt/docker-data/utility-apps-data/  → bind-mounted to /opt/docker-data inside LXC
    ├── docker-compose.yml
    ├── vaultwarden/
    └── kavita/                       (after migration)
```

**Inside LXC:**
```
/data/                        ← LXC working data
/opt/docker-data/
    ├── docker-compose.yml
    └── vaultwarden/
```

---

### Infrastructure as Code

**Terraform** (`homelab-iac/terraform/lxc/main.tf`) provisions the LXC container.
**Ansible** (`homelab-iac/ansible/playbooks/`) handles everything inside:

| Playbook | Purpose |
|----------|---------|
| `setup-base.yml` | Base packages, timezone, hostname |
| `install-docker.yml` | Docker Engine + Compose plugin |
| `deploy-vaultwarden.yml` | Vaultwarden container + config |

**Secrets:** `ansible/secrets.yml` (gitignored) — contains `vaultwarden_admin_token` as Argon2 PHC hash.

---

### Deployment

```bash
# 1. Provision LXC
cd ~/homelab-iac/terraform/lxc
terraform apply

# 2. Set bind mounts manually on pve1 host (Terraform bug — see Known Issues)
pct set 300 --mp0 /opt/lxc-data/utility-apps-data,mp=/data
pct set 300 --mp1 /opt/docker-data/utility-apps-data,mp=/opt/docker-data

# 3. Run Ansible playbooks
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l utility-apps
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l utility-apps
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-vaultwarden.yml -l utility-apps
```

---

### Known Issues & Gotchas

**1. Terraform bind mount HTTP 403**
`bpg/proxmox` provider returns HTTP 403 when setting bind mount points via `mount_point {}` block with a `root@pam` API token. Bind mounts must be set manually via `pct set` after `terraform apply`. The `mount_point` blocks remain in `main.tf` for documentation purposes; Terraform will detect and skip them if already set.

**2. `$$` escaping in docker-compose.yml**
Any environment variable value containing `$` (e.g. Argon2 hashes) must use `$$` in `docker-compose.yml` to prevent Docker from interpreting it as a shell variable. In the Ansible playbook, use the Jinja2 filter:
```yaml
- ADMIN_TOKEN={{ vaultwarden_admin_token | replace('$', '$$') }}
```

**3. Argon2 token for Vaultwarden admin panel**
Plain text `ADMIN_TOKEN` works but triggers a security warning. Generate a proper hash inside the container:
```bash
docker exec -it vaultwarden /vaultwarden hash --preset owasp
```
Store the resulting `$argon2id$...` string in `ansible/secrets.yml`.

**4. Ansible `hosts: all` required for `-l` limit to work**
If a playbook targets `hosts: proxmox_vms` and the host is in `proxmox_lxc` group, the `-l utility-apps` limit will be silently ignored. All general-purpose playbooks use `hosts: all`.

**5. SSH host key verification on first connect**
```bash
ssh-keyscan -H 10.100.20.30 >> ~/.ssh/known_hosts
```

---

### Design Decisions

- **Docker LXC over individual Alpine LXC per service** — consistent with `arr-stack` pattern on pve2; one host to manage, one Docker Compose file, Ansible deploys everything.
- **Debian 13 (Trixie)** — stable since July 2025; consistent with other LXC containers on pve1/pve2.
- **Bind mounts to host** — all persistent data lives outside rootfs. Migrating, snapshotting, or rebuilding the LXC never risks application data.
- **`ansible/secrets.yml` + `.gitignore`** — secrets never committed to repository; `secrets.yml.example` pattern planned for future reference.

---
---

## Deutsch

### Überblick

`utility-apps` ist ein Debian-13-LXC-Container auf pve1, der als Docker-Host für leichtgewichtige Benutzeranwendungen dient. Er ersetzt den früheren dedizierten Kavita-LXC (ebenfalls ID 300) und folgt demselben Docker-Host-Muster wie `arr-stack` auf pve2.

**Node:** pve1 (`10.100.20.10`)
**LXC-ID:** 300
**IP:** `10.100.20.30`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 Kerne | **Disk:** 8 GB (local-lvm)
**Nesting:** aktiviert (erforderlich für Docker)

---

### Dienste

| Dienst       | Port  | URL                              | Status |
|-------------|-------|----------------------------------|--------|
| Vaultwarden | 8080  | https://vault.damianzientek.de   | ✅     |
| Kavita      | 5000  | https://kavita.damianzientek.de  | 🔜 Migration ausstehend |
| Actual Budget | 5006 | https://budget.damianzientek.de | 🔜 geplant |
| Ntfy        | 80    | https://ntfy.damianzientek.de    | 🔜 geplant |

---

### Verzeichnisstruktur

**Auf dem Host (pve1):**
```
/opt/lxc-data/utility-apps-data/     → bind-gemountet nach /data im LXC
/opt/docker-data/utility-apps-data/  → bind-gemountet nach /opt/docker-data im LXC
    ├── docker-compose.yml
    └── vaultwarden/
```

**Im LXC:**
```
/data/
/opt/docker-data/
    ├── docker-compose.yml
    └── vaultwarden/
```

---

### Infrastructure as Code

**Terraform** (`homelab-iac/terraform/lxc/main.tf`) provisioniert den LXC-Container.
**Ansible** übernimmt alles innerhalb des Containers.

---

### Bekannte Probleme & Fallstricke

**1. Terraform Bind Mount HTTP 403**
Der `bpg/proxmox`-Provider gibt HTTP 403 zurück, wenn Bind Mounts mit einem `root@pam`-API-Token gesetzt werden. Bind Mounts müssen manuell via `pct set` gesetzt werden.

**2. `$$`-Escaping in docker-compose.yml**
Werte mit `$` (z.B. Argon2-Hashes) müssen `$$` in `docker-compose.yml` verwenden. Im Ansible-Playbook:
```yaml
- ADMIN_TOKEN={{ vaultwarden_admin_token | replace('$', '$$') }}
```

**3. Argon2-Token für das Vaultwarden-Admin-Panel**
```bash
docker exec -it vaultwarden /vaultwarden hash --preset owasp
```

---

### Designentscheidungen

- **Docker LXC statt einzelner Alpine-LXC pro Dienst** — konsistent mit dem `arr-stack`-Muster auf pve2.
- **Bind Mounts auf den Host** — alle persistenten Daten liegen außerhalb des Rootfs.
- **`ansible/secrets.yml` + `.gitignore`** — Secrets werden nie ins Repository committet.

---
---

## Polski

### Opis

`utility-apps` to kontener LXC z Debianem 13 na pve1, pełniący rolę hosta Dockera dla lekkich aplikacji użytkowych. Zastępuje wcześniejszy dedykowany LXC Kavity (również ID 300) i podąża za tym samym wzorcem Docker-host co `arr-stack` na pve2.

**Node:** pve1 (`10.100.20.10`)
**ID LXC:** 300
**IP:** `10.100.20.30`
**OS:** Debian 13 (Trixie)
**RAM:** 4096 MB | **CPU:** 2 rdzenie | **Dysk:** 8 GB (local-lvm)
**Nesting:** włączony (wymagany dla Dockera)

---

### Usługi

| Usługa       | Port  | URL                              | Status |
|-------------|-------|----------------------------------|--------|
| Vaultwarden | 8080  | https://vault.damianzientek.de   | ✅     |
| Kavita      | 5000  | https://kavita.damianzientek.de  | 🔜 migracja w toku |
| Actual Budget | 5006 | https://budget.damianzientek.de | 🔜 planowane |
| Ntfy        | 80    | https://ntfy.damianzientek.de    | 🔜 planowane |

---

### Struktura katalogów

**Na hoście (pve1):**
```
/opt/lxc-data/utility-apps-data/     → bind mount do /data w LXC
/opt/docker-data/utility-apps-data/  → bind mount do /opt/docker-data w LXC
    ├── docker-compose.yml
    └── vaultwarden/
```

**Wewnątrz LXC:**
```
/data/
/opt/docker-data/
    ├── docker-compose.yml
    └── vaultwarden/
```

---

### Infrastructure as Code

**Terraform** (`homelab-iac/terraform/lxc/main.tf`) tworzy kontener LXC.
**Ansible** obsługuje wszystko wewnątrz:

| Playbook | Zadanie |
|----------|---------|
| `setup-base.yml` | Podstawowe pakiety, strefa czasowa, hostname |
| `install-docker.yml` | Docker Engine + plugin Compose |
| `deploy-vaultwarden.yml` | Kontener Vaultwarden + konfiguracja |

**Sekrety:** `ansible/secrets.yml` (gitignore) — zawiera `vaultwarden_admin_token` jako hash Argon2 PHC.

---

### Wdrożenie

```bash
# 1. Utwórz LXC przez Terraform
cd ~/homelab-iac/terraform/lxc
terraform apply

# 2. Ustaw bind mounty ręcznie na hoście pve1 (bug Terraforma — patrz Znane problemy)
pct set 300 --mp0 /opt/lxc-data/utility-apps-data,mp=/data
pct set 300 --mp1 /opt/docker-data/utility-apps-data,mp=/opt/docker-data

# 3. Uruchom playbooki Ansible
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l utility-apps
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-docker.yml -l utility-apps
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/deploy-vaultwarden.yml -l utility-apps
```

---

### Znane problemy i pułapki

**1. Terraform bind mount HTTP 403**
Provider `bpg/proxmox` zwraca HTTP 403 przy ustawianiu bind mountów przez blok `mount_point {}` z tokenem `root@pam`. Bind mounty muszą być ustawiane ręcznie przez `pct set` po `terraform apply`. Bloki `mount_point` pozostają w `main.tf` dla celów dokumentacyjnych.

**2. Escapowanie `$$` w docker-compose.yml**
Wartości zmiennych środowiskowych zawierające `$` (np. hashe Argon2) muszą używać `$$` w `docker-compose.yml`, żeby Docker nie interpretował ich jako zmiennych powłoki. W playbooku Ansible:
```yaml
- ADMIN_TOKEN={{ vaultwarden_admin_token | replace('$', '$$') }}
```

**3. Token Argon2 dla panelu admina Vaultwarden**
Zwykły token tekstowy działa, ale wywołuje ostrzeżenie bezpieczeństwa. Wygeneruj właściwy hash wewnątrz kontenera:
```bash
docker exec -it vaultwarden /vaultwarden hash --preset owasp
```
Zapisz wynikowy string `$argon2id$...` w `ansible/secrets.yml`.

**4. `hosts: all` wymagane w playbookach dla działania `-l`**
Jeśli playbook celuje w `hosts: proxmox_vms`, a host jest w grupie `proxmox_lxc`, limit `-l utility-apps` zostanie cicho zignorowany. Wszystkie ogólne playbooki używają `hosts: all`.

**5. Weryfikacja klucza SSH przy pierwszym połączeniu**
```bash
ssh-keyscan -H 10.100.20.30 >> ~/.ssh/known_hosts
```

---

### Decyzje architektoniczne

- **Docker LXC zamiast osobnych Alpine LXC na usługę** — spójność z wzorcem `arr-stack` na pve2; jeden host do zarządzania, jeden plik Docker Compose, Ansible deployuje wszystko.
- **Debian 13 (Trixie)** — stabilny od lipca 2025; spójny z innymi kontenerami LXC na pve1/pve2.
- **Bind mounty na host** — wszystkie dane trwałe leżą poza rootfs. Migracja, snapshot lub odbudowa LXC nigdy nie ryzykuje danych aplikacji.
- **`ansible/secrets.yml` + `.gitignore`** — sekrety nigdy nie trafiają do repozytorium.

---

*Ostatnia aktualizacja: 2026-04 | Sesja: utility-apps LXC + Vaultwarden deployment*