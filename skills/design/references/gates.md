# Gates

**Load on every build.** Numbered, citable, non-negotiable. A hook that denies a write cites a gate number; so should you when you waive one.

Three sources, one numbering space:

| Range | Source | Where the detail lives |
|---|---|---|
| **1–57** | Hallmark slop-test | [`slop-test.md`](slop-test.md) — ported verbatim, **source of truth** |
| **58–65** | This repo — the gate order, scope, and derivation rules | Below |
| **66–88** | `design-taste-frontend` v2 production-test tells | [`production-tells.md`](production-tells.md) — micro-decoration signatures |
| **mechanical** | impeccable v4 detector, 68 deterministic rules | `detect.mjs`, mapped below |

Do not restate 1–57 here. Read [`slop-test.md`](slop-test.md). Do not restate 66–88 here. Read [`production-tells.md`](production-tells.md).

**Why 66–88 exist separately.** Gates 1–57 catch structural and visual slop. Gates 66–88 catch *micro-decoration* — version labels, numbered eyebrows, middle-dot chains, status dots, photo-credit captions, scroll cues, locale strips. Each looks like a deliberate designer choice in isolation; together they are the most recognisable AI-page signature in production. Load them on every marketing, landing, or portfolio build.

---

## Gates 58–65 · the gate-order rules

These exist because Tiers 0–2 are this system's contribution and nothing upstream enforces them.

### 58 · Tier not declared

Did the build state its tier out loud before picking any token? If no tier was named, fail. Silent tier selection is how Tier 1 gets skipped — the model reads brand evidence, does not register it as authority, and invents anyway. The declaration is cheap and makes the omission visible: *"Tier 1 — deriving from the Snajp wordmark and the existing type scale."*

### 59 · Token not traceable to tier evidence

At Tiers 0–2, can every colour, face, radius, and spacing step be traced to a named source — a `DESIGN.md` entry, a file in the codebase, the logo, the studied reference? A token that cannot be traced was invented, and invention is Tier 3 only. Fail per untraceable token. At Tier 3 this gate passes trivially.

### 60 · Demoted-skill palette in a Tier 0–2 build

Does the output contain a hardcoded value from a skill whose palette is fixed?

| Skill | Values that trip this gate |
|---|---|
| `minimalist-ui` | `#F7F6F3` `#FBFBFA` `#F9F9F8` `#EAEAEA` `#111111` `#2F3437` `#787774` `#333333` `#FDEBEC` `#E1F3FE` `#EDF3EC` `#FBF3DB` `#9F2F2D` `#1F6C9F` `#346538` `#956400` |
| `industrial-brutalist-ui` | `#F4F4F0` `#EAE8E3` `#050505` `#0A0A0A` `#121212` `#E61919` `#FF2A2A` `#4AF626` |
| `high-end-visual-design` | `#050505` `#FDFBF7` |

Auto-fail at Tiers 0–2. These skills may contribute craft vocabulary — spacing rhythm, detail patterns, elevation logic — but their palettes are overridden by the locked tokens. At Tier 3 the gate passes if the skill was chosen deliberately and by name.

**This gate is the instrumented trap.** Every firing is logged to the session ledger as a `trap` event with the file and whether it was caught before or after the write. See [`component-routing.md`](component-routing.md) § Telemetry.

### 61 · Undefined link colours

Are default `a` and `a:hover` colours defined from the palette, even when the page currently has no links? If not, fail. Links added later render browser-default blue, which is off-brand on every design ever made.

### 62 · Mobile hit target below 44px

Does every interactive element present at least a 44×44px touch target at mobile widths? Padding counts; visual size does not have to change. Fail per element below the floor.

### 63 · Value snapped to a framework default

Was a source value rounded to a grid step or a framework token? `13px` must not become `14px`; `5px` must not become `4px`; a brand orange must not become the nearest Tailwind orange. The source is ground truth and its odd numbers are the brand. Fail per snapped value.

Mechanically covered by `design-system-radius`, `design-system-font-size`, and `design-system-color` once `DESIGN.md` exists.

### 64 · Change beyond the ask

