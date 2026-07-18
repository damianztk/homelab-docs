# k3s — Installation and Setup | Installation und Einrichtung | Instalacja i konfiguracja

---

## Navigation | Navigation | Nawigacja

[🇬🇧 English](#en) | [🇩🇪 Deutsch](#de) | [🇵🇱 Polski](#pl)

---

<a name="en"></a>
## 🇬🇧 English

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Description

k3s is a lightweight, certified Kubernetes distribution packaged as a single binary. It runs on the k3s VM (ID 410) on pve2 as a single-node cluster used for learning, portfolio deployment, and hosting Grafana/Prometheus monitoring.

### Infrastructure

| Parameter | Value |
|-----------|-------|
| Host | pve2 (`10.x.x.x`) |
| VM ID | 410 |
| VM Name | k3s |
| IP | `10.x.x.x` |
| RAM | 10 GB |
| CPU | 2 vCPU |
| Disk | 40 GB (local-lvm) |
| OS | Debian 13 (cloud image) |
| k3s version | v1.35.5+k3s1 |
| Container runtime | containerd (default) |

### VM Creation — Terraform

Location: `~/homelab-iac/terraform/vm/pve2/`

The VM is created from a Debian 13 cloud image downloaded directly to pve2 — **not** cloned from a template. This approach is used because the Cloud-Init template (VM 9000) lives on pve1's `local-lvm` storage, which cannot be cloned cross-node.

```hcl
# Download Debian 13 cloud image to pve2 HDD
resource "proxmox_download_file" "debian13_cloud_image" {
  content_type = "import"
  datastore_id = "hdd-data-2tb-p2"
  node_name    = "pve2"
  url          = "https://cloud.debian.org/images/cloud/trixie/latest/debian-13-genericcloud-amd64.qcow2"
  file_name    = "debian-13-genericcloud-amd64.qcow2"
  overwrite    = false
}

# Create VM from downloaded image
resource "proxmox_virtual_environment_vm" "k3s" {
  name      = "k3s"
  node_name = "pve2"
  vm_id     = 410
  # Cloud-Init: IP 10.x.x.x, user damian, SSH key from WSL
}
```

```bash
cd ~/homelab-iac/terraform/vm/pve2
terraform plan
terraform apply
```

**Requirements:**
- Storage `hdd-data-2tb-p2` must have `Import` content type enabled (Datacenter → Storage → Edit)
- Provider version: `~> 0.106.0` (required for `proxmox_download_file` with `content_type = "import"`)

### Base Configuration — Ansible

After VM creation, configure base system and Docker:

```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/configure-vm.yml -l k3s
```

This runs two roles sequentially:
- `setup-base` — apt update, base packages, timezone (Europe/Berlin), hostname
- `docker` — Docker CE installation (for building images, not as k3s runtime)

### k3s Installation — Ansible

Location: `ansible/playbooks/install-k3s.yml`

```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-k3s.yml
```

**How install-k3s.yml works:**

```yaml
# Download installer separately (safer than curl | sh)
- name: Download k3s installer
  ansible.builtin.get_url:
    url: https://get.k3s.io
    dest: /tmp/k3s_install.sh
    mode: '0755'

# Run installer — creates: makes this idempotent
- name: Run k3s installer
  ansible.builtin.command:
    cmd: /tmp/k3s_install.sh
    creates: /usr/local/bin/k3s

# Wait for kubeconfig to appear — signals cluster is ready
- name: Wait for k3s to be ready
  ansible.builtin.wait_for:
    path: /etc/rancher/k3s/k3s.yaml
    timeout: 60

- name: Enable and start k3s service
  ansible.builtin.systemd:
    name: k3s
    enabled: true
    state: started
```

Why `get_url` + `command` instead of `curl | sh`:
- `curl | sh` is a security antipattern (executes remote code without verification)
- Pipes in `shell` module aren't idempotent
- `creates:` parameter doesn't work with pipes

### Default Components

After installation, k3s automatically deploys these pods in `kube-system` namespace:

| Pod | Purpose |
|-----|---------|
| coredns | DNS resolution inside the cluster |
| traefik | Ingress controller — HTTP routing (like NPM, but inside k8s) |
| helm-install-traefik | One-time job that installed Traefik via Helm (Completed) |
| local-path-provisioner | Automatically creates PersistentVolumes on local disk |
| metrics-server | Collects CPU/RAM metrics — needed for `kubectl top` |
| svclb-traefik | k3s ServiceLB — forwards external traffic to Traefik |

### Verifying Installation

```bash
# Check node status
ssh k3s "sudo k3s kubectl get nodes"
# Expected: NAME=k3s, STATUS=Ready, ROLES=control-plane

# Check all pods
ssh k3s "sudo k3s kubectl get pods -A"
# All should be Running or Completed

# k3s service status
ssh k3s "sudo systemctl status k3s"
```

### Container Runtime

k3s uses **containerd** as its container runtime — not Docker. This means:

- `docker ps` on the k3s VM shows nothing related to k3s pods
- Use `sudo crictl ps` to see containers at runtime level
- Use `sudo k3s kubectl get pods -A` to see pods at Kubernetes level
- Docker installed on this VM is for **building images**, not running k3s workloads

### Next Steps

After installation, configure for comfortable use:

1. **kubectl without sudo** — add user to `k3s` group or set permissions on kubeconfig
2. **kubeconfig in WSL** — copy `/etc/rancher/k3s/k3s.yaml` to WSL, update server IP, use `kubectl` locally

See the k3s operations guide for full kubectl usage documentation.

### Known Issues and Solutions

**Issue:** SSH `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED` after VM recreation
**Cause:** VM was destroyed and recreated with same IP — new SSH host key
**Solution:**
```bash
ssh-keygen -R 10.x.x.x
ssh-keyscan -H 10.x.x.x >> ~/.ssh/known_hosts
```

**Issue:** `terraform apply` fails with cross-node clone error
**Cause:** Template VM 9000 is on pve1's local-lvm, cannot be cloned to pve2
**Solution:** Use `proxmox_download_file` approach (already implemented) — downloads cloud image directly to pve2

**Issue:** `content_type = "import"` not accepted by provider
**Cause:** Older provider versions (< ~0.80) don't support `import` content type
**Solution:** Upgrade provider to `~> 0.106.0` in `terraform/vm/pve2/main.tf`

**Issue:** `proxmox_virtual_environment_download_file` deprecation warning
**Cause:** Renamed to `proxmox_download_file` in newer provider versions
**Solution:** Use `proxmox_download_file` (already implemented)

**Issue:** VM shows as `tainted` after failed apply
**Cause:** Apply failed midway — VM partially created
**Solution:** Run `terraform apply` again — Terraform automatically destroys and recreates tainted resources

**Issue:** Terraform requires SSH agent for VM creation with cloud image
**Cause:** Provider needs SSH access to pve2 for disk import operations
**Solution:** Add `ssh` block to provider + ensure ssh-agent is running:
```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519
```
Or add to provider:
```hcl
ssh {
  agent    = true
  username = "root"
  node {
    name    = "pve2"
    address = "10.x.x.x"
  }
}
```

---

<a name="de"></a>
## 🇩🇪 Deutsch

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Beschreibung

k3s ist eine leichtgewichtige, zertifizierte Kubernetes-Distribution, verpackt als einzelne Binärdatei. Sie läuft auf der k3s-VM (ID 410) auf pve2 als Single-Node-Cluster für Lernen, Portfolio-Deployment und Grafana/Prometheus-Monitoring.

### Infrastruktur

| Parameter | Wert |
|-----------|------|
| Host | pve2 (`10.x.x.x`) |
| VM ID | 410 |
| VM Name | k3s |
| IP | `10.x.x.x` |
| RAM | 10 GB |
| CPU | 2 vCPU |
| Disk | 40 GB (local-lvm) |
| OS | Debian 13 (Cloud Image) |
| k3s Version | v1.35.5+k3s1 |
| Container Runtime | containerd (Standard) |

### VM-Erstellung — Terraform

```bash
cd ~/homelab-iac/terraform/vm/pve2
terraform plan
terraform apply
```

Die VM wird aus einem Debian-13-Cloud-Image erstellt, das direkt auf pve2 heruntergeladen wird — **nicht** aus einem geklonten Template. Das Cloud-Init-Template (VM 9000) befindet sich auf dem lokalen `local-lvm`-Storage von pve1, der nicht knotenübergreifend geklont werden kann.

**Voraussetzung:** Storage `hdd-data-2tb-p2` muss den Content-Typ `Import` aktiviert haben (Datacenter → Storage → Bearbeiten).

### Basiskonfiguration — Ansible

```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/configure-vm.yml -l k3s
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-k3s.yml
```

### Standardkomponenten nach Installation

| Pod | Zweck |
|-----|-------|
| coredns | DNS-Auflösung innerhalb des Clusters |
| traefik | Ingress-Controller — HTTP-Routing |
| local-path-provisioner | Erstellt automatisch PersistentVolumes |
| metrics-server | Sammelt CPU/RAM-Metriken |
| svclb-traefik | Leitet externen Traffic an Traefik weiter |

### Bekannte Probleme und Lösungen

**Problem:** SSH `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED` nach VM-Neuerstellung
**Lösung:**
```bash
ssh-keygen -R 10.x.x.x
ssh-keyscan -H 10.x.x.x >> ~/.ssh/known_hosts
```

**Problem:** `terraform apply` schlägt mit Cross-Node-Klon-Fehler fehl
**Ursache:** Template VM 9000 befindet sich auf dem lokalen Storage von pve1
**Lösung:** `proxmox_download_file`-Ansatz verwenden (bereits implementiert)

**Problem:** `content_type = "import"` wird vom Provider nicht akzeptiert
**Ursache:** Ältere Provider-Versionen unterstützen den `import`-Content-Typ nicht
**Lösung:** Provider auf `~> 0.106.0` upgraden

---

<a name="pl"></a>
## 🇵🇱 Polski

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Opis

k3s to lekka, certyfikowana dystrybucja Kubernetes spakowana jako jeden plik binarny. Działa na VM k3s (ID 410) na pve2 jako single-node klaster używany do nauki, deployowania portfolio i hostowania monitoringu Grafana/Prometheus.

### Infrastruktura

| Parametr | Wartość |
|----------|---------|
| Host | pve2 (`10.x.x.x`) |
| VM ID | 410 |
| Nazwa VM | k3s |
| IP | `10.x.x.x` |
| RAM | 10 GB |
| CPU | 2 vCPU |
| Dysk | 40 GB (local-lvm) |
| OS | Debian 13 (cloud image) |
| Wersja k3s | v1.35.5+k3s1 |
| Container runtime | containerd (domyślny) |

### Tworzenie VM — Terraform

Lokalizacja: `~/homelab-iac/terraform/vm/pve2/`

VM jest tworzona z cloud image Debiana 13 pobranego bezpośrednio na pve2 — **nie** przez klonowanie template'u. Podejście z `proxmox_download_file` zostało użyte ponieważ template Cloud-Init (VM 9000) jest na `local-lvm` pve1, który nie może być klonowany cross-node.

**Wymagania przed `terraform apply`:**
- Storage `hdd-data-2tb-p2` musi mieć włączony typ contentu `Import` (Datacenter → Storage → Edit)
- Wersja providera: `~> 0.106.0` (wymagane dla `proxmox_download_file` z `content_type = "import"`)

```bash
cd ~/homelab-iac/terraform/vm/pve2
terraform plan
terraform apply
```

### Konfiguracja bazowa — Ansible

Po stworzeniu VM, skonfiguruj system bazowy i Dockera:

```bash
cd ~/homelab-iac
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/configure-vm.yml -l k3s
```

Uruchamia dwie role sekwencyjnie:
- `setup-base` — apt update, pakiety bazowe, timezone (Europe/Berlin), hostname
- `docker` — instalacja Docker CE (do budowania obrazów, nie jako runtime k3s)

### Instalacja k3s — Ansible

```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/install-k3s.yml
```

Dlaczego `get_url` + `command` zamiast `curl | sh`:
- `curl | sh` to antypattern bezpieczeństwa (wykonuje zdalny kod bez weryfikacji)
- Pipe w module `shell` nie jest idempotentny
- Parametr `creates:` nie działa z pipe

### Domyślne komponenty po instalacji

Po instalacji k3s automatycznie deployuje te pody w namespace `kube-system`:

| Pod | Przeznaczenie |
|-----|---------------|
| coredns | Rozwiązywanie DNS wewnątrz klastra |
| traefik | Ingress controller — routing HTTP (jak NPM, ale wewnątrz k8s) |
| helm-install-traefik | Jednorazowy job który zainstalował Traefika przez Helm (Completed) |
| local-path-provisioner | Automatycznie tworzy PersistentVolumes na lokalnym dysku |
| metrics-server | Zbiera metryki CPU/RAM — potrzebny do `kubectl top` |
| svclb-traefik | k3s ServiceLB — przekazuje ruch zewnętrzny do Traefika |

### Weryfikacja instalacji

```bash
# Status węzła
ssh k3s "sudo k3s kubectl get nodes"
# Oczekiwane: NAME=k3s, STATUS=Ready, ROLES=control-plane

# Wszystkie pody
ssh k3s "sudo k3s kubectl get pods -A"
# Wszystkie powinny być Running lub Completed

# Status serwisu k3s
ssh k3s "sudo systemctl status k3s"
```

### Container runtime

k3s używa **containerd** jako container runtime — nie Dockera. Oznacza to:

- `docker ps` na VM k3s nie pokazuje nic związanego z podami k3s
- Użyj `sudo crictl ps` żeby zobaczyć kontenery na poziomie runtime
- Użyj `sudo k3s kubectl get pods -A` żeby zobaczyć pody na poziomie Kubernetes
- Docker zainstalowany na tej VM służy do **budowania obrazów**, nie do uruchamiania workloadów k3s

### Następne kroki

Po instalacji skonfiguruj dla wygodniejszego użycia:

1. **kubectl bez sudo** — dodaj usera do grupy `k3s` lub ustaw uprawnienia na kubeconfig
2. **kubeconfig w WSL** — skopiuj `/etc/rancher/k3s/k3s.yaml` do WSL, zaktualizuj IP serwera, używaj `kubectl` lokalnie

### Znane problemy i rozwiązania

**Problem:** SSH `WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED` po odtworzeniu VM
**Przyczyna:** VM została zniszczona i odtworzona z tym samym IP — nowy klucz SSH hosta
**Rozwiązanie:**
```bash
ssh-keygen -R 10.x.x.x
ssh-keyscan -H 10.x.x.x >> ~/.ssh/known_hosts
```

**Problem:** `terraform apply` wywala błąd cross-node clone
**Przyczyna:** Template VM 9000 jest na local-lvm pve1, nie można klonować na pve2
**Rozwiązanie:** Podejście z `proxmox_download_file` (już zaimplementowane) — pobiera cloud image bezpośrednio na pve2

**Problem:** `content_type = "import"` nie jest akceptowany przez provider
**Przyczyna:** Starsze wersje providera (< ~0.80) nie obsługują typu contentu `import`
**Rozwiązanie:** Upgrade providera do `~> 0.106.0` w `terraform/vm/pve2/main.tf`

**Problem:** VM pokazuje się jako `tainted` po nieudanym apply
**Przyczyna:** Apply się nie dokończył — VM częściowo stworzona
**Rozwiązanie:** Uruchom `terraform apply` ponownie — Terraform automatycznie niszczy i odtwarza zasoby tainted

**Problem:** Terraform wymaga SSH agent przy tworzeniu VM z cloud image
**Przyczyna:** Provider potrzebuje dostępu SSH do pve2 dla operacji importu dysku
**Rozwiązanie:** Dodaj blok `ssh` do providera + upewnij się że ssh-agent działa:
```bash
eval $(ssh-agent -s)
ssh-add ~/.ssh/id_ed25519
```

### FAQ

**P: Dlaczego k3s zamiast "pełnego" Kubernetes?**
O: k3s to ta sama logika co K8s, jeden plik binarny, ~512MB RAM na węzeł. Idealny na homelab. Pełny K8s wymaga kilkunastu osobnych komponentów i jest zaprojektowany dla dużych klastrów w chmurze.

**P: Czy Docker zainstalowany na VM jest używany przez k3s?**
O: Nie. k3s używa `containerd` jako runtime. Docker na tej VM służy do budowania obrazów i lokalnego testowania kontenerów przed wrzuceniem na k3s.

**P: Czemu `docker ps` nic nie pokazuje na VM k3s?**
O: Bo kontenery k3s są zarządzane przez `containerd`, nie przez Docker daemon. Użyj `sudo crictl ps` lub `sudo k3s kubectl get pods -A`.

**P: Czy jeden węzeł to "prawdziwy" klaster?**
O: Tak — to single-node klaster. W produkcji używa się minimum 3 węzłów dla HA (high availability). Na homelabowym single-nodzie nie ma redundancji, ale wszystkie funkcje K8s działają identycznie.
