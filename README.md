<!-- markdownlint-disable MD033 -->
<div align="center">

# Homelab-docs

![Proxmox](https://img.shields.io/badge/Proxmox-VE_9-E57000?style=flat-square&logo=proxmox&logoColor=white) ![Fortigate](https://img.shields.io/badge/Fortinet-Fortigate_60E-EE3124?style=flat-square&logo=fortinet&logoColor=white) ![Cloudflare](https://img.shields.io/badge/Cloudflare-Tunnel-F38020?style=flat-square&logo=cloudflare&logoColor=white)

![k3s](https://img.shields.io/badge/k3s-Kubernetes-FFC61C?style=flat-square&logo=k3s&logoColor=black) ![Docker](https://img.shields.io/badge/Docker-Containers-2496ED?style=flat-square&logo=docker&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?style=flat-square&logo=terraform&logoColor=white) ![Ansible](https://img.shields.io/badge/Ansible-Automation-EE0000?style=flat-square&logo=ansible&logoColor=white) ![n8n](https://img.shields.io/badge/n8n-Automation-EA4B71?style=flat-square&logo=n8n&logoColor=white)

![Gitea](https://img.shields.io/badge/Gitea-Git_Server-609926?style=flat-square&logo=gitea&logoColor=white) ![AdGuard](https://img.shields.io/badge/AdGuard-DNS-68BC71?style=flat-square&logo=adguard&logoColor=white)

🇬🇧 Personal knowledge base documenting my homelab infrastructure —
configurations, guides, and troubleshooting notes.

🇩🇪 Persönliche Wissensdatenbank zur Dokumentation meiner
Homelab-Infrastruktur — Konfigurationen, Anleitungen und Notizen.

🇵🇱 Osobista baza wiedzy dokumentująca moją infrastrukturę homelab —
konfiguracje, instrukcje i notatki diagnostyczne.
</div>
<!-- markdownlint-enable MD033 -->

---

## Structure

```text
homelab-docs/
├── cheat-sheets/               # learning help, quick notes   
├── infrastructure/
│   ├── dell-wyse-3040/         # Dell Wyse 3040 Terminal-related instructions
│   ├── infrastructure-as-code/ # Ansible/Terraform instructions
│   ├── kubernetes/             # k8s instructions
│   ├── proxmox/                # LXC setup, backups, Proxmox config
│   └── overview.md             # Full hardware & software inventory
├── networking/
│   ├── dns/                    # DNS instructions and troubleshooting
│   └── network-topology.md
├── portfolio/                  # Portfolio Website-related docs
├── screenshots/                # Visual proof of concept, diagrams, future guide helpers
├── services/                   # install-guides for services and apps deployed in my homelab
├── tailscale/                  # Subnet router setup and more
└── README.md
```

## Infrastructure

Full hardware and software inventory → [overview.md](infrastructure/overview.md)

## Related repositories

| Repo | Purpose |
| ---- | ------- |
| `homelab-iac` | Infrastructure as Code - Ansible, Terraform (private) |
| [scripts](https://github.com/damianztk/scripts) | Automation scripts - backups, maintenance |
| [portfolio](https://github.com/damianztk/portfolio) | Personal portfolio website (not yet ready) |
