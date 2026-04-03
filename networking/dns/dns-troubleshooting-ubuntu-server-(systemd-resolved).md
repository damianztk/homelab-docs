# DNS Troubleshooting — Ubuntu Server (systemd-resolved)

> 🇬🇧 [English](#english) · 🇵🇱 [Polski](#polski) · 🇩🇪 [Deutsch](#deutsch)

---

<a name="english"></a>
# 🇬🇧 English

## Problem

After a network reconfiguration (e.g. new DNS server, migration from Pi-hole to AdGuard Home), the old DNS server still appears in `resolvectl status` despite updating netplan and `resolved.conf`.

---

## Diagnostics — Where to Start

### 1. Check the current DNS state
```bash
resolvectl status
```

Pay attention to:
- the **Global** section — DNS set via resolved.conf or netplan
- per-interface sections (e.g. **ens18**) — DNS provided by DHCP or netplan
- the `resolv.conf mode` field — critical information (see below)

### 2. Understand resolv.conf modes

| Mode | Meaning |
|---|---|
| `stub` | systemd-resolved manages `/etc/resolv.conf` — single source of truth |
| `foreign` | `/etc/resolv.conf` is managed externally (cloud-init, netplan, manually) — **resolved ignores and never overwrites it** |
| `managed` | resolved manages the file directly |

**`foreign` mode is the most common reason an old DNS entry won't go away.**

### 3. Check the contents of resolv.conf
```bash
cat /etc/resolv.conf
```

If you see an old DNS address here — this is the source of the problem.

```bash
# Also check whether it's a symlink or a real file
ls -la /etc/resolv.conf
```

---

## Solutions

### A) Quick fix — hand control back to systemd-resolved (recommended)

```bash
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
sudo systemctl restart systemd-resolved
resolvectl status
```

This turns `/etc/resolv.conf` into a symlink pointing to the stub resolver — from this point on, resolved is the single source of truth for DNS.

### B) DHCP is overriding DNS settings

If you see an old DNS address in the per-interface section of `resolvectl status` pushed by DHCP, add the following to your netplan config:

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

Apply the changes:
```bash
sudo netplan apply
```

### C) Cloud-init is restoring the old config on reboot

Cloud-init can overwrite network settings on every VM restart. To disable this behaviour:

```bash
sudo bash -c 'echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network.cfg'
```

Also check whether cloud-init has an old DNS address hardcoded:
```bash
cat /etc/cloud/cloud.cfg.d/*.cfg 2>/dev/null
cat /var/lib/cloud/instances/*/user-data.txt 2>/dev/null
```

### D) Verify resolved.conf

```bash
cat /etc/systemd/resolved.conf
cat /etc/systemd/resolved.conf.d/*.conf 2>/dev/null
```

Make sure `DNS=` and `FallbackDNS=` contain the correct addresses. After editing:
```bash
sudo systemctl restart systemd-resolved
```

---

## Expected Final State

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

Verify DNS is actually working:
```bash
resolvectl query google.com
dig google.com
```

---

## Environment Context

- **VM**: Ubuntu Server on Proxmox VE 9
- **Network**: SERVER_LAN (VLAN 20) — `10.100.20.0/24`
- **DNS**: AdGuard Home + Unbound on DELL Wyse 3040 — `10.100.30.2`
- **Previous DNS**: Pi-hole at `192.168.2.50` (old network `192.168.2.0/24`)

---
---

<a name="polski"></a>
# 🇵🇱 Polski

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

---
---

<a name="deutsch"></a>
# 🇩🇪 Deutsch

## Problem

Nach einer Netzwerkkonfigurationsänderung (z. B. neuer DNS-Server, Migration von Pi-hole zu AdGuard Home) erscheint der alte DNS-Server weiterhin in `resolvectl status`, obwohl netplan und `resolved.conf` bereits aktualisiert wurden.

---

## Diagnose — Wo anfangen

### 1. Aktuellen DNS-Status prüfen
```bash
resolvectl status
```

Auf folgendes achten:
- den **Global**-Abschnitt — DNS, der über resolved.conf oder netplan gesetzt wurde
- die interfacebezogenen Abschnitte (z. B. **ens18**) — DNS, der per DHCP oder netplan bereitgestellt wird
- das Feld `resolv.conf mode` — entscheidende Information (siehe unten)

### 2. Die resolv.conf-Modi verstehen

| Modus | Bedeutung |
|---|---|
| `stub` | systemd-resolved verwaltet `/etc/resolv.conf` — einzige Quelle der Wahrheit |
| `foreign` | `/etc/resolv.conf` wird extern verwaltet (cloud-init, netplan, manuell) — **resolved ignoriert die Datei und überschreibt sie nie** |
| `managed` | resolved verwaltet die Datei direkt |

**Der Modus `foreign` ist die häufigste Ursache dafür, dass ein alter DNS-Eintrag nicht verschwindet.**

### 3. Inhalt der resolv.conf prüfen
```bash
cat /etc/resolv.conf
```

Wenn hier eine alte DNS-Adresse steht — das ist die Ursache des Problems.

```bash
# Prüfen, ob es sich um einen Symlink oder eine echte Datei handelt
ls -la /etc/resolv.conf
```

---

## Lösungen

### A) Schnelle Lösung — Kontrolle an systemd-resolved übergeben (empfohlen)

```bash
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
sudo systemctl restart systemd-resolved
resolvectl status
```

Damit wird `/etc/resolv.conf` zu einem Symlink auf den Stub-Resolver — ab sofort ist resolved die einzige Quelle der Wahrheit für DNS.

### B) DHCP überschreibt die DNS-Einstellungen

Wenn im per-Interface-Abschnitt von `resolvectl status` eine alte DNS-Adresse erscheint, die per DHCP geliefert wird, folgendes zur netplan-Konfiguration hinzufügen:

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

Änderungen übernehmen:
```bash
sudo netplan apply
```

### C) Cloud-init stellt die alte Konfiguration beim Neustart wieder her

Cloud-init kann Netzwerkeinstellungen bei jedem VM-Neustart überschreiben. Um dieses Verhalten zu deaktivieren:

```bash
sudo bash -c 'echo "network: {config: disabled}" > /etc/cloud/cloud.cfg.d/99-disable-network.cfg'
```

Außerdem prüfen, ob cloud-init eine alte DNS-Adresse fest eingetragen hat:
```bash
cat /etc/cloud/cloud.cfg.d/*.cfg 2>/dev/null
cat /var/lib/cloud/instances/*/user-data.txt 2>/dev/null
```

### D) resolved.conf überprüfen

```bash
cat /etc/systemd/resolved.conf
cat /etc/systemd/resolved.conf.d/*.conf 2>/dev/null
```

Sicherstellen, dass `DNS=` und `FallbackDNS=` die richtigen Adressen enthalten. Nach der Bearbeitung:
```bash
sudo systemctl restart systemd-resolved
```

---

## Erwarteter Endzustand

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

Überprüfen, ob DNS tatsächlich funktioniert:
```bash
resolvectl query google.com
dig google.com
```

---

## Umgebungskontext

- **VM**: Ubuntu Server auf Proxmox VE 9
- **Netzwerk**: SERVER_LAN (VLAN 20) — `10.100.20.0/24`
- **DNS**: AdGuard Home + Unbound auf DELL Wyse 3040 — `10.100.30.2`
- **Vorheriger DNS**: Pi-hole unter `192.168.2.50` (altes Netzwerk `192.168.2.0/24`)