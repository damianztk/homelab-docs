# Proxmox – Typy Storage (Cheat-Sheet)

> Wersja: 2026-05 | Środowisko: PVE 9 | Autor: Damian Zientek

---

## Pojęcia podstawowe

**Content types** – co storage może przechowywać:
- `images` – obrazy dysków VM (`.qcow2`, `.raw`)
- `rootdir` – wolumeny CT (rootfs LXC)
- `iso` – obrazy ISO
- `backup` – pliki vzdump (`.vma`, `.tar.zst`)
- `snippets` – snippety (np. cloud-init YAML, hook skrypty)

**Dwa rodzaje storage:**
- **File storage** – dane jako pliki w systemie plików (Directory, NFS, BTRFS, ZFS)
- **Block storage** – surowe bloki bez FS (LVM, iSCSI, RBD) – szybsze, ale bez snapshotów per-plik

---

## Lokalne backendy

### Directory
Zwykły katalog na dowolnym FS (ext4, xfs). Domyślnie `/var/lib/vz/`.  
Obrazy dysków jako pliki `.qcow2` lub `.raw`.

| | |
| --- | --- |
| **Content** | VM images, CT volumes, ISO, backup, snippets |
| **Snapshoty** | ✅ (przez qcow2) |
| **Thin provisioning** | ✅ (qcow2) |
| **Kiedy używać** | Punkt wyjścia, ISO, backupy — praktycznie zawsze |
| **Ograniczenia** | qcow2 ma narzut I/O vs raw; snapshoty wolniejsze niż LVM-Thin |

> **Twój setup:** `local` (CT templates, ISO) i katalogi `/mnt/hdd-data`, `/mnt/hdd-data2` to Directory.

---

### LVM
Każdy dysk VM to osobny Logical Volume — format `raw`, bez systemu plików ponad tym.

| | |
| --- | --- |
| **Content** | VM images, CT volumes |
| **Snapshoty** | ❌ (brak użytecznych snapshotów) |
| **Thin provisioning** | ❌ |
| **Kiedy używać** | Gdy liczy się wydajność i nie potrzebujesz snapshotów |
| **Ograniczenia** | Każdy LV musi mieć z góry zaalokowany rozmiar |

---

### LVM-Thin ⭐
LVM z thin provisioning — LV nie zajmuje fizycznie miejsca z góry, tylko tyle ile faktycznie zapisano. Pełne snapshoty i klonowanie. **Domyślny wybór Proxmoxa.**

| | |
| --- | --- |
| **Content** | VM images, CT volumes |
| **Snapshoty** | ✅ (pełne, natywne) |
| **Thin provisioning** | ✅ |
| **Kiedy używać** | Domyślny backend dla dysków VM i CT rootfs |
| **Ograniczenia** | Thin pool może się przepełnić — wymaga monitorowania |

> **Twój setup:** `local-lvm` na obu węzłach to właśnie LVM-Thin.

---

### BTRFS
Copy-on-Write filesystem z natywnym wsparciem snapshotów, kompresji i RAID. Obrazy jako `.raw` z reflinks (snapshoty błyskawiczne, nie zajmują miejsca dopóki dane się nie rozjeżdżają).

| | |
| --- | --- |
| **Content** | VM images, CT volumes, ISO, backup, snippets |
| **Snapshoty** | ✅ (reflinks, bardzo szybkie) |
| **Thin provisioning** | ✅ (implicit, CoW) |
| **Kiedy używać** | Nowy dysk, alternatywa dla ZFS przy mniejszej złożoności |
| **Ograniczenia** | Mniej battle-tested niż ZFS; BTRFS RAID5/6 ma historię bugów |

---

### ZFS
Potężny CoW filesystem z własnym RAID (RAIDZ), checksumming każdego bloku, kompresja, snapshoty, deduplikacja. Natywne wsparcie w Proxmox — pool tworzysz bezpośrednio z UI.

| | |
| --- | --- |
| **Content** | VM images, CT volumes, ISO, backup, snippets |
| **Snapshoty** | ✅ (natywne, błyskawiczne) |
| **Thin provisioning** | ✅ (CoW) |
| **Kiedy używać** | Dedykowane dyski pod VM storage, maksymalna integralność danych |
| **Ograniczenia** | Wymaga dużo RAM (~1 GB/TB, realnie 8–16 GB+); skomplikowany w zarządzaniu |

---

## Sieciowe / współdzielone

### NFS
Montuje share z serwera NFS przez sieć. W klastrze Proxmox — jeden węzeł eksportuje storage, pozostałe montują. Umożliwia **live migration** VM między węzłami bez shared block storage.

| | |
| --- | --- |
| **Protokół** | NFSv3 / NFSv4 |
| **Kiedy używać** | Shared storage w klastrze (np. pve1 eksportuje → pve2 montuje) |
| **Ograniczenia** | Wydajność zależna od sieci; brak natywnych snapshotów po stronie Proxmoxa |

