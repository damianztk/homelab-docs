# **🛠️ Procedura Migracji Danych Docker**

**Usługa:** Uptime Kuma (przykład referencyjny)

**Cel:** Separacja logiki (`docker-compose.yml`) od danych persistent (`/opt/docker-data/`) w celu ujednolicenia architektury i przygotowania środowiska pod zautomatyzowane backupy.

## **🛑 Krok 1: Inicjalizacja struktury docelowej**

Tworzymy ustandaryzowane miejsce na dane aplikacji, odzwierciedlające strukturę z folderu domowego.

> Tworzenie kompletnej ścieżki docelowej:
```bash
sudo mkdir -p /opt/docker-data/uptime-kuma/kuma-data
```

## **⏸️ Krok 2: Zatrzymanie kontenera (Cold State)**

> [!IMPORTANT]
> **Zawsze przenosimy dane w stanie spoczynku, aby uniknąć uszkodzenia bazy (np. SQLite).**

 Przechodzimy do oryginalnego folderu z logiką aplikacji:

```bash
cd /home/damian/docker/uptime-kuma  
docker compose stop
```

## **📦 Krok 3: Kopiowanie absolutne**

**Kopiujemy zawartość oryginalnego katalogu z danymi.**
> [!IMPORTANT]
> **Kluczowe:** używamy kropki `.` na końcu ścieżki źródłowej, aby skopiować również wszystkie ukryte pliki (dotfiles).

Kopiowanie z zachowaniem atrybutów, uprawnień i ukrytych plików  

```bash
sudo cp -a /home/damian/docker/uptime-kuma/kuma-data/. /opt/docker-data/uptime-kuma/kuma-data/
```

## **🔍 Krok 4: Rygorystyczna Weryfikacja (Metoda Paranoika)**

> [!IMPORTANT]
> **Zanim dotkniemy czegokolwiek w konfiguracji, musimy mieć matematyczną pewność, że dane są tożsame.**

1. Weryfikacja wizualna i uprawnień  
```bash
ls -la /home/damian/docker/uptime-kuma/kuma-data/  
ls -la /opt/docker-data/uptime-kuma/kuma-data/
```

2. Weryfikacja wagi (rozmiar musi być identyczny)  
```bash
du -sh /home/damian/docker/uptime-kuma/kuma-data/  
du -sh /opt/docker-data/uptime-kuma/kuma-data/
```

3. Weryfikacja binarna (Ostateczny test)  
> Jeśli komenda nie zwróci żadnego wyniku (pusta linia) = SUKCES  

```bash
diff -r /home/damian/docker/uptime-kuma/kuma-data/ /opt/docker-data/uptime-kuma/kuma-data/
```

## **⚙️ Krok 5: Aktualizacja Logiki (YAML)**

Plik `docker-compose.yml` pozostaje w **oryginalnej** lokalizacji (`/home/damian/docker/uptime-kuma/`). Edytujemy go, aby wskazywał nową ścieżkę absolutną.

```bash
nano /home/damian/docker/uptime-kuma/docker-compose.yml
```

**Zmień sekcję volumes:**

*Przed zmianą (ścieżka relatywna):*
```bash
     volumes:  
      - ./kuma-data:/app/data
```

*Po zmianie (ścieżka stała):*
```bash
    volumes:  
      - /opt/docker-data/uptime-kuma/kuma-data:/app/data
```

## **Krok 5,5: UPRAWNIENIA**

Zanim wpiszesz `docker compose up -d`, upewnij się, że folder w `/opt/` ma właściwego właściciela. Masz dwie drogi:

- Opcja A: Standardowa (Najczęstsza w Dockerze)
Docker sam zadba o pliki wewnątrz, jeśli folder nadrzędny pozwoli mu tam wejść.

```Bash
sudo chown -R root:root /opt/docker-data/uptime-kuma/
sudo chmod -R 755 /opt/docker-data/uptime-kuma/
```

- Opcja B: Jeśli Kuma rzuci błędem "Permission Denied"
Niektóre kontenery (jak Uptime Kuma) preferują konkretnego użytkownika. Jeśli po starcie logi (docker compose logs) pokażą błąd uprawnień, wykonaj:

```Bash
sudo chown -R 1000:1000 /opt/docker-data/uptime-kuma/kuma-data/
```

> W Dockerze 1000:1000 to zazwyczaj pierwszy użytkownik w systemie – czyli Ty, Damian.


## **🚀 Krok 6: Start i Walidacja Usługi**

Podnosimy kontener z nowym mapowaniem.
```bash

docker compose up -d
```

**Po uruchomieniu kontenera Wejdź na stronę usługi przez przeglądarkę i upewnij się, że wszystkie monitory, logi i ustawienia są na swoim miejscu.**

## **🛡️ Krok 7: Kwarantanna starych danych**

Jeśli usługa wstała poprawnie, zmieniamy nazwę oryginalnego folderu z danymi, zabezpieczając go przed przypadkowym użyciem, ale jeszcze nie kasując.

> Zmiana nazwy katalogu w `/home/damian/docker/uptime-kuma/`  

```bash
mv kuma-data kuma-data-old
```

## **⏰ Krok 8: Harmonogram Usunięcia (Zadanie Manualne)**

Ustaw przypomnienie w kalendarzu w telefonie/systemie:

* **Tytuł:** Usunąć stare dane Uptime Kuma z Della Wyse  
* **Kiedy:** Równo za 72 godziny (3 dni) od wykonania Kroku 7\.

## **🗑️ Krok 9: Ostateczne czyszczenie (Po 72h)**

Jeśli przez 3 dni usługa działała stabilnie (żadnych błędów z bazą, uprawnieniami itp.), wykonujemy ostateczne czyszczenie serwera.

> Usuwamy bezpowrotnie starą strukturę  

```bash
rm -rf /home/damian/docker/uptime-kuma/kuma-data-old
```

### END