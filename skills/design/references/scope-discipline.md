# Scope discipline · what you may and may not touch

**Load on every edit to existing work. Always load on a targeted change.**

> Source: Anthropic's Claude Design output and content guidelines, ported at full fidelity. Blocks marked **[ours]** are this repo's framing.

**[ours]** This reference governs *when to do what*, which is where agent design work most often goes wrong in ways the user notices immediately: asked for one colour, it redesigns the section. These rules are what stop that.

---

## The targeted-change rule

> *"When the user asks for a small, targeted change — some text, a color, one element — change ONLY that: leave all other layout, spacing, margins, fonts, sizes, positions, colors, and content exactly as they are, don't redesign or 'improve' parts you weren't asked to touch, and prefer targeted string replacement over rewriting the file. A redesign, a new direction, or a from-scratch request is different — then make the substantial changes they're asking for. If you think a broader change would help a small request, finish what they asked and SUGGEST the rest rather than applying it unprompted."*

**[ours]** Unrequested improvement is not a bonus; it is unreviewed change mixed into a reviewed one. The user now has to audit a diff they didn't ask for. Finish the ask, then say what else you noticed.

## The inheritance checklist

> *"When adding to an existing UI, understand its visual vocabulary first and follow it: copywriting style, color palette, tone, hover/click states, animation styles, shadow + card + layout patterns, density, etc."*

**[ours]** Read this as a checklist, not a sentiment — eight axes, each checked before the first line:

1. Copywriting style
2. Colour palette
3. Tone
4. Hover and click states
5. Animation style
6. Shadow patterns
7. Card and layout patterns
8. Density

This is the binding inheritance rule from the front door, stated concretely. A section, component, feature, or state inside an established surface inherits that surface — it never starts a second identity.

## Colour

> *"Color usage: try to use colors from brand / design system, if you have one. If it's too restrictive, use oklch to define harmonious colors that match the existing palette. Avoid inventing new colors from scratch."*

## Links

> *"Link styling: always define default `a` and `a:hover` colors from the design's palette (alongside body resets), even when the design has no links yet — users add links later, and undefined links render browser-default blue."*

**[ours]** Gate 61. Cheap, invisible until it isn't.

## Version preservation

> *"When doing significant revisions of a design, copy it and edit the copy to preserve the old version (e.g. My Design.html, My Design v2.html)."*

**[ours]** In a git repo the branch usually covers this. Copy explicitly when the work is a standalone artifact outside version control, or when the user will want to compare side by side.

## Assets

> *"Copy needed assets from design systems or UI kits (do not reference them directly); make targeted copies of only the files you need, never bulk-copy large folders (>20 files)."*

---

## Content guidelines

### No filler

> *"**No filler.** Every element earns its place — never pad with placeholder text, dummy sections, or space-filling content; an empty-feeling section is a layout problem, not a content gap. One thousand no's for every yes. Avoid data slop (unneeded numbers, icons, stats). Less is more; bias towards minimalism."*

**[ours]** "An empty-feeling section is a layout problem, not a content gap" is the load-bearing sentence. The reflex when a section feels thin is to add a stat row or a third card. The fix is almost always composition.

### Ask before adding material

> *"**Ask before adding material.** If extra sections, pages, or copy would improve the design, ask first — the user knows their audience and goals better than you."*

### Create a system up front

> *"**Create a system up front:** after exploring design assets, vocalize it — a layout per element class (section headers, titles, images) with intentional variety and rhythm: varied section-starter backgrounds, full-bleed layouts when imagery is central. Max 1-2 background colors. Use an existing type design system if you have one; otherwise pick 1-2 font pairings and apply them consistently."*

**[ours]** *Vocalize it* — say the system out loud before building, so the user can correct the system rather than correcting twelve components one at a time.

### Minimum scales

> *"**Minimum scales:** 1920x1080 slide text never below 24px, ideally much larger; print documents 12pt minimum; mobile mockup hit targets never below 44px."*

**[ours]** The 44px mobile hit target is gate 62 and applies to all web work, not only mockups.

### AI slop tropes

> *"**Avoid AI slop tropes:** incl. but not limited to aggressive gradient backgrounds, emoji (unless explicitly part of the brand), rounded containers with left-border accent color, overused fonts (Inter, Roboto, Arial, Fraunces)."*
>
> *"Avoid drawing imagery using SVG; use placeholders and ask for real materials."*

**[ours]** All four font names are also in impeccable v4's `overused-font` detector rule, which additionally covers Geist, Plus Jakarta Sans, and Space Grotesk — so this fires mechanically.

