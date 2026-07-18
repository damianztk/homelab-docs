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

# Wzorce 1:1 z regexów w n8n.
# W Pythonie grupa (...) to \1, \2 — nie $1 jak w JS.
PATTERNS = [
    (re.compile(r'\b(10)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'), r'\1.x.x.x'),
    (re.compile(r'\b(192)\.168\.\d{1,3}\.\d{1,3}\b'), r'\1.168.x.x'),
    (re.compile(r'\b(172)\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b'), r'\1.x.x.x'),
]

def sanitize_text(text: str) -> tuple[str, int]:
    """Stosuje wszystkie 3 wzorce. Zwraca (nowy_tekst, liczba_zamian)."""
    total = 0
    for pattern, replacement in PATTERNS:
        text, count = pattern.subn(replacement, text)
        total += count
    return text, total

def main():
    apply_changes = '--apply' in sys.argv
    repo_root = Path(__file__).parent

    files_changed = 0
    replacements = 0

    for md_file in sorted(repo_root.rglob('*.md')):
        original = md_file.read_text(encoding='utf-8')
        sanitized, count = sanitize_text(original)

        if count == 0:
            continue

        files_changed += 1
        replacements += count
        print(f"{md_file.relative_to(repo_root)}: {count} zamian")

        if apply_changes:
            md_file.write_text(sanitized, encoding='utf-8')

    print(f"\n{'ZAPISANO' if apply_changes else 'DRY-RUN (nic nie zapisano)'}: "
          f"{files_changed} plików, {replacements} zamian")

    if not apply_changes and files_changed > 0:
        print("Uruchom z --apply, żeby zapisać.")

if __name__ == '__main__':
    main()