# Szablon tworzenia LXC (Alpine)


## 1. Przygotowanie hosta (Proxmox CLI)

### Tworzenie folderu na dane

```bash
mkdir -p /opt/lxc-data/<NAZWA_APLIKACJI>-data
```

### nadanie uprawnień dla tego folderu

```bash
chown -R 100000:100000 /opt/lxc-data/<NAZWA_APLIKACJI>-data
```

#### [!TIP]
Jeśli kiedyś jakaś aplikacja (np. baza danych) będzie miała problem z zapisem mimo tego chown, sprawdź wewnątrz kontenera komendą id, czy na pewno działa jako root, czy może ma swojego dedykowanego usera (np. mysql o ID 101). Wtedy mapowanie na hoście byłoby 100101. Ale na 99% Twój szablon z 100000 zadziała dla większości usług. (Gemini)


## 2. Komenda do stworzenia LXC:

```bash
TEMPLATE="local:vztmpl/alpine-3.22-default_20250617_amd64.tar.xz"

pct create <ID> $TEMPLATE \ # zastąpić <ID> numerem ID kontenera
  --hostname <NAZWA_HOSTA> \ # zastąpić <NAZWA_HOSTA> nazwą hosta
  --tags "<TAG1>;<TAG2>" # Ustawić tagi odpowiednie dla usługi.
  --unprivileged 1 \
  --cores 1 \ # Zrewidować
  --memory 512 \ # Zrewidować
  --swap 512 \ # Zrewidować
  --rootfs local-lvm:2 \
  --net0 name=eth0,bridge=vmbr0,ip=10.100.20.<ADRES_IP>/24,gw=10.100.20.254 \ # Zastąpić <ADRES_IP> końcowym numerem adresu IP
  --onboot 1 \
  --password <HASŁO> # Wybrać silne hasło!
```


## 3. Podpięcie xxx-data jako Bind Mount:

```bash
pct set <ID> -mp0 /opt/lxc-data/<NAZWA_APLIKACJI>-data,mp=/data # (lub mp=/app/data - zależnie od aplikacji!!!) zastąpić <ID> numerem kontenera.
```
