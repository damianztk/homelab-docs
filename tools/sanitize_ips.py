#!/usr/bin/env python3
"""
sanitize_ips.py — maskuje prywatne adresy IP w plikach .md,
tym samym wzorcem co node "Sanitize Sensitive Data" w n8n.

    python3 sanitize_ips.py           # dry-run: tylko pokazuje
    python3 sanitize_ips.py --apply   # zapisuje zmiany
"""

import re
import sys
from pathlib import Path

# Wzorce 1:1 z regexów w n8n. Grupa (...) w Pythonie to \1, \2 — nie $1 jak w JS.
PATTERNS = [
    (re.compile(r'\b(10)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), r'\1.x.x.x'),
    (re.compile(r'\b(192)\.168\.\d{1,3}\.\d{1,3}\b'), r'\1.168.x.x'),
    (re.compile(r'\b(172)\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b'), r'\1.x.x.x'),
]

# Dokładne, kanoniczne deklaracje CAŁEGO zakresu RFC1918 — generyczne,
# identyczne u każdego, nie zdradzają Twojej realnej adresacji.
# Rozpoznawane po masce /8, /12, /16 (granica całego bloku), nie po /24 (konkretna podsieć).
WHITELIST = [
    re.compile(r'\b10\.0\.0\.0/8\b'),
    re.compile(r'\b172\.16\.0\.0/12\b'),
    re.compile(r'\b192\.168\.0\.0/16\b'),
]

# Katalogi całkowicie wykluczone z maskowania (np. generyczne cheat-sheety).
# Dopisz nazwę katalogu jako string, jeśli chcesz go pominąć w całości.
SKIP_DIRS = ['cheat-sheets']

def protect_whitelist(text: str) -> tuple[str, dict[str, str]]:
    """Zamienia wpisy z WHITELIST na placeholdery, żeby nie zostały zamaskowane.
    Zwraca (tekst_z_placeholderami, mapa_placeholder->oryginał)."""
    placeholders = {}
    for i, pattern in enumerate(WHITELIST):
        for match in pattern.finditer(text):
            original = match.group(0)
            token = f"__WHITELIST_{i}_{len(placeholders)}__"
            placeholders[token] = original
            text = text.replace(original, token, 1)
    return text, placeholders

def restore_whitelist(text: str, placeholders: dict[str, str]) -> str:
    """Przywraca oryginalne wartości w miejsce placeholderów."""
    for token, original in placeholders.items():
        text = text.replace(token, original)
    return text

def sanitize_text(text: str) -> tuple[str, int]:
    """Chroni wyjątki, maskuje resztę, przywraca wyjątki. Zwraca (nowy_tekst, liczba_zmian)."""
    text, placeholders = protect_whitelist(text)

    total = 0
    for pattern, replacement in PATTERNS:
        text, count = pattern.subn(replacement, text)
        total += count

    text = restore_whitelist(text, placeholders)
    return text, total

def main():
    apply_changes = '--apply' in sys.argv
    repo_root = Path(__file__).parent.parent  # tools/ -> repo root

    files_changed = 0
    replacements = 0

    for md_file in sorted(repo_root.rglob('*.md')):
        rel_path = md_file.relative_to(repo_root)

        # Pomiń pliki w wykluczonych katalogach
        if any(part in SKIP_DIRS for part in rel_path.parts):
            continue

        original = md_file.read_text(encoding='utf-8')
        sanitized, count = sanitize_text(original)

        if count == 0:
            continue

        files_changed += 1
        replacements += count
        print(f"{rel_path}: {count} zamian")

        if apply_changes:
            md_file.write_text(sanitized, encoding='utf-8')

    print(f"\n{'ZAPISANO' if apply_changes else 'DRY-RUN (nic nie zapisano)'}: "
          f"{files_changed} plików, {replacements} zamian")

    if not apply_changes and files_changed > 0:
        print("Uruchom z --apply, żeby zapisać.")

if __name__ == '__main__':
    main()