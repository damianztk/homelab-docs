# Terraform — Homelab IaC Basics | Grundlagen | Podstawy

---

## Navigation | Navigation | Nawigacja

[🇬🇧 English](#en) | [🇩🇪 Deutsch](#de) | [🇵🇱 Polski](#pl)

---

<a name="en"></a>
## 🇬🇧 English

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### What is Terraform?

Terraform is an Infrastructure as Code (IaC) tool. Instead of clicking through a GUI to create VMs and LXC containers, you describe what you want in `.tf` files — Terraform compares that description with the current state and applies only what's missing or changed.

Key principle: **declarative**. You don't say "create a VM". You say "there should be a VM with these parameters". Terraform figures out how to get there.

### Project Structure

```
~/homelab-iac/
└── terraform/
    ├── lxc/
    │   ├── pve1/          # LXC containers on pve1 (utility-apps, PBS)
    │   │   ├── main.tf
    │   │   ├── variables.tf
    │   │   ├── terraform.tfvars   # ← gitignored! contains secrets
    │   │   └── terraform.tfstate  # ← gitignored! managed automatically
    │   └── pve2/          # LXC containers on pve2 (Frigate)
    └── vm/
        ├── pve1/          # VMs on pve1 (ansible-test VM 400)
        └── pve2/          # VMs on pve2 (k3s VM 410)
```

Each directory is an **independent Terraform context** with its own state file and provider version. You must `cd` into the right directory before running any Terraform command.

### Core Workflow

```bash
cd ~/homelab-iac/terraform/vm/pve1

terraform init          # first time only — downloads provider
terraform plan          # ALWAYS before apply — shows what will change
terraform apply         # creates/modifies infrastructure
terraform destroy       # destroys everything in this context
```

**Rules:**
- `terraform plan` before every `apply` — never apply blindly
- `terraform.tfvars` never committed to git (contains API token)
- `terraform.tfstate` never committed to git (managed automatically)

### Provider — bpg/proxmox

The provider that communicates with the Proxmox API.

```hcl
terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.106.0"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://10.100.20.10:8006"   # pve1
  api_token = var.proxmox_api_token
  insecure  = true                           # self-signed cert
}
```

**Provider versions in this homelab:**

| Directory | Version | Reason |
|-----------|---------|--------|
| vm/pve1 | 0.106.0 | ansible-test VM |
| vm/pve2 | 0.106.0 | k3s VM, needs `proxmox_download_file` |
| lxc/pve1 | 0.73.0 | DO NOT upgrade — breaking change in mount_point |
| lxc/pve2 | 0.73.0 | DO NOT upgrade — breaking change in mount_point |

### Creating a VM (Cloud-Init)

```hcl
resource "proxmox_virtual_environment_vm" "ansible_test" {
  name      = "ansible-test"
  node_name = "pve1"
  vm_id     = 400

  clone {
    vm_id = 9000    # Cloud-Init template
    full  = true
  }

  cpu    { cores = 2; type = "x86-64-v2-AES" }
  memory { dedicated = 2048 }

  initialization {
    ip_config {
      ipv4 { address = "10.100.20.40/24"; gateway = "10.100.20.254" }
    }
    user_account {
      username = "damian"
      keys     = ["ssh-ed25519 AAAA... damian-pc-wsl"]
    }
  }

  network_device { bridge = "vmbr0" }
  operating_system { type = "l26" }
  started = true
  vga { type = "serial0"; memory = 16 }
}
```

### Creating a VM from Cloud Image (without template)

Used when the template is on a different node — avoids cross-node clone limitation.

```hcl
# Step 1: download cloud image to target node
resource "proxmox_download_file" "debian13" {
  content_type = "import"
  datastore_id = "hdd-data-2tb-p2"
  node_name    = "pve2"
  url          = "https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2"
  file_name    = "debian-13-genericcloud-amd64.qcow2"
  overwrite    = false
}

# Step 2: create VM from downloaded image
resource "proxmox_virtual_environment_vm" "k3s" {
  name      = "k3s"
  node_name = "pve2"
  vm_id     = 410

  disk {
    datastore_id = "local-lvm"
    file_id      = proxmox_download_file.debian13.id
    interface    = "scsi0"
    size         = 40
    discard      = "on"
  }
  # ... rest same as clone-based VM
}
```

### Creating an LXC Container

```hcl
resource "proxmox_virtual_environment_container" "utility_apps" {
  node_name    = "pve1"
  vm_id        = 300
  unprivileged = true

  cpu    { cores = 2 }
  memory { dedicated = 4096 }
  disk   { datastore_id = "local-lvm"; size = 16 }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  initialization {
    hostname = "utility-apps"
    ip_config {
      ipv4 { address = "10.100.20.30/24"; gateway = "10.100.20.254" }
    }
    user_account {
      keys = ["ssh-ed25519 AAAA... damian-pc-wsl"]
    }
  }

  network_interface { name = "eth0"; bridge = "vmbr0" }
  features { nesting = true }   # required for Docker in LXC
}
```

### Variables and Secrets

`variables.tf` — declares variables:
```hcl
variable "proxmox_api_token" {
  description = "Proxmox API token"
  type        = string
  sensitive   = true
}
```

`terraform.tfvars` — actual values (gitignored!):
```hcl
proxmox_api_token = "root@pam!terraform=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### Multiple Resources in One File

Terraform manages all resources in the same directory as a single unit. Adding a second VM is as simple as adding another `resource` block:

```hcl
resource "proxmox_virtual_environment_vm" "second_vm" {
  name  = "second-vm"
  vm_id = 401
  # ...
}
```

`terraform plan` will show `1 to add` — the existing VM stays untouched.

### State and Drift

Terraform tracks what it created in `terraform.tfstate`. When you run `terraform plan`, it compares:
- What the `.tf` file says should exist
- What the state says was created
- What actually exists in Proxmox

If you change something manually (e.g. add a bind mount via `pct set`), there's a **drift** between state and reality. Terraform will try to "fix" this on next apply.

### Known Issues and Solutions

**Issue:** Bind mounts fail with HTTP 403 when using API token
**Cause:** Proxmox API restricts bind mount operations to `root@pam` authentication only. API tokens, even with Administrator role, cannot perform bind mounts.
**Solution:** Create LXC via Terraform (without mount_point), then add bind mounts manually:
```bash
pct set 300 -mp0 /opt/lxc-data/utility-apps-data,mp=/data
pct set 300 -mp1 /opt/docker-data/utility-apps-data,mp=/opt/docker-data
```

**Issue:** Cannot clone VM cross-node (template on pve1, VM should be on pve2)
**Cause:** Proxmox cannot clone from `local-lvm` storage across nodes — it's node-local.
**Solution:** Use `proxmox_download_file` to download cloud image directly to target node. Requires `Import` content type enabled on target storage (Datacenter → Storage → Edit).

**Issue:** `terraform plan` shows `destroy and then create` after provider upgrade
**Cause:** Breaking change in provider schema between versions (observed: mount_point schema changed between 0.73 and 0.106).
**Solution:** Keep lxc directories on 0.73.0. Always read CHANGELOG before upgrading provider.

**Issue:** VM shows `started = false → true` after provider upgrade
**Cause:** VM was manually stopped; provider now correctly detects the state mismatch.
**Solution:** This is expected behavior — apply will simply start the VM.

**Issue:** `terraform destroy -target` shows deprecation warnings
**Cause:** `-target` is not intended for regular use — only for emergencies.
**Solution:** Remove the resource block from `.tf` file, then run `terraform apply`. Clean approach with no warnings.

**Issue:** `terraform.tfstate` shows drift from manual changes
**Cause:** Something was changed outside Terraform (e.g. bind mounts, disk resize).
**Solution:** Either add the change to `.tf` file to match reality, or use `pct resize` instead of Terraform for disk changes.

### FAQ

**Q: Do I need `terraform init` every time?**
A: No — only once per directory, or when you change provider version or move to a new machine. After `destroy`+`apply` in the same directory, no `init` needed.

**Q: Can different directories use different provider versions?**
A: Yes. Each directory has its own `.terraform.lock.hcl` and state. This is intentional — keeps stable LXC on 0.73.0 while new VMs use 0.106.0.

**Q: What is `terraform.tfstate.backup`?**
A: Automatic backup of the previous state, created before every apply. Useful for recovery.

**Q: Can I rename a Terraform resource without destroying it?**
A: Not directly — rename requires `terraform state mv old_name new_name` before applying.

**Q: What does `tainted` mean in plan output?**
A: A resource that was partially created (apply failed midway). Terraform will destroy and recreate it on next apply.

---

<a name="de"></a>
## 🇩🇪 Deutsch

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Was ist Terraform?

Terraform ist ein Infrastructure as Code (IaC) Tool. Anstatt durch eine GUI zu klicken, um VMs und LXC-Container zu erstellen, beschreibt man in `.tf`-Dateien den gewünschten Zustand — Terraform vergleicht diese Beschreibung mit dem aktuellen Zustand und wendet nur das an, was fehlt oder geändert wurde.

Kernprinzip: **deklarativ**. Man sagt nicht "erstelle eine VM". Man sagt "es soll eine VM mit diesen Parametern existieren". Terraform findet heraus, wie dieser Zustand erreicht wird.

### Projektstruktur

```
~/homelab-iac/
└── terraform/
    ├── lxc/
    │   ├── pve1/          # LXC-Container auf pve1 (utility-apps, PBS)
    │   └── pve2/          # LXC-Container auf pve2 (Frigate)
    └── vm/
        ├── pve1/          # VMs auf pve1 (ansible-test VM 400)
        └── pve2/          # VMs auf pve2 (k3s VM 410)
```

Jedes Verzeichnis ist ein **unabhängiger Terraform-Kontext** mit eigener State-Datei und Provider-Version. Vor jedem Terraform-Befehl muss ins richtige Verzeichnis gewechselt werden.

### Grundlegender Workflow

```bash
cd ~/homelab-iac/terraform/vm/pve1

terraform init          # nur einmalig — lädt Provider herunter
terraform plan          # IMMER vor apply — zeigt was sich ändert
terraform apply         # erstellt/ändert Infrastruktur
terraform destroy       # zerstört alles in diesem Kontext
```

**Regeln:**
- `terraform plan` vor jedem `apply` — niemals blind anwenden
- `terraform.tfvars` niemals ins Git (enthält API-Token)
- `terraform.tfstate` niemals ins Git (wird automatisch verwaltet)

### Provider — bpg/proxmox

Der Provider kommuniziert mit der Proxmox API.

**Provider-Versionen in diesem Homelab:**

| Verzeichnis | Version | Grund |
|-------------|---------|-------|
| vm/pve1 | 0.106.0 | ansible-test VM |
| vm/pve2 | 0.106.0 | k3s VM, benötigt `proxmox_download_file` |
| lxc/pve1 | 0.73.0 | NICHT upgraden — Breaking Change in mount_point |
| lxc/pve2 | 0.73.0 | NICHT upgraden — Breaking Change in mount_point |

### Bekannte Probleme und Lösungen

**Problem:** Bind Mounts schlagen mit HTTP 403 fehl
**Ursache:** Proxmox API erlaubt Bind Mounts nur für `root@pam` — nicht für API-Tokens
**Lösung:** LXC per Terraform erstellen, dann Bind Mounts manuell per `pct set` hinzufügen

**Problem:** Cross-Node VM-Klon nicht möglich (Template auf pve1, VM soll auf pve2)
**Ursache:** Proxmox kann nicht von `local-lvm` Storage knotenübergreifend klonen
**Lösung:** `proxmox_download_file` verwenden, um Cloud-Image direkt auf den Zielknoten herunterzuladen

**Problem:** `terraform plan` zeigt `destroy and then create` nach Provider-Upgrade
**Ursache:** Breaking Change im Provider-Schema (beobachtet: mount_point zwischen 0.73 und 0.106)
**Lösung:** lxc-Verzeichnisse auf 0.73.0 belassen. CHANGELOG vor jedem Upgrade lesen.

**Problem:** `-target` zeigt Deprecation-Warnungen
**Ursache:** `-target` ist nicht für den regulären Einsatz gedacht
**Lösung:** Ressource-Block aus `.tf` entfernen, dann `terraform apply` ausführen

### FAQ

**F: Muss ich `terraform init` jedes Mal ausführen?**
A: Nein — nur einmalig pro Verzeichnis oder bei Provider-Versionsänderung.

**F: Können verschiedene Verzeichnisse unterschiedliche Provider-Versionen verwenden?**
A: Ja. Jedes Verzeichnis hat seine eigene `.terraform.lock.hcl` und seinen eigenen State.

**F: Was bedeutet `tainted` in der Plan-Ausgabe?**
A: Eine Ressource, die nur teilweise erstellt wurde (Apply ist mittendrin fehlgeschlagen). Terraform wird sie beim nächsten Apply zerstören und neu erstellen.

---

<a name="pl"></a>
## 🇵🇱 Polski

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Czym jest Terraform?

Terraform to narzędzie Infrastructure as Code (IaC). Zamiast klikać w GUI żeby tworzyć VM i kontenery LXC, opisujesz w plikach `.tf` co chcesz mieć — Terraform porównuje ten opis z aktualnym stanem i aplikuje tylko to, czego brakuje lub co się zmieniło.

Kluczowa zasada: **deklaratywność**. Nie mówisz "stwórz VM". Mówisz "powinna istnieć VM z tymi parametrami". Terraform sam wymyśli jak do tego dojść.

### Struktura projektu

```
~/homelab-iac/
└── terraform/
    ├── lxc/
    │   ├── pve1/          # LXC na pve1 (utility-apps, PBS)
    │   └── pve2/          # LXC na pve2 (Frigate)
    └── vm/
        ├── pve1/          # VM na pve1 (ansible-test VM 400)
        └── pve2/          # VM na pve2 (k3s VM 410)
```

Każdy katalog to **niezależny kontekst Terraform** z własnym plikiem state i własną wersją providera. Przed każdą komendą Terraform trzeba wejść do właściwego katalogu.

### Podstawowy workflow

```bash
cd ~/homelab-iac/terraform/vm/pve1

terraform init          # tylko raz — pobiera provider
terraform plan          # ZAWSZE przed apply — pokazuje co się zmieni
terraform apply         # tworzy/modyfikuje infrastrukturę
terraform destroy       # niszczy wszystko w tym kontekście
```

**Zasady:**
- `terraform plan` przed każdym `apply` — nigdy w ciemno
- `terraform.tfvars` nigdy do Gitea (zawiera token API)
- `terraform.tfstate` nigdy do Gitea (zarządzany automatycznie)

### Provider — bpg/proxmox

Provider komunikuje się z API Proxmoxa.

**Wersje providera w tym homelabiu:**

| Katalog | Wersja | Powód |
|---------|--------|-------|
| vm/pve1 | 0.106.0 | VM ansible-test |
| vm/pve2 | 0.106.0 | VM k3s, potrzebuje `proxmox_download_file` |
| lxc/pve1 | 0.73.0 | NIE UPGRADOWAĆ — breaking change w mount_point |
| lxc/pve2 | 0.73.0 | NIE UPGRADOWAĆ — breaking change w mount_point |

### Wiele zasobów w jednym pliku

Terraform zarządza wszystkimi zasobami w tym samym katalogu jako jedną całość. Dodanie drugiej VM to po prostu dodanie kolejnego bloku `resource`:

```hcl
resource "proxmox_virtual_environment_vm" "druga_vm" {
  name  = "druga-vm"
  vm_id = 401
  # ...
}
```

`terraform plan` pokaże `1 to add` — istniejąca VM zostaje nieruszona.

### Stan i rozbieżności (drift)

Terraform śledzi co stworzył w pliku `terraform.tfstate`. Przy `terraform plan` porównuje:
- Co plik `.tf` mówi że powinno istnieć
- Co state mówi że zostało stworzone
- Co faktycznie istnieje w Proxmoxie

Jeśli zmienisz coś ręcznie (np. dodasz bind mount przez `pct set`), powstaje **rozbieżność** między stanem a rzeczywistością. Terraform będzie próbował to "naprawić" przy następnym apply.

### Znane problemy i rozwiązania

**Problem:** Bind mounty nie działają przez Terraform (HTTP 403)
**Przyczyna:** API Proxmoxa ogranicza operacje bind mount do autentykacji `root@pam`. Tokeny API, nawet z rolą Administratora, nie mogą wykonywać bind mountów.
**Rozwiązanie:** Tworzysz LXC przez Terraform (bez mount_point), a potem dodajesz bind mounty ręcznie:
```bash
pct set 300 -mp0 /opt/lxc-data/utility-apps-data,mp=/data
pct set 300 -mp1 /opt/docker-data/utility-apps-data,mp=/opt/docker-data
```

**Problem:** Nie można sklonować VM cross-node (template na pve1, VM ma być na pve2)
**Przyczyna:** Proxmox nie może klonować ze storage `local-lvm` między węzłami — to storage lokalny.
**Rozwiązanie:** Użyj `proxmox_download_file` żeby pobrać cloud image bezpośrednio na docelowy węzeł. Wymaga włączenia typu contentu `Import` na docelowym storage (Datacenter → Storage → Edit).

**Problem:** `terraform plan` pokazuje `destroy and then create` po upgrade providera
**Przyczyna:** Breaking change w schemacie providera (zaobserwowane: schemat mount_point zmienił się między 0.73 a 0.106).
**Rozwiązanie:** Katalogi lxc zostają na 0.73.0. Zawsze czytaj CHANGELOG przed upgradeem providera.

**Problem:** `-target` pokazuje ostrzeżenia o deprecacji
**Przyczyna:** `-target` nie jest przeznaczony do regularnego użycia — tylko do sytuacji awaryjnych.
**Rozwiązanie:** Usuń blok resource z pliku `.tf`, potem `terraform apply`. Czyste podejście bez ostrzeżeń.

### FAQ

**P: Czy muszę wykonywać `terraform init` za każdym razem?**
O: Nie — tylko raz na katalog, albo przy zmianie wersji providera lub przeniesieniu na nową maszynę. Po `destroy`+`apply` w tym samym katalogu `init` nie jest potrzebny.

**P: Czy różne katalogi mogą używać różnych wersji providera?**
O: Tak. Każdy katalog ma własny `.terraform.lock.hcl` i stan. To jest celowe — stabilne LXC zostają na 0.73.0, nowe VM używają 0.106.0.

**P: Co oznacza `tainted` w outputcie planu?**
O: Zasób który został częściowo stworzony (apply się nie dokończył). Terraform zniszczy go i odtworzy przy następnym apply.

**P: Czy mogę zmienić nazwę zasobu Terraform bez jego niszczenia?**
O: Nie bezpośrednio — zmiana nazwy wymaga `terraform state mv stara_nazwa nowa_nazwa` przed apply.

**P: Co to jest `terraform.tfstate.backup`?**
O: Automatyczna kopia poprzedniego stanu, tworzona przed każdym apply. Przydatna do odtworzenia po błędzie.
