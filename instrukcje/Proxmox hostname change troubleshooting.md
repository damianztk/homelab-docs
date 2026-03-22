# Proxmox: Zmiana Hostname Node'a (i jak to naprawić gdy pójdzie nie tak)

**Data:** 2026-03-22  
**Node:** pve1 (poprzednio: `proxmox`)  
**Proxmox VE:** 9.1.6

---

## Kontekst

Zmiana hostname była konieczna przed utworzeniem klastra Proxmox. Proxmox wymaga FQDN (Fully Qualified Domain Name) jako hostname — samo `proxmox` nie wystarczy. Docelowa nazwa: `pve1.damiannazwisko.de`.

---

## Krok 1: Zmiana hostname

```bash
hostnamectl set-hostname pve1.damiannazwisko.de
```

Edytuj `/etc/hosts` — zmień linię ze starą nazwą:

```
10.100.20.10    pve1.damiannazwisko.de    pve1
```

Weryfikacja:

```bash
hostname --fqdn
# Powinno zwrócić: pve1.damiannazwisko.de
```

Reboot node'a.

---

## Problem: Po reboocie GUI pokazuje dwa node'y

Po zmianie hostname w Proxmox GUI pojawił się stary node `proxmox` oraz nowy `pve1` — każdy z osobnym storage'm. VM i LXC były widoczne pod starą nazwą.

**Przyczyna:** Proxmox przechowuje konfigurację node'a w `/etc/pve/nodes/<hostname>/`. Po zmianie hostname tworzony jest nowy katalog, stary zostaje.

```bash
ls /etc/pve/nodes/
# proxmox/   pve1/
```

---

## Próba naprawy: cp starych plików do nowego katalogu

```bash
cp -r /etc/pve/nodes/proxmox/* /etc/pve/nodes/pve1/
```

**Wynik:** Błędy `File exists` — część plików już istniała w nowym katalogu. cp nie nadpisuje domyślnie istniejących plików.

---

## Usunięcie starego katalogu

```bash
rm -rf /etc/pve/nodes/proxmox
```

Następnie restart usług:

```bash
systemctl restart pve-cluster
```

**Wynik:** Błąd — `pve-cluster.service failed`.

---

## Diagnoza błędu pve-cluster

```bash
systemctl status pve-cluster.service
```

Logi pokazały: `unable to acquire pmxcfs lock` — stary proces pmxcfs utknął i blokował start nowego.

**Rozwiązanie:**

```bash
killall pmxcfs
sleep 2
systemctl start pve-cluster
systemctl status pve-cluster
```

Po tym `pve-cluster` wystartował poprawnie (`active (running)`).

---

## Problem: VM i LXC zniknęły z GUI

Po naprawieniu klastra okazało się, że `/etc/pve/nodes/pve1/qemu-server/` i `/etc/pve/nodes/pve1/lxc/` są puste — pliki konfiguracyjne VM nie zostały poprawnie skopiowane (cp zawiódł gdy pmxcfs był niestabilny).

---

## Weryfikacja danych na LVM

Dane VM/LXC siedzą na LVM — niezależnie od konfiguracji Proxmoxa:

```bash
lvs
```

**Wynik:** Wszystkie volumeny obecne i nienaruszone:

```
vm-101-disk-0    32G   # HAOS
vm-101-disk-1    4M    # EFI
vm-102-disk-0    5G    # Tailscale
vm-103-disk-0    6G    # AdGuard Home
vm-104-disk-0    8G    # NPM
vm-200-disk-0    2G    # Gitea
```

> ⚠️ **Ważna lekcja:** Dane na LVM są bezpieczne nawet gdy konfiguracja Proxmoxa się posypie. Dyski fizyczne i konfiguracje to dwie niezależne warstwy.

---

## Naprawa: Przywrócenie konfiguracji z backupu

Na szczęście kopia `/etc/pve/` była zrobiona kilka dni wcześniej przez WinSCP.

Skopiowano przez WinSCP:
- `nodes/proxmox/qemu-server/101.conf` → `/etc/pve/nodes/pve1/qemu-server/101.conf`
- `nodes/proxmox/lxc/102.conf` → `/etc/pve/nodes/pve1/lxc/102.conf`
- `nodes/proxmox/lxc/103.conf` → `/etc/pve/nodes/pve1/lxc/103.conf`
- `nodes/proxmox/lxc/104.conf` → `/etc/pve/nodes/pve1/lxc/104.conf`
- `nodes/proxmox/lxc/200.conf` → `/etc/pve/nodes/pve1/lxc/200.conf`

Restart usług:

```bash
systemctl restart pvedaemon
systemctl restart pveproxy
```

Hard refresh GUI: **Ctrl+Shift+R**

**Wynik:** Wszystkie VM i LXC wróciły. Bulk start z GUI — wszystko uruchomione i działające.

---

## Czego NIE kopiować ze starego backupu

