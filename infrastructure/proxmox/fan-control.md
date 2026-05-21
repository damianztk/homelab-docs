# Fan Control — Homelab Proxmox Nodes

<!-- Language anchors -->
[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

---

<a name="english"></a>

# 🇬🇧 English

[🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

## Overview

This document covers fan control configuration for both Proxmox nodes. The approach differs per node due to hardware constraints — specifically the SuperIO chip on pve2 blocking PWM writes at the kernel level.

| Node | Motherboard | SuperIO Chip | Fan Control Method |
|------|-------------|--------------|-------------------|
| pve1 | Asus Prime B250M-C | NCT6775 (TBC) | BIOS Q-Fan (Silent preset) |
| pve2 | ASRock H270M Pro4 | NCT6683D | BIOS Fan-Tastic Tuning (Customize) |

---

## pve1 — Asus Prime B250M-C

### BIOS: Q-Fan Configuration

Location: `BIOS → Monitor → Q-Fan Configuration`

**CPU Fan Profile:** Silent preset  
**Result at idle (27°C CPU):** ~834 RPM CPU fan, ~1060 RPM chassis fans

The Silent preset is sufficient for the i5-7400 workload profile (Proxmox host with several LXC containers). No custom curve is required.

### OS: Kernel Modules

```bash
# /etc/modules
coretemp
# nct6775 — to be verified
```

> **TODO:** Verify SuperIO module for pve1. Run `sensors-detect` and check if `nct6775` detects the chip. If not, try `nct6683`.

---

## pve2 — ASRock H270M Pro4

### Key Finding: PWM Write is Blocked

The NCT6683D chip on this board is detected by the `nct6683` kernel driver, but **PWM write access is blocked at the driver level** — this is a known kernel limitation for this chip, not a permissions issue. As a result:

- `fancontrol` (lm-sensors) **cannot** control fans on this board
- `force=1` module parameter does **not** resolve PWM write blocking (it only unlocks unknown vendor IDs)
- Fan control must be handled entirely in BIOS

### Troubleshooting Log

| Attempt | Result |
|---------|--------|
| `modprobe nct6775` | `ERROR: could not insert 'nct6775': No such device` — wrong chip |
| `modprobe nct6683` | Loaded successfully — correct chip |
| `pwmconfig` | Found PWM channels but returned `Permission denied` on all |
| `modprobe nct6683 force=1` | Loads, but PWM write still blocked — not the solution |

### BIOS: Fan-Tastic Tuning

Location: `BIOS → H/W Monitor → FAN-Tastic Tuning`

> **Important:** The preset modes (Silent, Standard, Performance) cannot be edited. You must select **Customize** to use a custom fan curve. To activate Customize, click directly on the curve line in the graph — drag points will appear.

**Temperature source:** Monitor CPU (for all fans)

#### CPU Fan 1 & 2

| Point | CPU Temp | PWM % |
|-------|----------|-------|
| P1 | 40°C | 30% |
| P2 | 50°C | 45% |
| P3 | 60°C | 65% |
| P4 | 70°C | 85% |
| P5 | 80°C | 100% |

#### Chassis Fan 1 (Arctic P12 Pro PST)

| Point | CPU Temp | PWM % |
|-------|----------|-------|
| P1 | 40°C | 30% |
| P2 | 50°C | 40% |
| P3 | 60°C | 60% |
| P4 | 70°C | 80% |
| P5 | 80°C | 100% |

#### Chassis Fan 2 (Arctic P12 Pro PST)

Identical curve to Chassis Fan 1.

> **Note on minimum PWM:** ASRock Fan-Tastic Tuning enforces a minimum of 30% as a safety guard against fan stall. The Arctic P12 Pro PST can start reliably below this threshold, but 30% is a safe and sensible floor.

### OS: Kernel Modules

`nct6683` is used for **read-only** temperature and RPM monitoring via `sensors`. It does not control fan speed.

```bash
# /etc/modules
coretemp
nct6683
```

No `force=1` parameter is needed — the module detects the chip without it on this board.

Verify after reboot:

```bash
sensors
```

Expected output includes `nct6683-isa-0a10` with fan RPM readings and CPU temperatures from `coretemp-isa-0000`.

---

<a name="deutsch"></a>

# 🇩🇪 Deutsch

[🇬🇧 English](#english) | [🇵🇱 Polski](#polski)

## Überblick

Dieses Dokument beschreibt die Lüftersteuerung für beide Proxmox-Nodes. Die Methode unterscheidet sich je nach Node, da der SuperIO-Chip auf pve2 PWM-Schreibzugriffe auf Kernel-Ebene blockiert.

| Node | Mainboard | SuperIO-Chip | Steuerungsmethode |
|------|-----------|--------------|-------------------|
| pve1 | Asus Prime B250M-C | NCT6775 (zu bestätigen) | BIOS Q-Fan (Silent-Preset) |
| pve2 | ASRock H270M Pro4 | NCT6683D | BIOS Fan-Tastic Tuning (Customize) |

---

## pve1 — Asus Prime B250M-C

### BIOS: Q-Fan-Konfiguration

Pfad: `BIOS → Monitor → Q-Fan Configuration`

**CPU-Lüfterprofil:** Silent-Preset  
**Ergebnis im Leerlauf (27°C CPU):** ~834 RPM CPU-Lüfter, ~1060 RPM Gehäuselüfter

Das Silent-Preset ist für das Lastprofil des i5-7400 (Proxmox-Host mit mehreren LXC-Containern) ausreichend. Eine benutzerdefinierte Kurve ist nicht erforderlich.

### Betriebssystem: Kernel-Module

```bash
# /etc/modules
coretemp
# nct6775 — zu bestätigen
```

> **TODO:** SuperIO-Modul für pve1 verifizieren. `sensors-detect` ausführen und prüfen, ob `nct6775` den Chip erkennt.

---

## pve2 — ASRock H270M Pro4

### Wichtiger Befund: PWM-Schreibzugriff ist blockiert

Der NCT6683D-Chip wird vom `nct6683`-Kernel-Treiber erkannt, aber **PWM-Schreibzugriff ist auf Treiberebene blockiert** — eine bekannte Kernel-Einschränkung für diesen Chip. Daher gilt:

- `fancontrol` (lm-sensors) kann die Lüfter auf diesem Board **nicht** steuern
- Der Modulparameter `force=1` löst das Problem **nicht** (er entsperrt nur unbekannte Vendor-IDs)
- Die Lüftersteuerung muss vollständig im BIOS erfolgen

### Fehleranalyse

| Versuch | Ergebnis |
|---------|----------|
| `modprobe nct6775` | `ERROR: could not insert 'nct6775': No such device` — falscher Chip |
| `modprobe nct6683` | Erfolgreich geladen — richtiger Chip |
| `pwmconfig` | PWM-Kanäle gefunden, aber `Permission denied` auf allen |
| `modprobe nct6683 force=1` | Lädt, aber PWM-Schreibzugriff weiterhin blockiert |

### BIOS: Fan-Tastic Tuning

Pfad: `BIOS → H/W Monitor → FAN-Tastic Tuning`

> **Wichtig:** Die vordefinierten Modi (Silent, Standard, Performance) können nicht bearbeitet werden. Es muss **Customize** ausgewählt werden. Um Customize zu aktivieren, direkt auf die Kurve im Diagramm klicken — dann erscheinen die Ziehpunkte.

**Temperaturquelle:** Monitor CPU (für alle Lüfter)

#### CPU Fan 1 & 2

| Punkt | CPU-Temp | PWM % |
|-------|----------|-------|
| P1 | 40°C | 30% |
| P2 | 50°C | 45% |
| P3 | 60°C | 65% |
| P4 | 70°C | 85% |
| P5 | 80°C | 100% |

#### Chassis Fan 1 (Arctic P12 Pro PST)

| Punkt | CPU-Temp | PWM % |
|-------|----------|-------|
| P1 | 40°C | 30% |
| P2 | 50°C | 40% |
| P3 | 60°C | 60% |
| P4 | 70°C | 80% |
| P5 | 80°C | 100% |

#### Chassis Fan 2 (Arctic P12 Pro PST)

Identische Kurve wie Chassis Fan 1.

### Betriebssystem: Kernel-Module

`nct6683` wird ausschließlich für **Nur-Lese**-Überwachung (Temperaturen und RPM) über `sensors` verwendet.

```bash
# /etc/modules
coretemp
nct6683
```

Kein `force=1`-Parameter erforderlich. Nach dem Neustart verifizieren:

```bash
sensors
```

---

<a name="polski"></a>

# 🇵🇱 Polski

[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch)

## Przegląd

Dokument opisuje konfigurację sterowania wentylatorami na obu nodach Proxmox. Podejście różni się między nodami z powodu ograniczenia sprzętowego — chip SuperIO na pve2 blokuje zapis PWM na poziomie kernela.

| Node | Płyta główna | Chip SuperIO | Metoda sterowania |
|------|--------------|--------------|-------------------|
| pve1 | Asus Prime B250M-C | NCT6775 (do weryfikacji) | BIOS Q-Fan (preset Silent) |
| pve2 | ASRock H270M Pro4 | NCT6683D | BIOS Fan-Tastic Tuning (Customize) |

---

## pve1 — Asus Prime B250M-C

### BIOS: Konfiguracja Q-Fan

Ścieżka: `BIOS → Monitor → Q-Fan Configuration`

**Profil CPU Fan:** preset Silent  
**Wynik w idle (27°C CPU):** ~834 RPM wentylator CPU, ~1060 RPM wentylatory obudowy

Preset Silent jest wystarczający dla profilu obciążeniowego i5-7400 (host Proxmox z kilkoma kontenerami LXC). Krzywa niestandardowa nie jest potrzebna.

### System: Moduły kernela

```bash
# /etc/modules
coretemp
# nct6775 — do weryfikacji
```

> **TODO:** Zweryfikować moduł SuperIO dla pve1. Uruchomić `sensors-detect` i sprawdzić czy `nct6775` wykrywa chip.

---

## pve2 — ASRock H270M Pro4

### Kluczowe odkrycie: Zapis PWM jest zablokowany

Chip NCT6683D jest wykrywany przez driver `nct6683`, ale **zapis PWM jest zablokowany na poziomie drivera** — znane ograniczenie kernela dla tego chipa. W związku z tym:

- `fancontrol` (lm-sensors) **nie może** sterować wentylatorami na tej płycie
- Parametr modułu `force=1` **nie rozwiązuje** blokady zapisu PWM (odblokowuje tylko nieznane Vendor ID)
- Sterowanie wentylatorami musi odbywać się wyłącznie przez BIOS

### Log debugowania

| Próba | Wynik |
|-------|-------|
| `modprobe nct6775` | `ERROR: could not insert 'nct6775': No such device` — zły chip |
| `modprobe nct6683` | Załadowany poprawnie — właściwy chip |
| `pwmconfig` | Znalazł kanały PWM, ale `Permission denied` na wszystkich |
| `modprobe nct6683 force=1` | Ładuje się, ale zapis PWM nadal zablokowany |

### BIOS: Fan-Tastic Tuning

Ścieżka: `BIOS → H/W Monitor → FAN-Tastic Tuning`

> **Ważne:** Predefiniowane tryby (Silent, Standard, Performance) nie mogą być edytowane. Należy wybrać **Customize**. Aby aktywować Customize, kliknąć bezpośrednio na linię krzywej na wykresie — pojawią się punkty do przeciągania.

**Źródło temperatury:** Monitor CPU (dla wszystkich wentylatorów)

#### CPU Fan 1 & 2

| Punkt | Temp CPU | PWM % |
|-------|----------|-------|
| P1 | 40°C | 30% |
| P2 | 50°C | 45% |
| P3 | 60°C | 65% |
| P4 | 70°C | 85% |
| P5 | 80°C | 100% |

#### Chassis Fan 1 (Arctic P12 Pro PST)

| Punkt | Temp CPU | PWM % |
|-------|----------|-------|
| P1 | 40°C | 30% |
| P2 | 50°C | 40% |
| P3 | 60°C | 60% |
| P4 | 70°C | 80% |
| P5 | 80°C | 100% |

#### Chassis Fan 2 (Arctic P12 Pro PST)

Identyczna krzywa jak Chassis Fan 1.

> **Uwaga odnośnie minimalnego PWM:** Fan-Tastic Tuning wymusza minimum 30% jako zabezpieczenie przed zatrzymaniem wentylatora. Arctic P12 Pro PST teoretycznie startuje poniżej tego progu, ale 30% to bezpieczna i sensowna granica dolna.

### System: Moduły kernela

`nct6683` służy wyłącznie do **monitorowania w trybie tylko do odczytu** (temperatury i RPM) przez `sensors`. Nie steruje prędkością wentylatorów.

```bash
# /etc/modules
coretemp
nct6683
```

Parametr `force=1` nie jest potrzebny. Weryfikacja po restarcie:

```bash
sensors
```

Oczekiwany wynik zawiera `nct6683-isa-0a10` z odczytami RPM wentylatorów oraz temperatury CPU z `coretemp-isa-0000`.
