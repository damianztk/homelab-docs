# Szablon tworzenia LXC (Alpine)


## 1. Przygotowanie hosta (Proxmox CLI)

### Tworzenie folderu na dane

```bash
mkdir -p /var/lib/vz/xxx-data
```

### nadanie uprawnień dla tego folderu

```bash
chown -R 100000:100000 /var/lib/vz/xxx-data
```


## 2. Komenda do stworzenia LXC:

```bash
TEMPLATE="local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz"

pct create XXX $TEMPLATE \ # zastąpić xxx numerem ID kontenera
  --hostname xxx \ # zastąpić xxx nazwą hosta
  --tags "tag1;tag2" # Ustawić tagi odpowiednie dla usługi.
  --unprivileged 1 \
  --cores 1 \ #zrewidować
  --memory 512 \ #zrewidować
  --swap 512 \ #zrewidować
  --rootfs local-lvm:2 \
  --net0 name=eth0,bridge=vmbr0,ip=10.100.20.xxx/24,gw=10.100.20.254 \ # Zastąpić xxx numerem adresu IP
  --onboot 1 \
  --password HASLO # Wybrać silne hasło
```


## 3. Podpięcie xxx-data jako Bind Mount:

```bash
pct set XXX -mp0 /var/lib/vz/xxx-data,mp=/data # (lub mp=/app/data - zależnie od aplikacji!!!) zastąpić xxx numerem kontenera.
```
