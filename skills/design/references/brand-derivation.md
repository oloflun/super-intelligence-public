# Tier 1 · Brand derivation

**Load when the pre-flight scan found brand evidence: a logo or wordmark, a brand hex in code, a deployed site, `tailwind.config` colours, a favicon, or a brand PDF.**

This is where the design language comes from when the subject already has an identity. Not a catalogue, not a named lane, not the aesthetic the model reaches for by default — the subject's own evidence, interrogated until it yields a system.

> Source: Anthropic's Claude Design "Create design system" procedure, ported at full fidelity. Blocks marked **[ours]** are this repo's framing. Everything else is the upstream procedure and is the source of truth.

**[ours] Why this tier exists.** Three installed specialist skills hardcode complete palettes, and the model's own defaults cluster hard (cream + high-contrast serif + terracotta; near-black + one neon accent; broadsheet hairlines + italic serif + tracked mono labels). Any of those can be *correct* — but only when the brief calls for them. When brand evidence exists and the output lands on a training-data cluster anyway, the derivation didn't happen. project-a is the reference case: `#F27722` + Afacad uppercase + black surfaces + an asymmetric rhombus is derivable from the mark and the product, and no catalogue produces it.

---

## What counts as evidence

Ranked. Higher beats lower on conflict.

1. **An explicit brand commitment** in `PRODUCT.md` or stated by the user this session.
2. **The logo or wordmark file** — its hue, its geometry, its letterform character.
3. **Live production code** — `tailwind.config` colours, `:root` custom properties, `@font-face`, existing components.
4. **The deployed site** — read the CSS, not a screenshot.
5. **Favicon, app icon, social card** — often the only surviving artifact of an older identity.
6. **Brand PDF, deck, or guidelines doc** — treat as reference material, not as copy to paste.

**Screenshots rank last and never alone.** *"Do not recreate UIs from screenshots alone unless you have no other choice! Use the codebase, or Figma's get-design-context, as a source of truth. Screenshots are much lossier than code; use screenshots as a high-level guide but always find components in the codebase if you can!"*

---

## Rule 1 · The source is ground truth, values are exact

> *"The attached kit is the ground truth. When its values differ from the published conventions of a component library it resembles (shadcn, MUI, etc.), the kit wins. Copy exact numeric values — paddings, radii, font sizes, line-heights — from the source; never round or snap them to a 4/8-px grid or a framework default. If the kit says 5px, write 5px, not 4px."*

**[ours]** This is the single most-violated rule in agent design work and the direct antidote to the model normalising a brand into its own defaults. `13px` does not become `14px`. `5px` does not become `4px`. `#F27722` does not become `#F97316` because that's the Tailwind orange. A brand is made of its odd numbers; snapping them to a scale is how it stops being that brand. The `design-system-radius` and `design-system-color` detector rules enforce this mechanically once `DESIGN.md` exists.

## Rule 2 · Never fabricate identity

> *"Copy logos, icons and other visual assets into `assets/`. **If the provided sources contain no logo, do not create one**: render the brand name in plain type wherever a mark would go and note the absence in readme.md. Never draw, reconstruct, or approximate a company's real logo or brand mark from memory — even when the company seems identifiable from font names or sample content — and never rebrand the design system with a company identity the user didn't provide. NEVER draw your own SVGs or generate images; COPY icons programmatically if you can."*

## Rule 3 · Inventory is defined by the source

> *"When a concrete source defines the inventory (a mounted .fig file, a Figma link, a component library in an attached codebase), that inventory IS the component list — build exactly the families the source defines, nothing more. Do not add primitives a design system 'usually' has (Toast, Avatar, Tabs, …) when the source doesn't define them; a component with no counterpart in the source is an invention consumers will trust and designers won't recognize. If an addition is genuinely needed (e.g. an Icon wrapper for a glyph set), list it under 'Intentional additions' with a one-line reason."*

> *"Enumerate before you build: list the source's FULL component inventory FIRST, put every family on your todo list, and build ALL of them, tracking progress against that list. Do NOT stop at a 'core subset'. If you cannot finish, end your turn by reporting exactly which families remain unbuilt and ask the user whether to continue — never end silently incomplete."*

## Rule 4 · Stop on inaccessible resources

