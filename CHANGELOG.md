# Changelog

## 0.8.0 — 2026-08-27

### Added: statusintegritet, botten-upp-malbilder, matbar retrieval

Tvadelat skydd mot att ett projekts parkerade/aktiva status glider isar mellan
dokumentation och exekvering (project-d-lackan 2026-08-25/26), botten-upp
GOALS.md for alla aktiva projekt, och ett matverktyg for om agenten faktiskt
hittar det som redan finns i valvet.

**Nya skript** (`~/.agents/scripts/`, INTE ännu speglade i `scripts/` -- se
oppna tradar i sessionsloggen 2026-08-27):
- `project-consistency.py` -- jamfor ett projekts status over hubb, syskonfiler,
  dispatchkonfiguration, bead-grafen och alla stallen dar oppet arbete listas
- `build-patterns-index.py` -- bygger `~/.agents/patterns-index.json` ur BLOCKS.md,
  strategies.md, GOALS.md och skill-beskrivningar; sokhooken slar upp i den
- `retrieval-eval.py` -- 30-fragors evalsvit i tre klasser (fakta/lage/koppling),
  matt fore/efter i `~/.agents/retrieval-eval-{baseline-,}2026-08-2{6,7}*.json`

**Ny lokal vakt** (`~/.claude/watch/`, medvetet UTANFOR OneDrive):
- `file-integrity-watch.py` -- upptacker en bevakad fil som tyst ersatts med en
  aldre version (generationshash + mtime-bakat), sparar 14 dagars ogonblicksbilder,
  kan `--restore`

**Andrade skript:** `wake-gate.py` (tva nya kontroller + notisdedup mot
budgetsvalt), `assistant-layer-health.py` (check_hubs katalogskannar i stallet
for hardkodad lista), `generate-portfolio.py` (explicit varning vid saknad
status), `render-status.py` (park-medveten), `update-global-status.py`
(vagrar skriva Open-rad som namner parkerat projekt), `auto-conclude-sweeper.py`
(svepte tidigare ENDAST Telegram-sessioner -- 27 registrerade, noll matchade;
nu alla sessioner), `qmdv.py` + `brief-context.py` (kodning, ordval, stamning).

**Malbildssystem:** `wiki/projects/_templates/goals-template.md` + `GOALS.md`
i alla 12 aktiva projektrepon, byggda botten-upp ur kod/loggar/beads, inte
avskrivna fran de glesa hubbarna.

**Sprakkontrakt:** `~/.agents/_shared/report-style.md`, refererat fran
Drommens brief-steg, orkestratorn, conclude- och standup-skillarna.

Se `session-logs/2026-08-27-session-log.md` for fullstandig session-logg,
inklusive den kanda luckan i retrieval-tackningen (podcast-/klippningskallor
soks aldrig -- se Open Threads).

## 0.7.0 — 2026-08-26

### Added: assistentlagret (Fas 0-7) + skydd mot tyst filtillbakarullning

Byggde ut agentinfrastrukturen fran godkand plan till korande system, och
rotorsakade under arbetet en tyst datakorruption som slagit ut delar av bygget.

**Nya hookar** (`hooks/`, INTE registrerade i installeraren — se nedan):
- `session-start-brief.py` — snabb auto-standup, rena filreads (177 ms), plus
  sessionsregister for auto-conclude
- `brief-context.py` — ersatter `vault-context.py`; lagger projekt-digest ur
  hubbens frontmatter fore valvpekarna
- `correction-capture.py` — fangar korrektionsformade prompts till en JSONL
- `skill-trigger-telemetry.py` — mater under-triggning av skills

**Universell hook-kill-switch:** `CLAUDE_HOOKS_DISABLED` hedras nu av varje hook
(`design_hook_lib.py`/`marketing_hook_lib.py` delar `disabled()`, ovriga kollar
direkt). Kravs for att A/B-benchmarka lagret mot en ren profil.

**carl-hook.py:** innehalls-hash i dedup-signaturen (en andrad regel invaliderar
nu stale dedup-state), `FORCE_EMIT_EVERY_N` borttagen (~52 K tokens sparade per
40-promptsession pa oforandrad text).

