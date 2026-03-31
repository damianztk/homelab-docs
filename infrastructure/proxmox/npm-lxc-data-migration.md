# Migracja danych NPM (ID 104) do /opt/lxc-data — LV99 Edition
### NPM / ID 104 - to przykładowy ID LXC.

> **Uwaga — LVM-thin vs Directory storage:**
> Jeśli kontener jest na **local-lvm** (LVM-thin), rootfs pod `/var/lib/lxc/104/rootfs/`
> jest blokowym device i nie jest widoczny bez wcześniejszego zamontowania.
> Wymagane są dodatkowe kroki `pct mount` przed kopiowaniem i `pct unmount` po.
> Dla **Directory storage** (`local`, HDD directory) rootfs jest zawsze dostępny
> i kroki mount/unmount można pominąć.

## 1. Zatrzymaj kontener
```bash
pct stop 104
```

## 2. Utwórz katalogi docelowe i nadaj uprawnienia
```bash
mkdir -p /opt/lxc-data/npm-data/data
mkdir -p /opt/lxc-data/npm-data/letsencrypt
chown -R 100000:100000 /opt/lxc-data/npm-data/
```
> `chown` musi być przed kopiowaniem — `cp -a` zachowuje uprawnienia plików,
> ale nie nadpisze uprawnień katalogu-rodzica jeśli już istnieje jako root:root.

## 3. Zamontuj rootfs kontenera (tylko LVM-thin)
```bash
pct mount 104
```
> Montuje blokowy device kontenera pod `/var/lib/lxc/104/rootfs/`.
> Bez tego kroku katalog jest pusty.

## 4. Skopiuj dane
```bash
cp -a /var/lib/lxc/104/rootfs/data/. /opt/lxc-data/npm-data/data/
cp -a /var/lib/lxc/104/rootfs/etc/letsencrypt/. /opt/lxc-data/npm-data/letsencrypt/
```
> `.` zamiast `/*` — łapie również dotfiles (pliki zaczynające się od kropki).

## 5. Weryfikacja — waga
```bash
du -sh /var/lib/lxc/104/rootfs/data/
du -sh /opt/lxc-data/npm-data/data/

du -sh /var/lib/lxc/104/rootfs/etc/letsencrypt/
du -sh /opt/lxc-data/npm-data/letsencrypt/
```
> Wartości muszą być identyczne. Jeśli nie są — wróć do kroku 4.

## 6. Weryfikacja — uprawnienia
```bash
ls -la /var/lib/lxc/104/rootfs/data/
ls -la /opt/lxc-data/npm-data/data/

ls -la /var/lib/lxc/104/rootfs/letsencrypt/
ls -la /opt/lxc-data/npm-data/letsencrypt/
```
> Właściciel plików powinien być `100000:100000`.

## 7. Weryfikacja — zawartość
```bash
diff -r /var/lib/lxc/104/rootfs/data/ /opt/lxc-data/npm-data/data/
diff -r /var/lib/lxc/104/rootfs/etc/letsencrypt/ /opt/lxc-data/npm-data/letsencrypt/
```
> Brak outputu = katalogi są identyczne. Jeśli diff coś wypisuje — NIE IDŹ DALEJ.

## 8. Usuń stare dane z rootfs i odmontuj
```bash
find /var/lib/lxc/104/rootfs/data/ -mindepth 1 -delete
find /var/lib/lxc/104/rootfs/etc/letsencrypt/ -mindepth 1 -delete

pct unmount 104
```
> `find -mindepth 1 -delete` usuwa całą zawartość (włącznie z dotfiles),
> ale zostawia sam katalog z oryginalnymi uprawnieniami.
> `pct unmount` dopiero po usunięciu — nie wcześniej.

## 9. Skonfiguruj bind mounty
```bash
pct set 104 -mp0 /opt/lxc-data/npm-data/data,mp=/data
pct set 104 -mp1 /opt/lxc-data/npm-data/letsencrypt,mp=/etc/letsencrypt
```

## 10. Zweryfikuj konfigurację kontenera
```bash
pct config 104
```
> Output musi zawierać linie `mp0` i `mp1`. Jeśli ich nie ma — NIE STARTUJ kontenera,
> wróć do kroku 9 i sprawdź składnię.

## 11. Start
```bash
pct start 104
```

---

## Co poszło nie tak ostatnio (Tailscale)

Prawdopodobna przyczyna utraty stanu: `cp -a ./*` przy kopiowaniu użyło globu `/*`
który pominął dotfiles — katalog docelowy był niekompletny zanim w ogóle doszło do usuwania.
Tailscale wystartował z pustym katalogiem stanu i wygenerował nowy `.state`.

**Zasada na przyszłość:** zawsze używaj `.` zamiast `/*` przy `cp -a` i `find -mindepth 1 -delete` zamiast `rm -rf *` przy czyszczeniu.