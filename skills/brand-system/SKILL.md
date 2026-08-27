---
name: brand-system
description: "Build a complete design system folder from a brand's own materials — tokens, assets, components, UI kits, and a written guide — then emit it as a reusable {brand}-design skill. Use when the user asks to create a design system, brand kit, UI kit, or design tokens for a company; when they attach a codebase, Figma link, brand PDF, or deck and want the system extracted; or when a project needs a portable identity that survives across sessions. Fires on 'create a design system', 'build a brand kit', 'extract the design system', 'make our tokens', 'gör ett designsystem'."
user-invocable: true
---

# brand-system

Builds the durable artifact: a folder holding a brand's real assets, real tokens, real components, and a written guide — then packages it as a skill so the identity is loadable in any future session and any other project.

> Source: Anthropic's Claude Design "Create design system" procedure, ported at full fidelity. The interrogation content lives in [`design/references/brand-derivation.md`](../design/references/brand-derivation.md) and is the source of truth for *how* to derive; this skill is the *procedure and output shape*.

**When to use this instead of `design`.** `design` builds surfaces and derives a system as a by-product. This skill's deliverable *is* the system. Reach for it when the user asks for a design system directly, or when several surfaces will be built and the identity should be settled and portable first.

---

## What a design system is here

> *"Design systems are folders on the file system containing typography guidelines, colors, assets, brand style and tone guides, css styles, and React recreations of UIs, decks, etc. They give design agents the ability to create designs against a company's existing products, and create assets using that company's brand. Design systems should contain real visual assets (logos, brand illustrations, etc), low-level visual foundations (e.g. typography specifics; color system, shadow, border, spacing systems), reusable UI components, and high-level UI kits (full screens)."*

**Real assets, not descriptions of assets.** A system that says "the logo is orange" and contains no logo file is a document, not a system.

---

## Procedure

Build the todo list first, then work it.

1. **Explore the provided materials.** Read every asset — codebase, Figma, PDF, deck, deployed site. Find product copy; examine core screens; find any existing design-system definitions.
2. **Write `readme.md`** with the company/product context and the products represented. Record the sources you were given — full Figma links, repos, paths. *"Do not assume the reader has access, but store in case they do."*
3. **Extract decks** if any were attached: pull key assets and text to disk.
4. **Write the token files.** CSS custom properties on `:root` — base values (`--fg-1`, `--font-serif-display`) *and* semantic aliases (`--text-body`, `--surface-card`). Copy webfonts in and write the `@font-face` rules. Then the root entry as `@import` lines only, never inline rules.
5. **Write CONTENT FUNDAMENTALS** into `readme.md` — how copy is written, tone, casing, I vs you, emoji, vibe, **with specific examples**.
6. **Write VISUAL FOUNDATIONS** into `readme.md` — the full interrogation in [`brand-derivation.md`](../design/references/brand-derivation.md). *"answer ALL these questions."*
7. **Substitute missing fonts** from the nearest Google Fonts match. **Flag every substitution** and ask for the real files.
8. **Build foundation specimen cards** — see below.
9. **Copy assets in.** Logos, icons, illustrations, imagery. Then write an ICONOGRAPHY section: which icon system, is there an icon font, SVGs or PNGs, is emoji used, are unicode chars used as icons.
10. **Author the components** — see below.
11. **Build a UI kit per product** — see below.
12. **Sample slides**, only if a slide template was given.
13. **Index `readme.md`** — a manifest of the root folder plus a list of components and UI kits.
14. **Emit `SKILL.md`** — see below.
15. **Finish**: *"Do NOT summarize your output; just mention CAVEATS (e.g. things you were unable to do or unsure) and have a CLEAR, BOLD ASK for the user to help you ITERATE to make things PERFECT."*

---

## Layout

Only the root CSS entry is fixed: `styles.css` (or `index.css` / `globals.css` / `global.css` / `main.css` / `theme.css` / `tokens.css`, first match wins). *"Keep it as a list of `@import` lines only."*

Organize the rest however suits the brand. Default unless the codebase has its own convention:

```
tokens/            one file per concern — colors.css, typography.css, spacing.css
components/<group>/ reusable primitives, grouped by concern
ui_kits/<product>/  full-screen recreations of real product views
guidelines/         specimen cards and deeper-dive prose
assets/             logos, icons, illustrations, imagery
readme.md           the design guide and manifest
```

---

## Components

**The source defines the inventory.**

> *"When a concrete source defines the inventory (a mounted .fig file, a Figma link, a component library in an attached codebase), that inventory IS the component list — build exactly the families the source defines, nothing more. Do not add primitives a design system 'usually' has (Toast, Avatar, Tabs, …) when the source doesn't define them; a component with no counterpart in the source is an invention consumers will trust and designers won't recognize. If an addition is genuinely needed (e.g. an Icon wrapper for a glyph set), list it in readme.md under 'Intentional additions' with a one-line reason."*

> *"Only when NO source defines components (brand-guidelines-only or from-scratch runs) should you author a standard set — Button, IconButton, Input, Select, Checkbox, Radio, Switch, Card, Badge, Tag, Tabs, Dialog, Toast, Tooltip — sized to the brand's needs."*

> *"Enumerate before you build: list the source's FULL component inventory FIRST, put every family on your todo list, and build ALL of them, tracking progress against that list. Do NOT stop at a 'core subset'. If you cannot finish, end your turn by reporting exactly which families remain unbuilt and ask the user whether to continue — never end silently incomplete."*