**CARL (`carl/carl.json`):** DESIGN blir keyword-matchad i stallet for always_on;
GLOBAL-regel 4 omskriven (snabb auto-standup via hook ar nu sanktionerad, fulla
/standup forblir manuell); CONTRACT-regel 7 pekar mot `SOUL.md`; CONCLUDE-regel 5
rensad fran `gbrain sync`.

**Skills:** `recall` skriven utan gbrain (syntes via subagent i stallet for
`gb think`), `setup-gbrain` markerad deprecated.

### Fixed: gstack AskUserQuestion-hookarna hade aldrig kort pa Windows

De tre shims:en var registrerade som nakna, ociterade sokvagar utan interpreter.
Windows kan inte kora en bash-shebang-fil sa; varje `AskUserQuestion` no-oppade
tyst sedan installationen, vilket ar varfor `developer-profile.json` stod kvar pa
`sample_size: 0`. Fixade med `bash "..."` enligt filens egen konvention.

### Not distributed: de nya hookarna registreras inte av installeraren

`brief-context.py` och `session-start-brief.py` laser hardkodade valvsokvagar
(`OneDrive/Dokument/Obsidian/Knowledge Base`) och ar inte portabla. Filerna
foljer med paketet for versionering, men `designHookRegistrations()` utokas
medvetet INTE — en registrering skulle bryta installationer utan det valvet.
Gor dem sokvagsagnostiska forst.

## 0.6.3 — 2026-08-19

### Changed: impeccable script tree consolidated to `lib/` (ICM migration)

Ran RinDig/icm-architect against the design system. The audit found 3 stale
duplicate scripts in `impeccable/scripts/` (top-level copies of `lib/` versions)
and a missing catalog router.

- **Deleted** top-level `scripts/is-generated.mjs` (byte-identical dup),
  `scripts/design-parser.mjs` (stale; lib has the YAML-key fix),
  `scripts/impeccable-paths.mjs` (stale; lib is a superset). `lib/` is the single
  home for all three.
- **Repointed** `scripts/live-session-store.mjs` import to `./lib/impeccable-paths.mjs`
  (it was importing the stale top-level copy).
- **Added** `design/references/INDEX.md` — catalog router over the 100+ reference
  files ("catalog holds no books").
- Full backup of the design system at `~/.agents/backups/design-system-20260819-002506/`.
- Live hooks unchanged; verified `detect.mjs`/`context.mjs` resolve and the gate fires.

## 0.6.2 — 2026-08-18

### Changed: claudeep → deepclaude (DeepSeek backend)

Replaced the `claudeep` (npm) backend with **deepclaude** — the GitHub-based
routing proxy (three-proxy: router + DeepSeek + Anthropic in one Node process)
with mid-session backend switching (`ds` / `ant` / `backend`), auto-fallback on
Anthropic 401/402/403, and per-session proxy isolation on dynamic ports.

- **New `deepclaude/` package folder** (vendored from the live local install,
  MIT): bash launcher (`deepclaude.sh`), v2 per-session PowerShell launcher
  (`deepclaude.ps1`), `proxy/` runtime (`routing-proxy.mjs` etc.), `bin/ds|ant|backend`
  wrappers, and the `deepclaude-pretool.py` PreToolUse hook.
- **Installer Step 16** now deploys all files, `chmod +x`s the bash scripts,
  and additively wires the `PreToolUse(Bash)` hook into `settings.json`
  (same never-touch-foreign-blocks rule as the design hooks).
- **Git Bash note:** on Windows, `deepclaude.sh` and the `ds`/`ant`/`backend`
  wrappers are bash scripts — they run from Git Bash only; the PowerShell
  launcher works anywhere.
- Flag renamed `--no-claudeep` → `--no-deepclaude` (legacy flag still accepted).
- `docs/DEEPSEEK.md` rewritten for deepclaude; README references updated.

## 0.6.1 — 2026-08-15

