# LXC Data Migration to /opt/lxc-data

> 🇵🇱 [Polski](#-polski) | 🇬🇧 [English](#-english) | 🇩🇪 [Deutsch](#-deutsch)

---

# 🇵🇱 POLSKI

## Migracja danych LXC do /opt/lxc-data

> Ten poradnik używa NPM (ID 104) jako przykładu. Dostosuj ID kontenera i ścieżki dla innych usług.

> **Uwaga — LVM-thin vs Directory storage:**
> Jeśli kontener jest na **local-lvm** (LVM-thin), rootfs pod `/var/lib/lxc/104/rootfs/`
> jest blokowym device i nie jest widoczny bez wcześniejszego zamontowania.
> Wymagane są dodatkowe kroki `pct mount` przed kopiowaniem i `pct unmount` po.
> Dla **Directory storage** (`local`, HDD directory) rootfs jest zawsze dostępny
> i kroki mount/unmount można pominąć.

### 1. Zatrzymaj kontener
```bash
pct stop 104
```

### 2. Utwórz katalogi docelowe i nadaj uprawnienia
```bash
mkdir -p /opt/lxc-data/npm-data/data
mkdir -p /opt/lxc-data/npm-data/letsencrypt
chown -R 100000:100000 /opt/lxc-data/npm-data/
```
> `chown` musi być przed kopiowaniem — `cp -a` zachowuje uprawnienia plików,
> ale nie nadpisze uprawnień katalogu-rodzica jeśli już istnieje jako root:root.

### 3. Zamontuj rootfs kontenera (tylko LVM-thin)
```bash
pct mount 104
```
> Montuje blokowy device kontenera pod `/var/lib/lxc/104/rootfs/`.
> Bez tego kroku katalog jest pusty.

### 4. Skopiuj dane
```bash
cp -a /var/lib/lxc/104/rootfs/data/. /opt/lxc-data/npm-data/data/
cp -a /var/lib/lxc/104/rootfs/etc/letsencrypt/. /opt/lxc-data/npm-data/letsencrypt/
```
> `.` zamiast `/*` — łapie również dotfiles (pliki zaczynające się od kropki).

### 5. Weryfikacja — waga
```bash
du -sh /var/lib/lxc/104/rootfs/data/
du -sh /opt/lxc-data/npm-data/data/

du -sh /var/lib/lxc/104/rootfs/etc/letsencrypt/
du -sh /opt/lxc-data/npm-data/letsencrypt/
```
> Wartości muszą być identyczne. Jeśli nie są — wróć do kroku 4.

### 6. Weryfikacja — uprawnienia
```bash
ls -la /opt/lxc-data/npm-data/data/
ls -la /opt/lxc-data/npm-data/letsencrypt/
```
> Właściciel plików powinien być `100000:100000`.

### 7. Weryfikacja — zawartość
```bash
diff -r /var/lib/lxc/104/rootfs/data/ /opt/lxc-data/npm-data/data/
diff -r /var/lib/lxc/104/rootfs/etc/letsencrypt/ /opt/lxc-data/npm-data/letsencrypt/
```
> Brak outputu = katalogi są identyczne. Jeśli diff coś wypisuje — **NIE IDŹ DALEJ**.

### 8. Usuń stare dane z rootfs i odmontuj
```bash
find /var/lib/lxc/104/rootfs/data/ -mindepth 1 -delete
find /var/lib/lxc/104/rootfs/etc/letsencrypt/ -mindepth 1 -delete

pct unmount 104
```
> `find -mindepth 1 -delete` usuwa całą zawartość (włącznie z dotfiles),
> ale zostawia sam katalog z oryginalnymi uprawnieniami.
> `pct unmount` dopiero po usunięciu — nie wcześniej.

### 9. Skonfiguruj bind mounty
```bash
pct set 104 -mp0 /opt/lxc-data/npm-data/data,mp=/data
pct set 104 -mp1 /opt/lxc-data/npm-data/letsencrypt,mp=/etc/letsencrypt
```

### 10. Zweryfikuj konfigurację kontenera
```bash
pct config 104
```
> Output musi zawierać linie `mp0` i `mp1`. Jeśli ich nie ma — **NIE STARTUJ** kontenera,
> wróć do kroku 9 i sprawdź składnię.

### 11. Start
```bash
pct start 104
```

---

### Wnioski — incydent z Tailscale

Prawdopodobna przyczyna utraty stanu: `cp -a ./*` przy kopiowaniu użyło globu `/*`
który pominął dotfiles — katalog docelowy był niekompletny zanim w ogóle doszło do usuwania.
Tailscale wystartował z pustym katalogiem stanu i wygenerował nowy `.state`.

**Zasada na przyszłość:** zawsze używaj `.` zamiast `/*` przy `cp -a` i `find -mindepth 1 -delete` zamiast `rm -rf *` przy czyszczeniu.

---

# 🇬🇧 ENGLISH

> 🇵🇱 [Polski](#-polski) | 🇬🇧 [English](#-english) | 🇩🇪 [Deutsch](#-deutsch)

## LXC Data Migration to /opt/lxc-data

> This guide uses NPM (ID 104) as an example. Adjust the container ID and paths for other services.

> **Note — LVM-thin vs Directory storage:**
> If the container is on **local-lvm** (LVM-thin), the rootfs at `/var/lib/lxc/104/rootfs/`
> is a block device and is not visible without mounting it first.
> Steps `pct mount` and `pct unmount` are required.
> For **Directory storage** (`local`, HDD directory) rootfs is always accessible
> and mount/unmount steps can be skipped.

### 1. Stop the container
```bash
pct stop 104
```

### 2. Create target directories and set permissions
```bash
mkdir -p /opt/lxc-data/npm-data/data
mkdir -p /opt/lxc-data/npm-data/letsencrypt
chown -R 100000:100000 /opt/lxc-data/npm-data/
```
> `chown` must happen before copying — `cp -a` preserves file permissions
> but will not overwrite the parent directory owner if it already exists as root:root.

### 3. Mount container rootfs (LVM-thin only)
```bash
pct mount 104
```
> Mounts the container block device at `/var/lib/lxc/104/rootfs/`.
> Without this step the directory is empty.

### 4. Copy data
```bash
cp -a /var/lib/lxc/104/rootfs/data/. /opt/lxc-data/npm-data/data/
cp -a /var/lib/lxc/104/rootfs/etc/letsencrypt/. /opt/lxc-data/npm-data/letsencrypt/
```
> `.` instead of `/*` — also captures dotfiles (files starting with a dot).

### 5. Verify — size
```bash
du -sh /var/lib/lxc/104/rootfs/data/
du -sh /opt/lxc-data/npm-data/data/

du -sh /var/lib/lxc/104/rootfs/etc/letsencrypt/
du -sh /opt/lxc-data/npm-data/letsencrypt/
```
> Values must be identical. If not — go back to step 4.

### 6. Verify — permissions
```bash
ls -la /opt/lxc-data/npm-data/data/
ls -la /opt/lxc-data/npm-data/letsencrypt/
```
> File owner must be `100000:100000`.

### 7. Verify — contents
```bash
diff -r /var/lib/lxc/104/rootfs/data/ /opt/lxc-data/npm-data/data/
diff -r /var/lib/lxc/104/rootfs/etc/letsencrypt/ /opt/lxc-data/npm-data/letsencrypt/
```
> No output = directories are identical. If diff prints anything — **DO NOT CONTINUE**.

### 8. Delete old data from rootfs and unmount
```bash
find /var/lib/lxc/104/rootfs/data/ -mindepth 1 -delete
find /var/lib/lxc/104/rootfs/etc/letsencrypt/ -mindepth 1 -delete

pct unmount 104
```
> `find -mindepth 1 -delete` removes all contents (including dotfiles)
> but keeps the directory itself with its original permissions.
> `pct unmount` only after deletion — not before.

### 9. Configure bind mounts
```bash
pct set 104 -mp0 /opt/lxc-data/npm-data/data,mp=/data
pct set 104 -mp1 /opt/lxc-data/npm-data/letsencrypt,mp=/etc/letsencrypt
```

### 10. Verify container config
```bash
pct config 104
```
> Output must contain `mp0` and `mp1` lines. If not — **DO NOT START** the container,
> go back to step 9 and check the syntax.

### 11. Start
```bash
pct start 104
```

---

### Lessons learned — Tailscale incident

Probable cause of state loss: `cp -a ./*` used the glob `/*` which silently skipped dotfiles —
the target directory was incomplete before any deletion even took place.
Tailscale started with an empty state directory and generated a new `.state` file.

**Rule:** always use `.` instead of `/*` with `cp -a`, and `find -mindepth 1 -delete` instead of `rm -rf *` when cleaning up.

---

# 🇩🇪 DEUTSCH

> 🇵🇱 [Polski](#-polski) | 🇬🇧 [English](#-english) | 🇩🇪 [Deutsch](#-deutsch)

## LXC-Datenmigration nach /opt/lxc-data

> Diese Anleitung verwendet NPM (ID 104) als Beispiel. Container-ID und Pfade für andere Dienste anpassen.

> **Hinweis — LVM-thin vs. Directory-Storage:**
> Wenn der Container auf **local-lvm** (LVM-thin) liegt, ist das rootfs unter `/var/lib/lxc/104/rootfs/`
> ein Block-Device und ohne vorheriges Mounten nicht sichtbar.
> Die Schritte `pct mount` und `pct unmount` sind erforderlich.
> Bei **Directory-Storage** (`local`, HDD-Verzeichnis) ist das rootfs immer zugänglich
> und die Mount/Unmount-Schritte können übersprungen werden.

### 1. Container stoppen
```bash
pct stop 104
```

### 2. Zielverzeichnisse erstellen und Berechtigungen setzen
```bash
mkdir -p /opt/lxc-data/npm-data/data
mkdir -p /opt/lxc-data/npm-data/letsencrypt
chown -R 100000:100000 /opt/lxc-data/npm-data/
```
> `chown` muss vor dem Kopieren erfolgen — `cp -a` bewahrt Dateirechte,
> überschreibt jedoch nicht die Rechte des übergeordneten Verzeichnisses, wenn es bereits root:root gehört.

### 3. Container-rootfs mounten (nur LVM-thin)
```bash
pct mount 104
```
> Mountet das Block-Device des Containers unter `/var/lib/lxc/104/rootfs/`.
> Ohne diesen Schritt ist das Verzeichnis leer.

### 4. Daten kopieren
```bash
cp -a /var/lib/lxc/104/rootfs/data/. /opt/lxc-data/npm-data/data/
cp -a /var/lib/lxc/104/rootfs/etc/letsencrypt/. /opt/lxc-data/npm-data/letsencrypt/
```
> `.` statt `/*` — erfasst auch Dotfiles (Dateien, die mit einem Punkt beginnen).

### 5. Überprüfung — Größe
```bash
du -sh /var/lib/lxc/104/rootfs/data/
du -sh /opt/lxc-data/npm-data/data/

du -sh /var/lib/lxc/104/rootfs/etc/letsencrypt/
du -sh /opt/lxc-data/npm-data/letsencrypt/
```
> Die Werte müssen identisch sein. Falls nicht — zurück zu Schritt 4.

### 6. Überprüfung — Berechtigungen
```bash
ls -la /opt/lxc-data/npm-data/data/
ls -la /opt/lxc-data/npm-data/letsencrypt/
```
> Der Dateibesitzer muss `100000:100000` sein.

### 7. Überprüfung — Inhalt
```bash
diff -r /var/lib/lxc/104/rootfs/data/ /opt/lxc-data/npm-data/data/
diff -r /var/lib/lxc/104/rootfs/etc/letsencrypt/ /opt/lxc-data/npm-data/letsencrypt/
```
> Keine Ausgabe = Verzeichnisse sind identisch. Wenn diff etwas ausgibt — **NICHT FORTFAHREN**.

### 8. Alte Daten aus rootfs löschen und unmounten
```bash
find /var/lib/lxc/104/rootfs/data/ -mindepth 1 -delete
find /var/lib/lxc/104/rootfs/etc/letsencrypt/ -mindepth 1 -delete

pct unmount 104
```
> `find -mindepth 1 -delete` löscht den gesamten Inhalt (einschließlich Dotfiles),
> lässt aber das Verzeichnis selbst mit seinen ursprünglichen Rechten bestehen.
> `pct unmount` erst nach dem Löschen — nicht vorher.

### 9. Bind-Mounts konfigurieren
```bash
pct set 104 -mp0 /opt/lxc-data/npm-data/data,mp=/data
pct set 104 -mp1 /opt/lxc-data/npm-data/letsencrypt,mp=/etc/letsencrypt
```

### 10. Container-Konfiguration überprüfen
```bash
pct config 104
```
> Die Ausgabe muss `mp0`- und `mp1`-Zeilen enthalten. Falls nicht — Container **NICHT STARTEN**,
> zurück zu Schritt 9 und Syntax prüfen.

### 11. Start
```bash
pct start 104
```

---

### Lessons learned — Tailscale-Vorfall

Wahrscheinliche Ursache des Statusverlusts: `cp -a ./*` verwendete den Glob `/*`, der Dotfiles
stillschweigend übersah — das Zielverzeichnis war unvollständig, bevor überhaupt mit dem Löschen
begonnen wurde. Tailscale startete mit einem leeren Statusverzeichnis und erstellte eine neue `.state`-Datei.

**Regel:** Immer `.` statt `/*` bei `cp -a` verwenden und `find -mindepth 1 -delete` statt `rm -rf *` beim Bereinigen.
