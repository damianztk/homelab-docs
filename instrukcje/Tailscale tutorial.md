# Tailscale — od tunelu do domu do zero-trust networking

> Kompletny przewodnik po możliwościach Tailscale dla homelabu i nie tylko.  
> Napisany na bazie własnych doświadczeń z siecią opartą na Fortigate 60E, Proxmox VE 9 i VLANach.

---

## Spis treści

1. [Czym jest Tailscale i co go wyróżnia](#1-czym-jest-tailscale-i-co-go-wyróżnia)
2. [Subnet Router — brama do domowej sieci](#2-subnet-router--brama-do-domowej-sieci)
3. [Exit Node — prywatny tunel VPN z polskim IP](#3-exit-node--prywatny-tunel-vpn-z-polskim-ip)
4. [MagicDNS — nazwy zamiast adresów IP](#4-magicdns--nazwy-zamiast-adresów-ip)
5. [Certyfikaty HTTPS wewnątrz tailnetu](#5-certyfikaty-https-wewnątrz-tailnetu)
6. [Taildrop — bezpieczny transfer plików](#6-taildrop--bezpieczny-transfer-plików)
7. [ACL — serce konfiguracji zero-trust](#7-acl--serce-konfiguracji-zero-trust)
   - [Grupy użytkowników](#grupy-użytkowników)
   - [Tagi i tagOwners](#tagi-i-tagowners)
   - [Reguły dostępu](#reguły-dostępu)
   - [autoApprovers](#autoapprovers)
   - [Tailscale SSH](#tailscale-ssh)
8. [Apps i Services](#8-apps-i-services)
9. [Key Expiry i Tailscale Lock](#9-key-expiry-i-tailscale-lock)
10. [Webhooks](#10-webhooks)
11. [REST API, Auth Keys i Terraform](#11-rest-api-auth-keys-i-terraform)
12. [MFA i SSO](#12-mfa-i-sso)
13. [Praktyczna konfiguracja dla homelabu](#13-praktyczna-konfiguracja-dla-homelabu)
14. [FAQ](#14-faq)

---

## 1. Czym jest Tailscale i co go wyróżnia

Tailscale to prywatna sieć mesh oparta na **WireGuard**. Większość ludzi używa go jak zwykłego VPN — jeden serwer, reszta się łączy. Tailscale działa inaczej: każde urządzenie łączy się bezpośrednio z każdym innym, **bez centralnego punktu przez który leci cały ruch**.

To "mesh" jest kluczem. Zamiast:

```
Twój telefon → Serwer VPN → Dom
```

masz:

```
Twój telefon ←→ Dom (bezpośrednio, peer-to-peer)
```

Jeśli bezpośrednie połączenie nie jest możliwe (NAT, firewall), Tailscale używa relay serwerów (DERP), ale priorytetem zawsze jest połączenie bezpośrednie.

---

## 2. Subnet Router — brama do domowej sieci

Subnet Router to urządzenie w Twojej sieci (np. LXC na Proxmoxie), które **reprezentuje całą podsieć** w tailnecie. Inne urządzenia w tej podsieci nie muszą mieć zainstalowanego Tailscale — komunikacja idzie przez router.

### Konfiguracja

```bash
tailscale up \
  --advertise-routes=10.100.1.0/24,10.100.10.0/24,10.100.20.0/24,10.100.30.0/24,10.100.40.0/24,10.100.50.0/24,10.100.90.0/24,10.100.100.0/24 \
  --accept-routes \
  --ssh
```

> **Uwaga:** Jeśli masz już ustawione niestandardowe flagi (`--accept-routes`, `--ssh` itd.), Tailscale nie pozwoli ich nadpisać bez podania wszystkich naraz. Przy zmianie konfiguracji zawsze podawaj komplet flag.

Po wpisaniu komendy nowe podsieci pojawią się w panelu admina w sekcji **Awaiting Approval** — musisz je ręcznie zatwierdzić (lub skonfigurować `autoApprovers`, patrz niżej).

### Które podsieci warto rozgłaszać?

Przemyśl które podsieci faktycznie potrzebujesz zdalnie:

| Podsieć | Opis | Rozgłaszać? |
|---|---|---|
| 10.100.1.0/24 | Management | Tak |
| 10.100.10.0/24 | HOME LAN | Tak |
| 10.100.20.0/24 | SERVER (Proxmox) | Tak |
| 10.100.30.0/24 | DNS (AGH, Uptime Kuma) | Tak |
| 10.100.40.0/24 | WLAN HOME (drukarka) | Tak |
| 10.100.50.0/24 | WLAN VPN | Zależnie od planu |
| 10.100.90.0/24 | IoT (kamery, Shelly) | Tak |
| 10.100.100.0/24 | MEDIA | Tak |

Podsieci WLAN gdzie siedzą telefony i laptopy możesz pominąć — urządzenia te nie są "stałe" i poza domem ich w tej sieci nie ma.

---

## 3. Exit Node — prywatny tunel VPN z polskim IP

Exit Node to urządzenie w tailnecie które staje się **bramą wyjściową dla całego ruchu internetowego**. Innymi słowy: prywatny VPN z wyjściem w dowolnej lokalizacji, bez subskrypcji i bez pośredników.

### Przykład zastosowania

Masz TV w Niemczech który chcesz żeby korzystał z polskiego IP (dostęp do polskich serwisów streamingowych):

1. U brata w Polsce stawiasz mini PC / terminal z zainstalowanym Tailscale
2. Konfigurujesz go jako Exit Node:
   ```bash
   tailscale up --advertise-exit-node
   ```
3. TV (lub router) podłączasz do WLAN_VPN (VLAN 50)
4. Urządzenia w VLAN 50 kierujesz przez Exit Node u brata
5. Efekt: TV wychodzi z polskim IP

To jest **split-tunnel VPN** zbudowany wyłącznie z własnych urządzeń, bez żadnej zewnętrznej usługi.

---

## 4. MagicDNS — nazwy zamiast adresów IP

MagicDNS automatycznie przypisuje każdemu urządzeniu w tailnecie nazwę DNS:

```
node1.twoj-tailnet.ts.net
wyse3040.twoj-tailnet.ts.net
```

Zamiast pamiętać `100.x.x.x` — używasz nazwy. MagicDNS jest też **warunkiem koniecznym** dla certyfikatów HTTPS (patrz niżej).

---

## 5. Certyfikaty HTTPS wewnątrz tailnetu

Tailscale może wystawić prawdziwy certyfikat Let's Encrypt dla Twojej maszyny w tailnecie — bez wystawiania jej na internet.

**Jak to działa:**
- Certyfikat jest wystawiany na nazwę hosta (`node1.twoj-tailnet.ts.net`)
- Ważny i zaufany przez przeglądarki
- Widoczny **tylko dla urządzeń w Twoim tailnecie**

**Praktyczny efekt:** Koniec z ostrzeżeniami przeglądarki o niezaufanym certyfikacie gdy wchodzisz na Proxmox, AGH czy inne lokalne usługi przez Tailscale. Zielona kłódka, HTTPS, zero wyjątków.

> **Relacja z NPM + Let's Encrypt:** To nie jest konkurencja — to uzupełniające narzędzia. NPM z Let's Encrypt obsługuje usługi wystawione na zewnątrz (prawdziwa domena, publiczny internet). Certyfikaty Tailscale działają wyłącznie wewnątrz tailnetu. Oba mają swoje miejsce.

---

## 6. Taildrop — bezpieczny transfer plików

Taildrop to przesyłanie plików bezpośrednio między urządzeniami w tailnecie — peer-to-peer, przez zaszyfrowany tunel WireGuard, **bez żadnego serwera pośredniego**.

Filozoficznie bliski AirDrop, ale działa między dowolnymi systemami (Android, iOS, Windows, Linux) i przez internet, nie tylko lokalnie.

**Kiedy używać zamiast WhatsApp/Google Drive:**  
Gdy przesyłasz wrażliwe dokumenty (skany dowodów, dokumenty finansowe) — WhatsApp i Drive to pośrednicy, którzy przynajmniej teoretycznie mają dostęp do Twoich plików. Taildrop nie ma pośrednika.

---

## 7. ACL — serce konfiguracji zero-trust

ACL (Access Control List) to plik JSON który definiuje **kto może się z kim komunikować i na jakich zasadach**.

Domyślnie Tailscale działa w trybie "wszyscy widzą wszystkich". Jak tylko zaczniesz pisać własne ACL — domyślne zezwolenie znika. Obowiązuje **implicit deny**: czego nie ma w ACL, jest zablokowane.

Znasz to już z FortiOS — ta sama filozofia.

### Grupy użytkowników

Zamiast wymieniać adresy email w każdej regule, definiujesz grupę raz:

```json
{
  "groups": {
    "group:admins": ["damian@gmail.com"],
    "group:family": ["damian@gmail.com", "zona@gmail.com"]
  }
}
```

### Tagi i tagOwners

Tagi pozwalają pisać reguły per rola urządzenia, nie per adres IP. Tag musi mieć zdefiniowanego właściciela — bez tego Tailscale go nie przyjmie:

```json
{
  "tagOwners": {
    "tag:serwery":    ["group:admins"],
    "tag:home-cloud": ["group:admins"],
    "tag:iot":        ["group:admins"],
    "tag:subnet-router": ["group:admins"],
    "tag:exit-node":  ["group:admins"]
  }
}
```

**Dlaczego tagi są lepsze niż adresy IP:**  
Jak zmienisz adres IP kontenera — musisz pamiętać o aktualizacji ACL. Tag jest przypisany do maszyny, nie do adresu. Zmiana IP nie wymaga zmiany ACL.

### Reguły dostępu

```json
{
  "acls": [
    {
      "action": "accept",
      "src":    ["group:admins"],
      "dst":    ["tag:serwery:*"]
    },
    {
      "action": "accept",
      "src":    ["group:family"],
      "dst":    ["tag:home-cloud:80,443"]
    },
    {
      "action": "accept",
      "src":    ["group:family"],
      "dst":    ["tag:iot:80,443"]
    }
  ]
}
```

Czytasz to jak zdanie:
- Admini mają dostęp do wszystkich portów na serwerach
- Rodzina ma dostęp tylko do portów 80 i 443 na usługach home-cloud (HA, Immich, Vaultwarden, Paperless)
- Rodzina ma dostęp do paneli IoT przez przeglądarkę, ale nie do SSH

**Dlaczego to jest zero-trust w praktyce:**  
Nawet jeśli ktoś przejmie telefon żony i będzie miał aktywną sesję Tailscale — zobaczy tylko HA i spółkę. Proxmox, Gitea, AGH — niewidoczne.

### autoApprovers

Eliminuje ręczne zatwierdzanie subnet routes w panelu admina:

```json
{
  "autoApprovers": {
    "routes": {
      "10.100.0.0/16": ["tag:subnet-router"]
    },
    "exitNode": ["tag:exit-node"]
  }
}
```

Każde urządzenie z tagiem `subnet-router` może automatycznie rozgłaszać podsieci z zakresu `10.100.0.0/16` bez ręcznej akcji w panelu. Kluczowe gdy stawiasz maszyny przez Ansible lub Terraform.

### Tailscale SSH

Zastępuje zarządzanie kluczami SSH tożsamością Tailscale. Zamiast trzymać klucze publiczne w `~/.ssh/authorized_keys` na każdej maszynie — Tailscale sprawdza tożsamość przez ACL:

```json
{
  "ssh": [
    {
      "action": "accept",
      "src":    ["group:admins"],
      "dst":    ["tag:serwery"],
      "users":  ["root", "damian"]
    }
  ]
}
```

**Dodatkowe tryby:**

- `action: check` — przy każdym połączeniu SSH wymagana re-autoryzacja przez IdP (Google). Nawet aktywna sesja Tailscale nie wystarczy.
- **Session recording** — nagrywanie sesji SSH i wysyłanie logów do zewnętrznego systemu (głównie enterprise).

---

## 8. Apps i Services

**Apps** — pozwala udostępniać konkretne usługi innym użytkownikom w tailnecie bez dawania im dostępu do całej sieci. Granularność na poziomie pojedynczej usługi i portu. Pełną wartość zyskuje w połączeniu z dobrze skonfigurowanymi ACL.

**Services** — Tailscale aktywnie skanuje urządzenia w tailnecie i wyświetla jakie usługi na nich widzi (otwarte porty, protokoły). Automatyczna inwentaryzacja — "na tej maszynie widzę HTTP na 80, SSH na 22".

> **Uwaga prywatności:** Włączenie endpoint collection (Services) wysyła dane o Twojej sieci do Tailscale. Dla domowego użytku to raczej ciekawostka niż realna potrzeba — swoje usługi znasz na pamięć. Wartość rośnie przy dużych, rozproszonych infrastrukturach.

---

## 9. Key Expiry i Tailscale Lock

**Key Expiry** — każde urządzenie ma klucz który wygasa (domyślnie po 180 dniach). Użytkownik musi się re-autoryzować. Mechanizm bezpieczeństwa — jak ktoś straci urządzenie, klucz sam wygaśnie.

Na serwerach warto wyłączyć Key Expiry — nie chcesz żeby Proxmox wypadł z tailnetu o 3 w nocy. Na urządzeniach użytkowników (telefon, laptop) warto zostawić.

**Tailscale Lock** — dodatkowa warstwa bezpieczeństwa. Nowe urządzenia muszą być podpisane kryptograficznie przez zaufane urządzenie zanim dołączą do tailnetu. Nawet przejęcie konta Tailscale nie wystarczy — potrzebny jest fizyczny dostęp do zaufanej maszyny.

---

## 10. Webhooks

Tailscale może wysyłać powiadomienia do zewnętrznych systemów gdy coś się dzieje w tailnecie:

- Nowe urządzenie dołączyło
- Klucz wygasł
- Zmiana ACL
- Urządzenie offline

Możesz podpiąć to pod bota Telegram i dostawać powiadomienia na telefon bez zaglądania do panelu.

---

## 11. REST API, Auth Keys i Terraform

### REST API

Tailscale ma pełne REST API do zarządzania wszystkim — ACL, urządzeniami, kluczami, użytkownikami. Token generujesz w panelu admina w sekcji **Keys → API access tokens**.

Przykładowe zapytanie (lista urządzeń w tailnecie):

```
GET https://api.tailscale.com/api/v2/tailnet/moj-tailnet/devices
Authorization: Bearer tskey-api-xxx
```

Odpowiedź: JSON z listą urządzeń, ich adresami, tagami, statusem.

### Auth Keys

Służą do dodawania urządzeń do tailnetu **bez interaktywnego logowania**. Normalnie przy dodawaniu nowego urządzenia otwiera się przeglądarka. Auth key omija ten krok — wklejasz klucz w komendzie i urządzenie dołącza automatycznie.

Niezbędne przy automatycznym stawianiu maszyn przez Ansible lub Terraform.

### Terraform Provider

Tailscale ma oficjalny provider Terraform. Możesz trzymać całą konfigurację tailnetu jako kod, razem z konfiguracją Proxmox:

```hcl
resource "tailscale_acl" "main" {
  acl = jsonencode({
    groups = {
      "group:admins" = ["damian@gmail.com"]
      "group:family" = ["damian@gmail.com", "zona@gmail.com"]
    }
    tagOwners = {
      "tag:serwery"    = ["group:admins"]
      "tag:home-cloud" = ["group:admins"]
    }
    acls = [
      {
        action = "accept"
        src    = ["group:admins"]
        dst    = ["tag:serwery:*"]
      }
    ]
  })
}
```

Jeden `terraform apply` — i Proxmox, sieć, ACL, wszystko skonfigurowane razem, wersjonowane w Gitea.

---

## 12. MFA i SSO

**MFA** — Tailscale nie obsługuje MFA bezpośrednio, ale opiera się na zewnętrznym dostawcy tożsamości (IdP). Logujesz się przez Google, GitHub lub Microsoft. MFA konfigurujesz po stronie IdP — jeśli masz MFA na koncie Google, masz MFA na Tailscale.

**SSO** — dostępne na planach biznesowych. Pozwala podpiąć własny IdP (Okta, Azure AD) i zarządzać dostępem centralnie. Na planie osobistym Google jako IdP w zupełności wystarczy.

---

## 13. Praktyczna konfiguracja dla homelabu

Kompletny przykład ACL dla homelabu z VLANami, żoną i zero-trust:

```json
{
  "groups": {
    "group:admins": ["damian@gmail.com"],
    "group:family": ["damian@gmail.com", "zona@gmail.com"]
  },

  "tagOwners": {
    "tag:serwery":       ["group:admins"],
    "tag:home-cloud":    ["group:admins"],
    "tag:iot":           ["group:admins"],
    "tag:subnet-router": ["group:admins"],
    "tag:exit-node":     ["group:admins"]
  },

  "autoApprovers": {
    "routes": {
      "10.100.0.0/16": ["tag:subnet-router"]
    },
    "exitNode": ["tag:exit-node"]
  },

  "acls": [
    {
      "action": "accept",
      "src":    ["group:admins"],
      "dst":    ["*:*"]
    },
    {
      "action": "accept",
      "src":    ["group:family"],
      "dst":    ["tag:home-cloud:80,443,8123"]
    }
  ],

  "ssh": [
    {
      "action": "accept",
      "src":    ["group:admins"],
      "dst":    ["tag:serwery"],
      "users":  ["root", "damian"]
    }
  ]
}
```

**Co to osiąga:**
- Admin (Damian) ma dostęp do wszystkiego
- Żona widzi tylko usługi z tagiem `home-cloud` (HA, Immich, Vaultwarden, Paperless) przez HTTP/HTTPS
- Subnet router automatycznie zatwierdza podsieci bez klikania w panel
- SSH dostępny tylko dla adminów

---

## 14. FAQ

**Czy Tailscale to to samo co zwykły VPN?**  
Nie. Klasyczny VPN to jeden serwer przez który leci cały ruch. Tailscale tworzy sieć mesh — urządzenia łączą się bezpośrednio ze sobą. Brak centralnego wąskiego gardła, niższe opóźnienia, lepsza wydajność.

**Mam Subnet Router, widzę całą sieć — po co instalować Tailscale na każdej maszynie osobno?**  
Subnet Router daje dostęp do sieci, ale maszyny za nim są dla Tailscale "niewidzialne" — nie możesz ich tagować, nie możesz pisać ACL per urządzenie, nie możesz używać Tailscale SSH. Instalacja Tailscale bezpośrednio na maszynie czyni ją pełnoprawnym uczestnikiem tailnetu. Nie musisz tego robić na wszystkim — tylko tam gdzie potrzebujesz granularnej kontroli.

**Żona ma dostęp do HA przez Tailscale. Czy widzi kamery i Shelly z VLAN IoT?**  
Tak — ale pośrednio. Żona łączy się z HA, a HA samo komunikuje się z kamerami i Shelly przez sieć lokalną. Z perspektywy żony to transparentne — klika, lampka się zapala. Nie musi mieć bezpośredniego dostępu do VLAN IoT.

**Po co certyfikaty HTTPS w Tailscale, skoro mam już Let's Encrypt przez NPM?**  
NPM z Let's Encrypt obsługuje usługi wystawione na publiczny internet. Certyfikaty Tailscale działają wyłącznie wewnątrz tailnetu — dla usług które nigdy nie wyjdą na zewnątrz. Efekt: brak ostrzeżeń przeglądarki gdy wchodzisz na Proxmox czy AGH przez Tailscale.

**Czy Taildrop jest bezpieczniejszy niż WhatsApp do wysyłania dokumentów?**  
Tak. Taildrop to peer-to-peer przez zaszyfrowany tunel WireGuard — plik idzie bezpośrednio między urządzeniami, bez żadnego serwera pośredniego. WhatsApp, Messenger, Google Drive to pośrednicy którzy przynajmniej teoretycznie mają dostęp do przesyłanych plików.

**Czym różni się Tailscale Funnel od Cloudflare Tunnel?**  
Oba wystawiają usługi lokalnie na publiczny internet bez otwierania portów. Cloudflare Tunnel ma więcej opcji dla self-hostingu (własna domena, zaawansowane reguły, Cloudflare Access). Tailscale Funnel jest prostszy ale mniej elastyczny. Dla homelabu z własną domeną — Cloudflare Tunnel wygrywa.

**Co to jest REST API i czym różni się od zwykłego API?**  
REST (Representational State Transfer) to zestaw konwencji jak powinny wyglądać zapytania HTTP do API. Używasz standardowych metod: `GET` (pobierz), `POST` (utwórz), `PUT/PATCH` (zaktualizuj), `DELETE` (usuń). Adres URL mówi *co* chcesz zrobić, metoda HTTP mówi *jak*. Każde API które tych konwencji przestrzega — jest REST API.

**Czy mogę zarządzać ACL przez CLI zamiast panelu admina?**  
Przez `tailscale` CLI możesz zarządzać lokalnymi ustawieniami konkretnego urządzenia, ale globalna konfiguracja tailnetu (ACL, tagi, grupy) wymaga panelu admina lub REST API. Docelowo — Terraform provider pozwala trzymać całą konfigurację jako kod w repozytorium.

**Czym jest autoApprovers i kiedy jest potrzebny?**  
autoApprovers eliminuje ręczne zatwierdzanie subnet routes w panelu admina. Gdy przez Ansible lub Terraform automatycznie stawiasz nowe maszyny z Tailscale, nie chcesz pamiętać o logowaniu do panelu i klikaniu "approve". autoApprovers robi to automatycznie dla urządzeń z odpowiednim tagiem.

**Key Expiry — wyłączyć czy zostawić?**  
Na serwerach (Proxmox, LXC) — wyłączyć. Nie chcesz żeby infrastruktura wypadła z tailnetu o 3 w nocy bo wygasł klucz. Na urządzeniach użytkowników (telefony, laptopy) — zostawić. To mechanizm bezpieczeństwa na wypadek utraty urządzenia.

---

*Ostatnia aktualizacja: marzec 2026*  
*Infrastruktura: Fortigate 60E · Proxmox VE 9 · Tailscale Personal Plan*