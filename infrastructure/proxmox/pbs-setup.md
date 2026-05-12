# Proxmox Backup Server — Setup and Configuration | Einrichtung und Konfiguration | Konfiguracja i Setup

---

## Navigation | Navigation | Nawigacja

[🇬🇧 English](#en) | [🇩🇪 Deutsch](#de) | [🇵🇱 Polski](#pl)

---

<a name="en"></a>
## 🇬🇧 English

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Description

Proxmox Backup Server 4.x (PBS) runs in a privileged LXC container on pve1. It handles incremental, deduplicated backups of all LXC containers and VMs across both cluster nodes. PBS replaced the legacy vzdump-based GUI backup jobs. Configuration backups (scripts, `/etc/pve`, bind mount data) are handled separately by shell scripts.

### Infrastructure

| Parameter | Value |
|-----------|-------|
| Host | pve1 (`10.100.20.10`) |
| LXC ID | 900 |
| IP | `10.100.20.90` |
| Web UI | `https://10.100.20.90:8007` / `https://pbs.damianzientek.de` |
| PBS Version | 4.2 (Debian 13 Trixie) |
| Unprivileged | No (privileged required for loop devices) |

### Bind Mounts (pve1 host)

| Host path | LXC path | Purpose |
|-----------|----------|---------|
| `/mnt/hdd-data/backups/pbs-store` | `/mnt/datastore` | PBS datastore (backup chunks) |
| `/opt/lxc-data/pbs-data` | `/data` | PBS application data |

### Storage Layout

```
/mnt/hdd-data/              ← hdd-data-1tb-p1 (pve1)
└── backups/
    ├── pbs-store/          ← PBS datastore (~500 GB)
    ├── pve-configs/        ← config backup scripts (pve1 + pve2)
    └── dell-wyse/          ← Dell Wyse backup script
```

### Datastore

| Parameter | Value |
|-----------|-------|
| Name | `pve-backup` |
| Path | `/mnt/datastore` |
| GC Schedule | daily |
| Prune Schedule | daily |
| Keep Daily | 7 |
| Keep Weekly | 4 |
| Keep Monthly | 3 |

### Backup Job (PVE side)

Configured in Proxmox VE: **Datacenter → Backup**

| Parameter | Value |
|-----------|-------|
| Storage | `pbs-main` |
| Schedule | `03:30` daily |
| Mode | Snapshot |
| Compression | ZSTD |
| VMs/LXCs | 101, 102, 103, 104, 200, 300, 310, 311, 320 |

### IaC Management

**Terraform** (create LXC):
```bash
cd ~/homelab-iac/terraform/lxc/pve1
terraform plan
terraform apply
```

**After terraform apply** — bind mounts manually on pve1:
```bash
mkdir -p /mnt/hdd-data/backups/pbs-store
mkdir -p /opt/lxc-data/pbs-data
pct set 900 -mp0 /mnt/hdd-data/backups/pbs-store,mp=/mnt/datastore,backup=0
pct set 900 -mp1 /opt/lxc-data/pbs-data,mp=/data
pct set 900 --features nesting=1
pct reboot 900
```

**Ansible** (PBS installation):
```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l pbs
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-pbs.yml -l pbs
```

**After Ansible** — manual one-time setup:
1. Set root password: `pct exec 900 -- passwd`
2. Open PBS Web UI: `https://10.100.20.90:8007`
3. Add datastore: **Datastore → Add** → path `/mnt/datastore`, name `pve-backup`
4. Add PBS to PVE: **Datacenter → Storage → Add → Proxmox Backup Server**
   - ID: `pbs-main`, Server: `10.100.20.90`, Datastore: `pve-backup`
   - Fingerprint: copy from PBS Dashboard → Certificates

### Known Issues and Solutions

**Issue:** `terraform apply` fails with HTTP 403 on bind mount blocks
**Cause:** `bpg/proxmox` provider bug — bind mounts not allowed with `root@pam` API token
**Solution:** Remove all `mount_point` blocks from Terraform resource. Set bind mounts manually via `pct set` after apply.

**Issue:** `terraform apply` fails with HTTP 403 on `features` block for privileged LXC
**Cause:** Provider cannot set feature flags on privileged containers via API token
**Solution:** Remove `features` block from Terraform resource. Set nesting manually: `pct set 900 --features nesting=1`

**Issue:** After `terraform import`, `terraform plan` shows `-/+` (destroy+recreate)
**Cause:** Creation-time attributes (`unprivileged`, SSH keys, template) are not returned by Proxmox API after import — Terraform sees a diff
**Solution:** Add `lifecycle.ignore_changes` block to the resource:
```hcl
lifecycle {
  ignore_changes = [
    unprivileged,
    initialization[0].user_account,
    operating_system[0].template_file_id,
  ]
}
```

**Issue:** Proxmox warning: `Systemd 257 detected. You may need to enable nesting`
**Cause:** Systemd 257 (Debian 13) requires nesting inside LXC to function correctly
**Solution:** `pct set 900 --features nesting=1 && pct reboot 900`

---

<a name="de"></a>
## 🇩🇪 Deutsch

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Beschreibung

Proxmox Backup Server 4.x (PBS) läuft in einem privilegierten LXC-Container auf pve1. Er übernimmt inkrementelle, deduplizierte Backups aller LXC-Container und VMs auf beiden Cluster-Knoten. PBS hat die bisherigen vzdump-basierten GUI-Backup-Jobs ersetzt. Konfigurations-Backups (Skripte, `/etc/pve`, Bind-Mount-Daten) werden separat durch Shell-Skripte verwaltet.

### Infrastruktur

| Parameter | Wert |
|-----------|------|
| Host | pve1 (`10.100.20.10`) |
| LXC ID | 900 |
| IP | `10.100.20.90` |
| Web UI | `https://10.100.20.90:8007` / `https://pbs.damianzientek.de` |
| PBS Version | 4.2 (Debian 13 Trixie) |
| Unprivilegiert | Nein (privilegiert erforderlich für Loop-Devices) |

### Bind Mounts (pve1 Host)

| Host-Pfad | LXC-Pfad | Zweck |
|-----------|----------|-------|
| `/mnt/hdd-data/backups/pbs-store` | `/mnt/datastore` | PBS Datastore (Backup-Chunks) |
| `/opt/lxc-data/pbs-data` | `/data` | PBS Anwendungsdaten |

### Storage-Layout

```
/mnt/hdd-data/              ← hdd-data-1tb-p1 (pve1)
└── backups/
    ├── pbs-store/          ← PBS Datastore (~500 GB)
    ├── pve-configs/        ← Konfigurations-Backup-Skripte (pve1 + pve2)
    └── dell-wyse/          ← Dell Wyse Backup-Skript
```

### Datastore

| Parameter | Wert |
|-----------|------|
| Name | `pve-backup` |
| Pfad | `/mnt/datastore` |
| GC-Zeitplan | täglich |
| Prune-Zeitplan | täglich |
| Keep Daily | 7 |
| Keep Weekly | 4 |
| Keep Monthly | 3 |

### Backup-Job (PVE-Seite)

Konfiguriert in Proxmox VE: **Datacenter → Backup**

| Parameter | Wert |
|-----------|------|
| Storage | `pbs-main` |
| Zeitplan | `03:30` täglich |
| Modus | Snapshot |
| Komprimierung | ZSTD |
| VMs/LXCs | 101, 102, 103, 104, 200, 300, 310, 311, 320 |

### IaC-Verwaltung

**Terraform** (LXC erstellen):
```bash
cd ~/homelab-iac/terraform/lxc/pve1
terraform plan
terraform apply
```

**Nach terraform apply** — Bind Mounts manuell auf pve1:
```bash
mkdir -p /mnt/hdd-data/backups/pbs-store
mkdir -p /opt/lxc-data/pbs-data
pct set 900 -mp0 /mnt/hdd-data/backups/pbs-store,mp=/mnt/datastore,backup=0
pct set 900 -mp1 /opt/lxc-data/pbs-data,mp=/data
pct set 900 --features nesting=1
pct reboot 900
```

**Ansible** (PBS-Installation):
```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l pbs
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-pbs.yml -l pbs
```

**Nach Ansible** — Einmalige manuelle Einrichtung:
1. Root-Passwort setzen: `pct exec 900 -- passwd`
2. PBS Web UI öffnen: `https://10.100.20.90:8007`
3. Datastore hinzufügen: **Datastore → Add** → Pfad `/mnt/datastore`, Name `pve-backup`
4. PBS zu PVE hinzufügen: **Datacenter → Storage → Add → Proxmox Backup Server**
   - ID: `pbs-main`, Server: `10.100.20.90`, Datastore: `pve-backup`
   - Fingerprint: von PBS Dashboard → Certificates kopieren

### Bekannte Probleme und Lösungen

**Problem:** `terraform apply` schlägt fehl mit HTTP 403 bei Bind-Mount-Blöcken
**Ursache:** `bpg/proxmox` Provider-Bug — Bind Mounts nicht erlaubt mit `root@pam` API-Token
**Lösung:** Alle `mount_point`-Blöcke aus der Terraform-Ressource entfernen. Bind Mounts manuell via `pct set` nach apply setzen.

**Problem:** `terraform apply` schlägt fehl mit HTTP 403 bei `features`-Block für privilegierten LXC
**Ursache:** Provider kann Feature-Flags bei privilegierten Containern nicht via API-Token setzen
**Lösung:** `features`-Block aus Terraform-Ressource entfernen. Nesting manuell setzen: `pct set 900 --features nesting=1`

**Problem:** Nach `terraform import` zeigt `terraform plan` `-/+` (destroy+recreate)
**Ursache:** Creation-time-Attribute (`unprivileged`, SSH-Keys, Template) werden von der Proxmox-API nach dem Import nicht zurückgegeben — Terraform erkennt einen Unterschied
**Lösung:** `lifecycle.ignore_changes`-Block zur Ressource hinzufügen:
```hcl
lifecycle {
  ignore_changes = [
    unprivileged,
    initialization[0].user_account,
    operating_system[0].template_file_id,
  ]
}
```

**Problem:** Proxmox-Warnung: `Systemd 257 detected. You may need to enable nesting`
**Ursache:** Systemd 257 (Debian 13) benötigt Nesting innerhalb von LXC für korrekten Betrieb
**Lösung:** `pct set 900 --features nesting=1 && pct reboot 900`

---

<a name="pl"></a>
## 🇵🇱 Polski

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Opis

Proxmox Backup Server 4.x (PBS) działa w privileged kontenerze LXC 900 na pve1. Obsługuje inkrementalne, deduplikowane backupy wszystkich kontenerów LXC i maszyn wirtualnych na obu węzłach klastra. PBS zastąpił poprzednie zadania backupowe oparte o vzdump w GUI Proxmox. Backupy konfiguracji (skrypty, `/etc/pve`, dane bind mountów) są obsługiwane osobno przez skrypty shell.

### Infrastruktura

| Parametr | Wartość |
|----------|---------|
| Host | pve1 (`10.100.20.10`) |
| LXC ID | 900 |
| IP | `10.100.20.90` |
| Web UI | `https://10.100.20.90:8007` / `https://pbs.damianzientek.de` |
| Wersja PBS | 4.2 (Debian 13 Trixie) |
| Unprivileged | Nie (privileged wymagany dla loop devices) |

### Bind Mounty (pve1 host)

| Ścieżka hosta | Ścieżka w LXC | Przeznaczenie |
|---------------|---------------|---------------|
| `/mnt/hdd-data/backups/pbs-store` | `/mnt/datastore` | PBS datastore (chunki backupów) |
| `/opt/lxc-data/pbs-data` | `/data` | Dane aplikacji PBS |

### Layout storage

```
/mnt/hdd-data/              ← hdd-data-1tb-p1 (pve1)
└── backups/
    ├── pbs-store/          ← PBS datastore (~500 GB)
    ├── pve-configs/        ← skrypty config backup (pve1 + pve2)
    └── dell-wyse/          ← skrypt backup Dell Wyse
```

### Datastore

| Parametr | Wartość |
|----------|---------|
| Nazwa | `pve-backup` |
| Ścieżka | `/mnt/datastore` |
| GC Schedule | codziennie |
| Prune Schedule | codziennie |
| Keep Daily | 7 |
| Keep Weekly | 4 |
| Keep Monthly | 3 |

### Zadanie backupowe (strona PVE)

Skonfigurowane w Proxmox VE: **Datacenter → Backup**

| Parametr | Wartość |
|----------|---------|
| Storage | `pbs-main` |
| Harmonogram | `03:30` codziennie |
| Tryb | Snapshot |
| Kompresja | ZSTD |
| VMs/LXCs | 101, 102, 103, 104, 200, 300, 310, 311, 320 |

### Zarządzanie IaC

**Terraform** (tworzenie LXC):
```bash
cd ~/homelab-iac/terraform/lxc/pve1
terraform plan
terraform apply
```

**Po terraform apply** — bind mounty ręcznie na pve1:
```bash
mkdir -p /mnt/hdd-data/backups/pbs-store
mkdir -p /opt/lxc-data/pbs-data
pct set 900 -mp0 /mnt/hdd-data/backups/pbs-store,mp=/mnt/datastore,backup=0
pct set 900 -mp1 /opt/lxc-data/pbs-data,mp=/data
pct set 900 --features nesting=1
pct reboot 900
```

**Ansible** (instalacja PBS):
```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/setup-base.yml -l pbs
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-pbs.yml -l pbs
```

**Po Ansible** — jednorazowa konfiguracja ręczna:
1. Ustaw hasło roota: `pct exec 900 -- passwd`
2. Otwórz PBS Web UI: `https://10.100.20.90:8007`
3. Dodaj datastore: **Datastore → Add** → ścieżka `/mnt/datastore`, nazwa `pve-backup`
4. Dodaj PBS do PVE: **Datacenter → Storage → Add → Proxmox Backup Server**
   - ID: `pbs-main`, Server: `10.100.20.90`, Datastore: `pve-backup`
   - Fingerprint: skopiuj z PBS Dashboard → Certificates

### Znane problemy i rozwiązania

**Problem:** `terraform apply` zwraca HTTP 403 przy blokach bind mount
**Przyczyna:** Bug providera `bpg/proxmox` — bind mounty niedozwolone z tokenem API `root@pam`
**Rozwiązanie:** Usuń wszystkie bloki `mount_point` z zasobu Terraform. Ustaw bind mounty ręcznie przez `pct set` po apply.

**Problem:** `terraform apply` zwraca HTTP 403 przy bloku `features` dla privileged LXC
**Przyczyna:** Provider nie może ustawić feature flags dla privileged kontenerów przez token API
**Rozwiązanie:** Usuń blok `features` z zasobu Terraform. Ustaw nesting ręcznie: `pct set 900 --features nesting=1`

**Problem:** Po `terraform import` polecenie `terraform plan` pokazuje `-/+` (destroy+recreate)
**Przyczyna:** Creation-time atrybuty (`unprivileged`, klucze SSH, template) nie są zwracane przez API Proxmox po imporcie — Terraform widzi różnicę
**Rozwiązanie:** Dodaj blok `lifecycle.ignore_changes` do zasobu:
```hcl
lifecycle {
  ignore_changes = [
    unprivileged,
    initialization[0].user_account,
    operating_system[0].template_file_id,
  ]
}
```

**Problem:** Warning Proxmox: `Systemd 257 detected. You may need to enable nesting`
**Przyczyna:** Systemd 257 (Debian 13) wymaga nesting wewnątrz LXC do poprawnego działania
**Rozwiązanie:** `pct set 900 --features nesting=1 && pct reboot 900`