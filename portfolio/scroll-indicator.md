# ScrollIndicator — Mobile Section Navigation

<!-- Navigation -->
[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

---

<a name="english"></a>
## 🇬🇧 English

[🇩🇪 Deutsch](#deutsch) | [🇵🇱 Polski](#polski)

### Overview

`ScrollIndicator` is an Astro component that renders a vertical dot navigation on the right side of the screen, indicating which section of the single-page portfolio is currently in view. Each dot represents one section; the active dot is highlighted with the violet accent color.

**File:** `src/components/ScrollIndicator.astro`
**Used in:** `src/pages/en/index.astro`, `src/pages/de/index.astro`, `src/pages/pl/index.astro`

### Key Design Decision: Mobile-Only

The component is intentionally **visible only on mobile** (`flex md:hidden`), which is the reverse of the common convention (usually such indicators are desktop-only).

Reasoning:

- **Desktop** already has two orientation aids: a sticky top nav with direct section links, and the browser's native scrollbar. A dot indicator would be pure redundancy.
- **Mobile** has neither: the hamburger menu is hidden by default, and touch browsers suppress the native scrollbar. The only existing navigation aid was `BackToTop`. The dot indicator fills a real UX gap on mobile.

### Mechanism: IntersectionObserver

The component uses the [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API) — a native browser API that fires a callback only when an element crosses a visibility threshold, without listening to `scroll` events (which fire hundreds of times per second).

Key configuration:

```js
rootMargin: '-50% 0px -50% 0px',
threshold: 0,
```

`rootMargin: '-50% 0px -50% 0px'` creates an invisible activation line at the vertical center of the viewport. A section becomes "active" when it intersects this line — regardless of the section's height. This is more robust than a `threshold` value, which behaves inconsistently when sections have very different heights (e.g. Hero at `min-h-screen` vs Contact at variable height).

### Touch Target Sizing

The visual dot is `10px × 10px` (`w-2.5 h-2.5`), but the tappable `<a>` element is `36px × 36px` (`w-9 h-9`). This meets the Apple HIG and Material Design minimum touch target size of 44×44pt / 48×48dp. The larger hit area is invisible — only the small dot is rendered.

### i18n

Section labels are pulled from `translations.ts` via the `lang` prop:

```ts
const sections = [
  { id: 'hero',     label: n.home },
  { id: 'stack',    label: n.stack },
  { id: 'path',     label: n.path },
  { id: 'articles', label: n.articles },
  { id: 'contact',  label: n.contact },
];
```

Adding a new section requires:
  1. Adding a section `id` to the relevant component
  1. Adding a translation key to `translations.ts`
  1. Adding one entry to the `sections` array in `ScrollIndicator.astro`

### Required: Section IDs

The component targets sections by `id`. All five IDs must exist in the page:

| Section | Component | ID |
| ------- | --------- | --- |
| Hero | `Hero.astro` | `hero` |
| Stack | `Stack.astro` | `stack` |
| Path | `Path.astro` | `path` |
| Articles | `Articles.astro` | `articles` |
| Contact | `Contact.astro` | `contact` |

### Usage

```astro
---
import ScrollIndicator from '../../components/ScrollIndicator.astro';
---

<Base title={t.site_title} lang={lang}>
  <ScrollIndicator lang={lang} />
  <Hero lang={lang} />
  ...
</Base>
```

Position in the DOM does not matter — the element uses `position: fixed`.

---

<a name="deutsch"></a>
## 🇩🇪 Deutsch

[🇬🇧 English](#english) | [🇵🇱 Polski](#polski)

### Übersicht

`ScrollIndicator` ist eine Astro-Komponente, die eine vertikale Punktnavigation auf der rechten Seite des Bildschirms rendert und anzeigt, welcher Abschnitt der Single-Page-Portfolio-Website gerade sichtbar ist. Jeder Punkt steht für einen Abschnitt; der aktive Punkt wird mit der violetten Akzentfarbe hervorgehoben.

**Datei:** `src/components/ScrollIndicator.astro`
**Verwendet in:** `src/pages/en/index.astro`, `src/pages/de/index.astro`, `src/pages/pl/index.astro`

### Wichtige Designentscheidung: Nur auf Mobile

Die Komponente ist absichtlich **nur auf mobilen Geräten sichtbar** (`flex md:hidden`) — entgegen der gängigen Konvention (solche Indikatoren sind meist nur auf Desktop sichtbar).

Begründung:

- **Desktop** bietet bereits zwei Orientierungshilfen: eine fixierte obere Navigation mit direkten Abschnittslinks und die native Browser-Scrollleiste. Ein Punktindikator wäre reine Redundanz.
- **Mobile** hat keine davon: Das Hamburger-Menü ist standardmäßig ausgeblendet, und Touch-Browser blenden die native Scrollleiste aus. Die einzige vorhandene Navigationshilfe war `BackToTop`. Der Punktindikator füllt eine echte UX-Lücke auf Mobile.

### Mechanismus: IntersectionObserver

Die Komponente verwendet die [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API) — eine native Browser-API, die einen Callback nur auslöst, wenn ein Element einen Sichtbarkeitsschwellenwert überschreitet, ohne `scroll`-Events zu überwachen (die hunderte Male pro Sekunde feuern).

Wichtige Konfiguration:

```js
rootMargin: '-50% 0px -50% 0px',
threshold: 0,
```

`rootMargin: '-50% 0px -50% 0px'` erstellt eine unsichtbare Aktivierungslinie in der vertikalen Mitte des Viewports. Ein Abschnitt wird „aktiv", wenn er diese Linie schneidet — unabhängig von seiner Höhe. Dies ist robuster als ein `threshold`-Wert, der bei Abschnitten mit sehr unterschiedlichen Höhen inkonsistent reagiert (z.B. Hero mit `min-h-screen` vs. Contact mit variabler Höhe).

### Touch-Target-Größe

Der visuelle Punkt ist `10px × 10px` (`w-2.5 h-2.5`), aber das tappbare `<a>`-Element ist `36px × 36px` (`w-9 h-9`). Dies entspricht den Mindestanforderungen von Apple HIG und Material Design für Touch-Targets (44×44pt / 48×48dp). Der größere Trefferbereich ist unsichtbar — nur der kleine Punkt wird gerendert.

### i18n

Abschnittsbezeichnungen werden aus `translations.ts` über die `lang`-Prop bezogen:

```ts
const sections = [
  { id: 'hero',     label: n.home },
  { id: 'stack',    label: n.stack },
  { id: 'path',     label: n.path },
  { id: 'articles', label: n.articles },
  { id: 'contact',  label: n.contact },
];
```

Das Hinzufügen eines neuen Abschnitts erfordert:
  1. Hinzufügen einer Abschnitts-`id` zur entsprechenden Komponente
  1. Hinzufügen eines Übersetzungsschlüssels in `translations.ts`
  1. Hinzufügen eines Eintrags zum `sections`-Array in `ScrollIndicator.astro`

### Erforderliche: Abschnitts-IDs

Die Komponente zielt auf Abschnitte anhand ihrer `id`. Alle fünf IDs müssen auf der Seite vorhanden sein:

| Abschnitt | Komponente | ID |
| --------- | --------- | --- |
| Hero | `Hero.astro` | `hero` |
| Stack | `Stack.astro` | `stack` |
| Path | `Path.astro` | `path` |
| Articles | `Articles.astro` | `articles` |
| Contact | `Contact.astro` | `contact` |

### Verwendung

```astro
---
import ScrollIndicator from '../../components/ScrollIndicator.astro';
---

<Base title={t.site_title} lang={lang}>
  <ScrollIndicator lang={lang} />
  <Hero lang={lang} />
  ...
</Base>
```

Die Position im DOM spielt keine Rolle — das Element verwendet `position: fixed`.

---

<a name="polski"></a>
## 🇵🇱 Polski

[🇬🇧 English](#english) | [🇩🇪 Deutsch](#deutsch)

### Przegląd

`ScrollIndicator` to komponent Astro renderujący pionową nawigację kropkową po prawej stronie ekranu, wskazującą która sekcja portfolio jest aktualnie widoczna. Każda kropka reprezentuje jedną sekcję; aktywna kropka jest podświetlona violetowym kolorem akcentu.

**Plik:** `src/components/ScrollIndicator.astro`
**Używany w:** `src/pages/en/index.astro`, `src/pages/de/index.astro`, `src/pages/pl/index.astro`

### Kluczowa decyzja projektowa: Tylko na mobile

Komponent jest celowo **widoczny tylko na urządzeniach mobilnych** (`flex md:hidden`) — odwrotnie do powszechnej konwencji (takie wskaźniki są zazwyczaj widoczne tylko na desktopie).

Uzasadnienie:

- **Desktop** ma już dwa punkty orientacyjne: sticky nav z bezpośrednimi linkami do sekcji i natywny scrollbar przeglądarki. Wskaźnik kropkowy byłby czystą redundancją.
- **Mobile** nie ma żadnego z nich: hamburger menu jest domyślnie ukryte, a mobilne przeglądarki ukrywają natywny scrollbar. Jedyną pomocą nawigacyjną był `BackToTop`. Wskaźnik wypełnia realną lukę UX na mobile.

### Mechanizm: IntersectionObserver

Komponent używa [Intersection Observer API](https://developer.mozilla.org/en-US/docs/Web/API/Intersection_Observer_API) — natywnego API przeglądarki, które wywołuje callback tylko gdy element przekracza próg widoczności, bez nasłuchiwania zdarzeń `scroll` (które odpalają się setki razy na sekundę).

Kluczowa konfiguracja:

```js
rootMargin: '-50% 0px -50% 0px',
threshold: 0,
```

`rootMargin: '-50% 0px -50% 0px'` tworzy niewidzialną linię aktywacji na środku viewportu w pionie. Sekcja staje się „aktywna" gdy przecina tę linię — niezależnie od jej wysokości. To bardziej niezawodne niż wartość `threshold`, która zachowuje się niespójnie gdy sekcje mają bardzo różne wysokości (np. Hero z `min-h-screen` vs Contact o zmiennej wysokości).

### Rozmiar strefy dotyku

Wizualna kropka ma `10px × 10px` (`w-2.5 h-2.5`), ale klikalny element `<a>` ma `36px × 36px` (`w-9 h-9`). Spełnia to minimalne wymagania Apple HIG i Material Design dla elementów dotykowych (44×44pt / 48×48dp). Większa strefa kliknięcia jest niewidoczna — renderowana jest tylko mała kropka.

### i18n

Etykiety sekcji są pobierane z `translations.ts` przez prop `lang`:

```ts
const sections = [
  { id: 'hero',     label: n.home },
  { id: 'stack',    label: n.stack },
  { id: 'path',     label: n.path },
  { id: 'articles', label: n.articles },
  { id: 'contact',  label: n.contact },
];
```

Dodanie nowej sekcji wymaga:
  1. Dodania `id` do odpowiedniego komponentu
  1. Dodania klucza tłumaczenia w `translations.ts`
  1. Dodania jednego wpisu do tablicy `sections` w `ScrollIndicator.astro`

### Wymagane: ID sekcji

Komponent targetuje sekcje po `id`. Wszystkie pięć ID musi istnieć na stronie:

| Sekcja | Komponent | ID |
| ------ | --------- | --- |
| Hero | `Hero.astro` | `hero` |
| Stack | `Stack.astro` | `stack` |
| Path | `Path.astro` | `path` |
| Articles | `Articles.astro` | `articles` |
| Contact | `Contact.astro` | `contact` |

### Użycie

```astro
---
import ScrollIndicator from '../../components/ScrollIndicator.astro';
---

<Base title={t.site_title} lang={lang}>
  <ScrollIndicator lang={lang} />
  <Hero lang={lang} />
  ...
</Base>
```

Pozycja w drzewie DOM nie ma znaczenia — element używa `position: fixed`.
