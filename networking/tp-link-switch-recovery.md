# 🛠️ TP-Link Switch Recovery — Incident Log

**Languages:** [🇬🇧 English](#-english) | [🇩🇪 Deutsch](#-deutsch) | [🇵🇱 Polski](#-polski)

---

## 🇬🇧 English

### Summary

Recurring connectivity loss on a TP-Link TL-SG108PE managed switch across three separate incidents (March 2026 and July 2026). The switch keeps traffic flowing correctly between connected devices, but its own management plane becomes unreachable — first attributed to a factory reset, later to a DHCP lease issue, and finally suspected to be a firmware/hardware stability problem since it also occurred with a static IP configured.

### Incident #1 & #2 (17–18 March 2026)

**Trigger:** Planned port reconfiguration for a new Proxmox node.

**What happened:**
- The switch lost network contact and reset to its factory default IP (`192.168.x.x`).
- The firewall's device inventory showed the same MAC address in two different subnets at once (the factory-default subnet and the management VLAN), causing inventory/ARP conflicts.

**Recovery steps:**

1. Set a static IP on a laptop (`192.168.x.x`) and connect directly to the switch to reconfigure it.
1. On the firewall: clear the device inventory cache and the ARP table.
1. Re-confirm the DHCP reservation for the switch's MAC address on the management IP.
1. Force-refresh camera IP leases by disabling/re-enabling their switch ports (link flap) so they re-acquire an address on the correct VLAN.

**Lessons noted at the time:**

- Always download a `.bin` configuration backup after any change.
- Port Config → Disable/Enable is a simple way to force a device to renew its DHCP lease without touching PoE settings.
- An access point running in bridge mode needs its uplink port tagged for the data VLAN, while the port's PVID stays on the untagged management VLAN.

### Incident #3 (16 July 2026)

**Trigger:** No configuration change this time — Uptime Kuma reported the switch unreachable via ping. All connected devices (Proxmox host, cameras, access point) kept working normally; only the switch's own management IP stopped responding.

**Key diagnostic finding:** This time the switch had a **static IP already configured** — not a DHCP lease. It still became unreachable. This rules out "DHCP lease not renewed" as the root cause and points instead to a firmware or hardware-level fault causing the management stack to hang while the data plane keeps switching traffic normally.

**Recovery steps:**

1. Attempted remote diagnostics (clearing firewall device inventory, checking ARP) — no effect, unlike previous incidents.
1. Attempted to reach the switch from a directly-connected host by adding a temporary IP in the same subnet — no response.
1. Physical recovery: connected a laptop directly to the switch via a spare cable, bypassing the rest of the network entirely. This worked.
1. Updated the switch firmware to the latest available version.
1. Set a static IP directly on the switch (not via DHCP reservation).
1. Removed the DHCP MAC reservation on the firewall (no longer needed/relevant) and replaced it with a plain `/32` address object for firewall policy reference only.
1. Downloaded a fresh `.bin` configuration backup.

**Decision going forward:** Given this is the third occurrence — and the second time it happened despite doing "everything right" (static IP, no DHCP dependency) — the switch is being kept for now (budget reasons), but any further recurrence will trigger a replacement rather than another repair cycle. Candidates under consideration: Netgear GS308EP (smart-managed, all 8 ports PoE+) or a used FortiSwitch FS-108E-POE (full integration with the existing FortiGate via FortiLink, single-pane-of-glass management).

### Target VLAN Configuration (TP-Link, valid across incidents)

| Port | Device | VLAN 1 (Mgmt) | VLAN 20 (Server) | VLAN 90 (IoT) | PVID |
| :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Camera 1 | – | – | Untagged | 90 |
| 2 | Camera 2 | – | – | Untagged | 90 |
| 3 | Service port | Untagged | – | – | 1 |
| 4 | Access point | Untagged | – | Tagged | 1 |
| 5 | Service port | Untagged | – | – | 1 |
| 6 | Proxmox Node 2 | – | Untagged | – | 20 |
| 7 | Proxmox Node 1 | – | Untagged | – | 20 |
| 8 | Firewall uplink | Untagged | Tagged | Tagged | 1 |

### Key Takeaways

- 💾 **Always back up.** Download the `.bin` config file after every change — the switch has been fully reset twice.
- 🔌 **Static IP is not a silver bullet.** It prevented the DHCP-related failure mode but did *not* prevent the third incident — suggesting a deeper firmware/hardware issue.
- 🌐 **Management plane ≠ data plane.** In both incidents, connected devices kept working perfectly while the switch's own management interface was completely unreachable — these are separate failure domains.
- 🧹 **Firewall-side cache matters.** Clearing device inventory and ARP tables on the firewall was necessary (though not sufficient in incident #3) to resolve IP/MAC conflicts.
- ⚡ **Power stability is an open risk.** No UPS is currently in place; a brief power event is suspected as a possible trigger and is being evaluated as a future mitigation.

---

## 🇩🇪 Deutsch

### Zusammenfassung

Wiederkehrender Verbindungsverlust an einem verwalteten TP-Link TL-SG108PE Switch über drei separate Vorfälle hinweg (März 2026 und Juli 2026). Der Switch leitet den Datenverkehr zwischen den angeschlossenen Geräten weiterhin korrekt weiter, aber seine eigene Management-Ebene wird unerreichbar — zunächst einem Werksreset zugeschrieben, später einem DHCP-Lease-Problem, und schließlich als mögliches Firmware-/Hardware-Stabilitätsproblem vermutet, da es auch bei konfigurierter statischer IP auftrat.

### Vorfall #1 & #2 (17.–18. März 2026)

**Auslöser:** Geplante Port-Neukonfiguration für einen neuen Proxmox-Node.

**Was geschah:**

- Der Switch verlor den Netzwerkkontakt und setzte sich auf seine werksseitige Standard-IP (`192.168.x.x`) zurück.
- Das Geräteinventar der Firewall zeigte dieselbe MAC-Adresse gleichzeitig in zwei verschiedenen Subnetzen (dem Werks-Standard-Subnetz und dem Management-VLAN), was zu Inventar-/ARP-Konflikten führte.

**Wiederherstellungsschritte:**

1. Statische IP auf einem Laptop (`192.168.x.x`) gesetzt und direkt mit dem Switch verbunden, um ihn neu zu konfigurieren.
1. Auf der Firewall: Geräteinventar-Cache und ARP-Tabelle geleert.
1. DHCP-Reservierung für die MAC-Adresse des Switches auf der Management-IP erneut bestätigt.
1. IP-Lease der Kameras durch Deaktivieren/Aktivieren ihrer Switch-Ports (Link-Flap) erzwungen, damit sie eine Adresse im richtigen VLAN neu beziehen.

**Damals notierte Erkenntnisse:**

- Nach jeder Änderung immer ein `.bin`-Konfigurationsbackup herunterladen.
- Port Config → Disable/Enable ist eine einfache Methode, ein Gerät zur Erneuerung seines DHCP-Lease zu zwingen, ohne die PoE-Einstellungen zu berühren.
- Ein Access Point im Bridge-Modus benötigt einen getaggten Uplink-Port für das Daten-VLAN, während die PVID des Ports im untagged Management-VLAN bleibt.

### Vorfall #3 (16. Juli 2026)

**Auslöser:** Diesmal keine Konfigurationsänderung — Uptime Kuma meldete den Switch als per Ping nicht erreichbar. Alle angeschlossenen Geräte (Proxmox-Host, Kameras, Access Point) funktionierten normal weiter; nur die eigene Management-IP des Switches reagierte nicht mehr.

**Zentrale diagnostische Erkenntnis:** Diesmal hatte der Switch bereits eine **statische IP konfiguriert** — kein DHCP-Lease. Er wurde trotzdem unerreichbar. Das schließt "DHCP-Lease nicht erneuert" als Grundursache aus und deutet stattdessen auf einen Fehler auf Firmware- oder Hardware-Ebene hin, bei dem der Management-Stack hängen bleibt, während die Datenebene den Verkehr weiterhin normal schaltet.

**Wiederherstellungsschritte:**

1. Remote-Diagnose versucht (Geräteinventar der Firewall leeren, ARP prüfen) — anders als bei früheren Vorfällen ohne Wirkung.
1. Versucht, den Switch von einem direkt verbundenen Host aus durch temporäre IP im selben Subnetz zu erreichen — keine Reaktion.
1. Physische Wiederherstellung: Laptop direkt per Ersatzkabel mit dem Switch verbunden, den Rest des Netzwerks komplett umgangen. Das funktionierte.
1. Switch-Firmware auf die neueste verfügbare Version aktualisiert.
1. Statische IP direkt auf dem Switch gesetzt (nicht über DHCP-Reservierung).
1. DHCP-MAC-Reservierung auf der Firewall entfernt (nicht mehr benötigt/relevant) und durch ein einfaches `/32`-Adressobjekt nur zur Referenz in Firewall-Policies ersetzt.
1. Neues `.bin`-Konfigurationsbackup heruntergeladen.

**Weiteres Vorgehen:** Da dies der dritte Vorfall ist — und der zweite, obwohl "alles richtig gemacht" wurde (statische IP, keine DHCP-Abhängigkeit) — bleibt der Switch vorerst im Einsatz (aus Budgetgründen), aber ein weiteres Auftreten führt zum Austausch statt zu einer erneuten Reparaturrunde. In Betracht gezogene Kandidaten: Netgear GS308EP (Smart-Managed, alle 8 Ports PoE+) oder ein gebrauchter FortiSwitch FS-108E-POE (volle Integration mit der vorhandenen FortiGate via FortiLink, zentrale Verwaltung aus einer Oberfläche).

### Ziel-VLAN-Konfiguration (TP-Link, über alle Vorfälle hinweg gültig)

| Port | Gerät | VLAN 1 (Mgmt) | VLAN 20 (Server) | VLAN 90 (IoT) | PVID |
| :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Kamera 1 | – | – | Untagged | 90 |
| 2 | Kamera 2 | – | – | Untagged | 90 |
| 3 | Service-Port | Untagged | – | – | 1 |
| 4 | Access Point | Untagged | – | Tagged | 1 |
| 5 | Service-Port | Untagged | – | – | 1 |
| 6 | Proxmox Node 2 | – | Untagged | – | 20 |
| 7 | Proxmox Node 1 | – | Untagged | – | 20 |
| 8 | Firewall-Uplink | Untagged | Tagged | Tagged | 1 |

### Wichtigste Erkenntnisse

- 💾 **Immer Backups anlegen.** Nach jeder Änderung die `.bin`-Konfigurationsdatei herunterladen — der Switch wurde bereits zweimal komplett zurückgesetzt.
- 🔌 **Statische IP ist keine Wunderwaffe.** Sie verhinderte den DHCP-bedingten Fehlerfall, verhinderte aber *nicht* den dritten Vorfall — das deutet auf ein tieferliegendes Firmware-/Hardware-Problem hin.
- 🌐 **Management-Ebene ≠ Datenebene.** In beiden Vorfällen funktionierten die angeschlossenen Geräte einwandfrei weiter, während die eigene Management-Schnittstelle des Switches komplett unerreichbar war — das sind getrennte Fehlerdomänen.
- 🧹 **Firewall-seitiger Cache ist relevant.** Das Leeren von Geräteinventar und ARP-Tabelle auf der Firewall war notwendig (wenn auch bei Vorfall #3 nicht ausreichend), um IP-/MAC-Konflikte zu lösen.
- ⚡ **Stromstabilität ist ein offenes Risiko.** Derzeit ist keine USV vorhanden; ein kurzer Stromausfall wird als möglicher Auslöser vermutet und als künftige Gegenmaßnahme geprüft.

---

## 🇵🇱 Polski

### Podsumowanie

Powtarzająca się utrata łączności na zarządzalnym switchu TP-Link TL-SG108PE w trakcie trzech osobnych incydentów (marzec 2026 i lipiec 2026). Switch nadal poprawnie przełącza ruch między podłączonymi urządzeniami, ale jego własna płaszczyzna zarządzania staje się nieosiągalna — najpierw przypisano to resetowi do ustawień fabrycznych, później problemowi z DHCP lease, a ostatecznie podejrzewa się problem stabilności firmware/hardware, ponieważ wystąpiło to również przy skonfigurowanym statycznym IP.

### Incydent #1 i #2 (17–18 marca 2026)

**Wyzwalacz:** Planowa rekonfiguracja portu pod nowy node Proxmoksa.

**Co się stało:**

- Switch stracił łączność sieciową i zresetował się do domyślnego fabrycznego IP (`192.168.x.x`).
- Inwentarz urządzeń na firewallu pokazywał ten sam adres MAC jednocześnie w dwóch różnych podsieciach (domyślnej fabrycznej i VLAN zarządzania), co powodowało konflikty inwentarza/ARP.

**Kroki naprawcze:**

1. Ustawienie statycznego IP na laptopie (`192.168.x.x`) i bezpośrednie podłączenie do switcha w celu jego rekonfiguracji.
1. Na firewallu: wyczyszczenie cache inwentarza urządzeń oraz tablicy ARP.
1. Ponowne potwierdzenie rezerwacji DHCP dla adresu MAC switcha na IP zarządzania.
1. Wymuszenie odświeżenia lease'ów IP kamer poprzez wyłączenie/włączenie ich portów (link flap), aby ponownie pobrały adres z właściwego VLAN-u.

**Wnioski zanotowane wtedy:**

- Zawsze pobierać plik backupu konfiguracji `.bin` po każdej zmianie.
- Port Config → Disable/Enable to prosty sposób wymuszenia odnowienia DHCP lease bez ruszania ustawień PoE.
- Access point w trybie bridge wymaga tagowanego portu uplink dla VLAN-u danych, podczas gdy PVID portu pozostaje na untagged VLAN-ie zarządzania.

### Incydent #3 (16 lipca 2026)

**Wyzwalacz:** Tym razem żadna zmiana konfiguracji — Uptime Kuma zgłosiła switch jako nieosiągalny przez ping. Wszystkie podłączone urządzenia (host Proxmox, kamery, access point) działały normalnie; przestał odpowiadać wyłącznie własny adres IP zarządzania switcha.

**Kluczowe odkrycie diagnostyczne:** Tym razem switch miał już skonfigurowany **statyczny IP** — nie lease DHCP. Mimo to stał się nieosiągalny. To wyklucza "nieodnowiony lease DHCP" jako główną przyczynę i wskazuje raczej na usterkę na poziomie firmware lub hardware, przy której stack zarządzania się zawiesza, podczas gdy płaszczyzna danych nadal normalnie przełącza ruch.

**Kroki naprawcze:**

1. Próba diagnostyki zdalnej (czyszczenie inwentarza urządzeń na firewallu, sprawdzenie ARP) — w przeciwieństwie do poprzednich incydentów, bez efektu.
1. Próba dobicia się do switcha z bezpośrednio podłączonego hosta poprzez tymczasowy IP w tej samej podsieci — brak odpowiedzi.
1. Odzyskanie fizyczne: podłączenie laptopa bezpośrednio do switcha zapasowym kablem, całkowicie omijając resztę sieci. To zadziałało.
1. Aktualizacja firmware switcha do najnowszej dostępnej wersji.
1. Ustawienie statycznego IP bezpośrednio na switchu (nie przez rezerwację DHCP).
1. Usunięcie rezerwacji MAC DHCP na firewallu (już niepotrzebna/nieistotna) i zastąpienie jej zwykłym obiektem adresowym `/32`, wyłącznie jako punkt odniesienia w politykach firewalla.
1. Pobranie świeżego backupu konfiguracji `.bin`.

**Decyzja na przyszłość:** Ponieważ to już trzeci przypadek — a drugi mimo zrobienia "wszystkiego jak trzeba" (statyczny IP, brak zależności od DHCP) — switch zostaje na razie w użyciu (względy budżetowe), ale kolejne wystąpienie problemu oznacza wymianę zamiast kolejnej rundy napraw. Rozważane kandydatury: Netgear GS308EP (smart-managed, wszystkie 8 portów PoE+) lub używany FortiSwitch FS-108E-POE (pełna integracja z istniejącym FortiGate przez FortiLink, zarządzanie z jednego panelu).

### Docelowa konfiguracja VLAN (TP-Link, aktualna przez wszystkie incydenty)

| Port | Urządzenie | VLAN 1 (Mgmt) | VLAN 20 (Serwer) | VLAN 90 (IoT) | PVID |
| :--- | :--- | :---: | :---: | :---: | :---: |
| 1 | Kamera 1 | – | – | Untagged | 90 |
| 2 | Kamera 2 | – | – | Untagged | 90 |
| 3 | Port serwisowy | Untagged | – | – | 1 |
| 4 | Access point | Untagged | – | Tagged | 1 |
| 5 | Port serwisowy | Untagged | – | – | 1 |
| 6 | Proxmox Node 2 | – | Untagged | – | 20 |
| 7 | Proxmox Node 1 | – | Untagged | – | 20 |
| 8 | Uplink firewalla | Untagged | Tagged | Tagged | 1 |

### Najważniejsze wnioski

- 💾 **Zawsze rób backup.** Pobieraj plik konfiguracji `.bin` po każdej zmianie — switch był już dwukrotnie w pełni resetowany.
- 🔌 **Statyczny IP to nie cudowny lek.** Zapobiegł awarii związanej z DHCP, ale *nie* zapobiegł trzeciemu incydentowi — co sugeruje głębszy problem firmware/hardware.
- 🌐 **Płaszczyzna zarządzania ≠ płaszczyzna danych.** W obu incydentach podłączone urządzenia działały bez zarzutu, podczas gdy własny interfejs zarządzania switcha był całkowicie nieosiągalny — to osobne domeny awarii.
- 🧹 **Cache po stronie firewalla ma znaczenie.** Czyszczenie inwentarza urządzeń i tablicy ARP na firewallu było konieczne (choć niewystarczające przy incydencie #3), żeby rozwiązać konflikty IP/MAC.
- ⚡ **Stabilność zasilania to otwarte ryzyko.** Obecnie brak UPS-a; krótkotrwały zanik zasilania jest podejrzewany jako możliwy wyzwalacz i jest rozważany jako przyszłe działanie zapobiegawcze.
