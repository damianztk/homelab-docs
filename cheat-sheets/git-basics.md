# Git — Basics & Conventional Commits

## Conventional Commits

Format: `<typ>(<zakres>): <opis>`

| Typ | Kiedy używać |
|-----|-------------|
| `feat` | nowa funkcja, nowy playbook, nowy plik konfiguracyjny |
| `fix` | naprawa czegoś co nie działało |
| `docs` | tylko dokumentacja, README |
| `chore` | porządki, zmiana nazw, aktualizacja zależności |
| `refactor` | reorganizacja bez zmiany działania |
| `ci` | pipeline, Gitea Actions |

Zakres w nawiasie jest opcjonalny, ale pomaga przy kilku repozytoriach.

### Przykłady

```
feat(ansible): add proxmox node2 initial setup playbook
fix(scripts): correct rsync path in proxmox-backup.sh
docs(homelab-docs): add vlan overview and port mapping
chore(homelab-docs): rename files to kebab-case
refactor(ansible): split monolithic playbook into roles
ci(portfolio): add gitea actions deploy workflow
```

---

## Podstawowe komendy

```bash
# Status i historia
git status
git log --oneline

# Dodawanie i commitowanie
git add .
git add <plik>
git commit -m "feat(zakres): opis"

# Cofanie zmian (przed commitem)
git restore <plik>          # cofnij zmiany w pliku
git restore --staged <plik> # usuń z obszaru staged

# Zdalne repo
git push
git pull
git remote -v               # pokaż skonfigurowane remote

# Branche (podstawy)
git branch                  # lista branchy
git checkout -b <nazwa>     # stwórz i przejdź na nowy branch
git checkout main           # wróć na main
git merge <nazwa>           # scal branch do aktualnego
```

---

## Nazewnictwo plików

- Pliki i foldery: `kebab-case` → `proxmox-backup-setup.md`
- Bez wersji w nazwach: ~~`backup-script-v2.sh`~~ → `backup-script.sh`
- Historia zmian żyje w commitach, nie w nazwach plików