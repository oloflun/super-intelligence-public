# Tier 3 · Invention

**Load only when the gate reached Tier 3: no `DESIGN.md`, no brand evidence, no reference — or the user explicitly said "wing it" / "you pick" / "no idea".**

> Source: Anthropic's Claude Design "Frontend design" skill, ported verbatim below. Blocks marked **[ours]** are this repo's framing.

**[ours] The scoping line is the thesis of this whole skill.** Anthropic's own design product scopes its aesthetic-invention guidance as applying *"when designing frontend/UI work that is NOT governed by an existing brand or design system."* Invention is the fallback, not the default. If you arrived here with brand evidence unread, go back to [`brand-derivation.md`](brand-derivation.md).

---

## Frontend design (verbatim)

Use this guidance when designing frontend/UI work that is NOT governed by an existing brand or design system. Create distinctive HTML with exceptional attention to aesthetic details and creative choices.

### Design Thinking

Before coding, understand the context and commit to a BOLD aesthetic direction:

- **Purpose**: What problem does this interface solve? Who uses it?
- **Tone**: Pick an extreme: brutally minimal, maximalist chaos, retro-futuristic, organic/natural, luxury/refined, playful/toy-like, editorial/magazine, brutalist/raw, art deco/geometric, soft/pastel, industrial/utilitarian, etc. Use these for inspiration but design one that is true to the aesthetic direction.
- **Differentiation**: What makes this UNFORGETTABLE? What's the one thing someone will remember?

Choose a clear conceptual direction and execute it with precision. Bold maximalism and refined minimalism both work — the key is intentionality, not intensity.

### Aesthetics Guidelines

- **Typography**: Choose fonts that are beautiful, unique, and interesting. Avoid generic fonts like Arial and Inter; opt for distinctive, characterful choices. Pair a distinctive display font with a refined body font.
- **Color & Theme**: Commit to a cohesive aesthetic. Use CSS variables for consistency. Dominant colors with sharp accents outperform timid, evenly-distributed palettes.
- **Motion**: Use animations for effects and micro-interactions. Prioritize CSS-only solutions for HTML. Focus on high-impact moments: one well-orchestrated page load with staggered reveals creates more delight than scattered micro-interactions.
- **Spatial Composition**: Unexpected layouts. Asymmetry. Overlap. Diagonal flow. Grid-breaking elements. Generous negative space OR controlled density.
- **Backgrounds & Visual Details**: Create atmosphere and depth rather than defaulting to solid colors. Gradient meshes, noise textures, geometric patterns, layered transparencies, dramatic shadows, decorative borders, grain overlays.

Vary between light and dark themes, different fonts, different aesthetics. NEVER converge on the same choices across generations.

Match implementation complexity to the aesthetic vision. Maximalist designs need elaborate animations and effects. Minimalist designs need restraint, precision, and careful attention to spacing and subtle details.

---

## [ours] Calibration — the clusters to check yourself against

Invention is where the model's defaults have the most room to leak. impeccable v4 names the three clusters AI interfaces converge on regardless of subject:

- Warm cream ground, high-contrast serif display, terracotta or signal-red accent.
- Near-black with one neon accent and glowing edges.
- Broadsheet-editorial hairlines, italic display serif, small tracked mono labels.

> *"All are legitimate when the brief calls for them; the brief always wins. Where the brief leaves the aesthetic free, landing in one of them means the self-check failed: if someone could guess your aesthetic from the category alone, or from category-plus-avoidance, rework until neither answer is obvious."*

**A fourth cluster, with concrete values.** `design-taste-frontend` v2 names the premium-consumer default that impeccable's prose only gestures at — and names the actual hex families, which makes it checkable rather than a vibe:

> For premium-consumer briefs (cookware, wellness, artisan, luxury, heritage craft, DTC home goods) the LLM default is **warm beige/cream + brass/clay/oxblood/ochre + espresso/ink text**. Banned as *default* reaches:
> - Backgrounds: `#f5f1ea` `#f7f5f1` `#fbf8f1` `#efeae0` `#ece6db` `#faf7f1` `#e8dfcb`
> - Accents: `#b08947` `#b6553a` `#9a2436` `#9c6e2a` `#bc7c3a` `#7d5621`
> - Text: `#1a1714` `#1a1814` `#1b1814`
>
> *"Every premium-consumer site you have ever shipped uses this exact palette. The brand becomes invisible."*

