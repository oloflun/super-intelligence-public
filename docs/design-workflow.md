# The Design Workflow — Brand-Derivation Gate + Hook-Enforced Protocol

**Status:** proven in production · **v1 since:** 2026-07-09 · **v2 since:** 2026-07-27 · **Enforced by:** CARL `DESIGN` domain (always-on, prompt-level) + a PreToolUse/PostToolUse hook chain (edit-level, project-side)

## Why this exists

**v1 incident.** An agent session claimed design work was "visually verified" when the reference material had **never actually been opened** — iteration happened against imagination and was verified only against itself. The user caught it; trust was damaged. v1 made that failure structurally non-repeatable: verification against real reference material became a hard gate, not a habit.

**v2 incident.** v1 held at the top of a session and drifted after — CARL rules are injected once per prompt, but design decisions happen once per file write, and a build turn can be sixty tool calls long. Worse, three specialist skills in the design stack (`minimalist-ui`, `industrial-brutalist-ui`, `high-end-visual-design`) each hardcode a complete palette; routing to them as direction-setters overwrote whatever brand identity the project actually had, regardless of what was asked for. v2 fixes both: enforcement moved from prompt boundaries to file-write boundaries, and a brand-derivation gate now runs before any specialist gets to pick a colour.

## The rule

> **Brand derives direction. Skills supply craft. Themes are the last resort.**

## The gate (Tier 0–3)

First tier with evidence wins; lower tiers never run.

| Tier | Condition | Action |
|---|---|---|
| **0 · Locked** | `DESIGN.md` exists at the project root | Inherit it. Never re-derive. |
| **1 · Derive** | Logo, brand hex in code, a deployed site, tailwind config colours | Derive the language from that evidence. |
| **2 · Reference** | A URL or screenshot was supplied | Study it; borrow principle, never pixel. |
| **3 · Invent** | Genuinely nothing to derive from, or the user says "wing it" | Invent a named world. Themed skills only fire here. |

Full procedure: `skills/design/SKILL.md` and its `references/` — `brand-derivation.md` (Tier 1), `invention.md` (Tier 3), `gates.md` (the numbered rule set), `component-routing.md` (which craft skill fires for which component). `references/INDEX.md` is the catalog router over the whole reference shelf (added 2026-08-19).

Shared impeccable modules live in `skills/impeccable/scripts/lib/` — the top-level copies of `is-generated.mjs`, `design-parser.mjs`, `impeccable-paths.mjs` were consolidated away (2026-08-19, ICM migration). Import from `./lib/`, never from a top-level duplicate.

## The 4 verification steps (unchanged from v1, still CARL DESIGN rules)

1. **Before any UI edit:** invoke `Skill(design)`. It derives direction from the gate above before writing any token.
2. **During implementation:** additionally load the relevant framework-craft skills for the stack in use (e.g. `vercel-react-best-practices`, `vercel-react-view-transitions` for a React app) — see `component-routing.md` for the full signal-to-skill table, which routes per component rather than per project.
3. **After implementation:** run an interaction/animation audit with `emil-design-eng`. Every interaction must be smooth (eased, ~60fps, `prefers-reduced-motion` honored).
4. **Nothing is "done" without a real screenshot**, taken via a live browser preview and, whenever the project has reference material, compared side-by-side against it. Never claim visual verification without having actually opened the render. Procedure: `Skill(design-verify)`.

## What's new in v2: the hook chain

Six hooks move steps 1–4 from something the agent has to remember into something the harness enforces mechanically, on every file write:

| Hook | Event | Job |
|---|---|---|
| `design-intent.py` | `UserPromptSubmit` | Detects design intent, injects the active tier and this project's locked tokens (if any) |
| `design-gate.py` | `PreToolUse` (Write/Edit/MultiEdit) | **Denies** a write that violates the locked `DESIGN.md` contract — off-palette colour, undeclared font, a hardcoded hex from one of the three palette-locking specialist skills |
| `design-verify-gate.py` | `PreToolUse` (browser tools) | Injects the inspection discipline before the first look — batch probes, sweep 320/375/414/768, never trust an unread screenshot |
| `design-route.py` | `PostToolUse` (Write/Edit/MultiEdit) | Names the right craft skill for what was just written, per `component-routing.md` |
| `design-telemetry.py` | `PostToolUse` (Skill) | Attributes every skill invocation to the component it was called for |
| `design-stop.py` | `Stop` | Runs the deep detector pass and renders the session report |

Package copies live in `hooks/`; `install.mjs` deploys them to `~/.claude/hooks/` and wires them into `~/.claude/settings.json`, alongside the existing `carl-hook.py`. `upgrade.mjs` syncs the files and merges the hook registrations additively into an existing installation, without disturbing hooks the user already has.

Kill switch: `DESIGN_HOOKS_DISABLED=1`. The contract gate ships advisory by default; `DESIGN_GATE_BLOCKING=1` promotes it to a hard denial once a clean run is on record for a project.

## The session report — how you know it actually worked

Every session that touches UI files writes `.impeccable/design-session.jsonl` and, at `Stop`, a report to `.impeccable/design-report-<date>.md`. The number that matters is the **route-vs-invocation gap**: how often `design-route.py` named a skill and the agent never actually loaded it. That is the direct, mechanical measurement of the v1/v2 failure — a build that looks right but ships a gap-heavy report has not passed; it got lucky, and now there is a record of that instead of just a claim.

## The proof-gallery pattern

Where reference material exists for a project, verification artifacts should be saved, not just claimed:

- A headless capture script drives the app through every page/state and writes PNGs to a committed proof-gallery directory.
- The gallery is committed with the design change — reviewable proof in git history, not a claim in chat.
- For interactive states (hover, focus, expansion), expose a dev-only hook the capture script can call to drive state before capturing.

This is a technique, not a requirement — wire it when a project has real reference material worth diffing against; `Skill(design-verify)` covers the minimum bar (console clean, four breakpoints swept, a screenshot actually opened) for projects that don't.

## How enforcement works, end to end

- **CARL layer** (prompt-level, always-on): rules live in the `DESIGN` domain of `~/.carl/carl.json` (package copy: `carl/carl.json`), injected by `carl-hook.py` on every matching prompt. Decision log `design-001` records the v1 incident and its lesson; `design-002` records the v2 rebuild.
- **Hook layer** (edit-level, per-session): the six hooks above, wired via `~/.claude/settings.json`.
- Both layers are shared, generic config shipped to every installer user — **never put project-identifying content (a project name, an internal codename, a specific port, a path unique to one repo) into either layer.** A new GLOBAL CARL rule (added alongside `design-002`) requires asking the user before creating a new domain or adding project-scoped content to an always-on one, specifically because this workflow's own history includes a domain that leaked one project's specifics into the shared config before that rule existed.

## Adapting to a new project

1. If the project has a real identity — a logo, existing tokens, a deployed site — the gate finds it at Tier 1 automatically; nothing to configure.
2. Put reference material (real images, not vibes) wherever the project keeps such things and reference the path when asking for verification.
3. Ensure a browser-reachable preview exists (mock the backend if the app is native).
4. Wire a proof-gallery script if the project is design-heavy enough to warrant one; otherwise `Skill(design-verify)`'s standard checklist is enough.
5. Project-specific tuning belongs in that project's own `.carl/` scope or `DESIGN.md`, never in the shared package config.
