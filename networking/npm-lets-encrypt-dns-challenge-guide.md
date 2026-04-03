# Let's Encrypt DNS Challenge via Cloudflare in NPM Proxy Manager

> 🇬🇧 English first / 🇵🇱 Polski poniżej

---

## 🇬🇧 English

### What is DNS Challenge and why use it?

Let's Encrypt offers two ways to verify domain ownership:

- **HTTP challenge** — Let's Encrypt sends a request to your server on port 80. Requires the server to be publicly accessible.
- **DNS challenge** — Let's Encrypt asks you to add a specific TXT record to your DNS zone. **No open ports required** — works entirely behind NAT, VPN, or a closed firewall.

For a homelab where services are not publicly exposed, DNS challenge is the right choice.

---

### Prerequisites

- Domain managed in **Cloudflare** (nameservers pointing to Cloudflare)
- **NPM (Nginx Proxy Manager)** running and accessible
- Cloudflare account with API access

> ⚠️ If your domain is registered elsewhere but uses a custom provider's nameservers, the Cloudflare API will not have authority over your DNS records and will return an error. You must first migrate your DNS zone to Cloudflare (see FAQ below).

---

### Step 1 — Generate a Cloudflare API Token

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Go to **My Profile → API Tokens → Create Token**
3. Use the **"Edit zone DNS"** template
4. Under **Zone Resources**, select:
   - Include → Specific zone → *your domain*
