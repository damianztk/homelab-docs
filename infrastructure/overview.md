# Homelab — Infrastructure Overview

## Hardware

### Servrs
| Node | Mainboard | CPU | RAM | Storage |
|------|-------|-----|-----|---------|
| Node 1 | Asus Prime B250M-A | i5-7400 | 16GB | 250GB SSD + 1TB HDD + 1TB HDD |
| Node 2 | ASRock H270M Pro4 | i5-7600K | 32GB | 275GB m.2 SATA + 1TB HDD + 2TB HDD |
| DELL Wyse 3040 | Terminal | Intel Atom | 2GB | 16GB eMMC |

### Network
| Device | Role |
|------------|------|
| Vodafone Station | ISP Router |
| Fortigate 60E | Firewall / Router |
| TP-Link TL-SG108PE | Switch PoE (SERVER/IoT) |
| Netgear GS308E | Switch (HOME/MEDIA) |
| FortiAP 231F | AP |
| FortiAP U323EV-E | AP |

## VLANs
| VLAN | Name | Network |
|------|-------|------|
| 10 | HOME_LAN | 10.100.10.0/24 |
| 20 | SERVER_LAN | 10.100.20.0/24 |
| 30 | DNS_LAN | 10.100.30.0/24 |
| 40 | HOME_WLAN | 10.100.40.0/24 |
| 50 | PL_WLAN | 10.100.50.0/24 |
| 90 | IOT_VLAN | 10.100.90.0/24 |
| 100 | MEDIA_LAN | 10.100.100.0/24 |
| 200 | GUEST_WLAN | 10.100.200.0/24 |

> Check/fix names more precisely

## Software
### Node 1 (Proxmox VE 9)
- Tailscale (LXC) - subnet router Tailnet
- Adguard Home + Unbound + adguardhome-sync (LXC) - sencond Instance of AGH
- NPM (LXC) — reverse proxy
- Gitea (LXC) - version control, git
- Kavita (LXC) - digital eBook library
- Home Assistant (VM) - brain of Smart Home
...etc.

### Node 2 (Proxmox VE 9)
- Jellyfin (LXC) - Media Server

### Dell Wyse 3040 (Debian 13)
- Adguard Home - main AGH Instance, network's DNS server
- Unbound - private DNS resolver with DNSSEC
- Docker - used to manage additionary, lighter services
- Uptime Kuma (Docker Container) - infrastructure monitoring

---

> Last Update: 2026-04-28

> [!NOTE]  
> **Do dodania:**  
> wszystkie usługi z pve 1/2,  
> przerobienie działu Software na tabelę,  
> dodanie typu maszyny z przodu, dodania adresów IP, dodania lokalizacji Bind Mountów,  
> dodania nazwy użytkownika dla maszyny i aplikacji