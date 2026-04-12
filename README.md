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

---
> [!TIP]
> Stara wersja poniżej - opis LXC może się przydać

# Mój Homelab - Dokumentacja

To jest moje pierwsze repozytorium na własnym serwerze Gitea!

## Konfiguracja Gitea (15.03.2026)
* **Kontener**: LXC ID 200 (Alpine Linux)
* **Adres IP**: 10.100.20.200
* **Hasło roota**: (usunąłem hasło dla bezpieczeństwa)
* **Hasło Gitea / damian**: (usunąłem hasło dla bezpieczeństwa)
* **Przechowywanie**: Dane zmapowane do `/var/lib/vz/gitea-data` na SSD
* **Backup**: Automatyczny co noc o 3:30 na dysk HDD

## Sieć (FortiGate 60E)
* Gitea znajduje się w VLAN 20 (SERVER_LAN).

> [!NOTE]
> Zmienić plik README!! A info o Gitea do innego pliku!!
