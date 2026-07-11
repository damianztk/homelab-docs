# Ansible — Homelab IaC Basics | Grundlagen | Podstawy

---

## Navigation | Navigation | Nawigacja

[🇬🇧 English](#en) | [🇩🇪 Deutsch](#de) | [🇵🇱 Polski](#pl)

---

<a name="en"></a>
## 🇬🇧 English

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### What is Ansible?

Ansible is a configuration management tool. It connects to machines via SSH and configures them — installs packages, starts services, deploys applications. Unlike Terraform (which creates infrastructure), Ansible configures machines that already exist.

Key principle: **idempotency**. Run a playbook 10 times — the result is always the same. If something is already configured correctly, Ansible does nothing (`ok`). If it needs to change, it changes (`changed`). This is safe to re-run at any time.

### Project Structure

```
~/homelab-iac/
├── ansible.cfg                     # Ansible configuration (roles_path)
└── ansible/
    ├── inventory/
    │   └── hosts.yml               # all hosts and groups
    ├── playbooks/
    │   ├── configure-vm.yml        # combined playbook: setup-base + docker roles
    │   ├── setup-base.yml          # standalone: base system config
    │   ├── install-docker.yml      # standalone: Docker installation
    │   ├── install-k3s.yml         # k3s installation
    │   ├── deploy-utility-apps.yml # deploy utility-apps stack
    │   ├── deploy-frigate.yml      # deploy Frigate stack
    │   ├── deploy-wger.yml         # deploy wger stack
    │   └── install-pbs.yml         # PBS installation
    ├── roles/
    │   ├── setup-base/
    │   │   ├── tasks/main.yml
    │   │   └── defaults/main.yml
    │   └── docker/
    │       ├── tasks/main.yml
    │       └── defaults/main.yml
    ├── files/
    │   ├── utility-apps-compose.yml.j2
    │   ├── wger-compose.yml.j2
    │   ├── frigate-config.yml.j2
    │   └── nginx-wger.conf
    └── secrets.yml                 # gitignored! Ansible Vault or plain vars
```

### ansible.cfg

Located in `~/homelab-iac/` (same directory you run commands from):

```ini
[defaults]
roles_path = ansible/roles
```

This tells Ansible where to find roles relative to the project root.

### Inventory — hosts.yml

```yaml
all:
  children:
    proxmox_vms:
      hosts:
        ansible-test:
          ansible_host: 10.100.20.40
          ansible_user: damian
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
        k3s:
          ansible_host: 10.100.20.41
          ansible_user: damian
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
    proxmox_lxc:
      hosts:
        utility-apps:
          ansible_host: 10.100.20.30
          ansible_user: root
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
        frigate:
          ansible_host: 10.100.20.32
          ansible_user: root
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
        pbs:
          ansible_host: 10.100.20.90
          ansible_user: root
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

VMs use `ansible_user: damian` (Cloud-Init creates this user). LXC containers use `ansible_user: root` (direct root access).

### Running Playbooks

```bash
# Always run from ~/homelab-iac/
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml

# Dry run — check without making changes
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml --check

# Limit to specific host
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml -l k3s

# Limit to group
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml -l proxmox_lxc

# Quick connectivity test
ansible k3s -i ansible/inventory/hosts.yml -m ping
```

### Playbook Structure

```yaml
---
- name: Descriptive name shown during execution
  hosts: proxmox_vms        # host, group, or 'all'
  become: true              # sudo — required for system changes

  vars:
    my_variable: value      # local variables

  tasks:
    - name: Task description
      ansible.builtin.apt:
        name: curl
        state: present
```

### Common Modules

**apt** — package management:
```yaml
- name: Install packages
  ansible.builtin.apt:
    name:
      - curl
      - git
    state: present
    update_cache: true
```

**file** — files and directories:
```yaml
- name: Create directory
  ansible.builtin.file:
    path: /opt/mydir
    state: directory
    mode: "0755"
```

**get_url** — download files:
```yaml
- name: Download file
  ansible.builtin.get_url:
    url: https://example.com/file.sh
    dest: /tmp/file.sh
    mode: "0755"
```

**command** — run commands:
```yaml
- name: Run command
  ansible.builtin.command:
    cmd: /tmp/installer.sh
    creates: /usr/local/bin/installed-binary   # skip if this file exists (idempotency)
  register: result
  changed_when: false   # don't count as a change (for read-only commands)
```

**template** — Jinja2 templates:
```yaml
- name: Deploy config from template
  ansible.builtin.template:
    src: files/myconfig.yml.j2
    dest: /opt/docker-data/config.yml
```

**lineinfile** — manage lines in files:
```yaml
- name: Write to file
  ansible.builtin.lineinfile:
    path: /opt/test/hello.txt
    line: "Hello World"
    create: true    # create file if it doesn't exist
```

**systemd** — service management:
```yaml
- name: Enable and start service
  ansible.builtin.systemd:
    name: docker
    enabled: true
    state: started
```

**user** — user management:
```yaml
- name: Add user to group
  ansible.builtin.user:
    name: damian
    groups: docker
    append: true    # CRITICAL: add to existing groups, don't replace
```

**deb822_repository** — APT repositories (Debian 13+):
```yaml
- name: Add Docker APT repository
  ansible.builtin.deb822_repository:
    name: docker
    types: deb
    uris: https://download.docker.com/linux/debian
    suites: "{{ ansible_facts['distribution_release'] }}"
    components: stable
    architectures: "{{ dpkg_arch.stdout }}"
    signed_by: /etc/apt/keyrings/docker.asc
    state: present
```

**community.docker.docker_container** — manage containers:
```yaml
- name: Run container
  community.docker.docker_container:
    name: nginx-test
    image: nginx:alpine
    state: started
    restart_policy: unless-stopped
    ports:
      - "8080:80"
```

**community.docker.docker_compose_v2** — manage Compose stacks:
```yaml
- name: Deploy stack
  community.docker.docker_compose_v2:
    project_src: /opt/docker-data
    state: present
```

### Roles

A role is a reusable set of tasks. Instead of copying the same tasks into multiple playbooks, you define them once in a role and reference them by name.

**Role structure:**
```
ansible/roles/
└── docker/
    ├── tasks/
    │   └── main.yml      # the tasks themselves (no playbook header)
    └── defaults/
        └── main.yml      # default variable values
```

**tasks/main.yml** — just the task list, no `- name: Play` header:
```yaml
---
- name: Install Docker packages
  ansible.builtin.apt:
    name:
      - docker-ce
      - docker-ce-cli
    state: present
```

**defaults/main.yml** — default variables:
```yaml
---
docker_user: damian
```

**Using roles in a playbook:**
```yaml
---
- name: Configure VM with Docker
  hosts: proxmox_vms
  become: true

  roles:
    - setup-base
    - docker
```

Output shows role name prefix: `setup-base : Update apt cache`, `docker : Install Docker packages`

### Variables in register

```yaml
- name: Get architecture
  ansible.builtin.command: dpkg --print-architecture
  register: dpkg_arch         # save output to variable
  changed_when: false

- name: Use it later
  ansible.builtin.debug:
    msg: "Architecture: {{ dpkg_arch.stdout }}"
```

### loop — iterate over a list

```yaml
vars:
  containers:
    - name: nginx
      image: nginx:alpine
      port: 8080
    - name: vaultwarden
      image: vaultwarden/server:latest
      port: 8081

tasks:
  - name: Run containers
    community.docker.docker_container:
      name: "{{ item.name }}"
      image: "{{ item.image }}"
      ports: ["{{ item.port }}:80"]
    loop: "{{ containers }}"
```

### Installing Collections

Some modules require external collections:
```bash
ansible-galaxy collection install community.docker
ansible-galaxy collection install community.general
```

Check installed collections:
```bash
ansible-galaxy collection list | grep community
```

### Known Issues and Solutions

**Issue:** `apt_repository` fails on Debian 13
**Cause:** `apt-key` was removed in Debian 13. The `apt_repository` module uses it internally.
**Solution:** Use `deb822_repository` module instead. Also use `ansible_facts['distribution_release']` instead of `ansible_distribution_release`.

**Issue:** `docker_compose_v2` reports errors in `--check` mode
**Cause:** Compose modules can't fully simulate without actually connecting to Docker daemon.
**Solution:** Normal behavior — ignore `--check` errors for Compose tasks, run actual apply to verify.

**Issue:** Role not found — `the role 'setup-base' was not found`
**Cause:** `ansible.cfg` is missing or in wrong location, or `roles_path` is incorrect.
**Solution:** Ensure `ansible.cfg` is in `~/homelab-iac/` with `roles_path = ansible/roles`. Run commands from that directory.

**Issue:** `community.docker` module not found
**Cause:** Collection not installed.
**Solution:** `ansible-galaxy collection install community.docker`

**Issue:** `append: true` missing in user module
**Cause:** Without `append: true`, Ansible replaces all user groups instead of adding to them.
**Solution:** Always use `append: true` when adding a user to a group.

### FAQ

**Q: What's the difference between `ok` and `changed` in output?**
A: `ok` = task ran, nothing needed to change (already correct state). `changed` = task made a modification. `failed` = error. This is idempotency in action.

**Q: Can I use `hosts: all` and then limit with `-l`?**
A: Yes. `hosts: all` in the playbook, `-l k3s` on command line. The `-l` flag further restricts which hosts run.

**Q: What's the difference between a playbook and a role?**
A: A playbook is the full recipe (hosts, become, tasks). A role is a reusable module of tasks. Think of roles as functions in programming — write once, call from multiple playbooks.

**Q: Should I use `shell` or `command` module?**
A: `command` when possible — it doesn't go through a shell, safer. Use `shell` only when you need pipes (`|`), redirects (`>`), or shell variables. Even then, prefer `get_url` + `command` over `curl | sh`.

**Q: How do I pass secrets to Ansible?**
A: Store in `ansible/secrets.yml` (gitignored). Reference in playbook with `vars_files: [secrets.yml]`. Use `{{ variable_name }}` in tasks and templates.

---

<a name="de"></a>
## 🇩🇪 Deutsch

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Was ist Ansible?

Ansible ist ein Konfigurationsmanagement-Tool. Es verbindet sich über SSH mit Maschinen und konfiguriert sie — installiert Pakete, startet Dienste, deployt Anwendungen. Im Gegensatz zu Terraform (das Infrastruktur erstellt) konfiguriert Ansible Maschinen, die bereits existieren.

Kernprinzip: **Idempotenz**. Ein Playbook 10-mal ausführen — das Ergebnis ist immer gleich. Wenn etwas bereits korrekt konfiguriert ist, ändert Ansible nichts (`ok`). Wenn eine Änderung nötig ist, wird sie vorgenommen (`changed`).

### Grundlegender Workflow

```bash
# Immer aus ~/homelab-iac/ ausführen
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml

# Trockenlauf — prüfen ohne Änderungen vorzunehmen
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml --check

# Auf bestimmten Host beschränken
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml -l k3s
```

### Bekannte Probleme und Lösungen

**Problem:** `apt_repository` schlägt auf Debian 13 fehl
**Ursache:** `apt-key` wurde in Debian 13 entfernt
**Lösung:** Modul `deb822_repository` verwenden. `ansible_facts['distribution_release']` statt `ansible_distribution_release` nutzen.

**Problem:** Rolle nicht gefunden — `the role 'setup-base' was not found`
**Ursache:** `ansible.cfg` fehlt oder ist am falschen Ort, oder `roles_path` ist falsch
**Lösung:** `ansible.cfg` muss in `~/homelab-iac/` liegen mit `roles_path = ansible/roles`

**Problem:** `append: true` fehlt im user-Modul
**Ursache:** Ohne `append: true` ersetzt Ansible alle Benutzergruppen anstatt hinzuzufügen
**Lösung:** Immer `append: true` verwenden, wenn ein Benutzer einer Gruppe hinzugefügt wird

### FAQ

**F: Was ist der Unterschied zwischen `ok` und `changed` in der Ausgabe?**
A: `ok` = Task lief, nichts musste geändert werden. `changed` = Task hat eine Änderung vorgenommen. Das ist Idempotenz in Aktion.

**F: Was ist der Unterschied zwischen einem Playbook und einer Rolle?**
A: Ein Playbook ist das vollständige Rezept (Hosts, become, Tasks). Eine Rolle ist ein wiederverwendbares Modul aus Tasks — wie eine Funktion in der Programmierung.

---

<a name="pl"></a>
## 🇵🇱 Polski

> [English](#en) | [Deutsch](#de) | [Polski](#pl)

### Czym jest Ansible?

Ansible to narzędzie do zarządzania konfiguracją. Łączy się z maszynami przez SSH i konfiguruje je — instaluje pakiety, uruchamia serwisy, deployuje aplikacje. W odróżnieniu od Terraform (który tworzy infrastrukturę), Ansible konfiguruje maszyny które już istnieją.

Kluczowa zasada: **idempotencja**. Uruchom playbook 10 razy — wynik zawsze taki sam. Jeśli coś jest już poprawnie skonfigurowane, Ansible nic nie robi (`ok`). Jeśli trzeba coś zmienić — zmienia (`changed`). Bezpieczne do uruchamiania w dowolnym momencie.

### Podstawowy workflow

```bash
# Zawsze z katalogu ~/homelab-iac/
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml

# Dry run — sprawdzenie bez wprowadzania zmian
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml --check

# Ograniczenie do konkretnego hosta
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml -l k3s

# Ograniczenie do grupy
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/<playbook>.yml -l proxmox_lxc

# Test połączenia
ansible k3s -i ansible/inventory/hosts.yml -m ping
```

### Grupy hostów w playbooku

```yaml
hosts: proxmox_vms          # tylko VMs
hosts: proxmox_lxc          # tylko LXC
hosts: proxmox_vms,proxmox_lxc  # obie grupy
hosts: all                  # wszystko z inventory
hosts: all:!frigate         # wszyscy oprócz frigate
```

Możesz dalej zawęzić przez `-l` przy wywołaniu.

### Moduły — ważne szczegóły

**deb822_repository** (zamiast apt_repository na Debian 13):
```yaml
- name: Dodaj repozytorium Docker
  ansible.builtin.deb822_repository:
    name: docker
    types: deb
    uris: https://download.docker.com/linux/debian
    suites: "{{ ansible_facts['distribution_release'] }}"
    components: stable
    architectures: "{{ dpkg_arch.stdout }}"
    signed_by: /etc/apt/keyrings/docker.asc
    state: present
```

**command z creates** (idempotencja dla shell):
```yaml
- name: Uruchom instalator
  ansible.builtin.command:
    cmd: /tmp/installer.sh
    creates: /usr/local/bin/zainstalowany-binarny   # pomiń jeśli plik istnieje
```

**user z append** (KRYTYCZNE):
```yaml
- name: Dodaj usera do grupy docker
  ansible.builtin.user:
    name: damian
    groups: docker
    append: true    # BEZ TEGO — zastąpi WSZYSTKIE grupy usera
```

### Role

Rola to wielokrotnie używalny zestaw tasków. Zamiast kopiować te same taski do wielu playbooków, definiujesz je raz w roli i wywołujesz po nazwie.

Wyobraź sobie rolę jako **funkcję w programowaniu** — piszesz raz, wywołujesz gdzie potrzebujesz.

**Struktura roli:**
```
ansible/roles/
└── docker/
    ├── tasks/
    │   └── main.yml      # same taski, bez nagłówka playbooka
    └── defaults/
        └── main.yml      # domyślne wartości zmiennych
```

**Użycie w playbooku:**
```yaml
---
- name: Skonfiguruj VM z Dockerem
  hosts: proxmox_vms
  become: true

  roles:
    - setup-base    # wykonuje tasks/main.yml z roli setup-base
    - docker        # wykonuje tasks/main.yml z roli docker
```

W outputcie widać prefiks roli: `setup-base : Update apt cache`, `docker : Install Docker packages`

### ansible.cfg

Plik w `~/homelab-iac/` (tam skąd uruchamiasz komendy):
```ini
[defaults]
roles_path = ansible/roles
```

Ansible szuka `ansible.cfg` w katalogu z którego uruchamiasz komendę. Plik w `ansible/` albo `ansible/playbooks/` nie zadziała gdy wywołujesz z `~/homelab-iac/`.

### Znane problemy i rozwiązania

**Problem:** `apt_repository` wywala błąd na Debian 13
**Przyczyna:** `apt-key` został usunięty w Debianie 13. Moduł `apt_repository` używa go wewnętrznie.
**Rozwiązanie:** Używaj modułu `deb822_repository`. Używaj też `ansible_facts['distribution_release']` zamiast `ansible_distribution_release`.

**Problem:** Rola nie znaleziona — `the role 'setup-base' was not found`
**Przyczyna:** `ansible.cfg` nie istnieje lub jest w złym miejscu, albo `roles_path` jest niepoprawny.
**Rozwiązanie:** Upewnij się że `ansible.cfg` jest w `~/homelab-iac/` z `roles_path = ansible/roles`. Uruchamiaj komendy z tego katalogu.

**Problem:** Moduł `community.docker` nie znaleziony
**Przyczyna:** Kolekcja nie jest zainstalowana.
**Rozwiązanie:** `ansible-galaxy collection install community.docker`

**Problem:** `docker_compose_v2` zgłasza błędy w trybie `--check`
**Przyczyna:** Moduły Compose nie mogą w pełni symulować bez połączenia z demonem Docker.
**Rozwiązanie:** Normalne zachowanie — ignoruj błędy `--check` dla tasków Compose, uruchom właściwy apply żeby zweryfikować.

### FAQ

**P: Jaka jest różnica między `ok` a `changed` w outputcie?**
O: `ok` = task się wykonał, nic nie trzeba było zmieniać (stan już poprawny). `changed` = task wprowadził zmianę. `failed` = błąd. To jest idempotencja w akcji.

**P: Co jest różnicą między playbookiem a rolą?**
O: Playbook to pełny przepis (hosty, become, taski). Rola to wielokrotnie używalny moduł tasków. Rola to jak funkcja w programowaniu — piszesz raz, wywołujesz z wielu playbooków.

**P: Kiedy używać `shell` a kiedy `command`?**
O: `command` gdy tylko można — bezpieczniejsze, nie przechodzi przez shell. `shell` tylko gdy potrzebujesz pipe (`|`), redirect (`>`), lub zmiennych shell. Nawet wtedy preferuj `get_url` + `command` zamiast `curl | sh`.

**P: Jak przekazywać sekrety do Ansible?**
O: Przechowuj w `ansible/secrets.yml` (gitignored). Referencja w playbooku przez `vars_files: [secrets.yml]`. Używaj `{{ nazwa_zmiennej }}` w taskach i szablonach.

**P: Czy `--check` zawsze jest wiarygodny?**
O: Nie zawsze. Moduły `shell`/`command` z `creates` i `docker_compose_v2` mogą zgłaszać fałszywe błędy w trybie --check, bo nie mogą w pełni symulować. Traktuj `--check` jako wstępną weryfikację składni, nie gwarancję działania.
