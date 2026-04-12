# homelab-docs

🇬🇧 Personal knowledge base documenting my homelab infrastructure —
configurations, guides, and troubleshooting notes.

🇩🇪 Persönliche Wissensdatenbank zur Dokumentation meiner
Homelab-Infrastruktur — Konfigurationen, Anleitungen und Notizen.

🇵🇱 Osobista baza wiedzy dokumentująca moją infrastrukturę homelab —
konfiguracje, instrukcje i notatki diagnostyczne.

---

## Structure

```
homelab-docs/
├── cheat-sheets/       # learning help, quick notes   
├── infrastructure/
│   ├── proxmox/        # LXC setup, backups, Proxmox config
│   ├── dell-wyse-3040/ # AdGuard Home, Unbound, Uptime Kuma
│   ├── overview.md     # Full hardware & software inventory
│   └── terraform-ansible-cloudinit.md
├── networking/
│   ├── dns/            # AdGuard Home, Unbound, DNS troubleshooting
│   ├── network-topology.md
│   ├── npm-lets-encrypt-dns-challenge-guide.md
│   └── tp-link-switch-recovery.md
├── tailscale/          # Subnet router setup
├── screenshots/        # Visual proof of concept, diagrams, future guide helpers
└── README.md
```

## Infrastructure

Full hardware and software inventory → [overview.md](infrastructure/overview.md)

## Related repositories

| Repo | Purpose |
|------|---------|
| [homelab](https://gitea.damianzientek.de/damian/homelab) | Infrastructure as Code — Ansible, Terraform |
| [scripts](https://gitea.damianzientek.de/damian/scripts) | Automation scripts — backups, maintenance |
| [portfolio](https://gitea.damianzientek.de/damian/portfolio) | Personal portfolio website |