### Changed
- `api-key-setup` v1.1.0 — added Case B: apps that store provider credentials
  encrypted in their own DB via an authenticated API rather than an env var
  (common for CMS-style admin servers). Covers minting a local no-password dev
  session, entering the key via stdin only (never a CLI arg or echoed back),
  and — new Pitfall 7 — verifying against the app's own live test/validate
  endpoint rather than trusting that credential creation succeeded. Derived
  from setting a DeepSeek credential in an ExampleCMS pilot whose admin UI was
  unreachable (client-side extension interference); verified live via the
  app's own `.../credentials/:id/test` endpoint (`modelCount: 2`), not just a
  201 on creation.
- One new CARL decision logged in the `EXAMPLE_DESIGN` domain: when a
  design-system doc and a 1:1 rebuild's parity target conflict, measure the
  live reference and let it decide, not the doc. From a same-session incident
  where a DESIGN.md-driven font "fix" broke measured parity and was reverted.

## 0.6.0 — 2026-08-09

### Added
- `faithful-rebuild` skill — method and traps for rebuilding a live site 1:1 into
  another rendering engine (CMS, static-site importer, another framework) where
  parity is the acceptance test. Documents the core failure mode: geometry and
  computed-style diffs are blind to what is absent, unpainted, or non-functional,
  so pixels and driven interactions are first-class checks, not a formality.
  Derived from a six-page ExampleCMS rebuild in which every serious defect passed
  a diff reporting "0 findings".

## 0.5.0 (2026-08-08)

### New skill: api-key-setup

Generalized from a same-session incident on `project-b`: a hand-rolled,
twice-rewritten key-setup script for a DeepSeek/Gemini/ScrapeGraphAI agent
backend hit five of six documented pitfalls before landing on a stable
pattern — a relative `env_file` path silently reading zero keys depending on
`cwd`, `monkeypatch.delenv` being a no-op against `.env`-file-sourced values,
a test suite quietly losing hermeticity the moment a real key existed on the
machine, and `--push` almost sending backend-only secrets to an unrelated
Vercel project.

- **`skills/api-key-setup/SKILL.md`** — discover what keys a codebase
  actually reads, verify gitignore before writing anything, generate a
  project-specific setup script from a template, scope push/pull to the
  deploy targets that actually consume each key. Six pitfalls documented
  from the incident that produced this skill.
- **`skills/api-key-setup/templates/keys_template.py`** — the reusable
  script skeleton (fill in `KEYS`/`TARGET_FILES`, get `--check`/`--pull`/
  `--push` for free).

## 0.4.5 (2026-08-01)

### design skill: registers replace the single house style, exit bar goes mechanical

The design system was rebuilt after archaeology across three prior sessions
showed the v2 rework fixed v1's mechanical failures (hooks not firing, brand
contamination) but never asked why v1's output was *good* — craft-in-context
became 120 on-demand files, lane-naming disappeared, every quality gate stayed
negative. A flat, on-palette, generic page passed all 88 gates untouched.

- **`SKILL.md` "The craft floor"** — resident (not routed) section: name the
  aesthetic lane before code; a register table (editorial print / cinematic
  dark / illustrated dark / modern clean / warm photographic / historical art)
  picked from the business, not the file order; house physics with exact
  values; composition contract; apparatus budget (≤4 mono micro-labels outside
  print registers); a muted tone needs a value per ground; reduced motion
  removes motion, not content.
- **`references/house-physics.md`** (new) — structural invariants that hold in
  every register, then a per-register inventory with exact values extracted
  from real page source rather than described from memory.
- **`scripts/contrast.py` / `scripts/contrast_over_media.py`** (new) — both were
  wrong on their first real run in ways that would have passed a broken page:
  one only parsed `rgb()` against Tailwind 4's `oklch()`, the other measured
  text-over-photo against the page background instead of the rendered plate.
- **`hooks/design-stop.py`** — Stop now **blocks** when UI edits exist that no
  rendered image was Read afterward (capped at 2 blocks/session, then degrades
  to advisory). This is the mechanical version of "iterate until you honestly
  beat the references, verified on pixels" — previously only enforced when a
  user typed it as an explicit goal each session. Dedup no longer hashes the
  per-minute timestamp line (was spamming duplicate reports).
- **`hooks/design-session-start.py`** (new, `SessionStart`) — clears
  `.once-*`/`.design-verb`/`.stop-signature` on startup/clear. These never
  cleared before, so "once per session" silently meant "once per project,
  forever."
