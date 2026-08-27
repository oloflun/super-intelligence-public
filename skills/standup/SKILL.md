---
name: standup
description: "Project-scoped session initiation. Loads the current project's context — STATUS.md, latest session log, wiki project page, and global memory. Run at session start or when switching projects. Loads no other project's context except one bounded cross-project step: the global ~/STATUS.md Open: fields and memory/BLOCKS.md, which together list what is open and why work is parked everywhere else."
---

# /standup — Project-Scoped Session Initiation

**Sprakregler:** all text som gar till {{USER_NAME}} foljer `~/.agents/_shared/report-style.md` -- las den forst. Kortfattat: inga interna ord utan forklaring i samma mening, varje oppen trad ar minst en hel mening med nasta konkreta steg, varje forslag pekar pa ett delmal i projektets GOALS.md, och det ar arbetet i projekten som rapporteras -- inte bygget av verktygen.


Orients the session to the **current project only**. Reads project-local files anchored to
the current working directory, then bounded global memory. Never touches other projects.

## Why This Exists

Persistent projects accumulate decisions, state, and context across sessions. The standup
ingests what `/conclude` captured. They are a matched pair. The critical constraint: this
skill is anchored to the **current cwd** — it cannot accidentally load another project's context.

## Algorithm

### Step 1 — Resolve project slug

```bash
git rev-parse --show-toplevel 2>/dev/null || pwd
```

Take the basename of that path, lowercase, spaces → hyphens. This is `<slug>`.

If not in a git repo, use the cwd basename as the slug.

### Step 2 — Read project-local state (in this order)

Read these files, all anchored to `<slug>`. Stop adding context once you have enough to
orient the session:

1. **`<repo>/STATUS.md`** — canonical project state, priorities, open decisions.

2. **`<repo>/GOALS.md`** — projektets målbild: vad projektet är och för vem, vad
   "klart" betyder, delmålen i ordning, planerade funktioner (uppdelat i beslutat och
   föreslaget) och beroenden till andra projekt. **Läs den här före statusfilen.**
   STATUS.md säger var arbetet står; GOALS.md säger vart det är på väg, och det är
   det senare som avgör om ett förslag är relevant. Saknas filen: säg det, och erbjud
   att skapa den från `wiki/projects/_templates/goals-template.md`.

2. **Latest `<repo>/session-logs/YYYY-MM-DD-session-log*.md`** (most recent first) —
   what happened last session. If local logs are missing, fall back to:
   `~/.agents/memory/<slug>/sessions/` (mirrored copy).
   If the log contains a `<!-- session-state -->` block, parse it for structured metadata
   (open thread count, pending handoffs, suggested next focus).

3. **Latest `~/.agents/memory/<slug>/plans/`** — the active implementation plan.
   Fall back to project-local plan files if mirror is missing. Skip silently if none exists.

4. **`{{VAULT_PATH}}\wiki\projects\<slug>\<slug>.md`** — synthesized cross-session wiki summary for
   this project. Read if it exists. Skip if not yet created.

**Hard rule:** Only read files under `<repo>/`, `~/.agents/memory/<slug>/`, or
the vault wiki projects directory for `<slug>`. Never open another project's directory.

### Step 3 — Read global frozen-snapshot memory

Always load both (they are bounded by design, safe to always read):
- `{{VAULT_PATH}}\memory\MEMORY.md` (≤ 2 200 chars — environment facts, lessons, conventions)
- `{{VAULT_PATH}}\memory\USER.md` (≤ 1 375 chars — user preferences, profile)

The canonical workspace is `%LOCALAPPDATA%\hermes` (Windows-native Hermes Desktop App). The vault is on OneDrive at the path above. No WSL2, and **`~/vault-local` no longer exists as anything but a stale leftover** — it was the staging directory from when Hermes ran under WSL. It is a genuinely separate directory on disk, not a link, reached only by a lagging propagation job. Never read or write it. CARL GLOBAL rule 10.

Also load, and this one is deliberately **cross-project**:
- `...\Knowledge Base\memory\BLOCKS.md` (≤ 3 000 chars — why work stopped, everywhere)

### Step 3b — Open threads across every other project

This skill is otherwise anchored to the current project and must stay that way; the
wall is what keeps context cheap. This step is the one sanctioned channel through
it, and both its sources are capped or short enough to always afford.

Read both. They answer different questions and have different failure modes.

**1. `{{USER_HOME}}\STATUS.md` — the automatic list.**
Written by `update-global-status.py` on every `/conclude`, three entries per agent,
each carrying an `Open:` field. **This is the always-current source and it requires
no discipline to stay that way.** Parse the `Open:` fields for every project that
is not the current one and list them.

Print this every time, unabridged, even when it looks routine:

```
OPEN ELSEWHERE
  project-a     — seed route still publishes image-less products
  example-app   — landing page past the hero unfinished
  super-intel   — which infrastructure returns time is unmeasured
```

