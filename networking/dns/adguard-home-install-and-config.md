# AdGuard Home – Installation & First Configuration

[English](#english) · [Deutsch](#deutsch) · [Polski](#polski)

> Tested with **AdGuard Home v0.107.79** on **Debian 13 (Trixie)** – bare metal (Dell Wyse 3040) and Proxmox VE 9 LXC.

---

## English

[English](#english) · [Deutsch](#deutsch) · [Polski](#polski)

### 0. Placeholders

This document uses placeholders instead of real addresses. Replace them with your own values.

| Placeholder | What to insert |
| --- | --- |
| `<agh-host-ip>` | Static IP address of the machine running AdGuard Home |
| `<lan-subnet>` | Subnet (CIDR) allowed to query DNS, e.g. your home network. Multiple entries possible |
| `<gateway-ip>` | Router / gateway address (usually also the DHCP server) |
| `<admin-user>` | Name of the AGH admin account |
| `<your-domain>` | Your domain, if you use split-horizon DNS (section 6.9) |
| `<reverse-proxy-ip>` | Address of the reverse proxy (e.g. Nginx Proxy Manager) on the LAN |
| `<client-ip>` | Address of any client on the network – for testing |
| `<ui-port>` | Web UI port after installation (`80` in my setup) |

### 1. What it is and where it sits in the architecture

AdGuard Home (AGH) is a filtering DNS server. It does not resolve names on its own – it is a **forwarder**: it receives a client query, checks it against blocklists and, if the domain isn't blocked, forwards the query to an **upstream** and caches the answer.

```text
Client ──► AdGuard Home (<agh-host-ip>:53) ──► Upstream
            │ blocklists                         │
            │ cache                              ├─ Unbound (127.0.0.1:5335) – recursive, DNSSEC
            │ rewrites                           └─ or a public resolver (e.g. Quad9 DoH)
            └─ query log / statistics
```

In my homelab the upstream is a local **Unbound** (separate document), which resolves names recursively from the root servers and validates DNSSEC. A second AGH instance is replicated with **adguardhome-sync** (separate document).

### 2. Requirements

- Debian 12/13 or Ubuntu, root access (or `sudo`).
- A **static IP address** for the host (`<agh-host-ip>`) – a DNS server whose address changes breaks DNS for the whole network. Set it statically on the host or via a DHCP reservation on the router.
- Free port **53** (TCP+UDP) and a port for the web UI.
- If a host firewall is active (ufw/nftables): allow 53/tcp, 53/udp, 3000/tcp (setup wizard) and `<ui-port>`/tcp.

### 3. Installation A – Debian / Ubuntu (official script)

**Why this method:** it is the method recommended by AdGuardTeam. The script downloads the official release, unpacks it to `/opt/AdGuardHome` and registers AGH as a systemd service (`AdGuardHome -s install`). Nothing else – no repositories, no dependencies.

**3.1 Tools:**

```bash
apt update && apt install -y curl bind9-dnsutils
```

`bind9-dnsutils` provides `dig`, needed for testing.

**3.2 Check that port 53 is free:**

```bash
ss -tulpn | grep ':53 '
```

Empty output = free. On **Ubuntu** the port is usually taken by `systemd-resolved` (stub listener on `127.0.0.53`). Disable it as described in the AGH documentation:

```bash
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/adguardhome.conf << 'EOF'
[Resolve]
DNS=127.0.0.1
DNSStubListener=no
EOF
mv /etc/resolv.conf /etc/resolv.conf.backup
ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
systemctl reload-or-restart systemd-resolved
```

A plain Debian install usually has no `systemd-resolved` – skip this step.

**3.3 Download the script, review it, run it:**

The official instructions use `curl ... | sh`. Downloading the script to a file and reviewing it first is better – you are running code from the internet as root.

```bash
curl -s -S -L -o /tmp/agh-install.sh \
  https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh
less /tmp/agh-install.sh
sh /tmp/agh-install.sh -v
```

`-v` = verbose (you see every step). Default directory is `/opt`, channel `release` (stable).

**3.4 Verify the service:**

```bash
systemctl status AdGuardHome
ss -tulpn | grep AdGuardHome
```

Expected: service `active (running)`, listening on port `3000` (first-run wizard).

**3.5 Verify permissions:**

```bash
stat -c '%a %U:%G %n' /opt/AdGuardHome /opt/AdGuardHome/AdGuardHome
```

The directory and binary belong to `root:root` and **must not be world-writable** (the last digit must not be `7`, `6`, `3` or `2`). The binary runs as root – if any user can replace it, that user has a path to root. If the directory is e.g. `777`:

```bash
chmod go-w /opt/AdGuardHome
```

> From experience: after some time the directory on my host was `777`, although the release archive ships `755`. Cause unknown – so check this after updates too.

### 4. Installation B – Proxmox VE (Community Script, LXC)

**When:** you run Proxmox and want AGH in a lightweight LXC container. My second instance runs this way.

**4.1** Review the script on the community-scripts website (AdGuard Home entry), then in the **Proxmox node shell**:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/adguard.sh)"
```

**4.2** In the wizard:

- container OS: **Debian 13** (Alpine is an option – smaller, but different service management),
- choose **Advanced settings** and set a **static IP** (`<agh-host-ip>/<prefix>`) and gateway `<gateway-ip>` – by default the container gets a DHCP address.

**4.3 Differences from installation A:**

- the script installs the same official release to `/opt/AdGuardHome`, but creates **its own** systemd unit – logs go to `/var/log/AdGuardHome.out` and `/var/log/AdGuardHome.err`, not to the journal,
- in a Debian container, updates only via the web UI (the script's `update` doesn't do it).

Verify as in 3.4 and 3.5 – inside the container (`pct enter <vmid>`).

### 5. First-run wizard

Open `http://<agh-host-ip>:3000`.

| Step | Setting | Why |
| --- | --- | --- |
| Admin Web Interface | interface with `<agh-host-ip>`, port `<ui-port>` | Listen on one known address instead of "All interfaces" (`0.0.0.0`) – the UI isn't exposed on interfaces where you don't want it. |
| DNS server | interface with `<agh-host-ip>`, port `53` | Same reason. Also avoids conflicts with other services on `127.0.0.1:53`. |
| Authentication | `<admin-user>` + long random password from a password manager | The UI can disable filtering and change the upstream for the whole network. |

After the wizard, the UI is at `http://<agh-host-ip>:<ui-port>` and port `3000` stops listening.

### 6. Configuration – setting by setting

Everything is set in the web UI. The key in `AdGuardHome.yaml` is given in brackets – useful when comparing configurations.

> **Don't edit `AdGuardHome.yaml` while the service is running** – AGH will overwrite your changes. Manual edits only with the service stopped (section 9).

#### 6.1 Upstream DNS – *Settings → DNS settings → Upstream DNS servers* (`dns.upstream_dns`)

- **With local Unbound:** `127.0.0.1:5335`
- **Without Unbound:** an encrypted public resolver, e.g. `https://dns.quad9.net/dns-query`

Mode: **Load-balancing** (`upstream_mode: load_balance`) – irrelevant with one upstream; with several, AGH prefers the faster and more reliable one.

**Why Unbound:** your queries don't go to a single provider (Google, Cloudflare, Quad9) that would see your network's entire DNS history. Unbound asks the authoritative servers directly and validates DNSSEC itself.

#### 6.2 Bootstrap DNS (`dns.bootstrap_dns`)

```text
9.9.9.10
149.112.112.10
2620:fe::10
2620:fe::fe:10
```

**Why:** bootstrap is only used to resolve the **hostname** of an upstream (e.g. `dns.quad9.net`) – the chicken-and-egg problem. With an upstream given as an IP (`127.0.0.1:5335`) it is practically unused, but it must be valid in case you change the upstream.

#### 6.3 Private reverse DNS servers (`dns.local_ptr_upstreams`, `dns.use_private_ptr_resolvers`)

This makes the query log show device names instead of `<client-ip>`. AGH sends PTR queries for private addresses **only** to local resolvers (so they don't leak outside). Empty list = AGH takes the resolvers from the host OS.

Enter a server that knows client names – usually the router/DHCP server. First check whether it answers at all:

```bash
dig -x <client-ip> @<gateway-ip> +short
```

A name in the answer → enter `<gateway-ip>`. Empty answer → the router doesn't support PTR; you can name clients manually in *Settings → Client settings*.

#### 6.4 Rate limit (`dns.ratelimit`) → `0`

Default is `20` queries/s – **counted per /24 subnet** (`ratelimit_subnet_len_ipv4: 24`), not per client. On a home network the whole subnet shares one pool of 20 queries/s; anything above is silently dropped. This protection makes sense for public servers (amplification attacks); the AGH documentation explicitly says it is safe to disable when the server isn't reachable from the internet.

Keep `Refuse ANY` (`refuse_any: true`) enabled – it doesn't hurt, ANY queries are practically unused.

#### 6.5 Allowed clients – *Settings → DNS settings → Access settings* (`dns.allowed_clients`)

```text
<lan-subnet>
127.0.0.0/8
```

**Why:** when the list is not empty, AGH answers **only** these clients. It's a second layer of defence next to the firewall – even with a mistake in network rules, the server won't become an open resolver.

⚠️ Add all your subnets (VLANs, VPN) before saving – any subnet you leave out loses DNS immediately.

#### 6.6 DNSSEC (`dns.enable_dnssec`) → off with Unbound

This option only sets the DO bit in upstream queries and shows the status in the log. **Unbound does the validation** – for a bad signature it returns SERVFAIL, so the client never gets a forged answer anyway.

#### 6.7 Cache (`dns.cache_*`)

- size: default (4 MB) – enough for a home network,
- **Optimistic caching: off** – when enabled, AGH also serves expired entries. Unbound has its own cache and prefetch, so the gain is small, while the risk of a stale answer (e.g. after a service changes its IP) is real.

#### 6.8 Blocklists – *Filters → DNS blocklists* (`filters`)

My set (all from "Add blocklist → Choose from the list"):

| List | Purpose |
| --- | --- |
| AdGuard DNS filter | ads and trackers – baseline |
| AdAway Default Blocklist | mobile ads |
| OISD Blocklist Small | broad, well maintained, few false positives |
| Peter Lowe's Blocklist | ads/trackers |
| POL: CERT Polska List of malicious domains | malicious domains (PL) |
| Phishing URL Blocklist (PhishTank and OpenPhish) | phishing |
| Malicious URL Blocklist (URLHaus) | malware |

**Principle:** a few well-maintained lists instead of dozens – more lists mean more RAM and more false positives for little gain. Update interval: 24 h (default).

#### 6.9 DNS rewrites – *Filters → DNS rewrites* (`filtering.rewrites`) – optional

```text
*.<your-domain>  →  <reverse-proxy-ip>
```

**Split-horizon DNS:** on the LAN, your domain's subdomains point directly to the local reverse proxy instead of going out to the internet and back. It also keeps working when the internet connection is down.

#### 6.10 Query log and statistics – *Settings → General settings*

- Query log: 90 days in my setup (default); statistics: 24 h.
- On small flash storage (eMMC, SD card) consider shorter log retention – the log is written to disk continuously.

#### 6.11 Other – *Settings → General settings*

- **Blocking mode: Default** – blocked domains get `0.0.0.0` / `::`, the client gives up immediately.
- **Browsing security / Parental control: off** – they work by querying AdGuard's servers (domain hash prefixes). The blocklists from 6.8 already cover the protective role without sending anything outside.

### 7. Point the network to AGH

On the router, in the **DHCP** settings, set `<agh-host-ip>` as the DNS server.

- **Don't add a public DNS as secondary** (e.g. `8.8.8.8`) – clients use both servers interchangeably, so some queries bypass filtering.
- For redundancy, the second server should be a **second AGH instance** (synced with adguardhome-sync).

Clients pick up the new DNS after renewing the DHCP lease (or reconnecting).

### 8. Verification

```bash
# Normal resolution
dig @<agh-host-ip> example.com +short

# Blocked domain → expected 0.0.0.0
dig @<agh-host-ip> doubleclick.net +short

# Service logs
journalctl -u AdGuardHome -n 50 --no-pager
```

On Windows: `nslookup example.com` – the `Server` field must show `<agh-host-ip>`. Finally, check the *Query log* in the UI for client queries.

### 9. Maintenance

**Update:** the button in the UI (appears when a new version is out) or from the CLI:

```bash
/opt/AdGuardHome/AdGuardHome --update
```

After updating, repeat the permission check from 3.5.

**Manual config edit:**

```bash
systemctl stop AdGuardHome
cp /opt/AdGuardHome/AdGuardHome.yaml /opt/AdGuardHome/AdGuardHome.yaml.bak
vi /opt/AdGuardHome/AdGuardHome.yaml
/opt/AdGuardHome/AdGuardHome --check-config -c /opt/AdGuardHome/AdGuardHome.yaml
systemctl start AdGuardHome
```

**Backup:** `/opt/AdGuardHome/AdGuardHome.yaml` (entire configuration) + `/opt/AdGuardHome/data/` (log, statistics, lists).

**Password reset:** generate a bcrypt hash and put it in `users → password` (service stopped):

```bash
apt install -y apache2-utils
htpasswd -B -C 10 -n -b <admin-user> '<new-password>'
```

### 10. Known limitations

- **UI over plain HTTP.** The password travels unencrypted on the LAN. Restrict UI access to the management network with the firewall, or expose it via a reverse proxy with a certificate.
- **Client names in the log** depend on whether the router answers PTR queries (6.3).

### 11. Related documents

- Unbound – recursive resolver as upstream
- adguardhome-sync – configuration replication to a second instance

---

## Deutsch

[English](#english) · [Deutsch](#deutsch) · [Polski](#polski)

### 0. Platzhalter

Dieses Dokument verwendet Platzhalter statt echter Adressen. Ersetze sie durch deine eigenen Werte.

| Platzhalter | Was einsetzen |
| --- | --- |
| `<agh-host-ip>` | Statische IP-Adresse des Rechners, auf dem AdGuard Home läuft |
| `<lan-subnet>` | Subnetz (CIDR), das DNS abfragen darf, z. B. dein Heimnetz. Mehrere Einträge möglich |
| `<gateway-ip>` | Adresse des Routers / Gateways (meist auch DHCP-Server) |
| `<admin-user>` | Name des AGH-Admin-Kontos |
| `<your-domain>` | Deine Domain, falls du Split-Horizon-DNS nutzt (Abschnitt 6.9) |
| `<reverse-proxy-ip>` | Adresse des Reverse Proxys (z. B. Nginx Proxy Manager) im LAN |
| `<client-ip>` | Adresse eines beliebigen Clients im Netz – für Tests |
| `<ui-port>` | Port der Weboberfläche nach der Installation (bei mir `80`) |

### 1. Was es ist und wo es in der Architektur liegt

AdGuard Home (AGH) ist ein filternder DNS-Server. Er löst Namen nicht selbst auf – er ist ein **Forwarder**: Er nimmt die Anfrage des Clients an, prüft sie gegen Blocklisten und leitet sie, falls die Domain nicht blockiert ist, an einen **Upstream** weiter. Die Antwort landet im Cache.

```text
Client ──► AdGuard Home (<agh-host-ip>:53) ──► Upstream
            │ blocklists                         │
            │ cache                              ├─ Unbound (127.0.0.1:5335) – recursive, DNSSEC
            │ rewrites                           └─ or a public resolver (e.g. Quad9 DoH)
            └─ query log / statistics
```

In meinem Homelab ist der Upstream ein lokaler **Unbound** (eigenes Dokument), der Namen rekursiv ab den Root-Servern auflöst und DNSSEC validiert. Eine zweite AGH-Instanz wird per **adguardhome-sync** repliziert (eigenes Dokument).

### 2. Voraussetzungen

- Debian 12/13 oder Ubuntu, Root-Zugang (oder `sudo`).
- Eine **statische IP-Adresse** für den Host (`<agh-host-ip>`) – ändert sich die Adresse eines DNS-Servers, fällt DNS im ganzen Netz aus. Statisch am Host setzen oder per DHCP-Reservierung am Router.
- Freier Port **53** (TCP+UDP) und ein Port für die Weboberfläche.
- Bei aktiver Host-Firewall (ufw/nftables): 53/tcp, 53/udp, 3000/tcp (Einrichtungsassistent) und `<ui-port>`/tcp freigeben.

### 3. Installation A – Debian / Ubuntu (offizielles Skript)

**Warum diese Methode:** Sie wird von AdGuardTeam empfohlen. Das Skript lädt das offizielle Release herunter, entpackt es nach `/opt/AdGuardHome` und registriert AGH als systemd-Dienst (`AdGuardHome -s install`). Sonst nichts – keine Repositories, keine Abhängigkeiten.

**3.1 Werkzeuge:**

```bash
apt update && apt install -y curl bind9-dnsutils
```

`bind9-dnsutils` liefert `dig` für die Tests.

**3.2 Prüfen, ob Port 53 frei ist:**

```bash
ss -tulpn | grep ':53 '
```

Leere Ausgabe = frei. Unter **Ubuntu** belegt meist `systemd-resolved` den Port (Stub-Listener auf `127.0.0.53`). Deaktivieren laut AGH-Dokumentation:

```bash
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/adguardhome.conf << 'EOF'
[Resolve]
DNS=127.0.0.1
DNSStubListener=no
EOF
mv /etc/resolv.conf /etc/resolv.conf.backup
ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
systemctl reload-or-restart systemd-resolved
```

Ein reines Debian hat meist kein `systemd-resolved` – diesen Schritt überspringen.

**3.3 Skript herunterladen, prüfen, ausführen:**

Die offizielle Anleitung nutzt `curl ... | sh`. Besser: das Skript erst in eine Datei laden und durchsehen – du führst Code aus dem Internet als root aus.

```bash
curl -s -S -L -o /tmp/agh-install.sh \
  https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh
less /tmp/agh-install.sh
sh /tmp/agh-install.sh -v
```

`-v` = ausführliche Ausgabe (jeder Schritt sichtbar). Standardverzeichnis ist `/opt`, Kanal `release` (stabil).

**3.4 Dienst prüfen:**

```bash
systemctl status AdGuardHome
ss -tulpn | grep AdGuardHome
```

Erwartet: Dienst `active (running)`, lauscht auf Port `3000` (Einrichtungsassistent).

**3.5 Berechtigungen prüfen:**

```bash
stat -c '%a %U:%G %n' /opt/AdGuardHome /opt/AdGuardHome/AdGuardHome
```

Verzeichnis und Binary gehören `root:root` und **dürfen nicht für alle beschreibbar sein** (die letzte Ziffer darf nicht `7`, `6`, `3` oder `2` sein). Die Binary läuft als root – wer sie ersetzen kann, hat einen Weg zu root. Falls das Verzeichnis z. B. `777` hat:

```bash
chmod go-w /opt/AdGuardHome
```

> Aus Erfahrung: Nach einiger Zeit hatte das Verzeichnis auf meinem Host `777`, obwohl das Release-Archiv `755` mitbringt. Ursache unbekannt – deshalb auch nach Updates prüfen.

### 4. Installation B – Proxmox VE (Community Script, LXC)

**Wann:** Du nutzt Proxmox und willst AGH in einem schlanken LXC-Container. So läuft meine zweite Instanz.

**4.1** Skript auf der community-scripts-Website (Eintrag AdGuard Home) durchsehen, dann in der **Shell des Proxmox-Knotens**:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/adguard.sh)"
```

**4.2** Im Assistenten:

- Container-OS: **Debian 13** (Alpine möglich – kleiner, aber andere Dienstverwaltung),
- **Advanced settings** wählen und **statische IP** (`<agh-host-ip>/<prefix>`) sowie Gateway `<gateway-ip>` setzen – standardmäßig bekommt der Container eine DHCP-Adresse.

**4.3 Unterschiede zu Installation A:**

- das Skript installiert dasselbe offizielle Release nach `/opt/AdGuardHome`, legt aber eine **eigene** systemd-Unit an – Logs landen in `/var/log/AdGuardHome.out` und `/var/log/AdGuardHome.err`, nicht im Journal,
- im Debian-Container Updates nur über die Weboberfläche (das `update` des Skripts erledigt das nicht).

Prüfung wie in 3.4 und 3.5 – innerhalb des Containers (`pct enter <vmid>`).

### 5. Einrichtungsassistent

`http://<agh-host-ip>:3000` öffnen.

| Schritt | Einstellung | Warum |
| --- | --- | --- |
| Admin Web Interface | Interface mit `<agh-host-ip>`, Port `<ui-port>` | Lauschen auf einer bekannten Adresse statt „All interfaces“ (`0.0.0.0`) – die Oberfläche ist nicht auf Interfaces erreichbar, auf denen du sie nicht willst. |
| DNS server | Interface mit `<agh-host-ip>`, Port `53` | Gleicher Grund. Außerdem keine Konflikte mit anderen Diensten auf `127.0.0.1:53`. |
| Authentication | `<admin-user>` + langes Zufallspasswort aus dem Passwortmanager | Über die Oberfläche lassen sich Filterung abschalten und der Upstream des ganzen Netzes ändern. |

Nach dem Assistenten ist die Oberfläche unter `http://<agh-host-ip>:<ui-port>` erreichbar, Port `3000` lauscht nicht mehr.

### 6. Konfiguration – Einstellung für Einstellung

Alles wird in der Weboberfläche eingestellt. In Klammern steht der Schlüssel in `AdGuardHome.yaml` – hilfreich beim Vergleichen von Konfigurationen.

> **`AdGuardHome.yaml` nicht bei laufendem Dienst bearbeiten** – AGH überschreibt deine Änderungen. Manuelle Änderungen nur bei gestopptem Dienst (Abschnitt 9).

#### 6.1 Upstream-DNS – *Settings → DNS settings → Upstream DNS servers* (`dns.upstream_dns`)

- **Mit lokalem Unbound:** `127.0.0.1:5335`
- **Ohne Unbound:** ein verschlüsselter öffentlicher Resolver, z. B. `https://dns.quad9.net/dns-query`

Modus: **Load-balancing** (`upstream_mode: load_balance`) – bei einem Upstream egal, bei mehreren bevorzugt AGH den schnelleren und zuverlässigeren.

**Warum Unbound:** Deine Anfragen gehen nicht an einen einzelnen Anbieter (Google, Cloudflare, Quad9), der die komplette DNS-Historie deines Netzes sehen würde. Unbound fragt direkt die autoritativen Server und validiert DNSSEC selbst.

#### 6.2 Bootstrap-DNS (`dns.bootstrap_dns`)

```text
9.9.9.10
149.112.112.10
2620:fe::10
2620:fe::fe:10
```

**Warum:** Bootstrap dient nur dazu, den **Hostnamen** eines Upstreams (z. B. `dns.quad9.net`) aufzulösen – das Henne-Ei-Problem. Bei einem Upstream als IP (`127.0.0.1:5335`) wird er praktisch nicht genutzt, muss aber für einen späteren Upstream-Wechsel korrekt sein.

#### 6.3 Private reverse DNS servers (`dns.local_ptr_upstreams`, `dns.use_private_ptr_resolvers`)

Damit zeigt das Abfrageprotokoll Gerätenamen statt `<client-ip>`. AGH schickt PTR-Anfragen für private Adressen **nur** an lokale Resolver (damit nichts nach außen dringt). Leere Liste = AGH nimmt die Resolver des Host-Betriebssystems.

Trage einen Server ein, der die Client-Namen kennt – meist den Router/DHCP-Server. Vorher prüfen, ob er überhaupt antwortet:

```bash
dig -x <client-ip> @<gateway-ip> +short
```

Name in der Antwort → `<gateway-ip>` eintragen. Leere Antwort → der Router beherrscht kein PTR; Client-Namen kannst du manuell unter *Settings → Client settings* vergeben.

#### 6.4 Rate limit (`dns.ratelimit`) → `0`

Standard sind `20` Anfragen/s – **gezählt pro /24-Subnetz** (`ratelimit_subnet_len_ipv4: 24`), nicht pro Client. Im Heimnetz teilt sich also das ganze Subnetz 20 Anfragen/s; alles darüber wird stillschweigend verworfen. Dieser Schutz ist für öffentliche Server gedacht (Amplification-Angriffe); laut AGH-Dokumentation kann er abgeschaltet werden, wenn der Server nicht aus dem Internet erreichbar ist.

`Refuse ANY` (`refuse_any: true`) eingeschaltet lassen – schadet nicht, ANY-Anfragen werden praktisch nicht genutzt.

#### 6.5 Allowed clients – *Settings → DNS settings → Access settings* (`dns.allowed_clients`)

```text
<lan-subnet>
127.0.0.0/8
```

**Warum:** Ist die Liste nicht leer, antwortet AGH **ausschließlich** diesen Clients. Eine zweite Verteidigungslinie neben der Firewall – selbst bei einem Fehler in den Netzwerkregeln wird der Server kein offener Resolver.

⚠️ Vor dem Speichern alle Subnetze (VLANs, VPN) eintragen – ausgelassene Netze verlieren sofort DNS.

#### 6.6 DNSSEC (`dns.enable_dnssec`) → aus bei Unbound

Die Option setzt nur das DO-Bit in Upstream-Anfragen und zeigt den Status im Protokoll. **Die Validierung übernimmt Unbound** – bei ungültiger Signatur liefert er SERVFAIL, der Client bekommt also ohnehin keine gefälschte Antwort.

#### 6.7 Cache (`dns.cache_*`)

- Größe: Standard (4 MB) – reicht für ein Heimnetz,
- **Optimistic caching: aus** – eingeschaltet liefert AGH auch abgelaufene Einträge. Unbound hat eigenen Cache und Prefetch, der Gewinn ist also klein, das Risiko veralteter Antworten (z. B. nach IP-Wechsel eines Dienstes) real.

#### 6.8 Blocklisten – *Filters → DNS blocklists* (`filters`)

Mein Satz (alle über „Add blocklist → Choose from the list“):

| Liste | Zweck |
| --- | --- |
| AdGuard DNS filter | Werbung und Tracker – Basis |
| AdAway Default Blocklist | mobile Werbung |
| OISD Blocklist Small | breit, gut gepflegt, wenige Fehlalarme |
| Peter Lowe's Blocklist | Werbung/Tracker |
| POL: CERT Polska List of malicious domains | schädliche Domains (PL) |
| Phishing URL Blocklist (PhishTank and OpenPhish) | Phishing |
| Malicious URL Blocklist (URLHaus) | Malware |

**Prinzip:** wenige gut gepflegte Listen statt Dutzender – mehr Listen bedeuten mehr RAM und mehr Fehlblockierungen bei kaum Mehrwert. Aktualisierungsintervall: 24 h (Standard).

#### 6.9 DNS rewrites – *Filters → DNS rewrites* (`filtering.rewrites`) – optional

```text
*.<your-domain>  →  <reverse-proxy-ip>
```

**Split-Horizon-DNS:** Im LAN zeigen die Subdomains deiner Domain direkt auf den lokalen Reverse Proxy, statt ins Internet und zurück zu gehen. Funktioniert auch bei ausgefallener Internetverbindung.

#### 6.10 Abfrageprotokoll und Statistik – *Settings → General settings*

- Abfrageprotokoll: bei mir 90 Tage (Standard), Statistik: 24 h.
- Auf kleinem Flash-Speicher (eMMC, SD-Karte) kürzere Aufbewahrung erwägen – das Protokoll wird laufend auf die Platte geschrieben.

#### 6.11 Sonstiges – *Settings → General settings*

- **Blocking mode: Default** – blockierte Domains bekommen `0.0.0.0` / `::`, der Client gibt sofort auf.
- **Browsing security / Parental control: aus** – beide funktionieren über Anfragen an AdGuard-Server (Hash-Präfixe der Domains). Die Schutzfunktion übernehmen bereits die Listen aus 6.8, ohne etwas nach außen zu senden.

### 7. Netz auf AGH umstellen

Am Router in den **DHCP**-Einstellungen `<agh-host-ip>` als DNS-Server eintragen.

- **Keinen öffentlichen DNS als zweiten Server eintragen** (z. B. `8.8.8.8`) – Clients nutzen beide Server abwechselnd, ein Teil der Anfragen umgeht dann die Filterung.
- Für Redundanz sollte der zweite Server eine **zweite AGH-Instanz** sein (synchronisiert per adguardhome-sync).

Clients übernehmen den neuen DNS nach Erneuerung der DHCP-Lease (oder nach erneutem Verbinden).

### 8. Überprüfung

```bash
# Normal resolution
dig @<agh-host-ip> example.com +short

# Blocked domain → expected 0.0.0.0
dig @<agh-host-ip> doubleclick.net +short

# Service logs
journalctl -u AdGuardHome -n 50 --no-pager
```

Unter Windows: `nslookup example.com` – im Feld `Server` muss `<agh-host-ip>` stehen. Zum Schluss im *Query log* der Oberfläche prüfen, ob Client-Anfragen ankommen.

### 9. Wartung

**Update:** Button in der Oberfläche (erscheint bei neuer Version) oder per CLI:

```bash
/opt/AdGuardHome/AdGuardHome --update
```

Nach dem Update die Berechtigungsprüfung aus 3.5 wiederholen.

**Manuelle Konfigurationsänderung:**

```bash
systemctl stop AdGuardHome
cp /opt/AdGuardHome/AdGuardHome.yaml /opt/AdGuardHome/AdGuardHome.yaml.bak
vi /opt/AdGuardHome/AdGuardHome.yaml
/opt/AdGuardHome/AdGuardHome --check-config -c /opt/AdGuardHome/AdGuardHome.yaml
systemctl start AdGuardHome
```

**Backup:** `/opt/AdGuardHome/AdGuardHome.yaml` (gesamte Konfiguration) + `/opt/AdGuardHome/data/` (Protokoll, Statistik, Listen).

**Passwort zurücksetzen:** bcrypt-Hash erzeugen und unter `users → password` eintragen (Dienst gestoppt):

```bash
apt install -y apache2-utils
htpasswd -B -C 10 -n -b <admin-user> '<new-password>'
```

### 10. Bekannte Einschränkungen

- **Oberfläche über unverschlüsseltes HTTP.** Das Passwort geht im LAN im Klartext über die Leitung. Zugriff per Firewall auf das Management-Netz beschränken oder über einen Reverse Proxy mit Zertifikat bereitstellen.
- **Client-Namen im Protokoll** hängen davon ab, ob der Router PTR-Anfragen beantwortet (6.3).

### 11. Verwandte Dokumente

- Unbound – rekursiver Resolver als Upstream
- adguardhome-sync – Replikation der Konfiguration auf eine zweite Instanz

---

## Polski

[English](#english) · [Deutsch](#deutsch) · [Polski](#polski)

### 0. Placeholdery

W całym dokumencie zamiast prawdziwych adresów są placeholdery. Wstaw w ich miejsce własne wartości.

| Placeholder | Co wstawić |
| --- | --- |
| `<agh-host-ip>` | Statyczny adres IP maszyny, na której działa AdGuard Home |
| `<lan-subnet>` | Podsieć (CIDR), z której klienci mogą odpytywać DNS, np. twoja sieć domowa. Może być kilka wpisów |
| `<gateway-ip>` | Adres routera / bramy (zwykle też serwer DHCP) |
| `<admin-user>` | Nazwa konta administratora panelu AGH |
| `<your-domain>` | Twoja domena, jeśli używasz split-horizon DNS (sekcja 6.9) |
| `<reverse-proxy-ip>` | Adres reverse proxy (np. Nginx Proxy Manager) w sieci lokalnej |
| `<client-ip>` | Adres dowolnego klienta w sieci – do testów |
| `<ui-port>` | Port panelu WWW po instalacji (u mnie `80`) |

### 1. Co to jest i gdzie leży w architekturze

AdGuard Home (AGH) to serwer DNS z filtrowaniem. Nie rozwiązuje nazw sam – jest **forwarderem**: przyjmuje zapytanie od klienta, sprawdza je z listami blokad, a jeśli domena nie jest zablokowana, przekazuje zapytanie dalej do **upstreamu** i zapamiętuje odpowiedź w cache.

```text
Client ──► AdGuard Home (<agh-host-ip>:53) ──► Upstream
            │ blocklists                         │
            │ cache                              ├─ Unbound (127.0.0.1:5335) – recursive, DNSSEC
            │ rewrites                           └─ or a public resolver (e.g. Quad9 DoH)
            └─ query log / statistics
```

W moim homelabie upstreamem jest lokalny **Unbound** (osobny dokument), który rozwiązuje nazwy rekurencyjnie od serwerów root i waliduje DNSSEC. Druga instancja AGH jest replikowana przez **adguardhome-sync** (osobny dokument).

### 2. Wymagania

- Debian 12/13 lub Ubuntu, dostęp root (lub `sudo`).
- **Statyczny adres IP** hosta (`<agh-host-ip>`) – serwer DNS, któremu zmienia się adres, przestaje działać dla całej sieci. Ustaw go statycznie w systemie albo przez rezerwację DHCP na routerze.
- Wolny port **53** (TCP+UDP) oraz port na panel WWW.
- Jeśli na hoście działa firewall (ufw/nftables): zezwól na 53/tcp, 53/udp, 3000/tcp (kreator) i `<ui-port>`/tcp.

### 3. Instalacja A – Debian / Ubuntu (oficjalny skrypt)

**Dlaczego ta metoda:** to metoda zalecana przez AdGuardTeam. Skrypt pobiera oficjalne wydanie, rozpakowuje je do `/opt/AdGuardHome` i rejestruje AGH jako usługę systemd (`AdGuardHome -s install`). Nic więcej – nie dodaje repozytoriów ani zależności.

**3.1 Narzędzia:**

```bash
apt update && apt install -y curl bind9-dnsutils
```

`bind9-dnsutils` daje polecenie `dig`, potrzebne do testów.

**3.2 Sprawdź, czy port 53 jest wolny:**

```bash
ss -tulpn | grep ':53 '
```

Pusty wynik = wolny. Na **Ubuntu** port zwykle zajmuje `systemd-resolved` (stub listener na `127.0.0.53`). Wyłącz go zgodnie z dokumentacją AGH:

```bash
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/adguardhome.conf << 'EOF'
[Resolve]
DNS=127.0.0.1
DNSStubListener=no
EOF
mv /etc/resolv.conf /etc/resolv.conf.backup
ln -s /run/systemd/resolve/resolv.conf /etc/resolv.conf
systemctl reload-or-restart systemd-resolved
```

Na czystym Debianie `systemd-resolved` zwykle nie jest zainstalowany – ten krok pomijasz.

**3.3 Pobierz skrypt, przejrzyj go, uruchom:**

Oficjalna instrukcja to `curl ... | sh`. Lepiej jest najpierw pobrać skrypt do pliku i go przejrzeć – uruchamiasz kod z internetu jako root.

```bash
curl -s -S -L -o /tmp/agh-install.sh \
  https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh
less /tmp/agh-install.sh
sh /tmp/agh-install.sh -v
```

`-v` = tryb szczegółowy (widzisz każdy krok). Domyślny katalog to `/opt`, kanał `release` (stabilny).

**3.4 Weryfikacja usługi:**

```bash
systemctl status AdGuardHome
ss -tulpn | grep AdGuardHome
```

Oczekiwane: usługa `active (running)`, nasłuch na porcie `3000` (kreator pierwszego uruchomienia).

**3.5 Weryfikacja uprawnień:**

```bash
stat -c '%a %U:%G %n' /opt/AdGuardHome /opt/AdGuardHome/AdGuardHome
```

Katalog i binarka należą do `root:root` i **nie mogą być zapisywalne dla wszystkich** (ostatnia cyfra nie może być `7`, `6`, `3` ani `2`). Binarka działa jako root – jeśli dowolny użytkownik może ją podmienić, ma drogę do roota. Gdyby katalog miał np. `777`:

```bash
chmod go-w /opt/AdGuardHome
```

> Z doświadczenia: po jakimś czasie na moim hoście katalog miał `777`, choć archiwum wydania ma `755`. Przyczyna nieustalona – dlatego sprawdzaj to także po aktualizacjach.

### 4. Instalacja B – Proxmox VE (Community Script, LXC)

**Kiedy:** masz Proxmoxa i chcesz AGH w lekkim kontenerze LXC. Tak działa moja druga instancja.

**4.1** Przejrzyj skrypt na stronie community-scripts (sekcja AdGuard Home), potem w **shellu węzła Proxmox**:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/ct/adguard.sh)"
```

**4.2** W kreatorze:

- system kontenera: **Debian 13** (alternatywnie Alpine – mniejszy, ale inne zarządzanie usługą),
- wybierz **Advanced settings** i ustaw **statyczne IP** (`<agh-host-ip>/<prefix>`) oraz bramę `<gateway-ip>` – domyślnie kontener dostaje adres z DHCP.

**4.3 Różnice względem instalacji A:**

- skrypt instaluje to samo oficjalne wydanie do `/opt/AdGuardHome`, ale tworzy **własny** unit systemd – logi idą do `/var/log/AdGuardHome.out` i `/var/log/AdGuardHome.err`, a nie do journala,
- aktualizacja w kontenerze Debian tylko przez panel WWW (skrypt `update` tego nie robi).

Weryfikacja jak w 3.4 i 3.5 – wewnątrz kontenera (`pct enter <vmid>`).

### 5. Kreator pierwszego uruchomienia

Otwórz `http://<agh-host-ip>:3000`.

| Krok | Ustawienie | Dlaczego |
| --- | --- | --- |
| Admin Web Interface | interfejs z `<agh-host-ip>`, port `<ui-port>` | Nasłuch tylko na jednym, znanym adresie zamiast „All interfaces” (`0.0.0.0`) – panel nie jest wystawiony na interfejsach, na których go nie chcesz. |
| DNS server | interfejs z `<agh-host-ip>`, port `53` | Jw. Dodatkowo unikasz konfliktu z innymi usługami na `127.0.0.1:53`. |
| Authentication | `<admin-user>` + długie losowe hasło z menedżera haseł | Panel pozwala wyłączyć filtrowanie i zmienić upstream całej sieci. |

Po kreatorze panel jest pod `http://<agh-host-ip>:<ui-port>`, a port `3000` przestaje nasłuchiwać.

### 6. Konfiguracja – ustawienie po ustawieniu

Wszystko ustawiasz w panelu. W nawiasie podaję klucz w `AdGuardHome.yaml` – przydaje się przy porównywaniu konfiguracji.

> **Nie edytuj `AdGuardHome.yaml`, gdy usługa działa** – AGH nadpisze twoje zmiany. Edycja ręczna tylko przy zatrzymanej usłudze (sekcja 9).

#### 6.1 Upstream DNS – *Settings → DNS settings → Upstream DNS servers* (`dns.upstream_dns`)

- **Z lokalnym Unbound:** `127.0.0.1:5335`
- **Bez Unbound:** szyfrowany publiczny resolver, np. `https://dns.quad9.net/dns-query`

Tryb: **Load-balancing** (`upstream_mode: load_balance`) – przy jednym upstreamie bez znaczenia, przy kilku AGH wybiera szybszy i mniej zawodny.

**Dlaczego Unbound:** zapytania nie trafiają do jednego dostawcy (Google, Cloudflare, Quad9), który widziałby całą historię DNS twojej sieci. Unbound pyta bezpośrednio serwery autorytatywne i sam waliduje DNSSEC.

#### 6.2 Bootstrap DNS (`dns.bootstrap_dns`)

```text
9.9.9.10
149.112.112.10
2620:fe::10
2620:fe::fe:10
```

**Dlaczego:** bootstrap służy tylko do rozwiązania **nazwy** upstreamu (np. `dns.quad9.net`) – problem „jajka i kury”. Przy upstreamie podanym jako IP (`127.0.0.1:5335`) praktycznie nie jest używany, ale musi być poprawnie ustawiony na wypadek zmiany upstreamu.

#### 6.3 Private reverse DNS servers (`dns.local_ptr_upstreams`, `dns.use_private_ptr_resolvers`)

Dzięki temu w logu zapytań zamiast `<client-ip>` widzisz nazwę urządzenia. AGH wysyła zapytania PTR dla adresów prywatnych **tylko** do lokalnych resolverów (żeby nie wyciekały na zewnątrz). Pusta lista = AGH bierze resolvery z systemu hosta.

Wpisz tu serwer, który zna nazwy klientów – zwykle router/serwer DHCP. Najpierw sprawdź, czy w ogóle odpowiada:

```bash
dig -x <client-ip> @<gateway-ip> +short
```

Nazwa w odpowiedzi → wpisz `<gateway-ip>`. Pusta odpowiedź → router nie obsługuje PTR, nazwy klientów możesz nadać ręcznie w *Settings → Client settings*.

#### 6.4 Rate limit (`dns.ratelimit`) → `0`

Domyślnie `20` zapytań/s – **liczone per podsieć /24** (`ratelimit_subnet_len_ipv4: 24`), nie per klient. W sieci domowej cała podsieć dzieli więc jedną pulę 20 zapytań/s, a nadmiar jest po cichu odrzucany. Ta ochrona ma sens dla serwerów publicznych (ataki amplifikacji); dokumentacja AGH wprost mówi, że można ją wyłączyć, jeśli serwer nie jest dostępny z internetu.

`Refuse ANY` (`refuse_any: true`) zostaw włączone – nie przeszkadza, zapytania ANY są praktycznie nieużywane.

#### 6.5 Allowed clients – *Settings → DNS settings → Access settings* (`dns.allowed_clients`)

```text
<lan-subnet>
127.0.0.0/8
```

**Dlaczego:** gdy lista nie jest pusta, AGH odpowiada **wyłącznie** tym klientom. To druga warstwa obrony obok firewalla – nawet przy błędzie w regułach sieci serwer nie stanie się otwartym resolverem.

⚠️ Dopisz wszystkie swoje podsieci (VLAN-y, VPN), zanim zapiszesz – pominięte sieci od razu stracą DNS.

#### 6.6 DNSSEC (`dns.enable_dnssec`) → wyłączone przy Unbound

Ta opcja jedynie ustawia bit DO w zapytaniach do upstreamu i pokazuje status w logu. **Walidację robi Unbound** – przy podpisie niepoprawnym zwraca SERVFAIL, więc klient i tak nie dostanie sfałszowanej odpowiedzi.

#### 6.7 Cache (`dns.cache_*`)

- rozmiar: domyślny (4 MB) – wystarczy dla sieci domowej,
- **Optimistic caching: wyłączony** – przy włączonym AGH zwraca też wygasłe wpisy. Unbound ma własny cache i prefetch, więc zysk jest niewielki, a ryzyko nieaktualnej odpowiedzi (np. po zmianie IP usługi) realne.

#### 6.8 Listy blokad – *Filters → DNS blocklists* (`filters`)

Mój zestaw (wszystkie z katalogu „Add blocklist → Choose from the list”):

| Lista | Po co |
| --- | --- |
| AdGuard DNS filter | reklamy i trackery – baza |
| AdAway Default Blocklist | reklamy mobilne |
| OISD Blocklist Small | szeroka, dobrze utrzymana, mało fałszywych alarmów |
| Peter Lowe's Blocklist | reklamy/trackery |
| POL: CERT Polska List of malicious domains | złośliwe domeny (PL) |
| Phishing URL Blocklist (PhishTank and OpenPhish) | phishing |
| Malicious URL Blocklist (URLHaus) | malware |

**Zasada:** kilka dobrze utrzymanych list zamiast kilkudziesięciu – więcej list to więcej RAM i więcej fałszywych blokad, przy znikomym zysku. Interwał aktualizacji: 24 h (domyślny).

#### 6.9 DNS rewrites – *Filters → DNS rewrites* (`filtering.rewrites`) – opcjonalnie

```text
*.<your-domain>  →  <reverse-proxy-ip>
```

**Split-horizon DNS:** w sieci lokalnej subdomeny twojej domeny wskazują bezpośrednio na lokalny reverse proxy, zamiast wychodzić do internetu i wracać. Działa też, gdy łącze do internetu padnie.

#### 6.10 Query log i statystyki – *Settings → General settings*

- Query log: u mnie 90 dni (domyślnie), statystyki: 24 h.
- Na małym nośniku flash (eMMC, karta SD) rozważ krótszą retencję logu – log jest zapisywany na dysk ciągle.

#### 6.11 Pozostałe – *Settings → General settings*

- **Blocking mode: Default** – zablokowane domeny dostają `0.0.0.0` / `::`, klient od razu rezygnuje.
- **Browsing security / Parental control: wyłączone** – działają przez zapytania do serwerów AdGuard (prefiksy hashy domen). Funkcję ochronną pełnią już listy z 6.8, bez wysyłania czegokolwiek na zewnątrz.

### 7. Skieruj sieć na AGH

Na routerze, w ustawieniach **DHCP**, jako serwer DNS podaj `<agh-host-ip>`.

- **Nie dodawaj publicznego DNS jako drugiego** (np. `8.8.8.8`) – klienci używają obu serwerów zamiennie, więc część zapytań ominie filtrowanie.
- Jeśli chcesz redundancji, drugim serwerem powinna być **druga instancja AGH** (synchronizowana przez adguardhome-sync).

Klienci przejmą nowy DNS po odnowieniu dzierżawy DHCP (albo po ponownym połączeniu z siecią).

### 8. Weryfikacja

```bash
# Normal resolution
dig @<agh-host-ip> example.com +short

# Blocked domain → expected 0.0.0.0
dig @<agh-host-ip> doubleclick.net +short

# Service logs
journalctl -u AdGuardHome -n 50 --no-pager
```

Na Windowsie: `nslookup example.com` – w polu `Server` musi pojawić się `<agh-host-ip>`. Na koniec sprawdź w panelu *Query log*, czy widać zapytania od klientów.

### 9. Utrzymanie

**Aktualizacja:** przycisk w panelu (pojawia się przy nowej wersji) albo z CLI:

```bash
/opt/AdGuardHome/AdGuardHome --update
```

Po aktualizacji powtórz kontrolę uprawnień z 3.5.

**Ręczna edycja konfiguracji:**

```bash
systemctl stop AdGuardHome
cp /opt/AdGuardHome/AdGuardHome.yaml /opt/AdGuardHome/AdGuardHome.yaml.bak
vi /opt/AdGuardHome/AdGuardHome.yaml
/opt/AdGuardHome/AdGuardHome --check-config -c /opt/AdGuardHome/AdGuardHome.yaml
systemctl start AdGuardHome
```

**Backup:** `/opt/AdGuardHome/AdGuardHome.yaml` (cała konfiguracja) + `/opt/AdGuardHome/data/` (log, statystyki, listy).

**Reset hasła:** wygeneruj hash bcrypt i wpisz go w `users → password` (przy zatrzymanej usłudze):

```bash
apt install -y apache2-utils
htpasswd -B -C 10 -n -b <admin-user> '<new-password>'
```

### 10. Znane ograniczenia

- **Panel po HTTP bez TLS.** Hasło leci otwartym tekstem w sieci lokalnej. Ogranicz dostęp do panelu firewallem do sieci administracyjnej albo wystaw go przez reverse proxy z certyfikatem.
- **Nazwy klientów w logu** zależą od tego, czy router odpowiada na PTR (6.3).

### 11. Powiązane dokumenty

- Unbound – rekurencyjny resolver jako upstream
- adguardhome-sync – replikacja konfiguracji do drugiej instancji