- **`hooks/design-vision-track.py`** (new, `PostToolUse` on `Read`) — logs when
  a rendered image actually enters context; feeds the Stop-hook block above.
- **`hooks/design-verify-gate.py`** — inverted from "prefer read_page over
  screenshot, two rounds max" to "judge from pixels, iterate until a full pass
  finds nothing." Also fires on `mcp__claude-in-chrome__*`, not just
  `mcp__Claude_Browser__*`.
- **`hooks/design-route.py`** — registers cross-project roots (`.linked-roots`)
  so a build that spans repos stays visible to the Stop-hook report.

Verified: three blind one-shot builds from fresh subagents (a cold-bath club,
an antiquarian bindery, an opera festival with no worked register example on
disk) all cleared the reference bar on the first attempt. `verify-design-system.py`
80/80.

**Installer wiring, done.** `install.mjs` and `upgrade.mjs` both carry the
registration table, now 8 entries rather than 6:

- `design-vision-track.py` on `PostToolUse`/`Read` and `design-session-start.py`
  on `SessionStart` are appended for anyone who does not have them.
- The `design-verify-gate.py` matcher **widens** from `mcp__Claude_Browser__.*`
  to `(mcp__Claude_Browser__|mcp__claude-in-chrome__).*`. The old merge only
  asked "is this script present?", so a widened matcher would have been left at
  its old value forever on every existing install. Both mergers now reconcile
  the matcher when the block is one of ours and the value differs.

Verified against a simulated 0.4.4 `settings.json`: 6 changes on the first pass
(2 hooks added, 4 blocks created, 1 matcher widened), 0 on the second — and an
unrelated `carl-hook.py` block in the same event array was left untouched, which
is the property that matters most here.

## 0.4.4 (2026-07-28)

### /conclude: three permanent rules for infrastructure work

Infrastructure sessions kept producing correct code and stale documentation,
and kept leaving changes stranded on one machine. All three gaps are now closed
in the protocol itself rather than relying on memory.

- **Step 3c strengthened — installer sync is now unconditional for infra work.**
  A missing `.carl/upstream.json` gates the *automated* sync, never the
  obligation; if it is absent and infrastructure changed, say so and apply the
  change to the package by hand. The step now also records the trap that bit
  this project: `install.mjs`'s `deployTemplate()`/`wf()` **skip** writing when
  the destination already exists, so anything that must reach *existing* users
  needs an additive merge in both `install.mjs` and `upgrade.mjs`, not a file
  drop.
- **New Step 3d — vault project hub doc, mandatory for architecture or
  infrastructure work.** A single document explaining how the project works,
  living at `<repo-root>/<project-slug>.md` and surfacing in the vault through
  the project junction. The step leads with **search for an existing one first**
  — a stale duplicate is worse than none, because the vault agent may read the
  old one. Required contents: what the project is, the core decision flow, a
  document map with one line per significant file, invariants that bite if
  broken, how to verify, and current status. Superseded docs get marked stale,
  not deleted.
- **New Step 8b — reindex search.** `qmd update` whenever vault markdown
  changed (session logs, plans, wiki pages, hub docs) and `gbrain sync`
  whenever code, skills or agent guidance changed. Both non-fatal: on failure,
  log a warning and continue, because an unindexed vault is recoverable and a
  lost session log is not. Report the outcome of both; never claim the vault is
  searchable without having run them.

All three are mirrored into the CARL `CONCLUDE` domain (`carl/carl.json`), so
they inject on conclude prompts as well as living in the skill.

## 0.4.3 (2026-07-28)

### Product surfaces are a mode, not an exclusion

Dashboards, admin panels, settings screens, data tables and editors were listed
as out of scope. That was wrong for real work — they sit inside corporate sites
constantly. The boundary should be a **mode**, not an exclusion.

Audited the stack before proposing any import. **Nothing new was needed** — the
gap was routing, not skills. `impeccable` v4 already ships an **Operate mode**
with `reference/operate.md`, and it was never wired into the router. Everything
else was already installed: `shadcn-ui` (dashboard blocks, forms, tables,
command palette), `dataviz`, `ui-ux-pro-max` (`sortable-table`,
`empty-data-state`, `loading-chart`, `adaptive-navigation`),
`web-design-guidelines`, `impeccable harden` / `onboard`, and the Vercel/Next
framework skills.