### Emoji

> *"Emoji usage: only if design system uses"*

### Layout mechanics

> *"CSS: `text-wrap: pretty`, CSS grid and other advanced effects are your friends!"*

> *"**Strongly prefer flex/grid with `gap` over inline flow.** Lay out sibling groups (buttons, chips, icons, cards, nav items, toolbars) with `display: flex`/`grid` + `gap:`, not inline siblings spaced by source whitespace or per-element margins — gap spacing survives direct-manipulation edits (drag-reorder, delete, duplicate); whitespace text nodes don't. Inline flow is for runs of text with the occasional `<a>`/`<strong>`/`<em>`, not UI layout."*

### Canonical markup

> *"Write canonical HTML: close every non-void element explicitly, double-quote every attribute value, and don't self-close non-void elements."*

---

## Redesign protocol

> Source: `design-taste-frontend` (Leonxlnx/taste-skill) v2, Section 11. Ported at full fidelity.

**[ours]** This section governs *existing-site* work, where the targeted-change rule above governs *small* work. Misclassifying the mode is the single biggest source of bad redesign output — and it is exactly the risk on a rename-plus-merge job like Snajp, where "keep the soul" and "change the name" are both true at once.

### Detect the mode first

- **Greenfield** — no existing site, or a full overhaul is approved.
- **Redesign · preserve** — modernise without breaking the brand. Audit first, extract brand tokens, evolve gradually.
- **Redesign · overhaul** — new visual language over existing content. Treat as greenfield for visuals; preserve content and information architecture.

If ambiguous, ask **once**: *"Should this redesign preserve the existing brand, or are we starting visually from scratch?"*

**[ours]** This maps onto the gate in the front door: *preserve* is Tier 1 (derive from existing evidence), *overhaul* is Tier 1 or 3 depending on whether brand evidence survives the overhaul, and *greenfield* is Tier 3. A partial rebrand — new name, kept traits — is **preserve**, not greenfield, and impeccable v4 calls the same branch *"Incomplete brand: preserve confirmed assets and recognizable traits, then help the user expand the system."*

### Audit before touching

Document the current state before proposing changes:

- **Brand tokens** — primary and accent colours, type stack, logo treatment, radii.
- **Information architecture** — page tree, primary nav, key conversion paths.
- **Content blocks** — what exists, what is doing work, what is filler.
- **Patterns to preserve** — signature interactions, recognisable hero, copy voice.
- **Patterns to retire** — slop tells, broken layouts, dead links, generic stock imagery, performance traps.
- **SEO baseline** — ranking pages, meta titles, structured data, OG cards. **SEO migration is the number-one redesign risk.**

### Preservation rules

- **Do not change information architecture** unless asked. Keep page slugs, anchor IDs, and primary nav labels stable for SEO and muscle memory.
- **Extract brand colours before applying any palette calibration.** A brand that is already purple stays purple.
- **Preserve copy voice** unless a rewrite was asked for. Visual modernisation is not a content rewrite.
- **Honour existing accessibility wins.** Do not regress focus states, alt text, keyboard nav, or contrast.
- **Respect existing analytics events.** Do not rename buttons, form fields, or section IDs that downstream tracking depends on.

### Modernisation levers, in priority order

Apply in order; stop when the brief is satisfied.

1. **Typography refresh** — biggest visual lift per unit of risk.
2. **Spacing and rhythm** — section padding, vertical rhythm.
3. **Colour recalibration** — desaturate, unify neutrals, keep the brand accent.
4. **Motion layer** — micro-interactions on existing components.
5. **Hero and key-section recomposition** — restructure top-of-funnel.
6. **Full block replacement** — only when a block is unsalvageable.

Decision rule: if IA, content, and SEO are sound, take **targeted evolution** (levers 1–4) — roughly 70% of the value at 40% of the risk. Go to full redesign only when the visual debt is structural (broken IA, no design system, broken mobile). If the brand itself is changing, that is greenfield.

### What never changes silently

Never modify without explicit approval:

- URL structure and route slugs
- Primary nav labels
- Form field names or order (breaks analytics and autofill)
- Brand logo or wordmark
- Existing legal, consent, or cookie copy

---

## [ours] Motivated exclusion

Claude Design's **inline-styles-only** rule is deliberately **not** ported. It exists because that product streams designs into a live preview, where *"class-based CSS delays everything the user sees until both rules and markup have streamed."* That constraint does not apply to a Next.js or Tailwind codebase, where inline styles would defeat the token system that discipline 3 in the front door requires. It is listed here because it reads like a design principle and is not one.
