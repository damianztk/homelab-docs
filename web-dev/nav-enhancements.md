# Navbar Enhancements — Logo, Glow, Background

<!-- Navigation -->
[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

---

<a name="english"></a>

## 🇬🇧 English

[🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

### Overview

Three visual enhancements to `Nav.astro`:

1. **Inline SVG logo** — designer-supplied DZ monogram replacing plain text
2. **Dark mode glow** — subtle violet `drop-shadow` on logo and brand text
3. **Differentiated backgrounds** — nav slightly darker than body in light mode; unchanged in dark mode

### 1. Inline SVG Logo

The DZ monogram is embedded directly in the component as inline SVG. The paths come from the designer's `DZ.svg` file (CorelDRAW 2026, viewBox `0 0 21000 21000`).

**Critical change:** the original fill `#8358E6` (designer's violet) was replaced with `fill="var(--color-ac)"`. This ensures the logo automatically inherits the design system's accent color in both light and dark mode, and respects any future palette changes.

```astro
<a href={`/${lang}/`} class="nav-brand flex items-center gap-2 transition-opacity hover:opacity-80">
  <svg
    width="28"
    height="28"
    viewBox="0 0 21000 21000"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <path fill="var(--color-ac)" fill-rule="evenodd" clip-rule="evenodd" d="M6552.16 16204.02c..." />
    <path fill="var(--color-ac)" fill-rule="evenodd" clip-rule="evenodd" d="M16507.45 6613.35c..." />
  </svg>
  <span class="font-mono text-sm font-semibold text-ac">~/damian.zientek</span>
</a>
```

The `nav-brand` class is required for the dark mode glow CSS selectors (see below).

### 2. Dark Mode Glow

Applied via `<style>` block in `Nav.astro` using CSS `filter: drop-shadow()` on SVG and `text-shadow` on the brand text span. Both use `color-mix()` to keep the glow subtle rather than neon.

```css
:global(.dark) .nav-brand svg {
  filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-ac) 55%, transparent));
}
:global(.dark) .nav-brand span {
  text-shadow: 0 0 10px color-mix(in srgb, var(--color-ac) 45%, transparent));
}
```

`color-mix(in srgb, var(--color-ac) 55%, transparent)` blends the accent color with transparency at 55% — visible but not distracting. The `:global(.dark)` selector is necessary because Astro scopes `<style>` blocks to the component, but `.dark` is a class on `<html>` (outside the component's scope).

### 3. Nav Background

**Light mode:** nav uses `--color-surf2` (`#e8eaed`) instead of the default `--color-surf` (`#ffffff`). This makes the nav slightly darker than the page body (`--color-bg: #f0f2f5`), creating a visible separation without a harsh border.

**Dark mode:** nav stays on `--color-surf` (`#27272a`, zinc-800) — unchanged from the default.

```css
header {
  background-color: color-mix(in srgb, var(--color-surf2) 40%, transparent);
}
:global(.dark) header {
  background-color: color-mix(in srgb, var(--color-surf) 40%, transparent);
}
```

The `40%` opacity is preserved to maintain the `backdrop-blur-md` frosted glass effect on the header.

### ⚠️ Gotcha: `header` vs `nav` selector

The nav layout in `Nav.astro` is:

```html
<header class="fixed top-0 inset-x-0 ...">       ← full-width background
  <nav class="max-w-7xl mx-auto ...">             ← centered content
```

Applying background CSS to `nav` instead of `header` creates a visible rectangle in the center of the header — `nav` is constrained by `max-w-7xl` and does not span the full width. Always target `header` for background color changes.

Also: remove `bg-surf/40` from the `<header>` HTML class when switching to CSS-controlled background — Tailwind and the `<style>` block will conflict otherwise.

---

<a name="deutsch"></a>

## 🇩🇪 Deutsch

[🇬🇧 English](#english) | [🇵🇱 Polski](#polski)

### Übersicht

Drei visuelle Verbesserungen an `Nav.astro`:

1. **Inline-SVG-Logo** — vom Designer geliefertes DZ-Monogramm ersetzt einfachen Text
2. **Dark-Mode-Glow** — subtiler violetter `drop-shadow` auf Logo und Markentext
3. **Differenzierte Hintergründe** — Nav etwas dunkler als Body im Light Mode

### 1. Inline-SVG-Logo

Das DZ-Monogramm ist direkt als Inline-SVG in die Komponente eingebettet. Die Pfade stammen aus der Designerdatei `DZ.svg` (CorelDRAW 2026, viewBox `0 0 21000 21000`).

**Wichtige Änderung:** Der ursprüngliche Fill `#8358E6` (Violett des Designers) wurde durch `fill="var(--color-ac)"` ersetzt. So übernimmt das Logo automatisch die Akzentfarbe des Design-Systems in beiden Modi.

### 2. Dark-Mode-Glow

Angewendet über einen `<style>`-Block in `Nav.astro` mit CSS `filter: drop-shadow()` auf SVG und `text-shadow` auf dem Markentext-Span. Beide verwenden `color-mix()` für einen subtilen Effekt.

```css
:global(.dark) .nav-brand svg {
  filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-ac) 55%, transparent));
}
:global(.dark) .nav-brand span {
  text-shadow: 0 0 10px color-mix(in srgb, var(--color-ac) 45%, transparent));
}
```

### 3. Nav-Hintergrund

**Light Mode:** Nav verwendet `--color-surf2` (`#e8eaed`) statt `--color-surf` (`#ffffff`) — etwas dunkler als der Seitenhintergrund (`#f0f2f5`).

**Dark Mode:** Nav bleibt auf `--color-surf` (`#27272a`) — unverändert.

### ⚠️ Fallstrick: `header` vs `nav`-Selektor

Die Nav-Struktur verwendet `<header>` (volle Breite) mit `<nav>` innen (begrenzt durch `max-w-7xl`). CSS auf `nav` statt `header` anzuwenden erzeugt ein sichtbares Rechteck in der Mitte. Immer `header` für Hintergrundfarben verwenden.

`bg-surf/40` aus dem `<header>`-HTML-Tag entfernen, wenn auf CSS-gesteuertes Hintergrund umgestellt wird.

---

<a name="polski"></a>

## 🇵🇱 Polski

[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch)

### Przegląd

Trzy ulepszenia wizualne `Nav.astro`:

1. **Logo SVG inline** — monogram DZ od grafika zastępuje zwykły tekst
2. **Glow w dark mode** — subtelny violetowy `drop-shadow` na logo i tekście brand
3. **Zróżnicowane tła** — nav ciemniejszy niż body w light mode

### 1. Logo SVG inline

Monogram DZ jest osadzony bezpośrednio w komponencie jako inline SVG. Ścieżki pochodzą z pliku `DZ.svg` od grafika (CorelDRAW 2026, viewBox `0 0 21000 21000`).

**Kluczowa zmiana:** oryginalny fill `#8358E6` (kolor grafika) został zastąpiony przez `fill="var(--color-ac)"`. Logo automatycznie dziedziczy kolor akcentu design systemu w obu trybach kolorystycznych.

### 2. Glow w dark mode

Zastosowany przez blok `<style>` w `Nav.astro` używając CSS `filter: drop-shadow()` na SVG i `text-shadow` na tekście. Oba używają `color-mix()` dla subtelnego efektu.

```css
:global(.dark) .nav-brand svg {
  filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-ac) 55%, transparent));
}
:global(.dark) .nav-brand span {
  text-shadow: 0 0 10px color-mix(in srgb, var(--color-ac) 45%, transparent));
}
```

### 3. Tło Navbara

**Light mode:** nav używa `--color-surf2` (`#e8eaed`) zamiast `--color-surf` (`#ffffff`) — nieco ciemniejszy niż body (`#f0f2f5`).

**Dark mode:** nav pozostaje na `--color-surf` (`#27272a`) — bez zmian.

### ⚠️ Pułapka: selektor `header` vs `nav`

Struktura Nava używa `<header>` (pełna szerokość) z `<nav>` wewnątrz (ograniczonym przez `max-w-7xl`). Zastosowanie CSS na `nav` zamiast `header` tworzy widoczny prostokąt na środku headera. Zawsze targetować `header` przy zmianie koloru tła.

Usunąć `bg-surf/40` z atrybutu class tagu `<header>` przy przełączaniu na sterowanie CSS.
