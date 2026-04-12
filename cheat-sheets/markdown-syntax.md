# Markdown — Składnia

## Nagłówki

```markdown
# H1 — tytuł strony/dokumentu
## H2 — główna sekcja
### H3 — podsekcja
```

---

## Formatowanie tekstu

```markdown
**pogrubienie**
*kursywa*
~~przekreślenie~~
`kod inline`
```

---

## Listy

```markdown
- element nieuporządkowany
- kolejny element
  - zagnieżdżony element

1. element uporządkowany
2. kolejny element
```

---

## Linki i obrazy

```markdown
[tekst linku](https://adres.url)
[link do pliku w repo](infrastructure/overview.md)

![alt text](screenshots/nazwa-pliku.png)
![alt text](https://adres.url/obrazek.png)
```

---

## Tabele

```markdown
| Kolumna 1 | Kolumna 2 | Kolumna 3 |
|-----------|-----------|-----------|
| wartość   | wartość   | wartość   |
| wartość   | wartość   | wartość   |
```

Wyrównanie kolumn:
```markdown
| Lewo      | Środek      | Prawo      |
|:----------|:-----------:|-----------:|
| tekst     | tekst       | tekst      |
```

---

## Bloki kodu

````markdown
```bash
echo "blok kodu bash"
```

```yaml
klucz: wartość
```

```markdown
zagnieżdżony markdown
```
````

---

## Drzewka katalogów

Znaki do kopiowania:
```
├── folder lub plik (gałąź w środku)
└── folder lub plik (ostatnia gałąź)
│   (pionowa linia)
```

Przykład:
```
homelab-docs/
├── infrastructure/
│   ├── proxmox/
│   └── dell-wyse-3040/
├── networking/
│   └── dns/
└── README.md
```

---

## Cytaty i notatki

```markdown
> To jest cytat lub ważna informacja
```

Gitea obsługuje też callouts:
```markdown
> [!NOTE]
> Zwykła notatka

> [!WARNING]
> Ostrzeżenie

> [!TIP]
> Wskazówka
```

---

## Flagi i emoji

Wstawiasz bezpośrednio w tekście — kopiujesz i wklejasz.

| Symbol | Znaczenie |
|--------|-----------|
| 🇬🇧 | język angielski |
| 🇩🇪 | język niemiecki |
| 🇵🇱 | język polski |

**Windows:** `Win + .` → otwiera picker emoji

---

## Pozioma linia

```markdown
---
```