- **New `skills/design/references/product-surfaces.md`.** The gate does *not*
  change — product surfaces derive colour, type and radius from the same brand,
  and gate 65 (second identity) applies across the seam. The **register** does:
  one font family, fixed rem scale rather than fluid, Restrained colour floor,
  accent for state only, 150–250ms motion that conveys state, no page-load
  choreography, density and familiarity over expression. Eight states,
  skeletons over spinners, empty states that teach, overlays that escape their
  container.
- **Marketing references do not load there** — hero enrichment, macrostructures,
  the six-axis fingerprint, and production tells (gates 66–88). A version label
  in a product header is legitimate build metadata, not a tell.
- **Hand off the engine, keep the design** — TanStack / AG Grid, Monaco /
  CodeMirror, Fluent / Carbon / Atlaskit / Polaris, Apple HIG / Material,
  themed to the locked tokens. The router still owns tokens, mode declaration,
  state discipline and verification.
- **Automatic detection.** `component-routing.md` gains a `product` rule firing
  on dashboard/admin/settings/console/portal/table/editor paths and on
  `<DataTable`, `useReactTable`, `<CommandDialog`, `aria-sort`, `<Sidebar`,
  `<Skeleton`. No user input required; verified not to collide with the
  marketing route.
- **Mixed surfaces** (marketing site plus portal) are two modes on one token set.
- `skill-orchestration.md` §10 rewritten from "out of scope" to "a mode, not an
  exclusion"; genuine out-of-scope moved to §11.

### CARL: documentation sync at /conclude

New `CONCLUDE` rule — a session that changes architecture or infrastructure
must search the repo **and** the vault for documentation describing what
changed (README, ROUTER/ARCHITECTURE docs, workflow guides, wiki pages,
CHANGELOG), update everything now stale, and report what was checked versus
what was updated. The session log records what happened; the docs record how
the system works, and those drift apart silently.

Applied immediately to this session: `ROUTER.md` and `README.md` updated for
verb routing, tier `0-prose`, the marketing/product mode split, and the fact
that hooks can inject text and deny writes but **cannot load a skill**.

`verify-design-system.py`: 74 → 79 checks.

## 0.4.2 (2026-07-28)

### Skill orchestration foundation + a high-severity enforcement bug

Audited all ~40 design-capable skills across five packs to answer which
procedure owns which decision. Three findings.

- **Fixed: silent false-lock on prose-only `DESIGN.md`.** `tier()` reported
  `0-locked` on file existence alone. Five skills write a file by that name in
  three incompatible formats — `design-md` and gstack's `design-consultation`
  emit **prose only**, no token frontmatter. A prose `DESIGN.md` therefore made
  the system announce *"TIER 0 — LOCKED, inherit the system, do not re-derive"*
  while `design-gate.py` enforced nothing; verified empirically that a write
  with `#FF00FF` and Comic Sans passed silently. Strictly worse than having no
  `DESIGN.md`, because the model skips derivation *and* gets no enforcement.
  `tier()` now returns `0-locked` / `0-prose` / `ungated`, and `0-prose` states
  plainly that the contract gate is blind, pointing at `$impeccable document`.
- **New `skills/design/references/skill-orchestration.md`** — the foundation
  doc: seven phases, a verb-routing table, the redesign collision resolved as a
  three-procedure sequence (mode detection beats tier beats page shape), the
  `DESIGN.md` format problem, direction-vs-craft classification for every skill,
  verify ordering (audit read-only *before* fixing), the two parallel pipelines,
  nine known collisions with resolutions, and explicit out-of-scope.
- **Verb routing.** The system previously routed by *component* but never by
  *task type*, so build / redesign / audit / polish / study were treated
  identically. `design-intent.py` now detects eight verbs (English + Swedish),
  routes each to its owning procedure, and **re-fires on task-type change**
  rather than once per session — a mid-session pivot is exactly when the wrong
  procedure gets used.
