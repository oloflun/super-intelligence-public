# Production-test tells · gates 66–88

**Load on every marketing, landing, or portfolio build.**

> Source: `design-taste-frontend` (Leonxlnx/taste-skill) v2, Section 9.F. Ported at full fidelity. These came out of real LLM-generated landing-page tests — they are the signatures a model reaches for when it tries to *look designed*. Blocks marked **[ours]** are this repo's framing.

**[ours] Why these are separate from [`slop-test.md`](slop-test.md) gates 1–57.** Hallmark's set covers structural and visual slop (purple gradients, 3-column icon cards, centred hero, card-in-card). This set covers *micro-decoration* — the small labels, strips, dots, and captions a model sprinkles on to signal craft. They survive every other gate because individually each looks like a deliberate designer choice. Together they are the single most recognisable AI-page signature in production.

**Scope.** These are hard bans **by default**. Each is overridable when the brief explicitly calls for it — a genuine product-launch page may legitimately need a `BETA` label. The rule is that reaching for one *unprompted* is the failure.

---

## Hero and top-of-page

### 66 · Version labels in the hero
`V0.6`, `v2.0`, `BETA`, `INVITE-ONLY PREVIEW`, `EARLY ACCESS`, `ALPHA` as hero eyebrows. Banned as default. Acceptable only when the brief is explicitly about launch or preview status.

### 67 · "Brand · No. 01" sub-eyebrows
Micro-meta lines of the `Marrow · No. 01 · The 6-quart` shape. Skip them entirely.

### 68 · Decoration text strip at hero bottom
`BRAND. MOTION. SPATIAL.` · `TYPE / FORM / MOTION` · `DESIGN · BUILD · SHIP` · `ESTD. 2018 · LISBON` as a small mono-caps strip across the hero's base. Agency-portfolio cliché. Acceptable only when the strip carries real navigable links or real status info.

---

## Section labels and numbering

### 69 · Numbered eyebrows and range labels
`00 / INDEX`, `001 · Capabilities`, `06 · how it works`, `Index of Work, 2018 - 2026`. Eyebrows name the topic in plain language; they do not enumerate. Also covers `01 / 4`-style pagination on images and bento tiles — if the user can count, the label is noise.

Partially mechanical: impeccable's `numbered-section-labels` rule catches the common shapes.

### 70 · Micro-meta-sentences under eyebrows
A sentence like *"Each of these is a feature we ship today, not a roadmap promise."* sitting under a section heading. Eyebrow + headline + body is enough.

### 71 · Floating top-right sub-text in section headings
Giant left-aligned headline with a small explainer paragraph floating in the section header's top-right corner, aligned to nothing. Put the sub-text under the headline, or build a clean two-column header — not a corner floater.

### 72 · Generic step labels
`Stage 1 / Stage 2`, `Step 1 / Step 2`, `Phase 01 / Phase 02`, `Pass One / Pass Two`. The step's content is its label. If progression must show, use the verb directly (`Install`, `Configure`, `Ship`).

---

## Separators, dots, dashes

### 73 · Middle-dot as default separator
The `·` is rationed: **at most one per line** in a metadata strip. Not the default joiner for everything (`foo · bar · baz · qux`). Prefer line breaks, hairlines, or columns.

### 74 · Decorative status dots
A coloured dot before every nav link, list row, badge, or availability label. Zero by default. Acceptable only when the dot conveys real semantic state (live server status, a genuine availability flag), and then sparingly.

Partially mechanical: impeccable's `pulsing-dot` catches the animated variant.

### 75 · Em-dash, anywhere
**Zero tolerance.** `—` and separator-`–` are banned in headlines, eyebrows, pills, body copy, quotes, attribution, captions, button text, alt text. No "sparingly" allowance — that phrasing has been ignored in every prior round. Permitted dashes: the regular hyphen `-`, and the minus sign in maths.

Restructure instead: two sentences with a period, a comma, parentheses, or a colon. Quote attribution uses ` - ` or a line break.

**[ours]** This is the strictest form of a rule that appears in three places in this system: impeccable's `em-dash-overuse` detector rule (mechanical, threshold-based), `humanizer`'s style bans (in the copy gate), and here (zero-tolerance, visual). The zero-tolerance version wins.

---

## Typography flourishes