On a targeted request, did anything change besides what was asked? Layout, spacing, margins, fonts, sizes, positions, colours, and content outside the named target must be byte-identical. Improvements are *suggested in the reply*, never applied. Fail on any unrequested diff hunk.

Does not apply to redesign, new direction, or from-scratch requests — those are substantial by definition. See [`scope-discipline.md`](scope-discipline.md).

### 65 · Second identity inside an established surface

Does a new section, component, feature, or state introduce type, colour, motion, or component language that does not exist elsewhere on the surface? A local addition inherits; it does not start a second identity. Check the eight axes in [`scope-discipline.md`](scope-discipline.md) § inheritance checklist. Fail on any axis that diverges without the user asking for it.

---

## Reinterpreting gate 57

`slop-test.md` gate 57 fires when a `study` diagnosis is discarded in favour of a catalog theme. Its principle generalises to our gate order and is read as: **any derived or studied system discarded for a catalog theme, at any tier above 3, is an auto-fail.** The specific catalog-theme name list in the ported text is the Tier-3 vocabulary; the failure it describes — reverting to the attractor after doing the derivation work — is exactly what gates 59 and 60 catch at Tiers 1 and 2.

The ported file is not edited. This paragraph is the reinterpretation.

---

## Mechanical coverage

`detect.mjs` carries 68 deterministic rules. Run it once over changed files at Step 5; parse the JSON, because **exit code stays 0 when findings exist**.

```bash
node "$HOME/.agents/skills/impeccable/scripts/detect.mjs" --json <files>
```

Contract rules — these read `DESIGN.md` directly and are what `design-gate.py` denies on:

| Rule id | Enforces |
|---|---|
| `design-system-color` | Colour outside the `DESIGN.md` palette |
| `design-system-font` | Face not declared in `DESIGN.md` typography |
| `design-system-font-size` | Size outside the declared scale |
| `design-system-radius` | Radius outside the declared scale |

Slop rules overlapping our numbered gates: `side-tab` (gate 3 family), `gradient-text`, `dark-glow`, `radial-halo`, `radial-spotlight-glow`, `overused-font`, `italic-serif-display` (38a), `nested-cards`, `icon-tile-stack`, `hero-eyebrow-chip`, `numbered-section-labels` (54 family), `repeated-section-kickers`, `oversized-h1`, `flat-type-hierarchy`, `cream-palette`, `ai-color-palette`, `border-accent-on-rounded`, `gpt-thin-border-wide-shadow`, `edge-flush-cards`, `repeating-stripes-gradient`, `shape-assembled-illustration`, `codex-grid-background`.

Layout and responsive: `clipped-overflow-container`, `text-overflow`, `text-occlusion`, `first-viewport-column-overflow`, `body-text-viewport-edge`, `broken-image`, `image-hover-transform`, `layout-transition`.

Type and legibility: `low-contrast`, `gray-on-color`, `tiny-text`, `undersized-ui-text`, `line-length`, `tight-leading`, `wide-tracking`, `extreme-negative-tracking`, `all-caps-body`, `justified-text`, `single-font`, `heading-rhythm`, `skipped-heading`.

Copy — these run before the copy gate and catch its cheapest cases mechanically: `em-dash-overuse`, `marketing-buzzword`, `theater-slop-phrase`, `aphoristic-cadence`, `repeated-container-text`.

Motion and state: `bounce-easing`, `blinking-cursor`, `pulsing-dot`, `marquee`, `content-hidden-at-rest`, `monotonous-spacing`, `cramped-padding`, `script-error`.

**Not mechanically covered** — gates 58, 59, 60, 64, 65 and the whole gate order are model-enforced. `design-gate.py` and `design-route.py` cover 60 and 63 by pattern; the rest are judgment and are why the pre-emit self-critique exists.

---

## Waiving a gate

A gate may be waived only when the user's own brief calls for it. Say which gate, and why the brief overrides it, in one line. Never waive silently, and never waive by softening the element — rewrite it or keep it.

impeccable v4's rule governs: **the brief wins; your own habit does not.**

Persistent, project-wide exceptions go through the detector's config rather than being re-argued each session:

```bash
node "$HOME/.agents/skills/impeccable/scripts/hook-admin.mjs" ignore-value overused-font <Font> --shared --reason "..."
```
