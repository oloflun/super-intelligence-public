---
name: design-verify
description: "Inspect and verify a rendered UI before handing it back. Use whenever design or frontend work needs checking in a real browser — screenshots, console errors, responsive breakpoints, layout verification, design-system adherence, recreation fidelity. Fires on 'check the page', 'does it look right', 'verify this', 'screenshot it', 'test the responsive', 'is anything broken', or as Step 5 of the design skill. Enforces batched inspection instead of one-round-trip-per-question."
user-invocable: true
---

# design-verify

Verification is a bounded, batched pass — not an open-ended hunt. This skill exists because the two default failure modes are opposite and both expensive: shipping a render nobody looked at, and burning twenty round trips looking at it one question at a time.

> Source: the inspection discipline in Anthropic's Claude Design tool docs, mapped onto the `mcp__Claude_Browser__*` tools. Quoted rules are theirs; the mapping is ours.

---

## The floor

Non-negotiable before any render is judged:

1. **Console and network read first.** A layout critique of a page that threw on load is wasted work.
2. **All four breakpoints swept** — 320 / 375 / 414 / 768. Not "it looks responsive."
3. **Checks batched.** One call answering many questions, never many calls answering one each.
4. **A screenshot you didn't read doesn't count.** Capturing is not inspecting.
5. **Two rounds maximum.** Inspect, fix everything in one batch, confirm once, stop.

---

## Tool mapping

| Need | Tool | Rule |
|---|---|---|
| Open the page | `preview_start` (dev server from `.claude/launch.json`, or a URL) | Start once per session; reuse the tab |
| Navigate | `navigate` | — |
| See it | `computer` `{action:"screenshot"}` | Never as a second call just to look at a page you already loaded |
| Read text and structure | `read_page` | **Prefer over screenshot** for verifying copy, hierarchy, and labels — it is the accessibility tree, so it also shows what a screen reader gets |
| Find an element | `find` | After `read_page`; returns `ref_N` |
| Console | `read_console_messages` | Before judging the render |
| Network | `read_network_requests` | Broken images, failed fonts, 404s |
| Probe computed state | `javascript_tool` | **Batch — see below** |
| Breakpoints | `resize_window` | 320 / 375 / 414 / 768, plus `colorScheme` for dark mode |
| Interact | `computer` `{left_click, hover, scroll, type, key}` | For hover and open states before capturing |
| Forms | `form_input` | — |

**Batching, verbatim from the source:** *"batch your checks — write ONE snippet that answers all questions and returns an object… N serial calls are N full round-trips."*

```js
({
  overflowX: document.documentElement.scrollWidth > window.innerWidth,
  htmlOverflow: getComputedStyle(document.documentElement).overflowX,
  bodyOverflow: getComputedStyle(document.body).overflowX,
  brokenImgs: [...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.src),
  bareFr: [...document.querySelectorAll('*')]
    .filter(e => /(^|\s)1fr/.test(getComputedStyle(e).gridTemplateColumns || '') && e.querySelector('img'))
    .map(e => e.className),
  smallTargets: [...document.querySelectorAll('a,button,[role=button],input,select')]
    .map(e => e.getBoundingClientRect())
    .filter(r => r.width && (r.width < 44 || r.height < 44)).length,
  fonts: [...new Set([...document.querySelectorAll('h1,h2,h3,p,button,a')]
    .map(e => getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g,'').trim()))],
  linkColor: getComputedStyle(document.querySelector('a') || document.body).color
})
```

**Multi-state, verbatim:** *"To capture SEVERAL states, pass multiple steps in ONE call — never a series of single-step calls."* Drive hover/open/error states with `computer` actions, then capture — grouped, not one round trip per state.

**One round trip, not two:** *"do not call show_html and then save_screenshot to look at the same page."* If you just navigated, screenshot in the same batch.

**The user's view.** `screenshot_user_view` / `eval_js_user_view` map to `tabs_context` + `tabs_select` + `read_page`. Use only for state your own view cannot reproduce, or when the user says "look at what I'm seeing."

---

## Safety

**Verbatim, and it is not optional:**

> *"Never clear or remove localStorage/sessionStorage/indexedDB entries — storage is shared with the user's live view and may hold their work."*

Read storage freely. Never `clear()`, never `removeItem` on anything you did not write this session.

`javascript_tool` is for **debugging and inspection only**. Do not implement UI changes through it — edit the source. A fix that exists only in the live DOM is a fix that vanishes on reload and was never real.

---

## The checklist

From the source's verifier: *"console errors, screenshot, layout, JS probing, design-system adherence, recreation fidelity."*

**Load** — console clean; no failed network requests; no broken images or fonts.
**Layout** — no horizontal scroll at any of the four widths; `overflow-x: clip` on `html` and `body`, never `hidden` (gate 34); nothing clipped or occluded; image-bearing grid tracks use `minmax(0, 1fr)` (gate 50); display headers wrap inside long words (gate 51); section heads collapse to one column (gate 52).
**Type** — real copy at every breakpoint, not lorem; nothing overflows; measure 65–75ch; no two-line clickable text (gate 49).
**States** — hover, focus-visible, active, disabled, loading, error, empty all render. Keyboard focus is visible and ordered.
**Targets** — nothing interactive below 44×44 at mobile (gate 62).
**Links** — `a` and `a:hover` are palette colours, not browser blue (gate 61).
**Design-system adherence** — every face and colour on the page traces to the locked tokens.
**Recreation fidelity** — when rebuilding from a reference, values match the source exactly. `5px` is not `4px` (gate 63).
**Motion** — one authored moment, not scattered effects; `prefers-reduced-motion` honoured.

Then run the mechanical pass once:

```bash
node "$HOME/.agents/skills/impeccable/scripts/detect.mjs" --json <changed files>
```

68 deterministic rules, including the four `design-system-*` contract checks. **Exit code stays 0 when findings exist — parse the JSON.**

---

## Bounded iteration

impeccable v4's ceiling applies:

> *"Build fully, inspect once with a batched round (desktop and mobile together), fix everything it shows in one batch, confirm with at most one more round, and stop polishing. Open-ended self-QA burns the user's money doing worse what the finish handoffs do better."*

After the second round the build thread's polishing is over. What remains ships through `impeccable-finish-reviewer` — a fresh context finds more, cheaper, than a third round here. Pass it the request, the artifact path, the screenshot paths, the direction contract, and any hook findings; **screenshots you fail to pass are checks it cannot run.**

---

## Reporting

State what you checked, at which widths, and what you found. Findings first, then what you fixed, then what remains and why.

Never report "verified" for a check you did not run. If the dev server would not start, or a breakpoint was not swept, say which and why — a silent gap in verification is worse than a known one, because it reads as coverage.
