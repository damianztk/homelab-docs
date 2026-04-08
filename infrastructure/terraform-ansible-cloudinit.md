# Terraform + Ansible + Cloud-Init — VM Provisioning on Proxmox

---

## 🌐 Language / Sprache / Język

- [🇬🇧 English](#english)
- [🇵🇱 Polski](#polski)
- [🇩🇪 Deutsch](#deutsch)

---

<a name="english"></a>
# 🇬🇧 English

> **Jump to:** [🇵🇱 Polski](#polski) | [🇩🇪 Deutsch](#deutsch)

## Overview

This document describes the automated VM provisioning workflow used in this homelab.
Instead of manually clicking through a Proxmox GUI installer, a VM is created and configured entirely through code:

```
Terraform   → creates the VM (infrastructure as code)
Cloud-Init  → configures the OS on first boot (user, IP, SSH key)
Ansible     → installs packages and configures services
```

## Prerequisites

| Tool | Location | Version |
|------|----------|---------|
| Terraform | WSL Ubuntu | 1.14.8 |
| Ansible | WSL Ubuntu | 2.20.3 |
| VS Code | Windows 11 | - |
| SSH key | `~/.ssh/id_ed25519` | ed25519 |
| Proxmox API Token | Proxmox GUI | `root@pam!terraform` |

## Part 1: Preparing the Cloud-Init Template

### What is a Cloud-Init template?

A Cloud-Init template is a pre-installed, minimal Debian image (`.qcow2` format) that contains the Cloud-Init agent. Instead of running a full OS installer, Proxmox clones this image and Cloud-Init automatically configures the system on first boot — no manual intervention needed.

### Step 1: Download the Debian genericcloud image

On the Proxmox host (`pve1`):

```bash
wget -O /mnt/hdd-data/template/iso/debian-13-genericcloud-amd64.qcow2 \
  https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2
```

> **Note:** `genericcloud` is different from `netinst`. It has no installer — the OS is already installed inside the image.

### Step 2: Create the base VM

```bash
qm create 9000 --name debian-13-cloudinit-template --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0,tag=20
```

### Step 3: Import the cloud image as a disk

```bash
qm importdisk 9000 /mnt/hdd-data/template/iso/debian-13-genericcloud-amd64.qcow2 local-lvm
```

### Step 4: Attach the disk

```bash
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0
```

### Step 5: Add the Cloud-Init drive

```bash
qm set 9000 --ide2 local-lvm:cloudinit
```

> This creates a virtual CD-ROM that Proxmox uses to pass Cloud-Init configuration (IP, user, SSH key) to the VM on first boot.

### Step 6: Set boot order and serial console

```bash
qm set 9000 --boot c --bootdisk scsi0
qm set 9000 --serial0 socket --vga serial0
```

### Step 7: Convert to template

```bash
qm template 9000
```

> After this step, VM 9000 becomes a template — it cannot be started directly but can be cloned infinitely. Think of it as a mold: one mold, unlimited casts.

---

## Part 2: Terraform Configuration

### Project structure

```
~/terraform/proxmox-vm/
├── main.tf           # provider config + VM resource
├── variables.tf      # variable declarations
├── terraform.tfvars  # variable values (never commit to Git!)
└── .gitignore        # excludes sensitive files from Git
```

### Proxmox API Token

Create in Proxmox GUI: **Datacenter → Permissions → API Tokens → Add**

- User: `root@pam`
- Token ID: `terraform`
- Privilege Separation: unchecked

> ⚠️ Copy the token secret immediately — Proxmox shows it only once.

### main.tf

```hcl
terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.73.0"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://10.100.20.10:8006"
  api_token = var.proxmox_api_token
  insecure  = true
}

resource "proxmox_virtual_environment_vm" "ansible_test" {
  name      = "ansible-test"
  node_name = "pve1"
  vm_id     = 400

  clone {
    vm_id = 9000
    full  = true
  }

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  memory {
    dedicated = 2048
  }

  initialization {
    ip_config {
      ipv4 {
        address = "10.100.20.40/24"
        gateway = "10.100.20.254"
      }
    }
    user_account {
      username = "damian"
      keys     = ["ssh-ed25519 YOUR_PUBLIC_KEY_HERE"]
    }
  }

  network_device {
    bridge  = "vmbr0"
    vlan_id = 20
  }

  operating_system {
    type = "l26"
  }

  started = true
}
```

### variables.tf

```hcl
variable "proxmox_api_token" {
  description = "Proxmox API token"
  type        = string
  sensitive   = true
}
```

### terraform.tfvars

```hcl
proxmox_api_token = "root@pam!terraform=YOUR-TOKEN-HERE"
```

### .gitignore

```
*.tfvars
.terraform/
.terraform.lock.hcl
terraform.tfstate
terraform.tfstate.backup
```

### Terraform workflow

```bash
terraform init      # download provider (run once)
terraform plan      # preview what will be created/changed/destroyed
terraform apply     # apply the plan
terraform destroy   # destroy all resources defined in the config
```

> **Rule:** Always run `terraform plan` before `terraform apply`. Never apply blindly.

---

## Part 3: Ansible Configuration

### Project structure

```
~/ansible/
├── inventory/
│   └── hosts.yml     # list of managed hosts
└── playbooks/
    └── setup-base.yml  # base configuration playbook
```

### inventory/hosts.yml

```yaml
all:
  children:
    proxmox_vms:
      hosts:
        ansible-test:
          ansible_host: 10.100.20.40
          ansible_user: damian
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

### playbooks/setup-base.yml

```yaml
---
- name: Base VM configuration
  hosts: proxmox_vms
  become: true

  tasks:
    - name: Update apt cache
      apt:
        update_cache: true
        cache_valid_time: 3600

    - name: Install base packages
      apt:
        name:
          - curl
          - wget
          - htop
          - vim
          - git
          - ca-certificates
        state: present

    - name: Set timezone
      timezone:
        name: Europe/Berlin

    - name: Set hostname
      hostname:
        name: "{{ inventory_hostname }}"
```

### Ansible commands

```bash
# Test connectivity
ansible all -i ~/ansible/inventory/hosts.yml -m ping

# Run a playbook
ansible-playbook -i ~/ansible/inventory/hosts.yml ~/ansible/playbooks/setup-base.yml
```

### Understanding playbook output

```
ok      → task checked, nothing needed to change
changed → task made a change to the system
failed  → task failed (check error message)
```

> **Idempotency:** Running the same playbook multiple times always produces the same result. If something is already configured correctly, Ansible skips it (`ok`). This makes playbooks safe to run repeatedly.

---

## FAQ

**Q: Why use Cloud-Init instead of a regular installer?**
A: A regular Debian installer requires 10-15 minutes of manual clicking every time. Cloud-Init configures a new VM automatically in ~30 seconds. Once the template exists, every new VM is created with a single `terraform apply`.

**Q: What is the difference between VM 9000 and VM 400?**
A: VM 9000 is the template — a frozen, non-bootable image used as a base for cloning. VM 400 is an actual running VM, cloned from the template. You can have one template and unlimited clones.

**Q: Does Cloud-Init install the operating system?**
A: No. The OS is already installed inside the `genericcloud` image. Cloud-Init only performs first-boot configuration: sets hostname, IP, creates user, injects SSH key. It runs once and never again.

**Q: Why is `terraform.tfvars` in `.gitignore`?**
A: It contains the API token (a secret). Committing secrets to Git — even a private Gitea instance — is bad practice. Keep secrets local or use a secrets manager (Vaultwarden, HashiCorp Vault).

**Q: Can Terraform and Ansible manage LXC containers too?**
A: Yes. Terraform uses `proxmox_virtual_environment_container` resource. Ansible connects to LXC the same way as VMs — via SSH. The workflow is identical.

**Q: What is idempotency?**
A: A property meaning "running this operation multiple times produces the same result as running it once." Ansible is idempotent — it checks current state before making changes. If the system already matches the desired state, nothing happens.

**Q: Why store Terraform and Ansible files in Gitea?**
A: Version control for infrastructure. You can see when a VM configuration changed, revert mistakes, and rebuild everything from scratch. Also useful for portfolio — shows recruiters you practice IaC.

---

<a name="polski"></a>
# 🇵🇱 Polski

> **Przejdź do:** [🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch)

## Przegląd

Ten dokument opisuje zautomatyzowany workflow tworzenia VM używany w tym homelabiku.
Zamiast ręcznie klikać przez instalator Proxmoxa, VM jest tworzona i konfigurowana wyłącznie przez kod:

```
Terraform   → tworzy VM (infrastruktura jako kod)
Cloud-Init  → konfiguruje system przy pierwszym starcie (user, IP, klucz SSH)
Ansible     → instaluje pakiety i konfiguruje usługi
```

## Wymagania wstępne

| Narzędzie | Lokalizacja | Wersja |
|-----------|-------------|--------|
| Terraform | WSL Ubuntu | 1.14.8 |
| Ansible | WSL Ubuntu | 2.20.3 |
| VS Code | Windows 11 | - |
| Klucz SSH | `~/.ssh/id_ed25519` | ed25519 |
| Token API Proxmoxa | GUI Proxmoxa | `root@pam!terraform` |

## Część 1: Przygotowanie szablonu Cloud-Init

### Co to jest szablon Cloud-Init?

Szablon Cloud-Init to wstępnie zainstalowany, minimalny obraz Debiana (format `.qcow2`) zawierający agenta Cloud-Init. Zamiast uruchamiać pełny instalator systemu, Proxmox klonuje ten obraz, a Cloud-Init automatycznie konfiguruje system przy pierwszym starcie — bez żadnej ręcznej interwencji.

### Krok 1: Pobierz obraz Debian genericcloud

Na hoście Proxmox (`pve1`):

```bash
wget -O /mnt/hdd-data/template/iso/debian-13-genericcloud-amd64.qcow2 \
  https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2
```

> **Uwaga:** `genericcloud` różni się od `netinst`. Nie ma instalatora — system jest już zainstalowany wewnątrz obrazu.

### Krok 2: Utwórz bazową VM

```bash
qm create 9000 --name debian-13-cloudinit-template --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0,tag=20
```

### Krok 3: Zaimportuj obraz cloud jako dysk

```bash
qm importdisk 9000 /mnt/hdd-data/template/iso/debian-13-genericcloud-amd64.qcow2 local-lvm
```

### Krok 4: Podłącz dysk

```bash
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0
```

### Krok 5: Dodaj napęd Cloud-Init

```bash
qm set 9000 --ide2 local-lvm:cloudinit
```

> Tworzy wirtualny CD-ROM, przez który Proxmox przekazuje konfigurację Cloud-Init (IP, użytkownik, klucz SSH) do VM przy pierwszym starcie.

### Krok 6: Ustaw kolejność bootowania i konsolę szeregową

```bash
qm set 9000 --boot c --bootdisk scsi0
qm set 9000 --serial0 socket --vga serial0
```

### Krok 7: Zamień VM w szablon

```bash
qm template 9000
```

> Po tym kroku VM 9000 staje się szablonem — nie można jej uruchomić bezpośrednio, ale można ją klonować w nieskończoność. Szablon to forma odlewnicza: jedna forma, nieograniczona liczba odlewów.

---

## Część 2: Konfiguracja Terraform

### Struktura projektu

```
~/terraform/proxmox-vm/
├── main.tf           # konfiguracja providera + zasób VM
├── variables.tf      # deklaracje zmiennych
├── terraform.tfvars  # wartości zmiennych (nigdy nie commituj do Gita!)
└── .gitignore        # wyklucza wrażliwe pliki z Gita
```

### Token API Proxmoxa

Utwórz w GUI Proxmoxa: **Datacenter → Permissions → API Tokens → Add**

- User: `root@pam`
- Token ID: `terraform`
- Privilege Separation: odznaczone

> ⚠️ Skopiuj sekret tokena natychmiast — Proxmox pokazuje go tylko raz.

### main.tf

```hcl
terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.73.0"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://10.100.20.10:8006"
  api_token = var.proxmox_api_token
  insecure  = true
}

resource "proxmox_virtual_environment_vm" "ansible_test" {
  name      = "ansible-test"
  node_name = "pve1"
  vm_id     = 400

  clone {
    vm_id = 9000
    full  = true
  }

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  memory {
    dedicated = 2048
  }

  initialization {
    ip_config {
      ipv4 {
        address = "10.100.20.40/24"
        gateway = "10.100.20.254"
      }
    }
    user_account {
      username = "damian"
      keys     = ["ssh-ed25519 TWÓJ_KLUCZ_PUBLICZNY"]
    }
  }

  network_device {
    bridge  = "vmbr0"
    vlan_id = 20
  }

  operating_system {
    type = "l26"
  }

  started = true
}
```

### variables.tf

```hcl
variable "proxmox_api_token" {
  description = "Token API Proxmoxa"
  type        = string
  sensitive   = true
}
```

### terraform.tfvars

```hcl
proxmox_api_token = "root@pam!terraform=TWÓJ-TOKEN-TUTAJ"
```

### .gitignore

```
*.tfvars
.terraform/
.terraform.lock.hcl
terraform.tfstate
terraform.tfstate.backup
```

### Workflow Terraform

```bash
terraform init      # pobierz provider (raz na początku)
terraform plan      # podgląd co zostanie stworzone/zmienione/usunięte
terraform apply     # zastosuj plan
terraform destroy   # zniszcz wszystkie zasoby zdefiniowane w konfiguracji
```

> **Zasada:** Zawsze uruchamiaj `terraform plan` przed `terraform apply`. Nigdy nie aplikuj w ciemno.

---

## Część 3: Konfiguracja Ansible

### Struktura projektu

```
~/ansible/
├── inventory/
│   └── hosts.yml       # lista zarządzanych hostów
└── playbooks/
    └── setup-base.yml  # playbook bazowej konfiguracji
```

### inventory/hosts.yml

```yaml
all:
  children:
    proxmox_vms:
      hosts:
        ansible-test:
          ansible_host: 10.100.20.40
          ansible_user: damian
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

### playbooks/setup-base.yml

```yaml
---
- name: Bazowa konfiguracja VM
  hosts: proxmox_vms
  become: true

  tasks:
    - name: Aktualizuj cache apt
      apt:
        update_cache: true
        cache_valid_time: 3600

    - name: Zainstaluj podstawowe pakiety
      apt:
        name:
          - curl
          - wget
          - htop
          - vim
          - git
          - ca-certificates
        state: present

    - name: Ustaw strefę czasową
      timezone:
        name: Europe/Berlin

    - name: Ustaw hostname
      hostname:
        name: "{{ inventory_hostname }}"
```

### Komendy Ansible

```bash
# Test połączenia
ansible all -i ~/ansible/inventory/hosts.yml -m ping

# Uruchom playbook
ansible-playbook -i ~/ansible/inventory/hosts.yml ~/ansible/playbooks/setup-base.yml
```

### Rozumienie wyniku playbooka

```
ok      → task sprawdzony, nic nie trzeba było zmieniać
changed → task wprowadził zmianę w systemie
failed  → task się nie powiódł (sprawdź komunikat błędu)
```

> **Idempotentność:** Uruchomienie tego samego playbooka wielokrotnie zawsze daje ten sam wynik. Jeśli coś jest już poprawnie skonfigurowane, Ansible pomija ten krok (`ok`). Dzięki temu playbooki są bezpieczne do wielokrotnego uruchamiania.

---

## FAQ

**P: Dlaczego Cloud-Init zamiast zwykłego instalatora?**
O: Zwykły instalator Debiana wymaga 10-15 minut ręcznego klikania za każdym razem. Cloud-Init konfiguruje nową VM automatycznie w ~30 sekund. Gdy szablon istnieje, każda nowa VM jest tworzona jednym `terraform apply`.

**P: Jaka jest różnica między VM 9000 a VM 400?**
O: VM 9000 to szablon — zamrożony, nieuruchamialny obraz używany jako baza do klonowania. VM 400 to faktycznie działająca VM, sklonowana z szablonu. Jeden szablon, nieograniczona liczba klonów.

**P: Czy Cloud-Init instaluje system operacyjny?**
O: Nie. System jest już zainstalowany wewnątrz obrazu `genericcloud`. Cloud-Init wykonuje tylko konfigurację przy pierwszym starcie: ustawia hostname, IP, tworzy użytkownika, wgrywa klucz SSH. Odpala się raz i nigdy więcej.

**P: Dlaczego `terraform.tfvars` jest w `.gitignore`?**
O: Zawiera token API (sekret). Commitowanie sekretów do Gita — nawet prywatnej instancji Gitea — to zła praktyka. Trzymaj sekrety lokalnie lub użyj managera sekretów (Vaultwarden, HashiCorp Vault).

**P: Czy Terraform i Ansible mogą zarządzać kontenerami LXC?**
O: Tak. Terraform używa zasobu `proxmox_virtual_environment_container`. Ansible łączy się z LXC tak samo jak z VM — przez SSH. Workflow jest identyczny.

**P: Co to jest idempotentność?**
O: Właściwość oznaczająca "wielokrotne wykonanie tej operacji daje taki sam wynik jak jednokrotne". Ansible jest idempotentny — sprawdza aktualny stan przed wprowadzeniem zmian. Jeśli system już odpowiada stanowi docelowemu, nic się nie dzieje.

**P: Po co trzymać pliki Terraform i Ansible w Gitea?**
O: Kontrola wersji dla infrastruktury. Możesz zobaczyć kiedy zmieniła się konfiguracja VM, cofnąć błędy i odbudować wszystko od zera. Przydatne też dla portfolio — pokazuje rekruterom, że praktykujesz IaC.

---

<a name="deutsch"></a>
# 🇩🇪 Deutsch

> **Springen zu:** [🇬🇧 English](#english) | [🇵🇱 Polski](#polski)

## Überblick

Dieses Dokument beschreibt den automatisierten VM-Provisioning-Workflow in diesem Homelab.
Anstatt manuell durch einen Proxmox-GUI-Installer zu klicken, wird eine VM vollständig durch Code erstellt und konfiguriert:

```
Terraform   → erstellt die VM (Infrastruktur als Code)
Cloud-Init  → konfiguriert das OS beim ersten Start (Benutzer, IP, SSH-Schlüssel)
Ansible     → installiert Pakete und konfiguriert Dienste
```

## Voraussetzungen

| Tool | Speicherort | Version |
|------|-------------|---------|
| Terraform | WSL Ubuntu | 1.14.8 |
| Ansible | WSL Ubuntu | 2.20.3 |
| VS Code | Windows 11 | - |
| SSH-Schlüssel | `~/.ssh/id_ed25519` | ed25519 |
| Proxmox API-Token | Proxmox GUI | `root@pam!terraform` |

## Teil 1: Cloud-Init-Template vorbereiten

### Was ist ein Cloud-Init-Template?

Ein Cloud-Init-Template ist ein vorinstalliertes, minimales Debian-Image (`.qcow2`-Format) mit dem Cloud-Init-Agenten. Anstatt einen vollständigen OS-Installer auszuführen, klont Proxmox dieses Image, und Cloud-Init konfiguriert das System automatisch beim ersten Start — ohne manuellen Eingriff.

### Schritt 1: Debian genericcloud-Image herunterladen

Auf dem Proxmox-Host (`pve1`):

```bash
wget -O /mnt/hdd-data/template/iso/debian-13-genericcloud-amd64.qcow2 \
  https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2
```

> **Hinweis:** `genericcloud` unterscheidet sich von `netinst`. Es hat keinen Installer — das OS ist bereits im Image installiert.

### Schritt 2: Basis-VM erstellen

```bash
qm create 9000 --name debian-13-cloudinit-template --memory 2048 --cores 2 \
  --net0 virtio,bridge=vmbr0,tag=20
```

### Schritt 3: Cloud-Image als Festplatte importieren

```bash
qm importdisk 9000 /mnt/hdd-data/template/iso/debian-13-genericcloud-amd64.qcow2 local-lvm
```

### Schritt 4: Festplatte anschließen

```bash
qm set 9000 --scsihw virtio-scsi-pci --scsi0 local-lvm:vm-9000-disk-0
```

### Schritt 5: Cloud-Init-Laufwerk hinzufügen

```bash
qm set 9000 --ide2 local-lvm:cloudinit
```

> Erstellt ein virtuelles CD-ROM-Laufwerk, über das Proxmox die Cloud-Init-Konfiguration (IP, Benutzer, SSH-Schlüssel) beim ersten Start an die VM übergibt.

### Schritt 6: Boot-Reihenfolge und serielle Konsole festlegen

```bash
qm set 9000 --boot c --bootdisk scsi0
qm set 9000 --serial0 socket --vga serial0
```

### Schritt 7: VM in Template umwandeln

```bash
qm template 9000
```

> Nach diesem Schritt wird VM 9000 zu einem Template — sie kann nicht direkt gestartet, aber beliebig oft geklont werden. Das Template ist wie eine Gussform: eine Form, unbegrenzte Abgüsse.

---

## Teil 2: Terraform-Konfiguration

### Projektstruktur

```
~/terraform/proxmox-vm/
├── main.tf           # Provider-Konfiguration + VM-Ressource
├── variables.tf      # Variablendeklarationen
├── terraform.tfvars  # Variablenwerte (niemals in Git committen!)
└── .gitignore        # schließt sensible Dateien aus Git aus
```

### Proxmox API-Token

In Proxmox GUI erstellen: **Datacenter → Permissions → API Tokens → Add**

- User: `root@pam`
- Token ID: `terraform`
- Privilege Separation: deaktiviert

> ⚠️ Token-Secret sofort kopieren — Proxmox zeigt es nur einmal.

### main.tf

```hcl
terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.73.0"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://10.100.20.10:8006"
  api_token = var.proxmox_api_token
  insecure  = true
}

resource "proxmox_virtual_environment_vm" "ansible_test" {
  name      = "ansible-test"
  node_name = "pve1"
  vm_id     = 400

  clone {
    vm_id = 9000
    full  = true
  }

  cpu {
    cores = 2
    type  = "x86-64-v2-AES"
  }

  memory {
    dedicated = 2048
  }

  initialization {
    ip_config {
      ipv4 {
        address = "10.100.20.40/24"
        gateway = "10.100.20.254"
      }
    }
    user_account {
      username = "damian"
      keys     = ["ssh-ed25519 DEIN_ÖFFENTLICHER_SCHLÜSSEL"]
    }
  }

  network_device {
    bridge  = "vmbr0"
    vlan_id = 20
  }

  operating_system {
    type = "l26"
  }

  started = true
}
```

### variables.tf

```hcl
variable "proxmox_api_token" {
  description = "Proxmox API-Token"
  type        = string
  sensitive   = true
}
```

### terraform.tfvars

```hcl
proxmox_api_token = "root@pam!terraform=DEIN-TOKEN-HIER"
```

### .gitignore

```
*.tfvars
.terraform/
.terraform.lock.hcl
terraform.tfstate
terraform.tfstate.backup
```

### Terraform-Workflow

```bash
terraform init      # Provider herunterladen (einmalig)
terraform plan      # Vorschau was erstellt/geändert/gelöscht wird
terraform apply     # Plan anwenden
terraform destroy   # Alle in der Konfiguration definierten Ressourcen löschen
```

> **Regel:** Immer `terraform plan` vor `terraform apply` ausführen. Niemals blind anwenden.

---

## Teil 3: Ansible-Konfiguration

### Projektstruktur

```
~/ansible/
├── inventory/
│   └── hosts.yml       # Liste der verwalteten Hosts
└── playbooks/
    └── setup-base.yml  # Basis-Konfigurationsplaybook
```

### inventory/hosts.yml

```yaml
all:
  children:
    proxmox_vms:
      hosts:
        ansible-test:
          ansible_host: 10.100.20.40
          ansible_user: damian
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

### playbooks/setup-base.yml

```yaml
---
- name: Basis-VM-Konfiguration
  hosts: proxmox_vms
  become: true

  tasks:
    - name: Apt-Cache aktualisieren
      apt:
        update_cache: true
        cache_valid_time: 3600

    - name: Basispakete installieren
      apt:
        name:
          - curl
          - wget
          - htop
          - vim
          - git
          - ca-certificates
        state: present

    - name: Zeitzone festlegen
      timezone:
        name: Europe/Berlin

    - name: Hostname festlegen
      hostname:
        name: "{{ inventory_hostname }}"
```

### Ansible-Befehle

```bash
# Verbindung testen
ansible all -i ~/ansible/inventory/hosts.yml -m ping

# Playbook ausführen
ansible-playbook -i ~/ansible/inventory/hosts.yml ~/ansible/playbooks/setup-base.yml
```

### Playbook-Ausgabe verstehen

```
ok      → Task geprüft, keine Änderung notwendig
changed → Task hat eine Änderung am System vorgenommen
failed  → Task fehlgeschlagen (Fehlermeldung prüfen)
```

> **Idempotenz:** Das mehrfache Ausführen desselben Playbooks liefert immer dasselbe Ergebnis. Wenn etwas bereits korrekt konfiguriert ist, überspringt Ansible diesen Schritt (`ok`). Dadurch sind Playbooks sicher für wiederholte Ausführung.

---

## FAQ

**F: Warum Cloud-Init statt einem regulären Installer?**
A: Ein regulärer Debian-Installer erfordert jedes Mal 10-15 Minuten manuelles Klicken. Cloud-Init konfiguriert eine neue VM automatisch in ~30 Sekunden. Sobald das Template existiert, wird jede neue VM mit einem einzigen `terraform apply` erstellt.

**F: Was ist der Unterschied zwischen VM 9000 und VM 400?**
A: VM 9000 ist das Template — ein eingefrorenes, nicht startbares Image, das als Basis zum Klonen verwendet wird. VM 400 ist eine tatsächlich laufende VM, geklont vom Template. Ein Template, unbegrenzte Klone.

**F: Installiert Cloud-Init das Betriebssystem?**
A: Nein. Das OS ist bereits im `genericcloud`-Image installiert. Cloud-Init führt nur die Erstkonfiguration beim Start durch: setzt Hostname, IP, erstellt Benutzer, injiziert SSH-Schlüssel. Es läuft einmalig und nie wieder.

**F: Warum ist `terraform.tfvars` in `.gitignore`?**
A: Es enthält den API-Token (ein Geheimnis). Geheimnisse in Git zu committen — auch in eine private Gitea-Instanz — ist schlechte Praxis. Geheimnisse lokal aufbewahren oder einen Secrets-Manager verwenden (Vaultwarden, HashiCorp Vault).

**F: Können Terraform und Ansible auch LXC-Container verwalten?**
A: Ja. Terraform verwendet die Ressource `proxmox_virtual_environment_container`. Ansible verbindet sich mit LXC genauso wie mit VMs — über SSH. Der Workflow ist identisch.

**F: Was ist Idempotenz?**
A: Eine Eigenschaft, die bedeutet "diese Operation mehrfach auszuführen liefert dasselbe Ergebnis wie einmalig". Ansible ist idempotent — es prüft den aktuellen Zustand vor Änderungen. Wenn das System bereits dem Sollzustand entspricht, passiert nichts.

**F: Warum Terraform- und Ansible-Dateien in Gitea speichern?**
A: Versionskontrolle für Infrastruktur. Man kann sehen, wann sich eine VM-Konfiguration geändert hat, Fehler rückgängig machen und alles von Grund auf neu aufbauen. Auch nützlich für das Portfolio — zeigt Recruitern, dass man IaC praktiziert.