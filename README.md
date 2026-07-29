<!-- markdownlint-disable MD033 -->
<div align="center">

# Homelab-docs

![Proxmox](https://img.shields.io/badge/Proxmox-VE_9-E57000?style=flat-square&logo=proxmox&logoColor=white) ![Fortigate](https://img.shields.io/badge/Fortinet-Fortigate_60E-EE3124?style=flat-square&logo=fortinet&logoColor=white) ![Cloudflare](https://img.shields.io/badge/Cloudflare-Tunnel-F38020?style=flat-square&logo=cloudflare&logoColor=white)

![k3s](https://img.shields.io/badge/k3s-Kubernetes-FFC61C?style=flat-square&logo=k3s&logoColor=black) ![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?style=flat-square&logo=docker&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=flat-square&logo=terraform&logoColor=white) ![Ansible](https://img.shields.io/badge/Ansible-Automation-EE0000?style=flat-square&logo=ansible&logoColor=white) ![n8n](https://img.shields.io/badge/n8n-Automation-EA4B71?style=flat-square&logo=n8n&logoColor=white)

![Gitea](https://img.shields.io/badge/Gitea-Git_Server-609926?style=flat-square&logo=gitea&logoColor=white) ![AdGuard](https://img.shields.io/badge/AdGuard-DNS-68BC71?style=flat-square&logo=adguard&logoColor=white)

🇬🇧 Personal knowledge base documenting my homelab infrastructure —
configurations, guides, incident reports and troubleshooting notes.

🇩🇪 Persönliche Wissensdatenbank zur Dokumentation meiner
Homelab-Infrastruktur — Konfigurationen, Anleitungen, Incident-Berichte
und Notizen.

🇵🇱 Osobista baza wiedzy dokumentująca moją infrastrukturę homelab —
konfiguracje, instrukcje, raporty z incydentów i notatki diagnostyczne.
</div>
<!-- markdownlint-enable MD033 -->

---

## Structure

```text
homelab-docs/
├── cheat-sheets/            # Quick reference notes (Polish)
├── ci-cd/                   # Gitea Actions runner, build pipeline, private
│                            #   registry, multi-stage Docker builds
├── dev-environment/         # Workstation & tooling: WSL/VS Code, Node via nvm,
│                            #   AI pair programming (Aider)
├── infrastructure/
│   ├── backup/              # Backup strategy: PBS + host config backup scripts
│   ├── dell-wyse-3040/      # Thin-client specific tuning and procedures
│   ├── iac/                 # Terraform & Ansible: basics, VM/LXC provisioning
│   │                        #   workflows, role composition, Vault, gotchas
│   ├── kubernetes/          # k3s install & operations, Helm, Grafana+Prometheus
│   └── proxmox/             # LXC procedures, UID mapping, NFS between nodes,
│       │                    #   host configuration
│       └── cluster/         # Corosync QDevice as cluster tie-breaker
├── networking/
│   ├── dns/                 # AdGuard Home, Unbound, sync, TLS via DNS challenge
│   ├── vpn/                 # Tailscale, FortiGate dial-up IPSec
│   ├── cloudflare-tunnel-setup.md
│   ├── network-topology.md
│   └── tp-link-switch-recovery.md
├── screenshots/             # Images referenced by documents
├── services/                # Deployment docs & incident reports for hosted
│                            #   services (Gitea, n8n, Frigate, code-server,
│                            #   utility-apps…)
├── tools/                   # Repo maintenance scripts (IP sanitizer)
├── web-dev/                 # Portfolio website: Astro 6, Tailwind v4, components
├── queue.json               # Source queue for the AI blog pipeline (n8n)
└── README.md
```

## Conventions

- **Trilingual by default.** Most documents contain 🇬🇧 English, 🇩🇪 German and
  🇵🇱 Polish sections in a single file, with anchor-based navigation at the top.
- **Cheat-sheets are Polish-only** — they are personal quick references, not
  guides.
- **No real private addressing.** All private IPs are masked (`10.x.x.x`) before
  publishing. This is enforced by [`tools/sanitize_ips.py`](tools/sanitize_ips.py)
  and a [Gitea Actions check](.gitea/workflows/check-private-ips.yml) that runs
  on every push.
- **Documents are written from real sessions** — including the failures. Incident
  reports and troubleshooting notes describe what actually broke and how it was
  diagnosed, not idealized happy paths.

## Start here

A few documents that show the lab end-to-end:

| Topic | Document |
| ----- | -------- |
| Full CI/CD chain: push → build → registry → k3s deploy | [`ci-cd/gitea-actions-pipeline.md`](ci-cd/gitea-actions-pipeline.md) |
| Provisioning VMs with Terraform + Cloud-Init + Ansible | [`infrastructure/iac/`](infrastructure/iac/) |
| 2-node Proxmox cluster with a QDevice tie-breaker | [`infrastructure/proxmox/cluster/qdevice-tutorial.md`](infrastructure/proxmox/cluster/qdevice-tutorial.md) |
| Backup strategy: PBS + automated config backups | [`infrastructure/backup/`](infrastructure/backup/) |
| Network topology (sanitized diagram) | [`networking/network-topology.md`](networking/network-topology.md) |

## Related repositories

| Repo | Purpose |
| ---- | ------- |
| `homelab-iac` | Infrastructure as Code — Ansible, Terraform (private) |
| [scripts](https://github.com/damianztk/scripts) | Automation scripts — backups, maintenance |
| [portfolio](https://github.com/damianztk/portfolio) | Personal portfolio website ([damianzientek.de](https://damianzientek.de)) |
