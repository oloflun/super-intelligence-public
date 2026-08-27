# Copy gate

**Load whenever a user-facing string is written or changed.** Also available standalone as `design copy-audit <target>`.

Two stages, in order. Stage 1 decides *what the copy has to do*; stage 2 removes the tells that mark it as machine-written.

**Both rulesets apply in every language.** For Swedish — or any non-English copy — resolve the equivalent of each pattern rather than skipping it. The tells transfer: inflated significance, promotional adjectives, negative parallelism, forced triads, and manufactured drama are structural, not lexical. Do not treat any rule as English-only.

---

## Stage 1 · `copywriting`

Invoke `Skill(copywriting)`.

**Inputs, gathered first:** page purpose · audience · product/offer · traffic context (where the reader came from and what they already believe).

**Brand voice comes from the derived system.** The CONTENT FUNDAMENTALS section written during [`brand-derivation.md`](brand-derivation.md) — tone, casing, first vs second person, emoji, vibe, with real examples — is the input that makes this stage enforce *this brand's* voice instead of generically good copy. If that section does not exist yet, the gate still runs, but say that the voice is unconstrained.

**Structure.** Above the fold: headline, subheadline, CTA. Then social proof, problem, solution, how it works, objections, final CTA — as the page actually needs, not as a checklist to fill.

**Headline formulas** as starting points, not templates to ship: `{Achieve outcome} without {pain point}` · `The {category} for {audience}` · `Never {unpleasant event} again`.

**CTA formula:** `[Action Verb] + [What They Get] + [Qualifier if needed]`. "Start Free Trial" over "Sign Up".

**The five principles:**

1. Simple over complex — no jargon
2. Specific over vague — no buzzwords like "streamline"
3. Active over passive
4. Confident over qualified — remove hedging
5. Honest over sensational — fabricated claims create legal liability

**Prohibited:** exclamation points · weak CTAs ("Submit", "Learn More") · buried value propositions.

---

## Stage 2 · `humanizer`

Invoke `Skill(humanizer)` in embedded mode — final text only, no ceremony.

**The core constraint:** *"Preserve the information, not the shape."* Every fact survives; structure changes freely. **Never invent facts.** Match the author's voice unless a user-supplied sample overrides the style rules.

33 patterns in four families:

**Content** — inflated significance ("marking a pivotal moment") · undue notability emphasis · superficial "-ing" analyses · promotional language ("vibrant", "nestled") · vague attributions · formulaic "challenges" sections.

**Language** — overused AI vocabulary ("delve", "tapestry", "interplay") · copula avoidance ("serves as" for "is") · negative parallelism ("not only… but") · forced rule-of-three lists · synonym cycling · false ranges · passive voice · em and en dashes.

**Style** — em dashes banned outright (sample-override exception) · excessive boldface · inline-header lists · title-cased headings · emojis · curly quotes replaced with straight quotes.

**Communication** — chatbot artifacts ("I hope this helps") · knowledge-cutoff disclaimers · speculative gap-filling · sycophantic tone · filler phrases · excessive hedging · manufactured drama · aphorism formulas · theatrical rhetorical openers.

**One counterweight worth holding onto:** good human writing has personality. Sterile writing is equally suspect. The goal is copy that reads as written by someone, not copy sanded to neutrality.

---

## Interaction with the mechanical detector

Five detector rules catch the cheapest cases before this gate runs, and they fire on every UI edit:

`em-dash-overuse` · `marketing-buzzword` · `theater-slop-phrase` · `aphoristic-cadence` · `repeated-container-text`

Treat their findings as already-known. This gate covers what a regex cannot: structure, offer clarity, invented claims, voice.

## Interaction with honest copy

Discipline 2 in the front door and gate 46 bind here and are **not** overridable by stage 1's persuasion goals. If the user did not supply a metric, testimonial, logo, or case-study count, the copy does not get one. A stat-led layout with no stats becomes a different layout, a labelled placeholder, or an honest omission — never an invented number.

When stage 1 wants proof the product cannot supply, say so and offer the placeholder. *"+47% conversion"* invented to fill a proof bar is the single worst failure this gate can have.

---

## `copy-audit` — the standalone verb

Runs both stages over existing copy **without editing**.

1. Extract every user-facing string in scope — visible text, `alt`, `aria-label`, `placeholder`, `title`, button labels, error and empty states, meta title and description.
2. Run both stages against each.
3. Report as a table: **Before · After · Why**, one row per changed string, citing the stage and the specific rule.
4. Flag separately, never auto-fix: any string containing a **claim** — a metric, a customer count, a benchmark, a capability. Those need the user, not a rewrite.
5. Apply only on confirmation. On a live page this is a content change, and it is the user's call.

Scope note: run per surface, not per repo. A whole-codebase sweep produces a table nobody reads.
