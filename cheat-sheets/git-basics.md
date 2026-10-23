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

## Końce linii (CRLF / LF)

Windows kończy linie znakami `\r\n` (CRLF), Linux samym `\n` (LF). Skrypty bash z CRLF nie działają (`/bin/bash^M: bad interpreter`), a diffy pokazują zmianę całego pliku. Typowa przyczyna: plik zapisany w Notatniku albo edytorze po stronie Windows.

| Co | Polecenie |
| --- | --- |
| Wymuś LF w repo (plik `.gitattributes` w katalogu głównym) | `* text=auto eol=lf` |
| Przepisz już śledzone pliki według `.gitattributes` | `git add --renormalize .` |
| Pokaż końce linii plików w repo (`i/` = indeks, `w/` = katalog roboczy) | `git ls-files --eol` |
| Znajdź pliki z CRLF w indeksie | `git ls-files --eol \| grep 'i/crlf'` |
| Sprawdź jeden plik | `file skrypt.sh` (pokaże „with CRLF line terminators”) |
| Zamień CRLF na LF w jednym pliku | `sed -i 's/\r$//' skrypt.sh` |

`.gitattributes` jest w repo, więc działa na każdej maszynie i dla każdego, kto klonuje (także runnery i agenci) — w odróżnieniu od `git config core.autocrlf`, które obowiązuje tylko lokalnie. W VS Code aktualny format widać w prawym dolnym rogu (`LF`/`CRLF`); na stałe: `"files.eol": "\n"`.