### 76 · `<br>`-broken and italicised headlines
`for thirty<br><em>years.</em>` as a default "design move". Headlines read naturally first; they get clever only when the brief demands it.

**[ours]** Distinct from gate 38a / `italic-serif-display`, which ban italic display type outright. This gate bans the *break-and-italicise* composition even where an italic is otherwise legal.

### 77 · Vertical rotated text
`INDEX OF WORK, 2018 - 2026` rotated 90°. Agency-portfolio cliché. Only for an explicitly experimental brief where it serves real composition.

### 78 · Crosshair and hairline grid decoration
Vertical and horizontal rules drawn purely to make the page feel designed. Use them only when they organise real content.

---

## Fake product surfaces

### 79 · Div-based fake product UI
Fake task lists, terminals, dashboards built from styled `<div>`s to simulate a screenshot. The single most reliable LLM-design tell. Use a real screenshot, a generated image, a real component preview, or nothing.

**[ours]** Overlaps gate 47 (re-drawn chrome) — 47 bans the *frame* (browser bar, phone bezel), 79 bans the fabricated *content* inside it. Both apply.

### 80 · Fake version footers
`v0.6.2-rc.1`, `last sync 4s ago · main` inside a fake screenshot, or as a real footer on a marketing page. Build metadata is devtool fixture content, not landing-page content.

### 81 · Live-stock counters as decoration
`Reservation 412 of 800`. Only when the brief is a genuine limited-run waitlist with real data.

---

## Imagery treatment

### 82 · Pills and labels overlaid on images
`<span>` overlays on photos reading `Brand · 02`, `PLATE · BRAND`, `Field notes - journal`. Either let the image stand alone or caption it directly below, outside the frame.

### 83 · Photo-credit captions as decoration
`Field study no. 12 · Ines Caetano`, `Plate 03 · House archive`, `Frame XII · 35mm` under stock or placeholder images. Photo credit is legitimate only when crediting a real photographer for a real photo. Otherwise skip it, or use one functional line.

---

## Copy tells

### 84 · Performative-craftsman labels and social proof
- `Quietly in use at` / `Quietly trusted by` → use `Trusted by`, `Used at`, or let the logos speak.
- `From the field` / `Field notes` / `Currently on the bench` / `On our desks` / `Loose plates` → use plain functional labels (`Testimonials`, `Latest writing`) or none.
- Mock-humble industry asides (`We respect the French ones`).

Partially mechanical: impeccable's `theater-slop-phrase` and `marketing-buzzword` catch some phrasings.

### 85 · Atmospheric locale, time, and weather strips
`LIS 14:23 · 18°C` in a nav, `Lisbon, working with founders` in a hero, `1200-690 Lisbon, Portugal` as a footer flourish. Allowed only for a genuinely timezone-distributed studio, a travel brand, or a real physical venue. A plain contact address in the footer is fine; an atmospheric strip is not.

---

## Lists and comparison visuals

### 86 · `border-t` + `border-b` on every row
A ten-row spec table with a hairline under each row is the laziest available layout. Pick one (bottom border between rows, or a top border above the group) and use it sparingly. For lists over five items, reach for a real UI component instead of `<ul>` + `divide-y`.

### 87 · Scoring bars with filled background tracks
`bg-zinc-200` tracks with a partial fill, used as a comparison visual on a marketing page. Dashboard clutter. Prefer a number plus a small icon, or a thin inline bar with no background track.

---

## Scroll cues

### 88 · Any scroll cue
`Scroll`, `↓ scroll`, `Scroll to explore`, `Scroll to walk through it`, animated mouse-wheel icons. If the visitor has not scrolled, they are looking at the hero — they know what scrolling is. The bottom of the viewport does not need a label.

---

## [ours] Mechanical coverage summary

| Gate | Mechanically caught by |
|---|---|
| 69 | `numbered-section-labels` (common shapes only) |
| 74 | `pulsing-dot` (animated variant only) |
| 75 | `em-dash-overuse` (threshold, not zero-tolerance) |
| 76 | `italic-serif-display` (display italic, not the break-composition) |
| 84 | `theater-slop-phrase`, `marketing-buzzword` (some phrasings) |

Everything else in 66–88 is model-enforced. Run this file as a checklist before emit; the pre-emit self-critique in the front door is where it binds.