- **Documented, not integrated: two parallel pipelines.** gstack
  (`design-consultation` → `design-shotgun` → `design-html` → `design-review`)
  and Stitch (`enhance-prompt` → `stitch-design` → `design-md` →
  `react-components`). Both write their own `DESIGN.md`. Mixing either into a
  job mid-flight produces incoherent output; lane boundaries are now explicit.
- **Flagged:** the installed `hallmark` skill competes with `design` for
  auto-invocation on identical triggers while all 105 of its references are
  already ported byte-identical into `design/references/`. Left for a user
  decision rather than silently uninstalled. Also: `polish` carries a stale
  `/teach-impeccable` dependency (impeccable v3 naming) — prefer
  `impeccable polish`.
- `component-routing.md` — landing rule tightened; it was firing on any
  `page.tsx` and now requires a real marketing signal.
- `verify-design-system.py` — 60 → 74 checks.

## 0.4.1 (2026-07-28)

### taste-skill v2 absorbed into the design system

Upstream [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) shipped a
v2 restructure. Audited all seven of its skills against the installed copies:
`gpt-taste`, `minimalist-ui`, `industrial-brutalist-ui`, `high-end-visual-design`
and `redesign-existing-projects` are **byte-identical** between v1 and v2. Only
`design-taste-frontend` was rewritten (226 → 1206 lines) — and it was the one
skill the router never referenced.

Its content was deduplicated against Hallmark's 57 gates, impeccable's 68
detector rules and the existing references before porting, so nothing already
covered got duplicated in a weaker form.

- **`skills/design-taste-frontend`** — updated to v2.
- **New `skills/design/references/production-tells.md`** (gates 66–88) — about
  twenty empirically-derived micro-decoration signatures that survive every
  other gate because each looks like a deliberate designer choice in isolation:
  hero version labels, numbered/range eyebrows, middle-dot chains, decorative
  status dots, `<br>`-broken italic headlines, rotated text, crosshair
  decoration, div-based fake product UI, fake version footers,
  performative-craftsman labels, locale/weather strips, pills on images,
  photo-credit captions, live-stock counters, hero decoration strips, floating
  corner sub-text, `border-t`+`border-b` rows, filled-track scoring bars, scroll
  cues. Gate 75 is a zero-tolerance em-dash ban — the strictest of the three
  em-dash rules in the system and the one that wins. Each gate records what
  impeccable's detector already catches mechanically.
- **`scope-discipline.md`** — the redesign protocol: mode detection (greenfield
  / preserve / overhaul), audit-before-touching, preservation rules (IA, brand
  colours, copy voice, accessibility wins, analytics events), modernisation
  levers in priority order, and the never-change-silently list. A partial
  rebrand maps to *preserve*, not greenfield.
- **`invention.md`** — a fourth calibration cluster with concrete banned hex
  families (the premium-consumer beige+brass+oxblood+espresso default),
  extending impeccable's `cream-palette` prose into something checkable. Serif
  discipline folded in.
- **`process.md`** — the one-line "design read"; the three intensity dials
  (orthogonal to the tier gate: the tier decides where direction comes from,
  the dials decide how loud); the brief→official-design-system map (Fluent /
  Material / Carbon / Polaris / Atlaskit / Primer / GOV.UK / USWDS / Radix /
  shadcn), a capability the system previously lacked entirely; and the
  out-of-scope boundary.
- **`component-routing.md`** — `design-taste-frontend` now routes for page-scope
  landing, marketing and portfolio surfaces. Craft and structure only; like
  every other specialist it may not pick the palette at Tiers 0–2.

`verify-design-system.py` still 60/60.

## 0.4.0 (2026-07-27)

### Design System v2 — Brand-Derivation Gate + Edit-Boundary Hook Enforcement

The v1 design protocol (0.2.0) held at the top of a session and drifted after — CARL
rules inject once per prompt, but design decisions happen once per file write, and a
build turn can be sixty tool calls long. Three specialist skills in the stack
(`minimalist-ui`, `industrial-brutalist-ui`, `high-end-visual-design`) each hardcode a
complete palette; routing to them as direction-setters was overwriting whatever brand
identity a project actually had. v2 fixes both.

