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
├── screenshots/                # Visual proof of concept, diagrams, future guide helpers
├── tailscale/                  # Subnet router setup and more
├── services/                   # install-guides for services and apps deployed in my homelab
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
