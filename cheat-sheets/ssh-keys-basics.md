# SSH Keys – Podstawy

## Jak to działa?

Klucz SSH to para plików:

- 🔑 **Klucz prywatny** (`id_ed25519`) – trzymasz tylko u siebie, nigdy nie wysyłasz
- 🔒 **Klucz publiczny** (`id_ed25519.pub`) – dajesz serwerom / aplikacjom

Serwer przechowuje Twój klucz publiczny. Przy połączeniu sprawdza matematycznie, czy masz pasujący klucz prywatny. Hasło nie jest potrzebne.

---

## Generowanie klucza

```bash
ssh-keygen -t ed25519 -C "komentarz" -f ~/.ssh/id_ed25519_nazwa
```

| Flaga | Znaczenie |
| ------- | ----------- |
| `-t ed25519` | algorytm (preferowany nad RSA) |
| `-C "komentarz"` | etykieta widoczna w kluczu publicznym i panelach (np. Gitea) |
| `-f ~/.ssh/id_ed25519_nazwa` | ścieżka i nazwa pliku |

> **Passphrase** – dodatkowe hasło chroniące klucz prywatny. Dla Ansible/automatyzacji zostawiaj puste. Na kluczu osobistym warto ustawić.

---

## Struktura plików

```
~/.ssh/
├── id_ed25519              ← prywatny – chmod 600, tylko dla Ciebie
├── id_ed25519.pub          ← publiczny – dajesz serwerom
├── id_ed25519_gitea        ← prywatny dla Gitea
├── id_ed25519_gitea.pub    ← publiczny dla Gitea
├── config                  ← mapa: który klucz do czego
└── known_hosts             ← lista znanych serwerów (tworzy się auto)
```

---

## Dodawanie klucza do serwera

```bash
# automatycznie (zalecane)
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@adres_serwera

# ręcznie (jeśli ssh-copy-id nie działa)
mkdir -p ~/.ssh
echo "zawartość_pliku.pub" >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

---

## Plik ~/.ssh/config

Zamiast pamiętać adresy i opcje – definiujesz aliasy:

```
Host pve1
    HostName 10.100.20.10
    User root
    IdentityFile ~/.ssh/id_ed25519

Host pve2
    HostName 10.100.20.11
    User root
    IdentityFile ~/.ssh/id_ed25519

Host gitea
    HostName 10.100.20.20
    User git                      # zawsze "git" dla Gitea/GitHub
    IdentityFile ~/.ssh/id_ed25519_gitea
```

Połączenie skraca się wtedy do:

```bash
ssh pve1
ssh gitea
```

---

## Mapa kluczy – mój homelab

| Klucz | Do czego |
| ------- | ---------- |
| `id_ed25519` | Proxmox (pve1, pve2), LXC, VM – logowanie na serwery |
| `id_ed25519_gitea` | Gitea – git push/pull |
| `id_ed25519_ansible` | *(planowany)* Ansible – automatyzacja |

---

## Gitea – dodawanie klucza

Klucz publiczny (`*.pub`) wklejasz w:
**Settings → SSH and GPG Keys → Add Key**

Gitea przechowuje go w swojej bazie danych (nie na systemie plików).

---

## Ansible i Terraform

```yaml
# hosts.yml – inventory Ansible
utility-apps:
  ansible_host: 10.100.20.30
  ansible_user: root
  ansible_ssh_private_key_file: ~/.ssh/id_ed25519
```

```hcl
# main.tf – Terraform connection block
connection {
  type        = "ssh"
  user        = "root"
  private_key = file("~/.ssh/id_ed25519")
  host        = self.ip_address
}
```

---

## Dobre praktyki

| ✅ Rób | ❌ Nie rób |
| -------- | ----------- |
| Używaj ed25519 | Używaj RSA 1024-bit |
| Osobne klucze per rola/narzędzie | Jeden klucz do absolutnie wszystkiego |
| Tylko `.pub` kopiuj na serwery | Kopiować klucz prywatny gdziekolwiek |
| Backupuj `~/.ssh` w bezpiecznym miejscu | Wrzucać kluczy do repo Git |
| Ustaw passphrase na kluczu osobistym | Ignorować uprawnienia plików (chmod!) |
