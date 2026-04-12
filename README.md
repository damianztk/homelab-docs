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

### usunięcie no-subscription-message w Proxmox

```bash
sed -i "s/NotValidSubscription\!/false/g" /usr/share/javascript/proxmox-widget-toolkit/proxmoxlib.js
```