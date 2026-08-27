# Process · how to run a design task

**Load for any new surface.** Carries the working method and the question-calibration table.

> Source: Anthropic's Claude Design "Hi-fi design" skill, plus its top-level workflow and question guidance. Ported at full fidelity. Blocks marked **[ours]** are this repo's framing.

---

## The five steps

> *"Follow this general design process (use the todo list to remember): (1) ask questions, (2) find existing UI kits and collect design context — copy ALL relevant components and read ALL relevant examples; ask the user if you can't find them, (3) start your file with assumptions + context + design reasoning (as if you are a junior designer and the user is your manager), with placeholders for the designs, and show it to the user early, (4) build out the designs and show the user again ASAP; append some next steps, (5) use your tools to check, verify and iterate on the design."*

**[ours]** Step 3 is the one that gets skipped and shouldn't. Opening the artifact with your assumptions, the context you found, and your reasoning — written as a junior designer writing to their manager — is what lets the user redirect *before* you've built the wrong thing. It costs one short block and saves a rebuild. Show it early, with placeholders in place of the designs.

## The context mandate

> *"Good hi-fi designs do not start from scratch — they are rooted in existing design context. Ask the user to Import their codebase, or find a suitable UI kit / design resources, or ask for screenshots of existing UI. You MUST spend time trying to acquire design context, including components. If you cannot find them, ask the user for them. Mocking a full product from scratch is a LAST RESORT and will lead to poor design. If stuck, try listing design assets and ls'ing design system files — be proactive! Some designs may need multiple design systems — get them all."*

**[ours]** This is the gate order stated as a work habit. "Last resort" is Tier 3. "Get them all" matters on multi-brand or multi-product repos — one system found is not evidence the others don't exist.

## Placeholders beat bad guesses

> *"If you do not have an icon, asset or component, draw a placeholder: in hi-fi design, a placeholder is better than a bad attempt at the real thing."*

---

## When to ask, and how much

> *"In most cases, you should use the questions tool to ask questions at the start of a project."*

The calibration table — the valuable part, because it says when **not** to ask:

| Request | Ask? |
|---|---|
| "make a deck for the attached PRD" | Yes — audience, tone, length |
| "make a deck with this PRD for Eng All Hands, 10 minutes" | No — enough info was provided |
| "turn this screenshot into an interactive prototype" | Only if intended behavior is unclear from the images |
| "make 6 slides on the history of butter" | Yes — vague |
| "prototype an onboarding for my food delivery app" | **Ask a TON** |
| "recreate the composer UI from this codebase" | No |

> *"Use the questions tool when starting something new or the ask is ambiguous — one round of focused questions is usually right. Skip it for small tweaks, follow-ups, or when the user gave you everything you need."*

Asking well:

> *"Confirm the starting point and product context (UI kit, design system, codebase) with a QUESTION — if there is none, tell the user to attach one; starting without context always leads to bad design."*
>
> *"Ask whether they'd like variations, for which aspects, and what those variations should explore (novel UX, visuals, animations, copy) — and whether they want divergent visuals, interactions, or ideas."*
>
> *"Ask how much they care about flows, copy, and visuals; make variations concrete there, plus at least 4 problem-specific questions."*
>
> *"Ask at least 10 questions, maybe more."*

**[ours]** In Claude Code this is `AskUserQuestion`, which caps at 4 questions per call. For a genuinely open brief, use more than one round rather than cutting the interrogation down to four — but never open with a round the brief already answers. The pre-flight scan runs *first*: questions the codebase can answer are not questions.

**[ours]** impeccable v4's version of the same rule, which scopes it by surface mode: for a persuade surface clarify who must act, what they should believe, and what real proof can earn that belief; for an operate surface the task, information, important states, frequency, and constraints; for a read surface the reader's question, source material, structure, and wayfinding; for an experience surface what leads, how exploration unfolds, and which interaction matters. Across all four: *"ask what success looks like, what must remain untouched, and what would make a polished result feel wrong. Do not ask for CSS values or canned aesthetic lanes."*

---

## The design read, before anything else

> Source: `design-taste-frontend` (Leonxlnx/taste-skill) v2, Section 0.

Before any code, state one line: **"Reading this as: \<page kind> for \<audience>, with a \<vibe> language, leaning toward \<design system or aesthetic family>."**