**The contract per component** — three sibling files:

- `<Name>.jsx` (or `.tsx`) — `export function <Name>(props) {…}`, named PascalCase export. Self-contained: React only, styling via the CSS custom properties, no CSS-in-JS libs, no npm packages. Siblings may import each other relatively.
- `<Name>.d.ts` — the props interface. This is what gives the component its props contract; without it the component is still usable but carries no contract.
- `<Name>.prompt.md` — one sentence of "what & when", a small JSX usage example, then notable variants and props.

Plus one card HTML per directory showing key states and variants — *"dense and scannable, not a single default render."*

---

## Specimen cards

> *"Create foundation specimen cards (small HTML files). Target ~700×150px each (400px max) — err toward MORE small cards, not fewer dense ones. Split at the sub-concept level: separate cards for primary vs neutral vs semantic colors; display vs body vs mono type; spacing tokens vs a spacing-in-use example. A typical foundations set is 12–20+ cards. Skip titles and framing — just show the swatches/specimens/tokens directly with minimal decoration. Each card links `styles.css` so it picks up the real tokens."*

Each card's first line carries a tag: `<!-- @dsCard group="<Group>" viewport="700x<height>" subtitle="<one line>" name="<Card name>" -->`. Suggested groups: `Type`, `Colors`, `Spacing`, `Brand` — title-cased, consistent.

**[ours]** The `@dsCard` and `@startingPoint` tags index into Claude Design's own gallery and do nothing here — they are harmless, and kept so a system built here stays portable back into that tool. The cards themselves are useful regardless: they render the real tokens, so they are how you *see* whether the extraction was right.

---

## UI kits

> *"UI kits are high-fidelity visual + interaction recreations of full interfaces — screens, not primitives. They cut corners on functionality (not 'real production code') but are pixel-perfect, created by reading the original UI code if possible. UI kits compose the component primitives you authored above; don't re-implement Button inside a kit. A UI kit's `index.html` must look like a typical view of the product. These are recreations, not storybooks."*

Per product: explore the codebase and design context, build 3–5 core screens with interactive click-through, then iterate visually 1–2 times cross-referencing the source.

> *"You should get the visuals exactly right… Don't copy component implementations exactly; make simple mainly-cosmetic versions."*

> *"Cover every component family the source defines — coverage means the full enumerated inventory, not a hand-picked subset. Within a UI kit screen you may abbreviate repeated content (e.g. 3 rows standing in for 30 identical ones), but never skip a component family."*

> *"Do not invent new designs for UI kits. The job of the UI kit is to replicate the existing design, not create a new one. Copy the design, don't reinvent it. If you do not see it in the project, omit, or leave purposely blank with a disclaimer."*

---

## Guidance

> *"Run independently without stopping unless there's a crucial blocker."*

> *"When creating slides and UI kits, avoid cutting corners on iconography; instead, copy icon assets in! Do not create halfway representations of iconography using hand-rolled SVG, emoji, etc."*

> *"CRITICAL: Do not recreate UIs from screenshots alone unless you have no other choice! Use the codebase as a source of truth. Screenshots are much lossier than code."*

> *"The attached kit is the ground truth. When its values differ from the published conventions of a component library it resembles (shadcn, MUI, etc.), the kit wins. Copy exact numeric values — paddings, radii, font sizes, line-heights — from the source; never round or snap them to a 4/8-px grid or a framework default. If the kit says 5px, write 5px, not 4px."*

> *"Avoid these visual motifs unless you are sure you see them in the codebase or Figma: bluish-purple gradients, emoji cards, cards with rounded corners and colored left-border only."*

> *"Avoid reading SVGs — this is a waste of context! If you know their usage, just copy them and then reference them."*

> *"Stop if key resources are inaccessible: if a codebase was attached or mentioned, but you are unable to access it, you MUST stop and ask the user to re-attach it. NEVER go ahead spending tons of time making a design system if you cannot access all the resources the user gave you. This applies mid-run too: if reads start failing or rate-limiting partway through, stop and report exactly what you did and did not read — never infer or invent component names, structures, or values for content you could not read."*

**Logo safety, binding:**

> *"If the provided sources contain no logo, do not create one: render the brand name in plain type wherever a mark would go and note the absence in readme.md. Never draw, reconstruct, or approximate a company's real logo or brand mark from memory — even when the company seems identifiable from font names or sample content — and never rebrand the design system with a company identity the user didn't provide. NEVER draw your own SVGs or generate images; COPY icons programmatically if you can."*

---

## Output: the `{brand}-design` skill

The system becomes a skill so it is loadable anywhere. Write to `~/.agents/skills/{brand}-design/`, carrying the `readme.md` (both interrogations answered in full), the token files, and the copied assets.

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

## Output: `DESIGN.md`

**[ours]** Also write `DESIGN.md` at the target project root via `$impeccable document`, so the mechanical detector can enforce the system. Its frontmatter is what `design-system-color`, `design-system-font`, `design-system-font-size`, and `design-system-radius` read.

`colors`, `typography`, and `rounded` are **maps, not arrays** — array form silently fails to parse and every real colour then reports as undocumented. Full schema and worked example in [`brand-derivation.md`](../design/references/brand-derivation.md) § `DESIGN.md`.

Once it exists the project is **Tier 0**: every future surface inherits, and nothing re-derives.
