# 🛠️ Raport z odzyskiwania sieci i konfiguracji VLAN (17/18.03.2026)

## 📝 Podsumowanie incydentu

Planowe przygotowanie portu pod Node 2 (Proxmox) przerodziło się w całkowitą reanimację switcha TP-Link TL-SG108PE po utracie łączności i resecie do ustawień fabrycznych.

## 🔴 Przebieg awarii

1. Trigger: Próba zmiany konfiguracji portu zakończona utratą kontaktu ze switchem.
2. Problem: Switch po resecie wrócił do IP `192.168.0.1`.
3. Konflikt: FortiGate widział ten sam adres MAC w dwóch podsieciach jednocześnie (`192.168.0.1` w WAN/Vodafone oraz `10.100.1.13` w Management VLAN), co powodowało błędy w inwentarzu urządzeń.

## 🔧 Kroki naprawcze (Troubleshooting)

1. Odzyskanie dostępu: Ustawienie statycznego IP na laptopie (`192.168.0.100`) i bezpośrednie wpięcie w switch w celu zmiany adresu na docelowy.
2. Czyszczenie FortiGate:
  - Wyczyszczenie bazy inwentarza: `diagnose user device clear.`
  - Wyczyszczenie tablicy ARP: `execute clear system arp table.`
3. DHCP Reservation: Upewnienie się, że MAC switcha ma rezerwację na `10.100.1.13`.
4. Wymuszenie IP na kamerach: Użycie funkcji `Port Config` (Disable/Enable) w celu zrestartowania linku i wymuszenia pobrania IP z właściwego VLAN 90.

## 🕸️ Docelowa konfiguracja VLAN (TP-Link)

| Port | Urządzenie | VLAN 1 (Mgmt) | VLAN 20 (Srv) | VLAN 90 (IoT) | PVID |
| :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Kamera 1 | - | - | Untagged | 90 |
| 2 | Kamera 2 | - | - | Untagged | 90 |
| 3 | Serwisowy | Untagged | - | - | 1 |
| 4 | FortiAP | Untagged | - | Tagged | 1 |
| 5 | Serwisowy | Untagged | - | - | 1 |
| 6 | Node 2 (New) | - | Untagged | - | 20 |
| 7 | Node 1 (Old) | - | Untagged | - | 20 |
| 8 | FortiGate | Untagged | Tagged | Tagged | 1 |

## 💡 Lekcje na przyszłość

- Backup: Zawsze pobierać plik .bin po każdej zmianie (backup zrobiony 18.03.2026).
- PoE/Port Restart: Zamiast szukać PoE Config, można użyć Port Config -> Disable/Enable do zresetowania kamer.
- FortiAP: W trybie Bridge wymaga tagowania na switchu i untagged na PVID 1 dla zarządzania.

#### Status: Wszystkie systemy (Reolink, HA, Proxmox) sprawne.

---
> [!TIP]
> Zawsze po zmianach pobieraj plik backup `.bin` ze switcha!

---
---

# 🛠️ Raport z odzyskiwania sieci i konfiguracji VLAN (18.03.2026)

## 📝 Podsumowanie incydentu
Planowe przygotowanie portu pod **Node 2 (Proxmox)** zakończone pełnym resetem switcha i rekonfiguracją bazy FortiGate.

## 🕸️ Docelowa konfiguracja VLAN (TP-Link)

| Port | Urządzenie | VLAN 1 (Mgmt) | VLAN 20 (Srv) | VLAN 90 (IoT) | PVID |
| :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Kamera 1 | - | - | Untagged | 90 |
| 2 | Kamera 2 | - | - | Untagged | 90 |
| 3 | Serwisowy | Untagged | - | - | 1 |
| 4 | FortiAP | Untagged | - | Tagged | 1 |
| 5 | Serwisowy | Untagged | - | - | 1 |
| 6 | Node 2 (New) | - | Untagged | - | 20 |
| 7 | Node 1 (Old) | - | Untagged | - | 20 |
| 8 | FortiGate | Untagged | Tagged | Tagged | 1 |

## 🔧 Kluczowe komendy FortiGate
Podczas awarii użyto poniższych komend do wyczyszczenia konfliktów IP:

* `diagnose user device clear` - czyszczenie bazy urządzeń.
* `execute clear system arp table` - czyszczenie tablicy ARP.

---
> [!TIP]
> Zawsze po zmianach pobieraj plik backup `.bin` ze switcha!