# Cron — Składnia

## Format

```
* * * * * komenda
│ │ │ │ │
│ │ │ │ └── dzień tygodnia (0-7, 0 i 7 = niedziela)
│ │ │ └──── miesiąc (1-12)
│ │ └────── dzień miesiąca (1-31)
│ └──────── godzina (0-23)
└────────── minuta (0-59)
```

---

## Przykłady

```bash
# Co minutę
* * * * * /skrypt.sh

# Co godzinę (o pełnej godzinie)
0 * * * * /skrypt.sh

# Codziennie o 3:30 w nocy
30 3 * * * /skrypt.sh

# Co czwartek o 2:00 (twój rsync backup)
0 2 * * 4 /usr/local/bin/rsync-hdd-backup.sh

# Co tydzień w niedzielę o północy
0 0 * * 0 /skrypt.sh

# Pierwszego dnia każdego miesiąca o 4:00
0 4 1 * * /skrypt.sh

# Co 15 minut
*/15 * * * * /skrypt.sh

# Co 6 godzin
0 */6 * * * /skrypt.sh

# Od poniedziałku do piątku o 8:00
0 8 * * 1-5 /skrypt.sh
```

---

## Wartości specjalne

| Wartość | Znaczenie |
|---------|-----------|
| `*` | każda wartość |
| `*/n` | co n jednostek |
| `n-m` | zakres od n do m |
| `n,m` | konkretne wartości |

---

## Skróty (@)

```bash
@reboot     # przy każdym uruchomieniu systemu
@hourly     # co godzinę = 0 * * * *
@daily      # codziennie = 0 0 * * *
@weekly     # co tydzień = 0 0 * * 0
@monthly    # co miesiąc = 0 0 1 * *
```

---

## Zarządzanie crontabem

```bash
crontab -e          # edytuj crontab aktualnego użytkownika
crontab -l          # pokaż aktualny crontab
crontab -r          # usuń crontab (OSTROŻNIE)
crontab -u root -e  # edytuj crontab konkretnego użytkownika

# Systemowe crony (dla usług/skryptów root)
/etc/cron.d/        # pliki cron dla konkretnych usług
/etc/crontab        # systemowy crontab
```

---

## Logi i debugowanie

```bash
# Sprawdź czy cron działa
systemctl status cron

# Logi wykonania cronów
grep CRON /var/log/syslog
journalctl -u cron

# Przekierowanie wyjścia skryptu do logu
0 3 * * * /usr/local/bin/skrypt.sh >> /var/log/skrypt.log 2>&1
#                                                          └── stderr też do pliku
```

---

## Przydatne narzędzie

**crontab.guru** — wklej wyrażenie cron i zobaczysz kiedy się uruchomi:
`https://crontab.guru`