- **The rule**: brand derives direction, skills supply craft, themed skills are the
  last resort. A gate (Tier 0 locked / 1 derive from brand evidence / 2 study a
  supplied reference / 3 invent) runs before any specialist gets to pick a colour.
  Full procedure and 10 new reference docs in `skills/design/` — see
  `skills/design/SKILL.md`.
- **`skills/design`**: rebuilt on Hallmark's front-door structure (all 105 of its
  reference files ported byte-identical); its 20-theme catalog kept in full but
  demoted to Tier 3 only.
- **New skills**: `design-verify` (batched browser inspection procedure),
  `brand-system` (ports Anthropic's Create-design-system derivation procedure, emits a
  `{brand}-design` skill per project), `humanizer` (blader/humanizer — AI-writing-tell
  removal, paired with `copywriting` as a two-stage copy gate on every user-facing
  string, every language).
- **`skills/impeccable`**: upgraded 3.x → 4.0.2. Its 68-rule deterministic detector now
  supplies the mechanical layer this gate enforces against — 4 of those rules check a
  build's `DESIGN.md` frontmatter directly.
- **New `hooks/` package directory** — 6 hooks moving enforcement from prompt
  boundaries to file-write boundaries: `design-intent.py` (UserPromptSubmit, injects
  active tier + locked tokens), `design-gate.py` (PreToolUse, denies a write that
  violates the locked token contract), `design-verify-gate.py` (PreToolUse on browser
  tools, injects inspection discipline), `design-route.py` (PostToolUse, names the
  right craft skill per component), `design-telemetry.py` (PostToolUse on Skill,
  attributes invocations to components), `design-stop.py` (Stop, deep detector pass +
  session report). `install.mjs` deploys and wires them (new Step 3c); `upgrade.mjs`
  syncs the files and additively merges the hook registrations into an existing
  `settings.json` without disturbing hooks already there — verified by an 18-point
  fixture suite covering unrelated-hook preservation, idempotency, missing-file
  no-op, and malformed-JSON safety.
- **Kill switch** `DESIGN_HOOKS_DISABLED=1`; the contract gate ships advisory by
  default, `DESIGN_GATE_BLOCKING=1` promotes it to a hard denial per-shell.
- **The session report**: every session touching UI files writes
  `.impeccable/design-session.jsonl` and, at Stop, a report measuring the
  route-vs-invocation gap — how often a skill was named and never actually loaded.
  That gap is the direct, mechanical measurement of the v1/v2 failure mode.
- **CARL**: `EXAMPLE_DESIGN` domain removed and the `DESIGN` domain's example-app-specific
  content generalized — both were project-identifying content that had ended up in
  the shared, always-on config shipped to every installer user. New GLOBAL rule:
  never create a domain, or add project-identifying content to an always-on one,
  without asking first. Decision `design-002` records the v2 rebuild.
- **`docs/design-workflow.md`**: rewritten to document the gate + hook chain while
  keeping the v1 incident lesson and the proof-gallery pattern.
- **`templates/.claude-settings.json`**: fresh-install template now carries all 6
  design hook registrations alongside the existing `carl-hook.py` entry.

## 0.3.0 (2026-07-21)

### Installer Role Detection + Daily Auto-Update

- **Owner/Consumer split**: `--owner` flag creates `.carl/upstream.json` in vault, enabling
  conclude's upstream sync to push infra changes back to the repo. Consumer mode (default)
  has no upstream file — conclude Step 3c is a no-op.
- **Daily auto-update** (`--no-auto-update` to opt out): Sets up OS-native scheduler
  (systemd user timer / launchd / crontab / Windows Task Scheduler) that runs daily at
  09:00 with randomized delay.
- **Auto-update pipeline**: `git fetch` → SHA compare → `git pull --ff-only` →
  `node upgrade.mjs` → full health check → terminal report
- **Health check system**: Four-layer validation on every daily run:
  1. Package health (`health-check.mjs --installed`): npm, 208 skills, subsystems, MCP servers,
     CARL hook wiring, junctions, git status
  2. Installation health (`verify-install.mjs`): all paths, configs, MCP validation,
     repo status
  3. MCP health: parses `~/.mcp.json`, verifies each server's command exists in PATH
  4. CARL deep health: domain integrity, rule/decision counts, hook version, hook wiring in
     settings.json