> **Dla Twojego klastra:** najprostsze rozwiązanie shared storage bez dodatkowego hardware.

---

### SMB/CIFS
Jak NFS, ale protokół Windows/Samba. Przydatne gdy masz NAS (Synology, TrueNAS) który eksportuje CIFS.

| | |
| --- | --- |
| **Protokół** | SMB2/SMB3 |
| **Kiedy używać** | NAS z Synology/TrueNAS w środowisku mieszanym |
| **Ograniczenia** | Wolniejszy od NFS w środowiskach Linux |

---

### iSCSI
Block storage przez sieć. Serwer eksportuje "target" iSCSI (wirtualny dysk blokowy), Proxmox widzi go jak lokalny dysk. Używany z dedykowanymi SAN-ami.

| | |
| --- | --- |
| **Protokół** | iSCSI (TCP/IP) |
| **Kiedy używać** | TrueNAS z iSCSI targetem, enterprise SAN |
| **Ograniczenia** | Skomplikowana konfiguracja; raczej enterprise |

---

### ZFS over iSCSI
ZFS pool eksportowany jako iSCSI target (np. z TrueNAS) i montowany w Proxmox. Historycznie popularne, dziś wyparte przez natywny ZFS lub CephFS.

| | |
| --- | --- |
| **Kiedy używać** | Starsze setupy z TrueNAS; raczej legacy |
| **Ograniczenia** | Dwie warstwy złożoności; mało sensu w nowych setupach |

---

### CephFS + RBD
Rozproszony system storage — wiele węzłów tworzy jeden pool z replikacją i skalowaniem. **RBD** (RADOS Block Device) to block storage na Ceph. **CephFS** to filesystem na Ceph. Proxmox ma Ceph wbudowany — instalujesz bezpośrednio z UI.

| | |
| --- | --- |
| **Kiedy używać** | Klaster 3+ węzłów, środowiska produkcyjne wymagające HA storage |
| **Ograniczenia** | **Minimum 3 węzły** (quorum OSD); duże wymagania RAM i CPU; nie dla 2 węzłów |

> **Nie teraz.** Z 2 węzłami Ceph nie ma sensu. Temat do nauki, nie do wdrożenia.

---

### Proxmox Backup Server (PBS)
Nie tyle backend storage, co integracja z dedykowanym appliance'em backupowym. PBS oferuje deduplikację, enkrypcję i weryfikację backupów — znacznie wydajniejsze niż backup do zwykłego Directory.

| | |
| --- | --- |
| **Kiedy używać** | Backupy VM/CT z deduplikacją i enkrypcją |
| **Ograniczenia** | Wymaga osobnej instancji PBS (VM, LXC lub osobna maszyna) |

> **Roadmapa:** PBS jako LXC 900 na pve1 (IP `.90`), datastore `/mnt/hdd-data/backups/pbs-store/`.

---

### ESXi
Integracja z VMware ESXi datastores. Używane przy migracji z VMware lub w środowiskach hybrydowych.

> **Nie dotyczy** tego setupu.

---

## Podsumowanie — co używać w praktyce

| Backend | Use case | Status |
| --- | --- | --- |
| **Directory** | ISO, backupy, dane ogólne | ✅ W użyciu |
| **LVM-Thin** | Dyski VM i CT rootfs ze snapshotami | ✅ W użyciu (`local-lvm`) |
| **NFS** | Shared storage po rozbudowie klastra | 🔜 Do rozważenia |
| **PBS** | Backupy z deduplikacją | 🔜 Roadmapa (LXC 900) |
| **BTRFS** | Nowe dyski — alternatywa dla ZFS | 📚 Edukacyjnie |
| **ZFS** | Duże pule storage z integralnością danych | 📚 Edukacyjnie |
| **Ceph** | HA storage w klastrze 3+ węzłów | ❌ Za duże na 2 węzły |
| **iSCSI / ZFS over iSCSI** | Enterprise SAN, TrueNAS | ❌ Nie dotyczy |
| **ESXi** | VMware | ❌ Nie dotyczy |

---

## Szybka ściągawka — snapshoty i thin provisioning

| Backend | Snapshoty | Thin provisioning | Format dysków |
| --- | --- | --- | --- |
| Directory | ✅ (qcow2) | ✅ (qcow2) | `.qcow2`, `.raw` |
| LVM | ❌ | ❌ | raw block |
| LVM-Thin | ✅ | ✅ | raw block |
| BTRFS | ✅ (reflink) | ✅ (CoW) | `.raw` |
| ZFS | ✅ | ✅ (CoW) | zvol |
| NFS | zależnie od backendu | zależnie | `.qcow2`, `.raw` |
| RBD (Ceph) | ✅ | ✅ | rbd object |