Never summarise it to "a few open items". The list being *in front of the human*
is the entire mechanism; compressing it destroys the thing it is for.

**2. `...\Knowledge Base\memory\BLOCKS.md` — the curated list.**
Richer: each entry carries a `shape`, the abstract form of the block rather than
its project-specific wording. Written by hand at `/conclude`, so it can fall
behind — that is exactly why source 1 exists alongside it.

When a block elsewhere shares a shape with the one being resumed, say so in one
sentence and stop:

> `super-intelligence` is parked on the same shape: enforcement in the mechanism
> vs. enforcement in the instructions.

Do not offer to work on another project's items. Listing them is the whole job.

**Do not build a matcher for this.** Whether two shapes are really the same is the
human's judgment, and a handful of lines is enough to make it. Automated similarity
over a corpus this small fires on shared vocabulary and is worse than nothing.
Revisit only when the list gets too long to read, which is a long way off.

If `BLOCKS.md` is missing, say so once and continue on source 1 alone. If the
global `STATUS.md` is missing, that is a real fault — report it, because `/conclude`
should be maintaining it.

### Step 4 — Staleness detection

- If `STATUS.md` "Last updated" is >7 days ago, flag it.
- If the latest session log is >7 days old, flag it.
- If `session-state` block shows `handoffs_pending`, flag them.
These are informational — don't block on them.

### Step 4b — Memory-file health check

Check capacity of the hot memory files. Caps live in their frontmatter (`limit:` field):

```bash
mem_size=$(wc -c < "$VAULT/memory/MEMORY.md")
usr_size=$(wc -c < "$VAULT/memory/USER.md")
# MEMORY cap: 2200, USER cap: 1375
# VAULT = {{VAULT_PATH}}
```

- If `MEMORY.md` ≥ 80 % of cap (≥ 1 760 chars) → flag in standup output:
  `⚠️ MEMORY.md at <X>% cap (<size>/2200) — trigger conclude memory audit / manual offload to MEMORY-FULL.md`
- If `USER.md` ≥ 80 % of cap (≥ 1 100 chars) → flag similarly for USER.md.
- If either is **over** cap → escalate: `❌ MEMORY.md OVER cap (<size>/2200) — prune before next /conclude or new facts will be skipped.`

The prune procedure (manual, until automated):
1. Identify entries that are resolved, project-specific (belong in project memory), or >60 days old and not actively referenced.
2. Append them to `MEMORY-FULL.md` under a dated `## Memory-Tier Offload — YYYY-MM-DD` section.
3. Delete from `MEMORY.md`. Consolidate related entries into denser ones if possible.
4. Verify `wc -c MEMORY.md` is under cap.

### Step 5 — Check inbound chorus messages

```bash
chorus messages --agent <current-agent> --cwd "{{VAULT_PATH}}" --clear --json
```

Skip silently if chorus is not available. Also check:
```bash
cat "<repo>/.agent-chorus/CHECKPOINT.md" 2>/dev/null || true
```

Check `<repo>/Incoming/` for cross-project handoffs. If files exist, read them.
Flag anything in `<repo>/Outgoing/` that hasn't been routed.

### Step 6 — Output a concise summary

```
PROJECT: <slug>
LAST SESSION: <date> — <2-sentence summary of what was accomplished>
OPEN THREADS: <top 3, or "none">
CHORUS: <inbound messages, or "none">
FOCUS: <suggested next action from STATUS.md priorities or session open threads>
MEMORY HEALTH: <ok | "⚠️ MEMORY.md at X% — prune recommended" | "❌ over cap, prune required">

OPEN ELSEWHERE            ← from Step 3b. Always printed, never summarised.
  <project> — <open thread>
  <project> — <open thread>
```

`OPEN ELSEWHERE` is not optional and does not get collapsed when the list is long
or looks routine. It is the only place the other projects are visible at all, and
its whole purpose is that a block being resumed here might already have been solved
there.

Then wait for the user to confirm or correct before proceeding to any work.

Do not dump the full session log. Do not call `qmd query` unconditionally.
Keep the standup lean — it's a sync, not a report.

### Step 7 — Do NOT do these things

- Read files from other projects (only `<slug>`-scoped paths).
- Call `qmd query` unless the user's first message specifically requires it.
- Auto-fire globally via a hook — `/standup` is invoked manually at session start.
- Load all skills upfront — they are loaded on demand via ToolSearch.

## Invocation

```
/standup           # use cwd as the project root
/standup <path>    # explicit project root (for switching projects mid-session)
```

## Notes

- Global memory (vault `memory\MEMORY.md`, `USER.md`) is read-only here.
  Only `/conclude` writes to it.
- The vault is at `{{VAULT_PATH}}`.
  Hermes workspace is `%LOCALAPPDATA%\hermes`. No WSL2.
- After the standup summary, proceed to the user's task. Don't narrate it in detail.