- **Config system**: `~/.super-intelligence/config.json` stores runtime settings
  (`auto_update`, `repo_path`, `vault_path`, `owner_mode`, `last_check`). Read by all
  update scripts.
- **New scripts**: `auto-update.sh`, `auto-update.ps1`, `schedule-auto-update.sh`,
  `schedule-auto-update.ps1`, `remove-auto-update.sh`, `remove-auto-update.ps1`
- **Updated docs**: `docs/UPGRADE.md` (full rewrite), `docs/QUICKSTART.md` (auto-update
  section), `templates/CLAUDE.md` (automatic updates section)
- **Fixed**: `verify-install.mjs` broken `await import` in non-async top-level

## 0.2.0 (2026-07-10)

### Design Workflow (CARL-enforced)

- **DESIGN domain**: replaced the single router rule with the proven 4-step protocol
  (design router → framework-craft skills → emil-design-eng audit → screenshot-vs-
  reference gate) + decision `design-001`, adopted after a false-verification incident
  where design work was claimed "visually verified" without ever opening the reference
  images. Documented in `docs/design-workflow.md` including the proof-gallery pattern
  (headless screenshot script → committed PNGs).

### Conclude Upstream Sync (self-updating stack)

- **CONCLUDE domain**: new mandatory rule + decision `conclude-001` — every session
  that changes global agent infra (skills, CARL, hooks, MCP, templates) syncs it into
  this repo with VERSION bump + CHANGELOG + local commit. Never pushes automatically.
- **conclude skill**: new Step 3c "Upstream Sync Check" with the exact commands.

### Skills Registry Sync (141 → 208)

- 67 new skills vendored, notably: the **gstack** suite (browse/ship/canary/qa/
  design-consultation/plan-reviews/…), **ponytail** suite (lazy-dev enforcement +
  audit/review/debt), **agent-reach**, **ios-*** suite, **spec**, **pair-agent**,
  **tauri-react-visual-verify**, **make-pdf**, **last30days**, and updates to
  recall/ingest/standup/conclude.

### CARL Sync

- `carl/carl.json`: full sync from live — GLOBAL 9 rules/6 decisions, DEVELOPMENT
  +3 decisions, DESIGN 5 rules/1 decision, CONCLUDE 2 rules/1 decision.
  `carl/carl-hook.py` updated to the live hook.
  (A project-specific domain was briefly synced in here too; removed in 0.4.0 — see
  below. A domain or project-identifying rule should never land in this shared file
  without asking first, which is now itself a GLOBAL rule.)

### Upgrade Pipeline

- **upgrade.mjs**: skills/scripts sync is now content-aware — copies new files AND
  overwrites changed ones (byte compare), never deletes user-local files, and reports
  `+added / ~updated / unchanged` counts (dry-run reports without writing). Replaces
  the old copy-new-only robocopy that silently skipped modified skills.
- CARL rule merge now matches by rule TEXT (per-install sequential ids collide) and
  also merges decisions by id.

## 0.1.0 (2026-05-26)

### Initial Release

- **Agent Chorus**: Cross-agent JSONL messaging with provider contracts for Claude, Codex, Gemini, and Hermes
- **Skills**: 70+ reusable skill modules across design, development, marketing, SEO, and infrastructure
- **Memory System**: Three-tier hot/warm/cold memory with FTS5 sessions.db
- **QMD**: Hybrid semantic + keyword search with `.qmd.yaml` configuration
- **STATUS.md**: Cross-agent session index with `update-global-status.py`
- **Agent Configs**: CLAUDE.md, AGENTS.md, GEMINI.md templates with automatic sync
- **Syncthing Bridge**: Configuration templates for Windows↔WSL vault sync
- **Hermes/WSL**: Setup guide and platform-gated HERMES CARL domain
- **Karpathy Wiki**: Setup guide adapted for agent knowledge management
- **Auto-Export Pipeline**: Tampermonkey script + file watcher + ingest workflow
- **Backup**: Non-destructive append-only vault backup to dual mirrors
- **Installer**: One-shot `node install.mjs` for complete setup