5. Leave **Client IP Address Filtering** empty (NPM's IP may change on renewal)
6. Leave **TTL** empty (token must remain valid for automatic 90-day renewals)
7. Click **Continue to summary → Create Token**
8. **Copy the token immediately** — it will not be shown again

---

### Step 2 — Request the Certificate in NPM

1. Open NPM → **SSL Certificates → Add Certificate**
2. Select **Let's Encrypt**
3. Fill in:
   - **Domain Names**: your domain (e.g. `example.de` and/or `*.example.de` for wildcard)
   - **Email**: your email address
   - **DNS Challenge**: enable ✅
   - **DNS Provider**: Cloudflare
   - **Credentials**: paste your API token
4. Accept Let's Encrypt Terms of Service
5. Click **Save**

NPM will automatically add the `_acme-challenge` TXT record to Cloudflare, wait for propagation, verify it, and issue the certificate.

---

### Step 3 — Assign the Certificate to a Proxy Host

1. Go to **Hosts → Proxy Hosts**
2. Edit (or create) a host
3. Open the **SSL** tab
4. Select your newly created certificate from the list
5. Save

---

### Renewal

Certificates are valid for **90 days**. NPM renews them automatically before expiry — no manual action required as long as:
- The Cloudflare API token remains valid (no TTL set → no expiry)
- NPM is running at renewal time

---

### FAQ

**Q: I tried the Cloudflare API but got "Internal Error" in NPM.**  
A: Most likely your domain's nameservers are not pointing to Cloudflare. The Cloudflare API can only manage DNS records for zones where Cloudflare is the authoritative nameserver. Verify in Cloudflare Dashboard that your domain's status is **Active**.

**Q: My domain is registered at one provider but uses a different provider's nameservers. What now?**  
A: The DNS challenge uses whoever controls your nameservers — not the registrar. If your nameservers are at a custom provider with no public API, you have two options:
- Migrate the DNS zone to Cloudflare (change nameservers to Cloudflare's NS)
- Use manual DNS challenge (`certbot --manual`) — but this requires manual renewal every 90 days

**Q: Will migrating DNS to Cloudflare break my email?**  
A: Not if done correctly. Before changing nameservers, verify that Cloudflare has imported all your DNS records — especially MX and SPF (TXT) records. Cloudflare's automatic import usually catches all of them. Only change nameservers after confirming everything is in place.

**Q: Do I need to open any ports for DNS challenge?**  
A: No. That's the entire point. DNS challenge communicates via the Cloudflare API, not via your server's network connection.

**Q: Can I use a wildcard certificate (*.example.de)?**  
A: Yes — wildcard certificates are only possible with DNS challenge (not HTTP). Add both `example.de` and `*.example.de` as domain names in NPM.

**Q: The certificate says "Not Used" after creation. Is that a problem?**  
A: No. It just means the certificate hasn't been assigned to any proxy host yet. Assign it in the SSL tab of your proxy host.

---

---

## 🇵🇱 Polski

### Czym jest DNS Challenge i po co go używać?

Let's Encrypt oferuje dwa sposoby weryfikacji własności domeny:

- **HTTP challenge** — Let's Encrypt wysyła zapytanie do Twojego serwera na porcie 80. Wymaga publicznego dostępu do serwera.
- **DNS challenge** — Let's Encrypt prosi o dodanie konkretnego rekordu TXT do strefy DNS. **Nie wymaga otwartych portów** — działa za NAT-em, VPN-em lub zamkniętym firewallem.

W homelabiu, gdzie usługi nie są publicznie wystawione, DNS challenge to właściwy wybór.

---

### Wymagania

- Domena zarządzana przez **Cloudflare** (nameservery wskazują na Cloudflare)
- Działający i dostępny **NPM (Nginx Proxy Manager)**
- Konto Cloudflare z dostępem do API

> ⚠️ Jeśli domena jest zarejestrowana gdzie indziej, ale używa nameserverów innego dostawcy, Cloudflare API nie ma uprawnień do zarządzania rekordami DNS i zwróci błąd. Najpierw należy przenieść strefę DNS do Cloudflare (patrz FAQ poniżej).

---

### Krok 1 — Generowanie tokena API Cloudflare

1. Zaloguj się do [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Przejdź do **My Profile → API Tokens → Create Token**
3. Użyj szablonu **"Edit zone DNS"**
4. W sekcji **Zone Resources** wybierz:
   - Include → Specific zone → *Twoja domena*
5. **Client IP Address Filtering** zostaw puste (IP NPM może się zmieniać przy odnowieniu)
6. **TTL** zostaw puste (token musi być ważny dla automatycznych odnowień co 90 dni)
7. Kliknij **Continue to summary → Create Token**
8. **Skopiuj token od razu** — nie zostanie pokazany ponownie

---

### Krok 2 — Wygenerowanie certyfikatu w NPM

1. Otwórz NPM → **SSL Certificates → Add Certificate**
2. Wybierz **Let's Encrypt**
3. Uzupełnij:
   - **Domain Names**: Twoja domena (np. `example.de` i/lub `*.example.de` dla wildcard)
   - **Email**: Twój adres email
   - **DNS Challenge**: włącz ✅
   - **DNS Provider**: Cloudflare
   - **Credentials**: wklej token API
4. Zaakceptuj regulamin Let's Encrypt
5. Kliknij **Save**

NPM automatycznie doda rekord TXT `_acme-challenge` do Cloudflare, poczeka na propagację, zweryfikuje go i wystawi certyfikat.

---

### Krok 3 — Przypisanie certyfikatu do Proxy Host

1. Przejdź do **Hosts → Proxy Hosts**
2. Edytuj (lub utwórz) host
3. Otwórz zakładkę **SSL**
4. Wybierz z listy nowo utworzony certyfikat
5. Zapisz

---

### Odnowienie

Certyfikaty są ważne przez **90 dni**. NPM odnawia je automatycznie przed wygaśnięciem — nie wymaga żadnej ręcznej interwencji, o ile:
- Token API Cloudflare pozostaje ważny (brak TTL → brak wygaśnięcia)
- NPM działa w momencie odnowienia

---

### FAQ

**P: Próbowałem Cloudflare API, ale NPM zwrócił "Internal Error".**  
O: Najprawdopodobniej nameservery domeny nie wskazują na Cloudflare. Cloudflare API może zarządzać rekordami DNS tylko dla stref, gdzie Cloudflare jest autorytatywnym nameserverem. Sprawdź w Cloudflare Dashboard, czy status domeny to **Active**.

**P: Moja domena jest zarejestrowana u jednego dostawcy, ale używa nameserverów innej firmy. Co teraz?**  
O: DNS challenge używa tego, kto kontroluje Twoje nameservery — nie rejestratora. Jeśli nameservery są u dostawcy z własnym panelem bez publicznego API, masz dwie opcje:
- Przenieś strefę DNS do Cloudflare (zmień nameservery na Cloudflare'owe)
- Użyj ręcznego DNS challenge (`certbot --manual`) — ale wymaga ręcznego odnowienia co 90 dni

**P: Czy przeniesienie DNS do Cloudflare zepsuje mi pocztę email?**  
O: Nie, jeśli zrobisz to poprawnie. Przed zmianą nameserverów sprawdź, czy Cloudflare zaimportował wszystkie rekordy DNS — szczególnie MX i SPF (rekord TXT). Automatyczny import Cloudflare zazwyczaj je wszystkie wykrywa. Nameservery zmieniaj dopiero po potwierdzeniu, że wszystko jest na miejscu.

**P: Czy muszę otwierać jakieś porty dla DNS challenge?**  
O: Nie. Na tym polega cały sens. DNS challenge komunikuje się przez Cloudflare API, nie przez połączenie sieciowe Twojego serwera.

**P: Czy mogę użyć certyfikatu wildcard (*.example.de)?**  
O: Tak — certyfikaty wildcard są możliwe wyłącznie przez DNS challenge (nie przez HTTP). Dodaj zarówno `example.de` jak i `*.example.de` jako nazwy domen w NPM.

**P: Po wygenerowaniu certyfikat ma status "Not Used". Czy to problem?**  
O: Nie. Oznacza to tylko, że certyfikat nie został jeszcze przypisany do żadnego proxy hosta. Przypisz go w zakładce SSL swojego proxy hosta.

---


## 🇩🇪 Deutsch

### Was ist der DNS-Challenge und warum verwenden?

Let's Encrypt bietet zwei Methoden zur Verifizierung der Domain-Inhaberschaft:

- **HTTP-Challenge** — Let's Encrypt sendet eine Anfrage an deinen Server auf Port 80. Erfordert öffentlichen Zugang zum Server.
- **DNS-Challenge** — Let's Encrypt verlangt das Hinzufügen eines bestimmten TXT-Eintrags in die DNS-Zone. **Keine offenen Ports erforderlich** — funktioniert hinter NAT, VPN oder einer geschlossenen Firewall.

In einem Homelab, in dem Dienste nicht öffentlich erreichbar sind, ist der DNS-Challenge die richtige Wahl.

---

### Voraussetzungen

- Domain verwaltet über **Cloudflare** (Nameserver zeigen auf Cloudflare)
- Laufender und erreichbarer **NPM (Nginx Proxy Manager)**
- Cloudflare-Konto mit API-Zugang

> ⚠️ Wenn die Domain bei einem anderen Anbieter registriert ist und dessen eigene Nameserver verwendet, hat die Cloudflare API keine Kontrolle über die DNS-Einträge und gibt einen Fehler zurück. Zuerst muss die DNS-Zone zu Cloudflare migriert werden (siehe FAQ unten).

---

### Schritt 1 — Cloudflare API-Token generieren

1. Bei [Cloudflare Dashboard](https://dash.cloudflare.com) einloggen
2. Zu **My Profile → API Tokens → Create Token** navigieren
3. Die Vorlage **"Edit zone DNS"** verwenden
4. Unter **Zone Resources** auswählen:
   - Include → Specific zone → *deine Domain*
5. **Client IP Address Filtering** leer lassen (die IP von NPM kann sich bei der Erneuerung ändern)
6. **TTL** leer lassen (Token muss für automatische 90-Tage-Erneuerungen gültig bleiben)
7. Auf **Continue to summary → Create Token** klicken
8. **Token sofort kopieren** — er wird nicht erneut angezeigt

---

### Schritt 2 — Zertifikat in NPM anfordern

1. NPM öffnen → **SSL Certificates → Add Certificate**
2. **Let's Encrypt** auswählen
3. Ausfüllen:
   - **Domain Names**: deine Domain (z.B. `example.de` und/oder `*.example.de` für Wildcard)
   - **Email**: deine E-Mail-Adresse
   - **DNS Challenge**: aktivieren ✅
   - **DNS Provider**: Cloudflare
   - **Credentials**: API-Token einfügen
4. Let's Encrypt Nutzungsbedingungen akzeptieren
5. Auf **Save** klicken

NPM fügt automatisch den `_acme-challenge` TXT-Eintrag bei Cloudflare hinzu, wartet auf die Propagierung, verifiziert ihn und stellt das Zertifikat aus.

---

### Schritt 3 — Zertifikat einem Proxy Host zuweisen

1. Zu **Hosts → Proxy Hosts** navigieren
2. Einen Host bearbeiten (oder erstellen)
3. Den **SSL**-Tab öffnen
4. Das neu erstellte Zertifikat aus der Liste auswählen
5. Speichern

---

### Erneuerung

Zertifikate sind **90 Tage** gültig. NPM erneuert sie automatisch vor dem Ablauf — keine manuelle Aktion erforderlich, solange:
- Der Cloudflare API-Token gültig ist (kein TTL gesetzt → kein Ablauf)
- NPM zum Zeitpunkt der Erneuerung läuft

---

### FAQ

**F: Ich habe die Cloudflare API versucht, aber NPM gibt "Internal Error" zurück.**  
A: Höchstwahrscheinlich zeigen die Nameserver der Domain nicht auf Cloudflare. Die Cloudflare API kann DNS-Einträge nur für Zonen verwalten, bei denen Cloudflare der autoritative Nameserver ist. Im Cloudflare Dashboard prüfen, ob der Domain-Status **Active** ist.

**F: Meine Domain ist bei einem Anbieter registriert, verwendet aber Nameserver eines anderen Anbieters. Was nun?**  
A: Der DNS-Challenge verwendet denjenigen, der die Nameserver kontrolliert — nicht den Registrar. Wenn die Nameserver bei einem Anbieter mit eigenem Panel ohne öffentliche API liegen, gibt es zwei Optionen:
- DNS-Zone zu Cloudflare migrieren (Nameserver auf Cloudflare-NS ändern)
- Manuellen DNS-Challenge verwenden (`certbot --manual`) — erfordert jedoch manuelle Erneuerung alle 90 Tage

**F: Zerstört die Migration der DNS zu Cloudflare meine E-Mails?**  
A: Nicht, wenn es korrekt gemacht wird. Vor dem Ändern der Nameserver prüfen, ob Cloudflare alle DNS-Einträge importiert hat — insbesondere MX- und SPF-Einträge (TXT). Der automatische Import von Cloudflare erkennt sie normalerweise alle. Nameserver erst ändern, nachdem alles bestätigt wurde.

**F: Muss ich Ports für den DNS-Challenge öffnen?**  
A: Nein. Das ist der gesamte Sinn. Der DNS-Challenge kommuniziert über die Cloudflare API, nicht über die Netzwerkverbindung des Servers.

**F: Kann ich ein Wildcard-Zertifikat (*.example.de) verwenden?**  
A: Ja — Wildcard-Zertifikate sind nur über den DNS-Challenge möglich (nicht über HTTP). Sowohl `example.de` als auch `*.example.de` als Domain-Namen in NPM hinzufügen.

**F: Nach der Erstellung steht beim Zertifikat "Not Used". Ist das ein Problem?**  
A: Nein. Es bedeutet nur, dass das Zertifikat noch keinem Proxy Host zugewiesen wurde. Im SSL-Tab des Proxy Hosts zuweisen.

---

*Dokumentation basierend auf eigener Homelab-Konfiguration: NPM auf Proxmox VE 9 (LXC Debian), Domain bei Cloudflare.*