> *"Stop if key resources are inaccessible: if a codebase was attached or mentioned, but you are unable to access it, you MUST stop and ask the user to re-attach it. NEVER go ahead spending tons of time making a design system if you cannot access all the resources the user gave you. This applies mid-run too: if reads start failing or rate-limiting partway through, stop and report exactly what you did and did not read — never infer or invent component names, structures, or values for content you could not read."*

## Rule 5 · Icons are copied, never approximated

> *"For icons: FIRST copy the codebase's own icon font/sprite/SVGs into `assets/` if you can. Otherwise, if the set is CDN-available (e.g. Lucide, Heroicons), link it from CDN. If neither, substitute the closest CDN match (same stroke weight / fill style) and FLAG the substitution."*

> *"When creating slides and UI kits, avoid cutting corners on iconography; instead, copy icon assets in! Do not create halfway representations of iconography using hand-rolled SVG, emoji, etc."*

> *"Avoid reading SVGs — this is a waste of context! If you know their usage, just copy them and then reference them."*

---

## The VISUAL FOUNDATIONS interrogation

**Answer ALL of these.** This is the derivation itself — the questions are the procedure. An unanswered question is an axis where the model's default will leak in.

> *"Explore, update readme.md with VISUAL FOUNDATIONS section that talks about the visual motifs and foundations of the brand. Colors, type, spacing, backgrounds (images? full-bleed? hand-drawn illustrations? repeating patterns/textures? gradients?), animation (easing? fades? bounces? no anims?), hover states (opacity, darker colors, lighter colors?), press states (color? shrink?), borders, inner/outer shadow systems, protection gradients vs capsules, layout rules (fixed elements), use of transparency and blur (when?), color vibe of imagery (warm? cool? b&w? grain?), corner radii, what do cards look like (shadow, rounding, border), etc. whatever else you can think of. answer ALL these questions."*

Working checklist:

- **Colours** — every value, exact. Which is the ground, which is the accent, what proportion of surface does each carry.
- **Type** — families, weights, the real scale steps, tracking, the display/body relationship.
- **Spacing** — the actual rhythm, not the nearest standard scale.
- **Backgrounds** — images? full-bleed? hand-drawn illustration? repeating pattern or texture? gradients? flat?
- **Animation** — easing curves. Fades? Bounces? No animation at all?
- **Hover states** — opacity shift, darker, lighter, or a colour change?
- **Press states** — colour, shrink, both, neither?
- **Borders** — where, what weight, what colour.
- **Shadows** — inner and outer systems, separately.
- **Protection gradients vs capsules** — how does text sit on imagery?
- **Layout rules** — fixed elements, container behaviour, what is pinned.
- **Transparency and blur** — used at all? When specifically?
- **Imagery colour vibe** — warm, cool, black and white, grain?
- **Corner radii** — every distinct value in use.
- **Cards** — shadow, rounding, border. What does a card look like here?

**[ours]** Where the evidence is silent on an axis, say so explicitly rather than filling it from habit: *"No press-state evidence in the source; proposing a 1px translate consistent with the existing hover treatment."* A named assumption is recoverable. A silent default is not.