Rotate instead, and do not repeat the previous premium-consumer project's family: **Cold Luxury** (silver-grey + chrome + smoke) · **Forest** (deep green + bone + amber) · **Black and Tan** (true off-black + warm tan, no beige) · **Cobalt + Cream** · **Terracotta + Slate** (warm rust against cool grey, no brass) · **Olive + Brick + Paper** · **Pure monochrome + one saturated pop**.

Override: legitimate when the brand brief names those colours, or the identity is genuinely vintage/artisan/warm-craft *and* you can say why this palette fits this brand. Reaching for it because "this is a cookware brief" is the failure.

Mechanically, impeccable's `cream-palette` and `ai-color-palette` detector rules catch part of this. The hex list above is the specific form.

**Serif discipline.** v2 is blunter than the front door's face list: serif is *very discouraged as a default*, and *"creative brief = serif"* is called the single most-tested AI tell in production rounds. Default to sans display (Geist Display, ABC Diatype, Söhne Breit, Cabinet Grotesk Display, PP Neue Montreal) unless the brief names a serif or the family is genuinely editorial/luxury/publication/heritage *and* you can articulate the fit. `Fraunces` and `Instrument Serif` are banned outright as the two LLM-favourite display serifs. When emphasising a word inside a headline, use italic or bold **of the same family** — injecting a serif word into a sans headline is amateur.

Two altitudes, both must pass:

- **First-order** — could someone guess the palette from the category alone? (observability → dark blue; healthcare → white + teal; fintech → navy + gold; crypto → neon on black.) If yes, rework.
- **Second-order** — could they guess the aesthetic family from category-plus-anti-references? ("AI tool that isn't SaaS-cream → editorial-typographic.") This is the trap one tier deeper. If yes, rework.

Two more traps worth naming:

> *"Energy is not the enemy of trust: a brief's negative constraints (no gamification, no hype) rule out those devices, not exuberance, and adjectives describing the product's behavior (quiet support, calm coaching) do not dictate the surface's energy."*

> *"A brief-pinned world pins the world, not its softest rendition: the pinned world's full material range stays in play, and a rendition that matches what any model ships for that world failed the self-check at execution rather than selection."*

**Faces that mean you stopped looking.** Naming one of these requires a reason no other face could satisfy, and a subject association is never that reason: Fraunces, Playfair Display, Cormorant, Lora, Crimson, Newsreader, Syne, Space Grotesk, Space Mono, IBM Plex, Inter-as-display, DM Sans, DM Serif, Outfit, Plus Jakarta Sans, Instrument Sans.

## [ours] Name the world before you pick a token

Unnamed ambition becomes beige. Before any colour or type decision, write the direction as a name specific enough to be falsifiable — *"Klim Type Foundry orange drench"*, *"Bloomberg Terminal meets Swiss specimen"*, *"Liquid Death acid maximalism"*. Not *"modern and minimal"*, which is not a direction.

Then pick a **colour strategy** explicitly before picking colours: **Restrained** (tinted neutrals + one accent ≤10%), **Committed** (one saturated colour carries 30–60% of the surface), **Full palette** (3–4 named roles), or **Drenched** (the surface IS the colour). Marketing and showcase surfaces have permission for the bolder strategies; take them when the brief allows.

Dark or light is never a default. Write one sentence of physical scene — who uses this, where, under what ambient light, in what mood — and let it force the answer. *"Observability dashboard"* does not force an answer. *"SRE glancing at incident severity on a 27-inch monitor at 2am in a dim room"* does.

## [ours] Deeper structural invention

When the brief's *structure* is the open question and not just its surface:

- [`invention` via impeccable] — `$impeccable` `new-work` derives seven candidate directions from the audience's cultural world, ordered by resonance. Its concept-seed dice is **off** in this setup; use the derivation, choose deliberately, and record the choice.
- [`genres/`](genres/) — scopes the invented world into editorial / modern-minimal / atmospheric / playful.
- [`custom-theme.md`](custom-theme.md) and [`custom-craft.md`](custom-craft.md) — the made-to-measure OKLCH palette and free-font pairing protocol.
- [`macrostructures.md`](macrostructures.md) — 21 named page shapes. Read the index, load only your pick.
- [`themes/`](themes/) — the 20-theme catalog. **Only when the user asked you to just pick something.** Legitimate here and nowhere else.

## [ours] The demoted skills

`minimalist-ui`, `industrial-brutalist-ui`, and `high-end-visual-design` become available at this tier because there is no brand to overwrite. They are still fixed identities — choosing one means choosing Notion's greys, hazard red, or OLED black, so choose it *deliberately and by name*, not as a default. Everything above still applies: the category-reflex test does not exempt a skill's built-in palette.
