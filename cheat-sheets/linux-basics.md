# Linux — Podstawy

## Nawigacja i pliki

```bash
pwd                         # pokaż aktualny katalog
ls -la                      # lista plików (wszystkie + szczegóły)
cd /ścieżka                 # przejdź do katalogu
cd ..                       # przejdź poziom wyżej
cd ~                        # przejdź do katalogu domowego

cp -a źródło/ cel/          # kopiuj rekurencyjnie (zachowuje uprawnienia)
mv źródło cel               # przenieś lub zmień nazwę
rm plik                     # usuń plik
rm -rf katalog/             # usuń katalog rekurencyjnie (OSTROŻNIE)

# UWAGA na globy:
# cp źródło/* cel/          ← pomija dotfiles (.bashrc, .config itd.)
# cp -a źródło/. cel/       ← kopiuje WSZYSTKO włącznie z dotfiles ✓
```

---

## chmod — uprawnienia

Format: `chmod [uprawnienia] plik`

```bash
# Symboliczny
chmod +x skrypt.sh          # dodaj prawo do wykonania
chmod 755 skrypt.sh         # rwxr-xr-x (właściciel: wszystko, reszta: czyt+wyk)
chmod 644 plik.conf         # rw-r--r-- (właściciel: czyt+zapis, reszta: czyt)
chmod -R 755 katalog/       # rekurencyjnie

# Tabela wartości
# 7 = rwx (czyt + zapis + wykonanie)
# 6 = rw- (czyt + zapis)
# 5 = r-x (czyt + wykonanie)
# 4 = r-- (tylko czyt)
# 0 = --- (brak)
```

Trzy cyfry = [właściciel][grupa][pozostali]

---

## chown — właściciel

```bash
chown użytkownik plik
chown użytkownik:grupa plik
chown -R użytkownik:grupa katalog/   # rekurencyjnie

# W kontekście Proxmox LXC (UID mapping):
# UID 0 wewnątrz LXC = UID 100000 na hoście
# UID 1000 wewnątrz LXC = UID 101000 na hoście
chown -R 100000:100000 /opt/lxc-data/gitea-data/
```

---

## find

```bash
find /ścieżka -name "*.md"              # znajdź pliki po nazwie
find /ścieżka -type f                   # tylko pliki
find /ścieżka -type d                   # tylko katalogi
find /ścieżka -mindepth 1 -delete       # usuń zawartość katalogu (nie sam katalog)
find /ścieżka -mtime -7                 # pliki zmienione w ostatnich 7 dniach
find /ścieżka -size +100M               # pliki większe niż 100MB
```

---

## grep

```bash
grep "szukana fraza" plik
grep -r "szukana fraza" katalog/        # rekurencyjnie
grep -i "fraza" plik                    # bez rozróżniania wielkości liter
grep -n "fraza" plik                    # pokaż numery linii
grep -v "fraza" plik                    # pokaż linie BEZ frazy

# Przydatne kombinacje:
journalctl -u gitea | grep -i error
cat /var/log/syslog | grep -i "fail"
```

---

## systemctl

```bash
systemctl status usługa
systemctl start usługa
systemctl stop usługa
systemctl restart usługa
systemctl enable usługa     # uruchamiaj przy starcie systemu
systemctl disable usługa
systemctl reload usługa     # przeładuj konfigurację bez restartu

journalctl -u usługa        # logi usługi
journalctl -u usługa -f     # logi na żywo (follow)
journalctl -u usługa --since "1 hour ago"
```

---

## Sieć

```bash
ip a                        # interfejsy sieciowe i IP
ip r                        # tablica routingu
ping -c 4 8.8.8.8
curl -I https://adres.url   # sprawdź odpowiedź HTTP
dig domena.pl               # zapytanie DNS
dig @10.100.30.1 domena.pl  # zapytanie DNS do konkretnego serwera
ss -tulnp                   # otwarte porty i nasłuchujące procesy
```

---

## Dyski i przestrzeń

```bash
df -h                       # wolne miejsce na dyskach
du -sh /ścieżka             # rozmiar katalogu
lsblk                       # lista urządzeń blokowych
mount | grep /mnt           # aktualnie zamontowane dyski
```