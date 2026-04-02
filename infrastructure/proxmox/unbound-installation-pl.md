# Unbound — Instalacja i konfiguracja jako DNS Resolver dla AdGuard Home

> **Środowisko:** Debian 13.3  
> **Cel:** Instalacja Unbound jako lokalnego DNS resolvera działającego pod AdGuard Home  
> **Dotyczy:**
> - 🖥️ **Wyse** — DELL Wyse 3040 (Intel Atom, 2GB RAM, 16GB eMMC) — główna instancja AGH
> - 📦 **LXC** — LXC Debian na Proxmox Node 1 (1GB RAM, 6GB storage) — replika AGH

---

## Spis treści

1. [Koncepcja](#1-koncepcja)
2. [Instalacja Unbound](#2-instalacja-unbound)
3. [Root Hints](#3-root-hints)
4. [Root Key (DNSSEC)](#4-root-key-dnssec)
5. [Konfiguracja](#5-konfiguracja)
6. [Uruchomienie i weryfikacja](#6-uruchomienie-i-weryfikacja)
7. [Konfiguracja AdGuard Home](#7-konfiguracja-adguard-home)
8. [Różnice między maszynami](#różnice-między-maszynami)

---

## 1. Koncepcja

Domyślnie AdGuard Home wysyła zapytania DNS do zewnętrznych resolverów (np. `8.8.8.8`, `1.1.1.1`). Oznacza to, że dostawca resolvera widzi Twoje zapytania.

Unbound rozwiązuje ten problem działając jako **rekurencyjny resolver** — sam odpytuje kolejno serwery root, TLD i autorytatywne, bez udziału pośredników. AGH nadal blokuje reklamy i trackery, ale zapytania które go przejdą trafiają do Unbounda zamiast do zewnętrznego DNS.

```
Klient → AdGuard Home (blokowanie) → Unbound (127.0.0.1:5335) → Root Servers → ...
```

---

## 2. Instalacja Unbound

```bash
apt update && apt install unbound -y
```

Sprawdź czy usługa się uruchomiła:

```bash
systemctl status unbound
```

> ℹ️ Na tym etapie Unbound może zgłaszać błędy konfiguracji — to normalne, domyślny plik konfiguracyjny zostanie zastąpiony w kolejnych krokach.

---

## 3. Root Hints

Root hints to lista adresów głównych serwerów DNS (root servers). Unbound używa ich jako punktu startowego do rekurencyjnego rozwiązywania zapytań. Plik wymaga okresowego odświeżania (raz na kilka miesięcy wystarczy).

Pobierz aktualny plik:

```bash
curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
```

Sprawdź czy plik istnieje:

```bash
ls -la /var/lib/unbound/root.hints
```

---

## 4. Root Key (DNSSEC)

Plik `root.key` zawiera główny trust anchor DNSSEC — klucz publiczny, którym Unbound weryfikuje podpisy rekordów DNS. Unbound aktualizuje go automatycznie przy każdym starcie (jeśli dyrektywa `auto-trust-anchor-file` jest ustawiona w konfiguracji).

Sprawdź czy plik już istnieje:

```bash
ls -la /var/lib/unbound/root.key
```

Jeśli nie istnieje, wygeneruj go:

```bash
unbound-anchor -a /var/lib/unbound/root.key
```

> ⚠️ Polecenie `unbound-anchor` zwraca kod wyjścia `1` przy pierwszym uruchomieniu — to **normalne** i oznacza że klucz został świeżo pobrany, nie zaktualizowany. Nie jest to błąd.

Upewnij się że właścicielem pliku jest `unbound`:

```bash
chown unbound:unbound /var/lib/unbound/root.key
```

Sprawdź uprawnienia — powinny wyglądać tak:

```
-rw-r--r-- 1 unbound unbound 1248 ... /var/lib/unbound/root.key
```

> ℹ️ Unbound potrzebuje dostępu **do zapisu** (nie tylko odczytu) żeby móc aktualizować klucz. Jeśli kiedykolwiek odtwarzasz plik z backupu lub kopiujesz go ręcznie — zawsze sprawdź właściciela przez `chown unbound:unbound`.

---

## 5. Konfiguracja

Utwórz nowy plik konfiguracyjny (zastąpi domyślny):

```bash
nano /etc/unbound/unbound.conf.d/local.conf
```

### 🖥️ Wyse (2GB RAM — większy cache)

```conf
server:
    # --- Nasłuch i podstawy ---
    verbosity: 0
    interface: 127.0.0.1
    port: 5335
    do-ip4: yes
    do-udp: yes
    do-tcp: yes
    do-ip6: no
    prefer-ip6: no

    # --- Plik Root Hints i DNSSEC ---
    root-hints: "/var/lib/unbound/root.hints"
    auto-trust-anchor-file: "/var/lib/unbound/root.key"

    # --- Bezpieczeństwo i ukrywanie tożsamości ---
    hide-identity: yes
    hide-version: yes

    # --- Zabezpieczenia DNSSEC ---
    harden-glue: yes
    harden-dnssec-stripped: yes
    harden-referral-path: yes
    unwanted-reply-threshold: 10000
    use-caps-for-id: yes

    # --- Prefetching ---
    prefetch: yes
    prefetch-key: yes

    # --- Tuning wydajności (Intel Atom, 2GB RAM) ---
    num-threads: 1
    edns-buffer-size: 1232
    so-rcvbuf: 1m
    so-sndbuf: 1m

    # --- Cache ---
    msg-cache-size: 32m
    rrset-cache-size: 64m
    neg-cache-size: 8m

    # --- Ochrona przed DNS Rebinding ---
    private-address: 192.168.0.0/16
    private-address: 169.254.0.0/16
    private-address: 172.16.0.0/12
    private-address: 10.0.0.0/8
    private-address: fd00::/8
    private-address: fe80::/10

    # --- Kontrola dostępu ---
    access-control: 127.0.0.0/8 allow
```

### 📦 LXC (1GB RAM — zachowawczy cache)

```conf
server:
    # --- Nasłuch i podstawy ---
    verbosity: 0
    interface: 127.0.0.1
    port: 5335
    do-ip4: yes
    do-udp: yes
    do-tcp: yes
    do-ip6: no
    prefer-ip6: no

    # --- Plik Root Hints i DNSSEC ---
    root-hints: "/var/lib/unbound/root.hints"
    auto-trust-anchor-file: "/var/lib/unbound/root.key"

    # --- Bezpieczeństwo i ukrywanie tożsamości ---
    hide-identity: yes
    hide-version: yes

    # --- Zabezpieczenia DNSSEC ---
    harden-glue: yes
    harden-dnssec-stripped: yes
    harden-referral-path: yes
    unwanted-reply-threshold: 10000
    use-caps-for-id: yes

    # --- Prefetching ---
    prefetch: yes
    prefetch-key: yes

    # --- Tuning wydajności (LXC, 1GB RAM) ---
    num-threads: 1
    edns-buffer-size: 1232
    so-rcvbuf: 1m
    so-sndbuf: 1m

    # --- Cache ---
    msg-cache-size: 16m
    rrset-cache-size: 32m
    neg-cache-size: 4m

    # --- Ochrona przed DNS Rebinding ---
    private-address: 192.168.0.0/16
    private-address: 169.254.0.0/16
    private-address: 172.16.0.0/12
    private-address: 10.0.0.0/8
    private-address: fd00::/8
    private-address: fe80::/10

    # --- Kontrola dostępu ---
    access-control: 127.0.0.0/8 allow
```

---

## 6. Uruchomienie i weryfikacja

Przed restartem sprawdź składnię konfiguracji:

```bash
unbound-checkconf
```

Powinno zwrócić:
```
unbound-checkconf: no errors in /etc/unbound/unbound.conf
```

Zrestartuj Unbound:

```bash
systemctl restart unbound
systemctl status unbound
```

Przetestuj czy Unbound odpowiada na porcie 5335:

```bash
dig google.com @127.0.0.1 -p 5335
```

W odpowiedzi powinieneś zobaczyć sekcję `ANSWER SECTION` z adresem IP oraz flagę `NOERROR` w nagłówku.

Przetestuj DNSSEC (zapytanie o domenę z podpisem):

```bash
dig sigok.verteiltesysteme.net @127.0.0.1 -p 5335
```

Odpowiedź powinna zawierać flagę `ad` (Authenticated Data) w nagłówku — oznacza to że DNSSEC działa poprawnie.

---

## 7. Konfiguracja AdGuard Home

Po uruchomieniu Unbound wskaż go jako upstream DNS w AdGuard Home:

1. Otwórz panel AGH → **Ustawienia** → **Ustawienia DNS**
2. W sekcji **Upstream DNS servers** wpisz:
   ```
   127.0.0.1:5335
   ```
3. Usuń wszystkie inne upstream serwery (np. `8.8.8.8`, `1.1.1.1`)
4. Kliknij **Testuj upstreams** — powinno zwrócić `OK`
5. Zapisz ustawienia

---

## Różnice między maszynami

| | 🖥️ Wyse 3040 | 📦 LXC Proxmox |
|---|---|---|
| RAM | 2GB | 1GB |
| `msg-cache-size` | 32m | 16m |
| `rrset-cache-size` | 64m | 32m |
| `neg-cache-size` | 8m | 4m |
| Rola AGH | Główna instancja | Replika (adguardhome-sync) |

Wszystkie pozostałe parametry konfiguracji są identyczne.

---

## Odświeżanie Root Hints

Plik `root.hints` warto odświeżać co kilka miesięcy. Możesz to zrobić ręcznie:

```bash
curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root
systemctl restart unbound
```

Lub zautomatyzować przez cron — np. raz na kwartał:

```bash
crontab -e
```

```
0 3 1 */3 * curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.root && systemctl restart unbound
```

---

*Dokumentacja wygenerowana na podstawie konfiguracji przeprowadzonej w kwietniu 2026.*