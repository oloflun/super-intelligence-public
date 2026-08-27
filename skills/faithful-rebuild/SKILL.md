---
name: faithful-rebuild
description: Use when rebuilding an existing live site 1:1 into a different rendering engine — a CMS, a static-site importer, another framework — where the standard is "indistinguishable from the original", not "close enough". Covers measuring the original as the spec, authoring against it, importing, and verifying by three independent instruments. Also use when a migration or port has to preserve exact spacing, typography, hover behaviour and imagery. Not for greenfield design or for redesigns where the look is allowed to change.
version: 1.0.0
---

# Faithful rebuild

Rebuilding a live site into another engine, where **parity is the acceptance
test**. The original is the specification; the source code is not.

## The one thing to internalise

**Numeric checks are blind to what is absent, unpainted, or non-functional.**

Across a six-page rebuild, every serious defect passed a geometry diff that
reported "0 findings":

| Defect | Numeric diff said | Caught by |
|---|---|---|
| Hamburger button imported completely empty | clean | screenshot |
| Mobile menu could not open at all | clean | driving the interaction |
| An entire page missing from the server (404) | clean until the height diff went -1071 | luck, one page later |
| 30 of 56 product images loaded but never painted | clean | screenshot |
| A large product photo behind a page title that should have none | clean | screenshot |
| Carousel arrows published with no icon | clean | screenshot |
| Card description permanently expanded | clean | screenshot |

Geometry diffs catch what MOVED. They cannot see an element that is absent from
one side, an image that is loaded but undecoded, or a button that renders
perfectly and does nothing. Budget for pixels and driven interactions as
first-class checks, not as a final formality.

## Method

### 1. Measure the original — it is the spec

Capture with ONE instrument, then reuse that exact instrument on the rebuild so
the two sides are directly comparable:

- Full-page screenshots at every breakpoint you intend to support.
- Per-element computed styles, collapsed by `tag + class` signature.
- `scrollHeight` per page per breakpoint — the cheapest, highest-signal check
  you have. An exact match across five widths is strong evidence.
- The states a static capture cannot show: hover, open menus, mid-transition.

**Measure, do not infer from source.** A utility class that is never generated
renders as nothing. On the site this skill came from, 118 elements carried
`font-afacad` and only `h1`/`h2` actually rendered it — a raw CSS rule did the
work while the utility was dead. Reproducing the *intent* would have broken
parity on 117 elements. Twice during the rebuild, "fixing" that dead utility
made pills and headings visibly the wrong width.

### 2. Reproduce as-rendered, including what looks like a bug

Parity is the standard; improvements are a separate, later decision. Expect to
find and deliberately keep things like:
- A gap utility that compiles to a margin on an inline element, where it does nothing.
- Two competing colour classes where source order silently picks the loser.
- A nav label uppercased in JS on some items and by CSS on others.
- A link to a route that does not exist.

Write each one down as you reproduce it, with the measurement that proves it.
Otherwise the next person "fixes" it.

### 3. Author static, import, then bind

If the target has a static-site importer, use it: you get real pages, editable
style rules, media and fonts in one pass, and the whole thing is re-runnable.
Author semantic classes with the measured values — not the original's utility
soup, which imports as hundreds of unusable bare classes.

**Then bind the data.** A pixel-perfect grid of hardcoded cards is a copy, not a
CMS. Until the grids read from the database, adding a product changes nothing.
Say so plainly rather than counting those pages as done.

### 4. Verify with three independent instruments

One is not enough, and they fail differently:

1. **Geometry + computed style** — catches what moved.
2. **Visible copy, per instance** — catches text the geometry diff hides.
   Signature collapsing keeps only the first of N identical elements, so five
   footer links become one entry and four copy errors vanish.
3. **Driven interactions** — hover, menus, carousels. Assert that the ORIGINAL
   actually changes before comparing; otherwise a probe that never fires reads
   as a pass on both sides.
4. **Pixels, read into context.** Non-negotiable. This is what catches the rest.

### 5. Make the loop one command and re-runnable

Reset → author → assert the plan → import → post-import fixes → publish →
capture → diff. Every iteration goes through the same path. Anything you do by
hand once, you will forget the second time.

## Traps that generalise

These came from one specific importer, but the *shapes* recur in any port.

**Leaf modules discard children.** A `<button>` that maps to a leaf module keeps
its `textContent` and drops every child element — icons vanish silently. Hit
three separate times. Author such controls as containers and convert them after
import.

**Tree-shaking removes rules whose classes never appear in the markup.** A state
class added only by JS at runtime means the rule is stripped at publish, and the
feature is dead. Invert the state: ship `is-collapsed` in the HTML and have JS
remove it.

**Derived rule names collide.** If the importer names a rule from its selector's
leading class, `.site ::selection` registers as `site` and overwrites `.site`.
Same for a grouped selector followed by a single-class override. Assert after
every import that each authored `.foo` still exists as a rule.

**Breakpoint boundaries must be exclusive.** `min-width: 768` applies AT 768, so
a `max-width: 768px` breakpoint overrides it there and collapses one layout into
another. Use `767.98px`.

**Image defaults differ.** `loading="lazy"` and `decoding="async"` are sensible
defaults and neither may match the original. `decoding="async"` in particular
leaves images loaded but unpainted — `complete === true`, nothing on screen.

**Body-level classes are often dropped.** Put the page wrapper on a real element.

**A stray `*/` inside a CSS comment** closes it early and silently eats the next
rule. Cost two rules before it was found; the rule count still added up.

**Store/server sync can silently drop a row.** An import reported 7 pages, the
client held 7, the server had 6, and nothing errored. Always diff the client's
set against the server's after a write.

## Verification scripts to build

Keep them small, and make each one refuse to pass vacuously:

- `capture.mjs` — same instrument for both sides.
- `diff-geometry.mjs` — key elements by `tag + text`, skip untexted and
  zero-box elements, and report scrollHeight per breakpoint first.
- `diff-text.mjs` — compare joined visible copy, not a node list; a single
  insertion desyncs a node-by-node walk and hides everything after it.
- `check-interactions.mjs` — drive each state, `scrollIntoView` before hovering
  (viewport coordinates miss anything below the fold), and **throw if the
  original does not change**.
- `preview-plan.mjs` — assert every authored class survives the import BEFORE
  committing anything.

## Reporting

State what is verified and by which instrument, and what is not. "Visually
verified" means pixels were read. If a probe was written but its results are
untrustworthy, say the states are **unverified**, not that they differ — a
broken probe reporting differences is worse than no probe, because it sends the
next person chasing ghosts.
