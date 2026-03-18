# Przygotowanie Hosta Proxmox do wykonania skryptu `proxmox_backup_msmtp.sh`

### 1. Zainstaluj `msmtp` i `mailutils` na **Proxmox host**
```bash
apt update
apt install -y msmtp msmtp-mta mailutils
```

### 2. Konfiguracja `/etc/msmtprc`

Edytuj `/etc/msmtprc` i wklej (przykład Gmail App Password):

```bash
defaults
auth on
tls on
tls_trust_file /etc/ssl/certs/ca-certificates.crt
logfile /var/log/msmtp.log

account default
host smtp.gmail.com
port 587
from admin@twojadomena.pl
user admin@twojadomena.pl
password "TWOJE_HASLO_APP"

chmod 600 /etc/msmtprc
```

#### Test:

```bash
echo "Test msmtp" | msmtp -a default admin@twojadomena.pl
```

### 3. Skrypt backupu (pełny — zapisz jako `/usr/local/bin/proxmox_backup_msmtp.sh`)

> [!IMPORTANT]
> Plik skryptu v3 znajduje się w Repo

1. Wklej cały skrypt (dostosowany do Twojego storage nazwa: `hdd-storage` lub `/mnt/hdd-data`). Poniżej finalna wersja (dostosuj **STORAGE** do nazwy storage w Proxmox GUI — jeżeli dodałeś `/mnt/hdd-data`, nazwa storage mogła być np. `hdd-data` w GUI; użyj tej nazwy)

2.  Dostosuj: `STORAGE="hdd-data"` na nazwę, którą dodałeś w Proxmox GUI; jeśli używasz `/mnt/hdd-data`, w GUI prawdopodobnie nazwa storage to `hdd-data`.

Nadaj prawa:

```bash
chmod +x /usr/local/bin/proxmox_backup_msmtp.sh
```

### 4. Cron: uruchamianie codziennie

Edytuj crontab:

```bash
crontab -e
```

dodaj:
```bash
0 2 * * * /usr/local/bin/proxmox_backup_msmtp.sh >> /var/log/proxmox_backup/cron.log 2>&1
```

### 5. Ręczny test

Uruchom skrypt ręcznie i sprawdź mail:

```bash
/usr/local/bin/proxmox_backup_msmtp.sh
```

sprawdź `/var/log/proxmox_backup/*.log` i `/var/log/msmtp.log`
