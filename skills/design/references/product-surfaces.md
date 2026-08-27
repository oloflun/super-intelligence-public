# Product surfaces

**Load when the target is a dashboard, admin panel, settings screen, data table, form flow, editor, or any authenticated in-app surface.**

These live inside corporate sites constantly — a marketing site with a customer portal, a pricing page that leads into a dashboard demo, an admin area behind a login. They are **not out of scope**; they are a **different mode of the same system**.

---

## The one rule that changes, and the one that doesn't

**Does not change: the gate.** Product surfaces still derive their colour, type, and radius from the brand. A Tier-0 locked project's dashboard uses the same tokens as its landing page. Brand identity transfers completely.

**Does change: what "good" means.** Marketing taste does *not* transfer. Big display type, generous whitespace, expressive scroll choreography, and surprise are virtues on a landing page and defects in a dashboard.

> *"Product UI's failure mode isn't flatness, it's strangeness without purpose: over-decorated buttons, mismatched form controls, gratuitous motion, display fonts where labels should be, invented affordances for standard tasks. The bar is earned familiarity. The tool should disappear into the task."*
> — `impeccable` `reference/operate.md`

Same brand, different job. A visitor on a landing page is deciding; a user on a dashboard is working.

---

## The workflow

### Step 1 · Declare the mode

Say it out loud alongside the tier, exactly as on a marketing surface:

> *"Tier 0 locked. **Operate mode** — settings panel, user is mid-task. Density and familiarity over expression."*

impeccable v4's four modes: **Persuade** (marketing, the visitor decides) · **Operate** (app UI, the visitor completes a task) · **Read** (docs, the visitor understands) · **Experience** (portfolio, the artifact leads). Pick from the *surface*, not the product — a dev tool's landing page is still Persuade; a fashion house's docs are still Read.

### Step 2 · Load the register

`impeccable`'s [`reference/operate.md`](../../impeccable/reference/operate.md) is the taste layer. It is short and it is the authority for this mode. The essentials:

- **Typography** — one family is usually right; no display/body pairing. **Fixed rem scale, not fluid** (a clamp-sized `h1` that shrinks in a sidebar looks worse, not better). Tighter ratio, 1.125–1.2. Prose still 65–75ch; tables can run 120ch+.
- **Colour** — Restrained is the floor. Accent is for primary actions, current selection, and state indicators **only, never decoration**. Add a second neutral layer for sidebars, toolbars, and panels.
- **Motion** — 150–250ms. Motion conveys **state**, not decoration. **No orchestrated page-load sequences** — users load into a task, they don't want to watch it arrive.
- **Layout** — responsive behaviour is *structural* (collapse the sidebar, make the table responsive), not fluid typography.

### Step 3 · Route the craft

| Building | Invoke | Note |
|---|---|---|
| Any primitive, dashboard block, form, table, command palette | `shadcn-ui` | Never ship in default state — theme it to the locked tokens |
| Chart, metric tile, analytics panel | `dataviz` | Categorical palette derives from the locked accent, never `dataviz` placeholders |
| Table sorting/empty/loading, nav pattern, chart UX | `ui-ux-pro-max` | Its 99 UX guidelines are the product-UI rulebook. **Its 161 palettes are a Tier-3 menu — never a source here** |
| Form validation, error recovery, i18n, edge cases | `impeccable harden` | |
| Empty states, first-run, activation | `impeccable onboard` | |
| Interaction feel, easing, gesture | `emil-design-eng` | **Retime to product cadence** — its marketing-grade choreography is wrong here |
| Route/state transitions | `vercel-react-view-transitions` | State change only, not decoration |
| Framework correctness | `next-best-practices` · `vercel-react-best-practices` · `vercel-composition-patterns` | |
| Interface compliance review | `web-design-guidelines` | Vercel interface guidelines |

**Do not load** on a product surface: `hero-enrichment.md`, `macrostructures.md`, `structure.md`'s six-axis fingerprint, `production-tells.md`. They are page-composition and marketing-decoration references. Gates 66–88 assume a marketing surface — a version label in a *product* header is legitimate build metadata, not a tell.

### Step 4 · The eight states, non-negotiable

Every interactive component ships: **default · hover · focus-visible · active · disabled · loading · error · success**. This is already the component-branch rule in the front door; on product surfaces it is stricter because state *is* the interface.

Plus, from `operate.md`:
- **Skeleton states for loading**, not spinners in the middle of content.
- **Empty states that teach the interface**, not "nothing here."
- **Consistent affordances across the surface.** Same button shape, same form-control vocabulary, same icon style. *"If the save button looks different in two places, one is wrong."*
- **Overlays escape their container.** An absolutely-positioned dropdown inside `overflow: hidden`/`auto` gets clipped — use `<dialog>`, the popover API, `position: fixed`, or a portal.

### Step 5 · Verify

`Skill(design-verify)` as normal, plus the product-specific checks: every state rendered (not just the happy path), keyboard navigation and focus order, tables at real row counts rather than three demo rows, empty and error states actually reachable.

---

## Product constraints — the slop list for this mode

From `operate.md`, these are to Operate mode what gates 66–88 are to marketing:

- Decorative motion that doesn't convey state
- Inconsistent component vocabulary across screens
- Display fonts in UI labels, buttons, or data
- Reinventing standard affordances for flavour — custom scrollbars, weird form controls, non-standard modals
- Heavy colour or full-saturation accents on inactive states
- **Modal as first thought.** *"Modals are usually laziness. Exhaust inline and progressive alternatives first."*

## Product permissions — what this mode may do that marketing may not

- System fonts and familiar sans defaults
- Standard navigation: top bar + side nav, breadcrumbs, tabs, command palettes
- **Density.** Many rows, many labels, dense information where users need it
- **Consistency over surprise.** The same vocabulary screen to screen is a virtue; delight is saved for moments, not pages

---

## When to hand off entirely

Some surfaces have an official system that outranks both deriving and inventing. Per [`process.md`](process.md) § official design systems and taste-skill v2 §13, hand off rather than hand-rolling:

| Surface | Reach for |
|---|---|
| Enterprise dashboard in a Microsoft/Google/IBM/Atlassian/Shopify context | Fluent · Material 3 · Carbon · Atlaskit · Polaris |
| Serious data grid — virtualization, pinning, grouping, 10k+ rows | TanStack Table or AG Grid, themed to the locked tokens |
| Code editor | Monaco or CodeMirror with official skinning |
| Native mobile | Apple HIG / Material directly |
| Realtime collaborative UI (presence, cursors, OT) | Different problem class — say so |

Handing off is not a failure. Applying landing-page taste to a data grid is.

**Note the difference from the old wording:** these surfaces were previously listed as *out of scope for the router entirely*. They are not. The router still owns the **tokens, the mode declaration, the state discipline, and the verification** — it just doesn't hand-roll the grid engine.

---

## Mixed surfaces

A corporate site with a portal is **two modes in one project, one token set**. Handle it explicitly:

- The marketing pages run Persuade with the full marketing reference stack.
- The portal runs Operate with this file.
- **Both inherit the same `DESIGN.md`.** The dashboard is not a second identity — that is gate 65.
- The seam between them (a "Log in" CTA leading into the app) should feel continuous in brand and deliberate in mode shift. Same colours and type; different density, motion, and affordances.

Declare the switch when crossing it: *"Leaving Persuade, entering Operate for `/app`. Same tokens, product cadence from here."*