| Plik | Kopiować? | Powód |
|------|-----------|-------|
| `qemu-server/*.conf` | ✅ Tak | Konfiguracje VM |
| `lxc/*.conf` | ✅ Tak | Konfiguracje LXC |
| `user.cfg` | ✅ Tak (jeśli masz wielu userów) | Użytkownicy Proxmoxa |
| `vzdump.cron` | ✅ Tak | Harmonogram backupów |
| `pve-root-ca.pem` | ❌ Nie | Nowy node ma własne certyfikaty |
| `pve-www.key` | ❌ Nie | Nowy node ma własne klucze |
| `authkey.pub` | ❌ Nie | Nowy node ma własne klucze |

---

## Wnioski i lekcje

1. **Rób backup `/etc/pve/` przed każdą większą zmianą.** Dzisiaj backup uratował całą konfigurację.
2. **`/etc/pve/` to wirtualny filesystem (pmxcfs)** — nie kopiuj go gdy pmxcfs jest niestabilny lub zatrzymany.
3. **Dane na LVM są niezależne od konfiguracji Proxmoxa** — nawet przy utracie wszystkich confów, dyski VM są bezpieczne.
4. **Przed zmianą hostname sprawdź** czy masz świeży backup `/etc/pve/nodes/<stara_nazwa>/`.
5. **Prawidłowa kolejność zmiany hostname:**
   - Zrób backup
   - Zmień hostname (`hostnamectl`)
   - Edytuj `/etc/hosts`
   - Skopiuj zawartość `/etc/pve/nodes/<stara_nazwa>/` do `/etc/pve/nodes/<nowa_nazwa>/` **gdy pmxcfs działa**
   - Usuń stary katalog
   - Reboot

---

## FAQ — pytania które zadałem podczas troubleshootingu

**Q: Instalator Proxmoxa mówi "Hostname does not look like a fully qualified domain name" — czy mogę zignorować?**  
A: To tylko ostrzeżenie, nie błąd — możesz kliknąć OK i kontynuować z samym `pve2`. Ale lepiej od razu wpisać FQDN w formacie `pve2.twojadomena.de` — zaoszczędzi to problemów przy konfiguracji DNS i klastra.

---

**Q: Czy samo wpisanie domeny w hostname "upublicznia" mój serwer?**  
A: Nie. Hostname to tylko nazwa identyfikacyjna maszyny. DNS lokalny (AdGuard) rozwiązuje ją tylko wewnątrz sieci. Internet nie wie o istnieniu tego wpisu i nie ma jak się dostać — dopóki świadomie nie wystawisz usługi przez Cloudflare Tunnel, otwarty port lub inną metodę.

---

**Q: Czy usunięcie `/etc/pve/nodes/proxmox` usunie mi wszystkie VM i dane?**  
A: Nie. Ten katalog zawiera tylko **pliki konfiguracyjne** VM i LXC. Dane (dyski) siedzą na LVM (`/dev/pve/`) lub na HDD — tam ich nie ruszamy. Najgorsze co może się stać to utrata konfiguracji, którą można odbudować. Dane fizyczne są bezpieczne.

---

**Q: Co robi `killall pmxcfs` i czy to bezpieczne?**  
A: `killall pmxcfs` zabija wszystkie procesy o nazwie `pmxcfs` (Proxmox Cluster File System). Jest bezpieczne gdy pmxcfs jest w stanie błędu i nie odpowiada — czyli dokładnie w tej sytuacji. `sleep 2` po nim daje systemowi chwilę na posprzątanie przed ponownym startem.

---

**Q: Skąd wiem że dane na LVM są bezpieczne skoro nic nie widzę w GUI?**  
A: Komenda `lvs` pokazuje fizyczne volumeny na LVM niezależnie od stanu Proxmoxa. Jeśli widzisz tam `vm-101-disk-0`, `vm-102-disk-0` itd. — dane są na dysku. GUI Proxmoxa pokazuje tylko to co ma w konfiguracji (`.conf` pliki) — gdy konfiguracje znikną, GUI jest "ślepe", ale dyski żyją.

---

**Q: Czy `cp -r` z błędami "File exists" coś uszkodził?**  
A: Nie. Błąd `File exists` przy `cp` oznacza tylko że plik już istnieje w miejscu docelowym i cp go nie nadpisał. To zachowanie domyślne — bezpieczne. Gdybyś chciał nadpisać, użyłbyś flagi `-f`. W tym przypadku błędy były niegroźne.

---

## Mapa VM/LXC (stan po naprawie)

| ID | Typ | Nazwa | Storage |
|----|-----|-------|---------|
| 101 | VM (QEMU) | haos-17.1 | local-lvm |
| 102 | LXC | tailscale | local-lvm |
| 103 | LXC | agh-proxmox | local-lvm |
| 104 | LXC | npm | local-lvm |
| 200 | LXC | gitea | local-lvm |