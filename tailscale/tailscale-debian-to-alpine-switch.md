WORK IN PROGRESS
# Tailscale LXC - migracja z Debian do Alpine

### 1. Przygotowanie

1.
    Zanotuj ID Debian LXC (np. 101) — to będzie ID Alpine
1.
    Zanotuj dokładne flagi z tailscale up na obecnym Debianie:

    ```bash
    tailscale status
    # lub sprawdź jak tailscale był uruchomiony
    cat /etc/systemd/system/tailscale.service  # jeśli masz custom unit
    ```

1.
    Zanotuj rekord w `/etc/pve/lxc/101.conf` dotyczący **bind mounta** - żebyś wiedział dokładnie jak go odtworzyć w nowym LXC

### 2. Zatrzymanie Debian LXC

Zatrzymaj Debian LXC przez GUI lub `pct stop 101`

> [!IMPORTANT]
> Nie usuwaj go jeszcze — ma zostać jako "rezerwa" do czasu weryfikacji

### 3. Tworzenie Alpine LXC

**W GUI:**
- **Create CT** → `CT ID` ustaw ręcznie na `101`.
- **Template**: `Alpine`, najnowszy dostępny.
- **Konfiguracja sieciowa** identyczna jak na Debianie (`bridge`, `VLAN tag` jeśli używasz, ``statyczny IP``).
- **RAM/CPU** możesz dać mniej niż miał Debian - Tailscale nie potrzebuje dużo.

### 4. Bind mount

1.
    Przed startem kontenera dodaj bind mount w `/etc/pve/lxc/101.conf`:

    ```bash
    mp0: /opt/lxc-data/tailscale-data,mp=/var/lib/tailscale
    ```

1.
    Sprawdź ownership na hoście — powinien być `100000:100000`:

    ```bash
    ls -la /opt/lxc-data/tailscale-data
    ```

    > Jeśli nie - `chown -R 100000:100000 /opt/lxc-data/tailscale-data`

### 5. Konfiguracja Alpine LXC

1. Uruchom kontener i wejdź do środka:

    ```bash
    pct start 101
    pct enter 101
    ```

1. Zaktualizuj repo i zainstaluj paczki:

    ```bash
    apk update && apk add tailscale ethtool
    ```

1. Skonfiguruj `GRO fix` - utwórz plik:

    ```bash
    cat > /etc/local.d/tailscale-gro.start << 'EOF'
    #!/bin/sh
    ethtool -K eth0 rx-udp-gro-forwarding on rx-gro-list off
    EOF
    chmod +x /etc/local.d/tailscale-gro.start
    rc-update add local default
    ```

1. Włącz i uruchom Tailscale przy starcie:

    ```bash
    rc-update add tailscale default
    rc-service tailscale start
    ```

### 6. Uruchomienie Tailscale

1.
    Sprawdź czy dane z bind mounta są widoczne:

    ```bash
    ls -la /var/lib/tailscale
    ```

    > powinien być plik `tailscaled.state`

1.
    Uruchom Tailscale z tymi samymi flagami co na Debianie:

    ```bash
    tailscale up --advertise-routes=10.x.x.x/24,10.x.x.x/24,... --accept-dns=false
    ```
    > [!NOTE]
    > Dzięki istniejącemu `tailscaled.state` - bez re-authu, bez nowego urządzenia w Admin Console

### 7. Weryfikacja

1.
    Sprawdź status:

    ```bash
    tailscale status
    tailscale ip
    ```

1.
    Z zewnątrz (przez Tailscale na telefonie/laptopie) sprawdź dostęp do `10.100.20.x` - np. `ping` do `pve1` lub `NPM`.
1.
    Sprawdź w Tailscale Admin Console że subnet routes są nadal zatwierdzone i aktywne
1.
    Zrebootuj LXC i sprawdź czy Tailscale i GRO fix wstają automatycznie:

    ```bash
    pct reboot 101
    # po chwili
    pct enter 101
    tailscale status
    ```

### 8. Sprzątanie

Jak wszystko działa - usuń Debian LXC przez GUI (lub `pct destroy <stary_id>` jeśli miał inny ID)

> [!IMPORTANT]
> Jedyne miejsce gdzie może być niespodzianka to **krok 17** - jeśli flagi `tailscale up` różnią się od tych z którymi był zarejestrowany węzeł, Tailscale może poprosić o potwierdzenie w Admin Console (nie o pełny re-auth). Dlatego **krok 2** jest ważny - żebyś wiedział dokładnie jakich flag używać.
