# Proxmox — Komendy

## LXC — kontenery

```bash
# Lista i status
pct list
pct status <vmid>

# Start / stop / restart
pct start <vmid>
pct stop <vmid>
pct shutdown <vmid>         # graceful stop
pct reboot <vmid>

# Wejście do kontenera
pct enter <vmid>

# Konfiguracja
pct config <vmid>           # pokaż konfigurację kontenera
pct set <vmid> -memory 512  # zmień ilość RAM (MB)

# Snapshoty
pct snapshot <vmid> <nazwa>
pct listsnapshot <vmid>
pct rollback <vmid> <nazwa>

# Montowanie rootfs kontenera na hoście (dla LXC na local-lvm)
pct mount <vmid>            # montuje do /var/lib/lxc/<vmid>/rootfs
pct unmount <vmid>
```

---

## QEMU — maszyny wirtualne

```bash
qm list
qm status <vmid>
qm start <vmid>
qm stop <vmid>
qm shutdown <vmid>
qm reboot <vmid>
qm config <vmid>
```

---

## Backup — vzdump

```bash
# Backup do konkretnego storage
vzdump <vmid> --storage <storage-name> --compress zstd --mode snapshot

# Backup z retencją
vzdump <vmid> --storage <storage-name> --compress zstd --maxfiles 7

# Backup wszystkich VM/LXC
vzdump --all --storage <storage-name> --compress zstd
```

---

## Storage

```bash
pvesm list <storage-name>           # lista plików w storage
pvesm status                        # status wszystkich storage
pvesm scan lvm                      # skanuj dostępne LVM

# Konfiguracja storage
cat /etc/pve/storage.cfg
```

---

## Klaster

```bash
pvecm status                        # status klastra
pvecm nodes                         # lista nodów
pvesh get /cluster/resources        # wszystkie zasoby klastra (JSON)
```

---

## Sieć i konfiguracja hosta

```bash
# Konfiguracja sieci
cat /etc/network/interfaces

# Logi Proxmox
journalctl -u pveproxy              # logi API/UI
journalctl -u pvedaemon             # logi głównego demona
tail -f /var/log/pve/tasks/active   # aktywne zadania

# Certyfikaty
pvenode cert info                   # informacje o certyfikacie
```

---

## pvesh — API z linii komend

```bash
pvesh get /nodes                                    # lista nodów
pvesh get /nodes/<node>/lxc                         # lista LXC na nodzie
pvesh get /nodes/<node>/qemu                        # lista VM na nodzie
pvesh get /nodes/<node>/storage                     # storage na nodzie
pvesh get /nodes/<node>/tasks --limit 10            # ostatnie zadania
```

---

## Przydatne ścieżki

| Ścieżka | Co tam jest |
|---------|-------------|
| `/etc/pve/` | Konfiguracja klastra (nodes, storage, users) |
| `/etc/pve/storage.cfg` | Konfiguracja storage |
| `/etc/pve/nodes/<node>/` | Konfiguracja konkretnego noda |
| `/var/lib/vz/` | Domyślna lokalizacja danych LXC/VM |
| `/opt/lxc-data/` | Bind mounty danych LXC (twoja konwencja) |
| `/var/log/pve/` | Logi Proxmox |
| `/usr/local/bin/` | Twoje skrypty (backup, monitoring) |