**[ours] Deriving from a mark.** When the logo is the strongest evidence: pull the **hue** from its dominant colour (measure it, don't eyeball it); pull **geometry** from its construction — a mark built on diagonals licenses asymmetric section breaks, one built on circles doesn't; pull **type character** from the wordmark's letterforms — its weight, width, and whether it is geometric, humanist, or grotesque narrows the display face to a family, not to a specific font. Then tint the neutrals toward the brand hue (chroma 0.005–0.01) so the ground belongs to the same world as the accent.

## The CONTENT FUNDAMENTALS interrogation

> *"Explore, then update readme.md with a CONTENT FUNDAMENTALS section: how is copy written? What is tone, casing, etc? I vs you, etc? are emoji used? What is the vibe? Include specific examples"*

- How is copy written — long or clipped, formal or direct?
- Tone.
- Casing — sentence case, title case, all-caps labels?
- First person or second? "We" or "you" or neither?
- Emoji — used at all?
- The vibe, in the brand's own words.
- **Include specific examples** — pull real strings from the source.

**[ours]** This section is the input to the copy gate. Without it the gate enforces generically good copy instead of *this brand's* voice.

---

## Colour, when the evidence runs out

> *"Color usage: try to use colors from brand / design system, if you have one. If it's too restrictive, use oklch to define harmonious colors that match the existing palette. Avoid inventing new colors from scratch."*

Extend, don't replace. A palette needing a fifth step derives it in OKLCH from the four that exist.

---

## Output

### Token files

> *"Explore the codebase and/or figma design contexts and write the token CSS files — CSS custom properties on `:root`, both base values (`--fg-1`, `--font-serif-display`) and semantic aliases (`--text-body`, `--surface-card`). Copy any webfonts/ttfs into the project and write the `@font-face` rules in a CSS file. Then write the root `styles.css` as a list of `@import` lines only (never inline rules there) that reaches every token and font-face file."*

Default layout, unless the codebase has its own convention:

- `tokens/` — one file per concern (`colors.css`, `typography.css`, `spacing.css`), each `@import`ed from the root entry.
- `components/<group>/` — reusable primitives.
- `assets/` — logos, icons, illustrations, imagery.
- Root entry is `styles.css` / `index.css` / `globals.css` / `global.css` / `main.css` / `theme.css` / `tokens.css`, first match wins.

> *"If you are missing font files, find the nearest match on Google Fonts. Flag this substitution to the user and ask for updated font files."*

### `DESIGN.md`

**[ours]** The derived system is recorded as `DESIGN.md` at the project root, written by `$impeccable document` **from the built world, not before it** — impeccable v4's rule holds: *"a rulebook written before the build gets defended against reality instead of describing it."*

The YAML frontmatter is machine-readable and the detector reads it directly. `colors`, `typography`, and `rounded` are **maps, not arrays** — array form silently fails to parse and every real colour then reports as undocumented:

```yaml
---
name: Snajp
description: One-line tagline
colors:
  ink: "#0B0B0C"
  paper: "#F5F3EF"
  accent: "#F27722"
typography:
  display:
    fontFamily: "Afacad"
    fontSize: "72px"
  body:
    fontFamily: "Source Serif 4"
    fontSize: "17px"
rounded:
  card: "5px"
---
```

Colour keys are descriptive slugs (`oxblood-deep`, not `blue-800`). Typography is one entry per role, carrying only props that are real for the project. Skip anything the project doesn't have — *"Empty scale keys or fabricated tokens pollute the spec."* Properties the schema can't hold (tonal ramps, shadows, motion, breakpoints, full component snippets) go in the `.impeccable/design.json` sidecar.

Once this file exists the project is **Tier 0** and this reference does not run again.

### The `{brand}-design` skill

**[ours]** The persistence layer. A derived system that lives only in one repo has to be re-derived in every future session; emitted as a skill it is loadable anywhere.

> *"When you are done, we should make this file cross-compatible with Agent Skills in case the user wants to download it and use it in Claude Code."*

```markdown
---
name: {brand}-design
description: Use this skill to generate well-branded interfaces and assets for {brand}, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.
If creating visual artifacts (slides, mocks, throwaway prototypes, etc), copy assets out and create static HTML files for the user to view. If working on production code, you can copy assets and read the rules here to become an expert in designing with this brand.
If the user invokes this skill without any other guidance, ask them what they want to build or design, ask some questions, and act as an expert designer who outputs HTML artifacts _or_ production code, depending on the need.
```

Write it to `~/.agents/skills/{brand}-design/`, carrying the README (with both interrogation sections answered in full), the token files, and the copied assets.

---

## Partial and changing brands

**[ours]** A rename, a pivot, or a half-finished identity is **not** a licence to invent. impeccable v4's branch applies:

> *"**Incomplete brand:** preserve confirmed assets and recognizable traits, then help the user expand the system for this new surface."*

Procedure: list what is **confirmed** (traits the user named as worth keeping), what is **changing** (explicitly stated), and what is **unresolved**. Derive only into the unresolved space. Confirmed traits are constraints, not suggestions — if the user says "keep the large fonts", the large fonts survive every other change on the page.

---

## Finishing

> *"You are done! Do NOT summarize your output; just mention CAVEATS (e.g. things you were unable to do or unsure) and have a CLEAR, BOLD ASK for the user to help you ITERATE to make things PERFECT."*

**[ours]** Report every substituted font, every named assumption on a silent axis, and every source you could not read.
