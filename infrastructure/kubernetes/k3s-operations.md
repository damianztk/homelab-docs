# k3s — Operations Guide | Betriebshandbuch | Przewodnik operacyjny

<!-- Navigation -->
[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

---

<a name="english"></a>

## 🇬🇧 English

[🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

### Overview

This guide covers day-to-day operations of the k3s cluster: kubectl setup, core Kubernetes concepts, Helm package manager, and the monitoring stack. It assumes k3s is already installed (see `k3s-install.md`).

**Cluster:** Single-node k3s on VM 410 (`10.x.x.x`, pve2, 10GB RAM, 2 vCPU, 40GB disk)

---

### 1. kubectl Setup in WSL

kubectl is the Kubernetes CLI — it communicates with the k3s API server over the network using a kubeconfig file. It does not need to run on the k3s VM itself.

#### Install kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client
```

#### Copy kubeconfig from k3s VM

The kubeconfig file is owned by root on the VM — copy it via a temporary file:

```bash
mkdir -p ~/.kube
ssh k3s "sudo cp /etc/rancher/k3s/k3s.yaml /home/damian/k3s.yaml && sudo chown damian:damian /home/damian/k3s.yaml"
scp k3s:/home/damian/k3s.yaml ~/.kube/config
ssh k3s "rm /home/damian/k3s.yaml"
```

#### Fix server IP

The default kubeconfig points to `127.0.0.1` (localhost of the VM). Change it to the actual VM IP:

```bash
sed -i 's/127.0.0.1/10.x.x.x/' ~/.kube/config
```

#### Verify

```bash
kubectl get nodes
# Expected: NAME=k3s  STATUS=Ready  ROLES=control-plane
```

> **Note:** After VM destroy+recreate with the same IP, run `ssh-keygen -R 10.x.x.x` and `ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts` before copying kubeconfig again.

---

### 2. Core kubectl Commands

| Command | Description |
| --------- | ------------- |
| `kubectl get nodes` | List cluster nodes with status |
| `kubectl get pods -A` | List all pods across all namespaces |
| `kubectl get pods -n <ns>` | List pods in a specific namespace |
| `kubectl get services` | List services in default namespace |
| `kubectl get namespaces` | List all namespaces |
| `kubectl get ingress -A` | List all ingress rules |
| `kubectl describe node k3s` | Full node details (resources, conditions, pods) |
| `kubectl describe pod <name>` | Full pod details (events, containers, mounts) |
| `kubectl logs <pod>` | Container logs |
| `kubectl logs <pod> --all-containers` | Logs from all containers in a pod |
| `kubectl top pods -A` | Real-time CPU/RAM per pod |
| `kubectl exec -it <pod> -- bash` | Shell inside a container |
| `kubectl apply -f <file>` | Create or update resources from YAML |
| `kubectl delete -f <file>` | Delete resources defined in YAML |
| `kubectl port-forward svc/<name> <local>:<remote> -n <ns>` | Temporary port tunnel for debugging |

**Useful flags:**

- `-n <namespace>` — target a specific namespace
- `-A` — all namespaces
- `-o yaml` — output full resource definition as YAML
- `-o wide` — extra columns (node IP, etc.)
- `--watch` — live updates (Ctrl+C to stop)

---

### 3. Kubernetes Resource Types

Every resource in k3s is defined by a YAML file with this structure:

```yaml
apiVersion: <group/version>   # which API handles this resource
kind: <ResourceType>           # what type of resource
metadata:                      # name, namespace, labels
spec:                          # what the resource should do
```

#### Namespace

Logical isolation inside the cluster. Analogy: VLANs in networking.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: portfolio
```

```bash
kubectl create namespace portfolio
kubectl get namespaces
kubectl delete namespace portfolio   # deletes ALL resources inside
```

Default namespaces in k3s:

- `default` — where resources land if no namespace is specified
- `kube-system` — k3s system components (CoreDNS, Traefik, etc.)
- `kube-public`, `kube-node-lease` — internal Kubernetes use

#### Deployment

Declares desired state: "I want 1 replica of nginx running". k3s continuously reconciles actual state toward desired state (self-healing).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-test
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-test
  template:
    metadata:
      labels:
        app: nginx-test
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
```

#### Service

Gives pods a stable network address. Pods are ephemeral — their IPs change on restart. Service maintains a fixed ClusterIP and DNS name pointing to matching pods (via `selector`).

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-test
  namespace: default
spec:
  selector:
    app: nginx-test       # matches pods with this label
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP         # internal only — correct for use with Ingress
```

Service types:

- `ClusterIP` — internal cluster access only (default, recommended with Ingress)
- `NodePort` — exposes port directly on VM — avoid in production
- `LoadBalancer` — for cloud providers — not used in homelab

#### Ingress

Routes external HTTP/HTTPS traffic to Services based on hostname or path. Traefik (installed by k3s by default) reads Ingress resources and configures routing.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-test
  namespace: default
spec:
  rules:
    - host: nginx-test.damianzientek.de
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-test
                port:
                  number: 80
```

#### ConfigMap

External configuration for applications — environment variables, config files — stored in the cluster separately from the container image.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: portfolio-config
  namespace: portfolio
data:
  SITE_URL: "https://damianzientek.de"
  ENVIRONMENT: "production"
```

#### Secret

Same as ConfigMap but for sensitive data (passwords, API tokens). Values are base64-encoded.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-admin-secret
  namespace: monitoring
type: Opaque
stringData:              # stringData auto-encodes to base64
  admin-user: admin
  admin-password: "yourpassword"
```

> **Security pattern:** Never commit Secret files to Git. Add `k8s/*-secret.yml` to `.gitignore`. Create Secrets manually with `kubectl apply -f` before deploying dependent apps.

#### PersistentVolumeClaim (PVC)

Requests storage from the cluster. k3s `local-path-provisioner` automatically creates a directory on the VM when a PVC is created.

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: prometheus-data
  namespace: monitoring
spec:
  accessModes:
    - ReadWriteOnce     # one pod can write at a time
  resources:
    requests:
      storage: 5Gi
```

> **Note:** For a static Astro portfolio, PVC is not needed — static files live inside the container image.

---

### 4. Routing Architecture

```
Browser
  ↓
Cloudflare Tunnel (future — for public traffic)
  ↓
NPM (10.x.x.x) — homelab-wide reverse proxy
  ↓
Traefik (10.x.x.x:80) — k3s Ingress controller
  ↓
Service (ClusterIP) — stable internal address
  ↓
Pod — running container
```

**DNS resolution:** AdGuard Home wildcard `*.damianzientek.de → 10.x.x.x` covers everything. NPM proxy host forwards specific domains to Traefik at `10.x.x.x`.

**NPM settings for k3s services:** Force SSL ✓ | HTTP/2 ✓ | Websockets ✓ (for Grafana/n8n) | Block Common Exploits ✗

---

### 5. Helm

Helm is a package manager for Kubernetes. A **chart** is a packaged application (collection of YAML templates + default values). A **release** is a deployed instance of a chart.

Analogy: `apt install` for Debian, but for Kubernetes applications.

#### Install Helm v4

```bash
wget https://get.helm.sh/helm-v4.1.4-linux-amd64.tar.gz
tar -zxvf helm-v4.1.4-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
rm helm-v4.1.4-linux-amd64.tar.gz && rm -rf linux-amd64/
helm version
```

> **Note:** The `get-helm-3` script installs Helm v3 despite the name. For v4, download the binary directly.

#### Core commands

```bash
helm repo add <name> <url>       # add chart repository
helm repo update                  # fetch latest chart versions
helm search repo <name>           # find charts in added repos
helm install <release> <chart> -f values.yml --namespace <ns> --create-namespace
helm upgrade <release> <chart> -f values.yml --namespace <ns>
helm uninstall <release> --namespace <ns>
helm list -A                      # list all releases
```

---

### 6. Monitoring Stack (kube-prometheus-stack)

Deploys Prometheus + Grafana + node-exporter + kube-state-metrics via Helm.

**Location:** `k8s/monitoring-values.yml`

#### Prerequisites

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

#### Grafana admin secret

Create `k8s/grafana-secret.yml` (add to `.gitignore`):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-admin-secret
  namespace: monitoring
type: Opaque
stringData:
  admin-user: admin
  admin-password: "yourpassword"
```

```bash
kubectl create namespace monitoring
kubectl apply -f k8s/grafana-secret.yml
```

#### Deploy

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f k8s/monitoring-values.yml
```

#### Upgrade

```bash
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f k8s/monitoring-values.yml
```

#### Verify

```bash
kubectl get pods -n monitoring
# All pods should show Running status
# Grafana shows 3/3 (main container + 2 sidecars for dashboard/datasource provisioning)

kubectl top pods -n monitoring
```

#### Access

NPM proxy host: `grafana.damianzientek.de` → `http://10.x.x.x:80`
Login: `admin` / password from `grafana-secret.yml`

Prometheus and Alertmanager data sources are pre-configured automatically by the chart.

---

### 7. Troubleshooting

#### `kubectl` connection refused

kubeconfig still points to `127.0.0.1`:

```bash
sed -i 's/127.0.0.1/10.x.x.x/' ~/.kube/config
```

#### Pod stuck in `Pending`

Usually insufficient resources. Check:

```bash
kubectl describe pod <name> -n <namespace>
# Look for "Insufficient memory" or "Insufficient cpu" in Events
```

#### Pod stuck in `2/3` or `CrashLoopBackOff`

Check logs:

```bash
kubectl logs <pod> -n <namespace> --all-containers
```

#### Grafana `context deadline exceeded` / handler timeout

Grafana 13 unified storage requires adequate CPU. Increase limits in `monitoring-values.yml`:

```yaml
grafana:
  resources:
    limits:
      cpu: 500m      # was 200m
      memory: 512Mi  # was 256Mi
```

Then: `helm upgrade monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f k8s/monitoring-values.yml`

#### `OOMKilled` — pod killed by out-of-memory

VM ran out of memory. Check real usage:

```bash
ssh k3s "free -h"
# "available" column shows actual free memory
# Proxmox UI shows used+cache — misleading
```

#### `502 Bad Gateway` from NPM

Port binding issue or Traefik not routing. Verify Ingress exists:

```bash
kubectl get ingress -A
```

#### Grafana plugin install failures (`tls: unrecognized name`)

Cosmetic — Grafana tries to fetch optional plugins from grafana.com on startup. Not related to core functionality, safe to ignore.

---

<a name="deutsch"></a>

## 🇩🇪 Deutsch

[🇬🇧 English](#english) | [🇵🇱 Polski](#polski)

### Übersicht

Dieser Leitfaden behandelt den täglichen Betrieb des k3s-Clusters: kubectl-Einrichtung, Kubernetes-Grundkonzepte, Helm-Paketmanager und den Monitoring-Stack. k3s muss bereits installiert sein (siehe `k3s-install.md`).

**Cluster:** Single-Node k3s auf VM 410 (`10.x.x.x`, pve2, 10 GB RAM, 2 vCPU, 40 GB Disk)

---

### 1. kubectl-Einrichtung in WSL

kubectl ist das Kubernetes-CLI — es kommuniziert über das Netzwerk mit dem k3s-API-Server mittels einer kubeconfig-Datei. Es muss nicht auf der k3s-VM selbst laufen.

#### kubectl installieren

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client
```

#### kubeconfig von der k3s-VM kopieren

Die kubeconfig-Datei gehört auf der VM root — über eine temporäre Datei kopieren:

```bash
mkdir -p ~/.kube
ssh k3s "sudo cp /etc/rancher/k3s/k3s.yaml /home/damian/k3s.yaml && sudo chown damian:damian /home/damian/k3s.yaml"
scp k3s:/home/damian/k3s.yaml ~/.kube/config
ssh k3s "rm /home/damian/k3s.yaml"
```

#### Server-IP korrigieren

Die Standard-kubeconfig zeigt auf `127.0.0.1` (localhost der VM). Auf die tatsächliche VM-IP ändern:

```bash
sed -i 's/127.0.0.1/10.x.x.x/' ~/.kube/config
```

#### Überprüfung

```bash
kubectl get nodes
# Erwartet: NAME=k3s  STATUS=Ready  ROLES=control-plane
```

---

### 2. Wichtige kubectl-Befehle

| Befehl | Beschreibung |
| -------- | -------------- |
| `kubectl get nodes` | Cluster-Knoten mit Status auflisten |
| `kubectl get pods -A` | Alle Pods in allen Namespaces |
| `kubectl get pods -n <ns>` | Pods in einem bestimmten Namespace |
| `kubectl get services` | Services im Standard-Namespace |
| `kubectl get namespaces` | Alle Namespaces |
| `kubectl get ingress -A` | Alle Ingress-Regeln |
| `kubectl describe node k3s` | Vollständige Knotendetails |
| `kubectl describe pod <name>` | Vollständige Pod-Details (Events, Container) |
| `kubectl logs <pod> --all-containers` | Logs aller Container im Pod |
| `kubectl top pods -A` | Echtzeit CPU/RAM pro Pod |
| `kubectl exec -it <pod> -- bash` | Shell im Container |
| `kubectl apply -f <datei>` | Ressourcen aus YAML erstellen/aktualisieren |
| `kubectl delete -f <datei>` | Ressourcen aus YAML löschen |

---

### 3. Kubernetes-Ressourcentypen

#### Namespace

Logische Isolierung innerhalb des Clusters. Analogie: VLANs im Netzwerk.

```bash
kubectl create namespace portfolio
kubectl delete namespace portfolio   # löscht ALLE Ressourcen darin
```

#### Deployment

Deklariert den gewünschten Zustand: „Ich möchte 1 Replik von nginx laufend haben." k3s gleicht den Ist-Zustand kontinuierlich auf den Soll-Zustand ab (Self-Healing).

#### Service

Gibt Pods eine stabile Netzwerkadresse. Pods sind ephemer — ihre IPs ändern sich beim Neustart. Ein Service hat eine feste ClusterIP und einen DNS-Namen.

Service-Typen:

- `ClusterIP` — nur interner Cluster-Zugriff (Standard, empfohlen mit Ingress)
- `NodePort` — exponiert Port direkt auf der VM — in Produktion vermeiden
- `LoadBalancer` — für Cloud-Anbieter — im Homelab nicht verwendet

#### Ingress

Routet externen HTTP/HTTPS-Traffic an Services basierend auf Hostname oder Pfad. Traefik (standardmäßig von k3s installiert) liest Ingress-Ressourcen und konfiguriert das Routing.

#### ConfigMap

Externe Konfiguration für Anwendungen — Umgebungsvariablen, Konfigurationsdateien — getrennt vom Container-Image im Cluster gespeichert.

#### Secret

Wie ConfigMap, aber für sensible Daten (Passwörter, API-Token). Werte sind base64-kodiert.

> **Sicherheitshinweis:** Secret-Dateien niemals in Git committen. `k8s/*-secret.yml` zur `.gitignore` hinzufügen.

#### PersistentVolumeClaim (PVC)

Fordert Speicher vom Cluster an. Der `local-path-provisioner` von k3s erstellt automatisch ein Verzeichnis auf der VM.

---

### 4. Routing-Architektur

```
Browser
  ↓
Cloudflare Tunnel (zukünftig — für öffentlichen Traffic)
  ↓
NPM (10.x.x.x) — homelab-weiter Reverse Proxy
  ↓
Traefik (10.x.x.x:80) — k3s Ingress Controller
  ↓
Service (ClusterIP) — stabile interne Adresse
  ↓
Pod — laufender Container
```

**DNS-Auflösung:** AdGuard Home Wildcard `*.damianzientek.de → 10.x.x.x`. NPM-Proxy-Host leitet spezifische Domains an Traefik weiter.

**NPM-Einstellungen für k3s-Dienste:** Force SSL ✓ | HTTP/2 ✓ | Websockets ✓ | Block Common Exploits ✗

---

### 5. Helm

Helm ist ein Paketmanager für Kubernetes. Ein **Chart** ist eine gepackte Anwendung. Ein **Release** ist eine bereitgestellte Chart-Instanz.

Analogie: `apt install` für Debian, aber für Kubernetes-Anwendungen.

#### Helm v4 installieren

```bash
wget https://get.helm.sh/helm-v4.1.4-linux-amd64.tar.gz
tar -zxvf helm-v4.1.4-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
rm helm-v4.1.4-linux-amd64.tar.gz && rm -rf linux-amd64/
helm version
```

> **Hinweis:** Das Skript `get-helm-3` installiert trotz des Namens Helm v3. Für v4 die Binärdatei direkt herunterladen.

#### Wichtige Befehle

```bash
helm repo add <name> <url>
helm repo update
helm install <release> <chart> -f values.yml --namespace <ns> --create-namespace
helm upgrade <release> <chart> -f values.yml --namespace <ns>
helm uninstall <release> --namespace <ns>
helm list -A
```

---

### 6. Monitoring-Stack (kube-prometheus-stack)

Installiert Prometheus + Grafana + node-exporter + kube-state-metrics über Helm.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
kubectl apply -f k8s/grafana-secret.yml
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f k8s/monitoring-values.yml
```

**Zugriff:** NPM-Proxy-Host `grafana.damianzientek.de` → `http://10.x.x.x:80`

---

### 7. Fehlerbehebung

#### Grafana `context deadline exceeded`

CPU-Limit zu niedrig für Grafana 13. In `monitoring-values.yml` erhöhen:

```yaml
grafana:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
```

Dann: `helm upgrade monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f k8s/monitoring-values.yml`

#### `OOMKilled` — Pod durch Speichermangel beendet

Tatsächlichen Speicher prüfen:

```bash
ssh k3s "free -h"
# Proxmox-UI zeigt used+cache — irreführend
```

#### Pod in `Pending` hängt

```bash
kubectl describe pod <name> -n <namespace>
# Events auf "Insufficient memory" oder "Insufficient cpu" prüfen
```

---

<a name="polski"></a>

## 🇵🇱 Polski

[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch)

### Przegląd

Ten przewodnik obejmuje codzienną obsługę klastra k3s: konfigurację kubectl, podstawowe koncepty Kubernetes, menedżer pakietów Helm i stack monitoringu. k3s musi być już zainstalowany (patrz `k3s-install.md`).

**Klaster:** Single-node k3s na VM 410 (`10.x.x.x`, pve2, 10 GB RAM, 2 vCPU, dysk 40 GB)

---

### 1. Konfiguracja kubectl w WSL

kubectl to narzędzie CLI Kubernetes — komunikuje się z API serverem k3s przez sieć używając pliku kubeconfig. Nie musi działać na samej VM k3s.

#### Instalacja kubectl

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
kubectl version --client
```

#### Kopiowanie kubeconfig z VM k3s

Plik kubeconfig należy do roota na VM — skopiuj przez plik tymczasowy:

```bash
mkdir -p ~/.kube
ssh k3s "sudo cp /etc/rancher/k3s/k3s.yaml /home/damian/k3s.yaml && sudo chown damian:damian /home/damian/k3s.yaml"
scp k3s:/home/damian/k3s.yaml ~/.kube/config
ssh k3s "rm /home/damian/k3s.yaml"
```

#### Poprawienie IP serwera

Domyślny kubeconfig wskazuje na `127.0.0.1` (localhost VM). Zmień na rzeczywisty IP VM:

```bash
sed -i 's/127.0.0.1/10.x.x.x/' ~/.kube/config
```

#### Weryfikacja

```bash
kubectl get nodes
# Oczekiwane: NAME=k3s  STATUS=Ready  ROLES=control-plane
```

> **Uwaga:** Po destroy+recreate VM z tym samym IP uruchom `ssh-keygen -R 10.x.x.x` i `ssh-keyscan 10.x.x.x >> ~/.ssh/known_hosts` przed ponownym kopiowaniem kubeconfig.

---

### 2. Podstawowe komendy kubectl

| Komenda | Opis |
| --------- | ------ |
| `kubectl get nodes` | Lista węzłów klastra ze statusem |
| `kubectl get pods -A` | Lista wszystkich podów we wszystkich namespace'ach |
| `kubectl get pods -n <ns>` | Pody w konkretnym namespace |
| `kubectl get services` | Services w domyślnym namespace |
| `kubectl get namespaces` | Lista wszystkich namespace'ów |
| `kubectl get ingress -A` | Wszystkie reguły Ingress |
| `kubectl describe node k3s` | Pełne szczegóły węzła (zasoby, warunki, pody) |
| `kubectl describe pod <name>` | Pełne szczegóły poda (eventy, kontenery, mounty) |
| `kubectl logs <pod> --all-containers` | Logi wszystkich kontenerów w podzie |
| `kubectl top pods -A` | Rzeczywiste zużycie CPU/RAM per pod |
| `kubectl exec -it <pod> -- bash` | Shell wewnątrz kontenera |
| `kubectl apply -f <plik>` | Stwórz lub zaktualizuj zasoby z YAML |
| `kubectl delete -f <plik>` | Usuń zasoby zdefiniowane w YAML |
| `kubectl port-forward svc/<name> <local>:<remote> -n <ns>` | Tymczasowy tunel portów do debugowania |

**Przydatne flagi:**

- `-n <namespace>` — wskaż konkretny namespace
- `-A` — wszystkie namespace'y
- `-o yaml` — pełna definicja zasobu jako YAML
- `--watch` — aktualizacje na żywo (Ctrl+C żeby zatrzymać)

---

### 3. Typy zasobów Kubernetes

Każdy zasób w k3s jest definiowany przez plik YAML z tą strukturą:

```yaml
apiVersion: <group/version>   # które API obsługuje ten zasób
kind: <TypZasobu>              # jaki typ zasobu
metadata:                      # nazwa, namespace, etykiety
spec:                          # co zasób ma robić
```

#### Namespace

Logiczna izolacja wewnątrz klastra. Analogia: VLANy w sieci.

```bash
kubectl create namespace portfolio
kubectl delete namespace portfolio   # usuwa WSZYSTKIE zasoby w środku
```

Domyślne namespace'y w k3s:

- `default` — tu trafiają zasoby gdy nie podasz namespace'u
- `kube-system` — komponenty systemowe k3s (CoreDNS, Traefik itd.)
- `kube-public`, `kube-node-lease` — wewnętrzne użycie Kubernetes

#### Deployment

Deklaruje pożądany stan: „Chcę żeby działała 1 replika nginx". k3s ciągle uzgadnia stan rzeczywisty z pożądanym (self-healing).

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-test
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-test
  template:
    metadata:
      labels:
        app: nginx-test
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
```

#### Service

Daje podom stały adres sieciowy. Pody są efemeryczne — ich IP zmienia się przy restarcie. Service ma stały ClusterIP i nazwę DNS wskazującą na pasujące pody (przez `selector`).

```yaml
apiVersion: v1
kind: Service
metadata:
  name: nginx-test
  namespace: default
spec:
  selector:
    app: nginx-test       # pasuje do podów z tą etykietą
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP         # tylko wewnętrzny — poprawnie z Ingressem
```

Typy Service:

- `ClusterIP` — tylko dostęp wewnątrz klastra (domyślny, zalecany z Ingressem)
- `NodePort` — wystawia port bezpośrednio na VM — unikać w produkcji
- `LoadBalancer` — dla chmury — nie używamy w homelabie

#### Ingress

Routuje zewnętrzny ruch HTTP/HTTPS do Serwisów na podstawie nazwy hosta lub ścieżki. Traefik (domyślnie instalowany przez k3s) czyta zasoby Ingress i konfiguruje routing.

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-test
  namespace: default
spec:
  rules:
    - host: nginx-test.damianzientek.de
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-test
                port:
                  number: 80
```

#### ConfigMap

Zewnętrzna konfiguracja dla aplikacji — zmienne środowiskowe, pliki konfiguracyjne — przechowywana w klastrze osobno od obrazu kontenera.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: portfolio-config
  namespace: portfolio
data:
  SITE_URL: "https://damianzientek.de"
  ENVIRONMENT: "production"
```

#### Secret

To samo co ConfigMap, ale dla wrażliwych danych (hasła, tokeny API). Wartości są zakodowane base64.

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-admin-secret
  namespace: monitoring
type: Opaque
stringData:              # stringData automatycznie koduje do base64
  admin-user: admin
  admin-password: "twojehaslo"
```

> **Wzorzec bezpieczeństwa:** Nigdy nie commituj plików Secret do Git. Dodaj `k8s/*-secret.yml` do `.gitignore`. Twórz Secrety ręcznie przez `kubectl apply -f` przed deployowaniem zależnych aplikacji.

#### PersistentVolumeClaim (PVC)

Żąda przestrzeni dyskowej od klastra. `local-path-provisioner` k3s automatycznie tworzy katalog na VM gdy PVC zostanie stworzony.

> **Uwaga:** Dla statycznego portfolio Astro PVC nie jest potrzebny — pliki statyczne są wewnątrz obrazu kontenera.

---

### 4. Architektura routingu

```
Przeglądarka
  ↓
Cloudflare Tunnel (docelowo — dla ruchu publicznego)
  ↓
NPM (10.x.x.x) — reverse proxy dla całego homelabu
  ↓
Traefik (10.x.x.x:80) — Ingress controller k3s
  ↓
Service (ClusterIP) — stały adres wewnętrzny
  ↓
Pod — działający kontener
```

**Rozwiązywanie DNS:** Wildcard AdGuard Home `*.damianzientek.de → 10.x.x.x` pokrywa wszystko. NPM proxy host przekierowuje konkretne domeny do Traefika na `10.x.x.x`.

**Ustawienia NPM dla usług k3s:** Force SSL ✓ | HTTP/2 ✓ | Websockets ✓ (Grafana, n8n) | Block Common Exploits ✗

---

### 5. Helm

Helm to menedżer pakietów dla Kubernetes. **Chart** to spakowana aplikacja (szablony YAML + domyślne wartości). **Release** to wdrożona instancja charta.

Analogia: `apt install` dla Debiana, ale dla aplikacji Kubernetes.

#### Instalacja Helm v4

```bash
wget https://get.helm.sh/helm-v4.1.4-linux-amd64.tar.gz
tar -zxvf helm-v4.1.4-linux-amd64.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/helm
rm helm-v4.1.4-linux-amd64.tar.gz && rm -rf linux-amd64/
helm version
```

> **Uwaga:** Skrypt `get-helm-3` mimo nazwy instaluje Helm v3. Dla v4 pobierz binarny plik bezpośrednio.

#### Podstawowe komendy

```bash
helm repo add <nazwa> <url>       # dodaj repozytorium chartów
helm repo update                   # pobierz najnowsze wersje chartów
helm search repo <nazwa>           # znajdź charty w dodanych repo
helm install <release> <chart> -f values.yml --namespace <ns> --create-namespace
helm upgrade <release> <chart> -f values.yml --namespace <ns>
helm uninstall <release> --namespace <ns>
helm list -A                       # lista wszystkich release'ów
```

---

### 6. Stack monitoringu (kube-prometheus-stack)

Instaluje Prometheus + Grafana + node-exporter + kube-state-metrics przez Helm.

**Lokalizacja:** `k8s/monitoring-values.yml`

#### Wymagania wstępne

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
```

#### Secret dla Grafany

Stwórz `k8s/grafana-secret.yml` (dodaj do `.gitignore`):

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-admin-secret
  namespace: monitoring
type: Opaque
stringData:
  admin-user: admin
  admin-password: "twojehaslo"
```

```bash
kubectl create namespace monitoring
kubectl apply -f k8s/grafana-secret.yml
```

#### Deploy

```bash
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  -f k8s/monitoring-values.yml
```

#### Upgrade

```bash
helm upgrade monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  -f k8s/monitoring-values.yml
```

#### Weryfikacja

```bash
kubectl get pods -n monitoring
# Wszystkie pody powinny mieć status Running
# Grafana pokazuje 3/3 (główny kontener + 2 sidecary do dashboardów/datasource'ów)

kubectl top pods -n monitoring
```

#### Dostęp

NPM proxy host: `grafana.damianzientek.de` → `http://10.x.x.x:80`
Login: `admin` / hasło z `grafana-secret.yml`

Prometheus i Alertmanager są automatycznie skonfigurowane jako data sources przez chart.

---

### 7. Rozwiązywanie problemów

#### kubectl — connection refused

kubeconfig nadal wskazuje na `127.0.0.1`:

```bash
sed -i 's/127.0.0.1/10.x.x.x/' ~/.kube/config
```

#### Pod utknął w `Pending`

Zwykle niewystarczające zasoby. Sprawdź:

```bash
kubectl describe pod <name> -n <namespace>
# Szukaj "Insufficient memory" lub "Insufficient cpu" w sekcji Events
```

#### Pod utknął w `2/3` lub `CrashLoopBackOff`

Sprawdź logi:

```bash
kubectl logs <pod> -n <namespace> --all-containers
```

#### Grafana `context deadline exceeded` / handler timeout

Grafana 13 unified storage wymaga odpowiedniego CPU. Zwiększ limity w `monitoring-values.yml`:

```yaml
grafana:
  resources:
    limits:
      cpu: 500m      # było 200m
      memory: 512Mi  # było 256Mi
```

Następnie: `helm upgrade monitoring prometheus-community/kube-prometheus-stack --namespace monitoring -f k8s/monitoring-values.yml`

#### `OOMKilled` — pod zabity przez brak pamięci

VM skończyła pamięć. Sprawdź rzeczywiste zużycie:

```bash
ssh k3s "free -h"
# Kolumna "available" pokazuje faktycznie wolną pamięć
# UI Proxmoxa pokazuje used+cache — mylące
```

Proxmox pokazuje `used + buff/cache` jako zajęte. Linux agresywnie cachuje pamięć — to normalne zachowanie, nie problem.

#### `502 Bad Gateway` z NPM

Sprawdź czy Ingress istnieje:

```bash
kubectl get ingress -A
```

#### Błędy instalacji pluginów Grafany (`tls: unrecognized name`)

Kosmetyczne — Grafana próbuje pobrać opcjonalne pluginy z grafana.com przy starcie. Nie wpływa na podstawową funkcjonalność, można zignorować.

---

### FAQ

**P: Jaka jest różnica między Deploymentem a Podem?**
O: Pod to najmniejsza jednostka w k8s — jeden lub więcej kontenerów działających razem. Deployment to wyższa warstwa abstrakacji która zarządza podami: pilnuje żeby zawsze działała odpowiednia liczba replik, obsługuje rolling updates i rollbacki. Bezpośrednio nie tworzy się podów — tworzy się Deploymenty.

**P: Dlaczego `docker ps` nie pokazuje kontenerów k3s?**
O: k3s używa `containerd` jako runtime, nie Dockera. Użyj `sudo crictl ps` na VM lub `kubectl get pods -A` z WSL.

**P: Czy mogę mieć dwie aplikacje na tej samej domenie ale różnych ścieżkach?**
O: Tak — Ingress obsługuje routing po ścieżce. `damianzientek.de/blog` i `damianzientek.de/api` mogą wskazywać na różne Service'y.

**P: Co się stanie z danymi gdy pod zostanie zrestartowany?**
O: Dane zapisane wewnątrz kontenera znikają. Dane w PVC (PersistentVolumeClaim) przeżywają restart. Dla statycznego portfolio (Astro) — nie ma co persystować, pliki są w obrazie.

**P: Dlaczego Proxmox pokazuje 100% RAM a `free -h` pokazuje dużo wolnego?**
O: Proxmox wyświetla `used + buff/cache`. Linux agresywnie używa wolnej pamięci jako cache (żeby nie marnować). Cache jest natychmiast oddawany aplikacjom gdy go potrzebują. Rzeczywiste zużycie to kolumna `available` w `free -h`.