Read six signals to get there: page kind · vibe words the user actually used · reference signals (URLs, screenshots, named competitors) · **audience** (the audience picks the aesthetic, not your taste) · brand assets that already exist · quiet constraints (accessibility-first, public-sector, regulated, trust-first commerce, kids' products — these *override* aesthetic preference).

If the brief is ambiguous, ask **exactly one** question, never a multi-question dump, and only when the read genuinely diverges: *"Should this feel closer to Linear-clean or Awwwards-experimental?"* If you can infer confidently, do not ask — declare the read and proceed.

**[ours]** This sits alongside the tier declaration, not instead of it. The tier says *where direction comes from*; the design read says *what the surface is and who it is for*. Both go in the opening block: *"Tier 1, deriving from the Snajp wordmark. Reading this as: B2B SaaS landing for Swedish SMB buyers, Nordic-SaaS language, leaning Tailwind + a sans display."*

## Intensity dials

v2 sets three dials after the read, and gates layout, motion, and density decisions on them:

- **`DESIGN_VARIANCE`** 1 = perfect symmetry → 10 = artsy chaos
- **`MOTION_INTENSITY`** 1 = static → 10 = cinematic
- **`VISUAL_DENSITY`** 1 = art gallery → 10 = packed cockpit

Baseline `8 / 6 / 4`. Inference: minimalist/Linear-style → `5-6 / 3-4 / 2-3` · premium consumer → `7-8 / 5-7 / 3-4` · agency/Awwwards → `9-10 / 8-10 / 3-4` · trust-first/public-sector/regulated → `3-4 / 2-3 / 4-5` · redesign-preserve → match existing, motion +1 · redesign-overhaul → variance +2, motion +2.

**[ours]** Orthogonal to the gate: the tier decides *where the palette and type come from*, the dials decide *how loud the execution is*. A Tier-0 locked brand can still be built at variance 9 or variance 4. Full table in `design-taste-frontend`'s Sections 1.A–1.B.

## When an official design system is the authority

> Source: v2 Section 2. **[ours]** A capability this system otherwise lacks — the gate assumes direction is derived or invented, but some domains have an official system that outranks both.

| Brief reads as | Reach for |
|---|---|
| Microsoft / enterprise SaaS / dashboards | `@fluentui/react-components` |
| Google-ish, Material-flavoured product | `@material/web` + Material 3 tokens |
| IBM-style B2B / enterprise analytics | `@carbon/react` |
| Shopify app surfaces | Polaris (required for admin UI) |
| Atlassian / Jira-style product | `@atlaskit/*` |
| GitHub-style devtool or community page | `@primer/css` / `@primer/react-brand` |
| Public-sector UK service | `govuk-frontend` (regulatorily expected) |
| US public-sector / trust-first | `uswds` |
| Modern accessible React foundation | `@radix-ui/themes` |
| Modern SaaS where you own the components | shadcn/ui — **never ship in default state** |
| Tailwind-based SaaS / indie marketing | Tailwind v4 utilities |

**Honesty rule:** if the brief reads as one of these, install and use the **official** package. Do not recreate its CSS by hand, and do not import its tokens then override 90% of them. **One system per project** — never Fluent mixed with Carbon, never shadcn inside Material.

When the brief names an *aesthetic* rather than a system (glassmorphism, bento, brutalism, editorial, dark-tech, aurora, kinetic type), there is no official package — build with native CSS plus a maintained component library, and be honest in comments about what is borrowed inspiration. Specifically: **Apple Liquid Glass has no official web package**; any web version is a `backdrop-filter` approximation and must be labelled as one.

**Out of scope for the marketing-page rules entirely:** dashboards and dense product UI (use the systems above), data tables (TanStack, AG Grid), multi-step forms, code editors (Monaco, CodeMirror), native mobile (Apple HIG, Material), realtime collaborative UIs. If the brief is one of those, say so, point at the right tool, and apply only the parts of this system that genuinely fit.

## Options and variations

> *"Give options: try to give 3+ variations across several dimensions. Mix by-the-book designs that match existing patterns with new and novel interactions, including interesting layouts, metaphors, and visual styles. Have some options that use color or advanced CSS; some with iconography and some without. Start your variations basic and get more advanced and creative as you go! Try remixing the brand assets and visual DNA in interesting ways — play with scale, fills, texture, visual rhythm, layering, novel layouts, type treatments. The goal is not the perfect option; it's exploring atomic variations the user can mix and match."*

> *"CSS, HTML, JS and SVG are amazing. Users often don't know what they can do. Surprise the user."*

Presentation format → [`options.md`](options.md). Low-fidelity exploration first → [`wireframe.md`](wireframe.md).

---

## Working method

> *"Understand what the user needs, explore the resources they provided (design systems, UI kits, files, links) before building, and keep a todo list for multi-step work."*

> *"Batch tool calls aggressively: when exploring, issue ALL the read / list / grep calls you need in ONE assistant turn, never one at a time. When editing, emit ALL file writes and edits as parallel tool calls in one assistant turn — do not write-then-check-then-write."*

> *"End with an extremely brief summary — caveats and next steps only."*

### Working economically

> *"Your tokens are the user's time and money — spend them on the design, not ceremony."*
>
> - *"Write compact code: comments only where genuinely non-obvious; no banner comments, no narrating markup, no blank line between every block."*
> - *"Prefer targeted edits over rewrites, and never re-print file contents in chat or re-write a file unchanged."*
> - *"Within a turn, read a file at most once — after your own write or edit, your version is the truth; don't re-read to check your own work."* (Files can change between turns, so re-reading at the start of a new turn is fine.)
> - *"Plan each file before emitting it so it lands right in one pass instead of write-then-revise."*

### Commit to your first reasonable plan

> *"When you've identified a reasonable approach, execute it. Do not re-deliberate between near-equivalent options ('should I use X or Y?'), second-guess a plan you've already justified, or re-read files you've already understood. Your first reasonable choice is almost always good enough — dithering between close alternatives costs iterations without improving the result. Decide, act, move on."*

**[ours]** This does not license skipping the gate. Deciding fast is about *near-equivalent* choices — which of two good spacing rhythms, which of two workable layouts. It is not about whether to derive from the brand.

---

## Verification and finishing

Verification is its own skill — invoke `Skill(design-verify)`.

**[ours]** impeccable v4's bound on iteration, which prevents the open-ended self-QA loop:

> *"Build fully, inspect once with a batched round (desktop and mobile together), fix everything it shows in one batch, confirm with at most one more round, and stop polishing. Open-ended self-QA burns the user's money doing worse what the finish handoffs do better."*

Two rounds is the ceiling. What remains after that ships through the finish handoff — `impeccable-finish-reviewer` in a fresh context — not through more rounds here.
