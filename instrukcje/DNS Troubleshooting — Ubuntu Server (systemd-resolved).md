# DNS Troubleshooting — Ubuntu Server (systemd-resolved)

## Problem

Po zmianie konfiguracji sieci (np. nowy adres DNS, migracja z Pi-hole na AdGuard Home) stary serwer DNS nadal pojawia się w `resolvectl status` mimo edycji netplan i `resolved.conf`.

---

## Diagnostyka — od czego zacząć

### 1. Sprawdź aktualny stan DNS
```bash
resolvectl status
```

Zwróć uwagę na:
- sekcję **Global** — DNS ustawiony przez resolved.conf lub netplan
- sekcję per-interfejs (np. **ens18**) — DNS podany przez DHCP lub netplan
- pole `resolv.conf mode` — kluczowa informacja (patrz niżej)

### 2. Sprawdź tryb resolv.conf

| Tryb | Znaczenie |
|---|---|
| `stub` | resolved zarządza `/etc/resolv.conf` — wszystko idzie przez jeden punkt |
| `foreign` | `/etc/resolv.conf` jest zarządzany zewnętrznie (cloud-init, netplan, ręcznie) — **resolved go ignoruje i nie nadpisuje** |
| `managed` | resolved zarządza plikiem bezpośrednio |

**Tryb `foreign` to najczęstsza przyczyna "starego DNS, który nie znika".**

### 3. Sprawdź zawartość resolv.conf
```bash
cat /etc/resolv.conf
```

Jeśli widzisz stary adres DNS — to właśnie tutaj siedzi problem.

```bash
# Sprawdź też czy to symlink czy prawdziwy plik
ls -la /etc/resolv.conf
```

---

## Rozwiązania

### A) Szybka naprawa — oddaj kontrolę systemd-resolved (zalecane)

```bash
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
sudo systemctl restart systemd-resolved
resolvectl status
```

To sprawia że `/etc/resolv.conf` staje się symlinkiem do stub resolvera — od tej pory resolved jest jedynym źródłem prawdy.

### B) DNS przez DHCP nadpisuje ustawienia

Jeśli przy interfejsie w `resolvectl status` widać stary DNS podany przez DHCP, dodaj do pliku netplan:

```yaml
network:
  ethernets:
    ens18:
      dhcp4: true
      dhcp4-overrides:
        use-dns: false
      nameservers:
        addresses: [10.100.30.2]
  version: 2
```

Następnie zastosuj:
```bash
sudo netplan apply
```

### C) Cloud-init przywraca starą konfigurację przy restarcie

Cloud-init może nadpisywać ustawienia sieci przy każdym restarcie VM. Żeby to zablokować:

```bash
sudo bash -c 'echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network.cfg'
```

Sprawdź też czy cloud-init nie ma zakodowanego starego DNS:
```bash
cat /etc/cloud/cloud.cfg.d/*.cfg 2>/dev/null
cat /var/lib/cloud/instances/*/user-data.txt 2>/dev/null
```

### D) Weryfikacja resolved.conf

```bash
cat /etc/systemd/resolved.conf
cat /etc/systemd/resolved.conf.d/*.conf 2>/dev/null
```

Upewnij się że `DNS=` i `FallbackDNS=` mają właściwe adresy. Po edycji:
```bash
sudo systemctl restart systemd-resolved
```

---

## Pożądany stan końcowy

```
Global
     Protocols: -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
resolv.conf mode: stub
     DNS Servers: 10.100.30.2

Link 2 (ens18)
  Current Scopes: DNS
       Protocols: +DefaultRoute ...
     DNS Servers: 10.100.30.2
```

Sprawdzenie czy DNS faktycznie działa:
```bash
resolvectl query google.com
dig google.com
```

---

## Kontekst środowiska

- **VM**: Ubuntu Server na Proxmox VE 9
- **Sieć**: SERVER_LAN (VLAN 20) — `10.100.20.0/24`
- **DNS**: AdGuard Home + Unbound na DELL Wyse 3040 — `10.100.30.2`
- **Poprzedni DNS**: Pi-hole na `192.168.2.50` (stara sieć `192.168.2.0/24`)