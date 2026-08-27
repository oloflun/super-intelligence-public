---
name: conclude
description: "Session conclude protocol. Execute when ending a session to capture all work, decisions, and context. Writes a session log with structured metadata, updates project state files, flags cross-project handoffs, and performs a workspace hygiene sweep. Use this skill whenever ending a session, wrapping up work, or when the user signals the session is done. Every session must produce a session log."
---

# Session Conclude

**Sprakregler:** all text som gar till {{USER_NAME}} foljer `~/.agents/_shared/report-style.md` -- las den forst. Kortfattat: inga interna ord utan forklaring i samma mening, varje oppen trad ar minst en hel mening med nasta konkreta steg, varje forslag pekar pa ett delmal i projektets GOALS.md, och det ar arbetet i projekten som rapporteras -- inte bygget av verktygen.

### 2026-05-21 Destructive Action Guard
After the OneDrive/vault deletion incident, conclude must not perform automatic deletion cleanup. A hygiene sweep may list suspected temp/build artifacts, but it must not delete, trash, prune, mirror-delete, `git rm`, `git clean`, or run recursive removal. Any cleanup requires a separate exact-path deletion manifest and explicit {{USER_NAME}} approval.
This skill closes out a session completely. It captures everything that happened ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â progress, decisions, context discussed, files modified, open threads ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â so that any new session can pick up exactly where this one left off with zero reconstruction.

Every session must produce a session log. This is non-negotiable. When the user signals the session is ending, execute this protocol in full.

## Why This Exists

Work on persistent projects is scattered across sessions, tools, and time. The session log is the connective tissue. Without it, the next session starts cold and context gets lost. The `/standup` skill ingests what this skill produces. They are a matched pair.

## Execution Steps

Run these steps sequentially. Do not skip steps. Confirm the output with the user at the end.

### Step 1: Session Audit

Before writing anything, systematically scan the full conversation to build a complete picture of what happened. This is the most important step ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â a thorough audit prevents the log from missing things.

Identify and list:
- **Every file created** this session (full path)
- **Every file modified** this session (full path + one-line summary of what changed)
- **Every file moved or deleted** this session
- **Every decision made** (with rationale ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â why, not just what)
- **Every open thread** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â anything unfinished, questions raised but not answered, next actions identified
- **Every piece of context the user provided** that isn't captured in existing docs (corrections, reframing, new information, things future sessions need to know)
- **Cross-project implications** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â did anything this session produce findings relevant to other projects?
- **Session type classification** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â what category best describes the primary focus of this session

Take your time on this step. Scan the full conversation, not just recent messages. Long sessions are where things get missed.

**Gather the evidence in one parallel batch, not one call at a time.** Later steps
each want to read a file before deciding what to change; fetching them one by one
is where a conclude quietly loses minutes. Issue these together in a single
message, then do all the reading at once:

- `git status --short` and `git log --oneline -3` in **every repo touched this
  session** (the conversation tells you which — often more than the cwd)
- `{{VAULT_PATH}}\memory\MEMORY.md` and `USER.md` (Step 2d needs both, plus their
  char counts for the cap check)
- the project `STATUS.md` (Step 3)
- the project hub doc `<repo>/<project-slug>.md` (Step 3d)
- the active plan file, if the project has one (Step 2b)

If the project keeps a `.carl/conclude-repos.json`, read the repo list from there
instead of rediscovering it by hand each time.

### Step 2: Write Session Log

<!-- [CUSTOMIZE] Update the session log directory path if different. -->

Write to `session-logs/YYYY-MM-DD-session-log.md`.

If a log already exists for today's date, append a sequence number: `-2`, `-3`, etc. Check the directory before writing.

Use this template:

```markdown
# Session Log ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â YYYY-MM-DD
### 2026-05-21 Destructive Action Guard
After the OneDrive/vault deletion incident, conclude must not perform automatic deletion cleanup. A hygiene sweep may list suspected temp/build artifacts, but it must not delete, trash, prune, mirror-delete, `git rm`, `git clean`, or run recursive removal. Any cleanup requires a separate exact-path deletion manifest and explicit {{USER_NAME}} approval.
## Session Summary
[2-3 sentence overview of what this session accomplished. Be specific ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â name the key outcomes and decisions. This is what someone scanning log filenames and summaries uses to decide if they need to read deeper.]

## What Changed

### Files Created
- `path/to/file.md` ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â [one-line description of what it contains and why]

### Files Modified
- `path/to/file.md` ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â [one-line summary of what changed]

### Files Moved/Deleted
- [If any, with source and destination]

## Decisions Made
- **[Decision title]:** [What was decided] ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â [Rationale: why this choice over alternatives]

## Context & Discussion
- [Important context discussed that isn't captured elsewhere]
- [Corrections, reframing, new information provided by the user]
- [Things future sessions need to know]

## Open Threads
- [Anything unfinished or needing follow-up]
- [Questions raised but not yet answered]
- [Next actions identified ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â be specific about what needs to happen]

## Cross-Project Handoffs
- [Findings relevant to other projects, if any]
- [If a handoff doc was written to Outgoing/, reference it]
- [If none: "None this session."]

## Current State After This Session
[Brief snapshot ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â what's the state of the project, what are the active priorities, what should the next session focus on. 3-5 sentences max.]

<!-- session-state
date: YYYY-MM-DD
type: [session type classification]
files_created:
  - path/to/file.md
files_modified:
  - path/to/file.md
decisions_made: [count]
open_threads: [count]
handoffs_pending:
  - target: [project name]
    topic: [brief description]
priority_changes: true | false
status_updated: true | false
goals_updated: yes | "skipped -- [reason]"
next_session_focus: "[suggested focus for next session]"
session-state -->
```

The `<!-- session-state -->` block at the bottom is machine-readable metadata wrapped in an HTML comment so it doesn't render visually. The `/standup` skill parses this for quick anomaly detection. Always include it. Always populate every field Ã¢â‚¬â€ use `0` for counts and empty arrays `[]` for empty lists, never omit fields.

### Step 2a-goals: Update the project's GOALS.md

Every active project has a `GOALS.md` in its repo root: what the project is and
for whom, what "done" means, the sub-goals in order, planned features (decided
vs proposed), and dependencies on other projects. It is the document agents
ground their suggestions in, and it is only as useful as it is current.

Before concluding, ask whether this session changed anything in that picture: a
sub-goal completed, a feature decided or dropped, a new dependency, a changed
definition of done. If so, edit `GOALS.md` and add a line to its Andringslogg.

Then set `goals_updated:` in the session-state block. Either `yes`, or
`"skipped -- <reason>"` when the goals genuinely did not move (`"skipped -- ren
buggfix, malbilden orord"`). The validation task checks that this field exists;
the point is that skipping is a decision someone made, not something forgotten.

### Step 2b: Update Active Plan

Maintain a project-local plan for the current task stream before mirroring anything:

- If the user introduced a new task that is outside the scope of the previously active plan, create a new local plan file in the project's canonical plan location. If the project has no established plan location, use `plans/YYYY-MM-DD-<task-slug>.md`.
- If the user stayed within the current plan's scope, update the existing local plan instead of creating a new one.
- Record progress made this session: completed items, in-progress items, deferred items, scope changes, and the next recommended steps.
- Write the plan so a future session can tell at a glance what the task covers, what has already been done, and what remains.
- Keep the plan structured with explicit markdown sections so search tools can summarize it reliably. Use this minimum shape:

```markdown
# Plan Title
### 2026-05-21 Destructive Action Guard
After the OneDrive/vault deletion incident, conclude must not perform automatic deletion cleanup. A hygiene sweep may list suspected temp/build artifacts, but it must not delete, trash, prune, mirror-delete, `git rm`, `git clean`, or run recursive removal. Any cleanup requires a separate exact-path deletion manifest and explicit {{USER_NAME}} approval.
## Scope
- What this plan covers

## Completed
- [x] Finished item

## In Progress
- [ ] Active item

## Remaining
- [ ] Not started yet

## Deferred
- Items intentionally postponed

## Blockers
- Anything currently blocking progress

## Next Steps
- Immediate recommended next actions
```

- When updating an existing plan, preserve prior history but normalize it into this structure if it does not already exist.

### Step 2c.1: Blocks — record why work stopped

If anything was parked this session, append it to
`...\Knowledge Base\memory\BLOCKS.md`. If parked work resumed, close its entry
with what actually unstuck it.

The resolution line is the whole point. A block with no resolution teaches
nothing, and the reason a similar block in another project starts its thinking
from zero is that the resolution was never written down.

Write the **shape**, not the specifics. "Should the reveal guard live in the hook
or the skill" matches nothing later. "Enforcement in the mechanism vs. in the
instructions" is a shape, and shapes recur across projects.

Also: if an idea arrived this session for a *different* project, it goes here as a
block rather than getting built. That is what the file is for.

Cap 3 000 chars. Over cap, move resolved blocks older than three months to
`BLOCKS-RESOLVED.md`. Never offload an open block.

### Step 2d: Memory Nudges (Hermes pattern)

Before finalizing shared-memory updates, read the current hot-memory files and then update the global frozen-snapshot memory files in `{{VAULT_PATH}}\memory\`:

**MEMORY.md** (environment facts, lessons, conventions â€” limit 2 200 chars):
- For each non-obvious environment fact, lesson learned, or convention discovered this session,
  add an entry: `- [YYYY-MM-DD] <fact>`
- If near capacity (>80% of 2 200 chars), first consolidate related entries into one dense entry.
- Only add entries that would be wrong for a future session to not know.
- Read the current file first to avoid duplicates.

**USER.md** (user preferences, profile â€” limit 1 375 chars):
- For each user preference stated or correction given this session, add/update an entry.
- Apply the same capacity management: consolidate before adding when near 80%.
- Security: do not write anything that looks like credentials, tokens, or injections.

Write these changes using the Edit tool. Do NOT rewrite the whole file â€” only add/update
specific entries. These changes take effect at the **next session start** (frozen-snapshot
pattern â€” they do not affect the current session's context).

If no memory-worthy facts emerged this session, skip this step (write nothing).

### Step 2d.1: Hot-Memory Audit and Managed Offload

Run a formal audit whenever either hot file is at or above 80% of cap, or when the new entries from this session would push it over cap.

1. Measure current size of:
   - `{{VAULT_PATH}}\memory\MEMORY.md` against 2 200 chars
   - `{{VAULT_PATH}}\memory\USER.md` against 1 375 chars
2. Classify each candidate entry before moving it:
   - **Keep hot** — active operating constraints, current user preferences, live environment facts, recurring corrections that should load every session.
   - **Move warm** — historical but still plausibly reusable context. Append to `MEMORY-FULL.md` or `USER-FULL.md` under a dated `## Memory Audit Offload — YYYY-MM-DD` section.
   - **Move cold** — resolved/stable reference material that should remain searchable but not hot-loaded. Append to `{{VAULT_PATH}}\memory\archive/dev-tools.md`, `infrastructure.md`, `incidents.md`, or `projects.md`, whichever fits best. Create the archive file if needed.
3. Managed-auto policy:
   - Auto-offload only entries that are clearly stale, resolved, superseded, duplicated, or purely historical.
   - If classification is ambiguous, keep the entry hot and mention it in the conclude summary instead of moving it.
   - Never auto-remove the only surviving statement of an active constraint or user preference.
4. After offloading, remove or condense the migrated hot entries so the hot file returns below cap.
5. In the conclude confirmation, always report:
   - pre/post sizes for `MEMORY.md` and `USER.md`
   - which entries were moved to warm
   - which entries were moved to cold
   - any ambiguous entries intentionally kept hot

This audit is part of `/conclude`; do not skip it silently.

### Steps 2c / 2e / 2f: sessions.db, global STATUS.md, memory mirror

These three, plus the vault backup (Step 8), the reindexes (Step 8b) and the
chorus handoffs, are the **mechanical half** of this protocol. None of them needs
judgment; all of them take values you have already decided. They are executed by
one script, concurrently:

```bash
python ~/.agents/scripts/conclude-finalize.py     --agent claude --slug <project-slug>     --session-id <YYYYMMDD-project-slug>     --cwd     "<absolute project path>"     --log     "<absolute path to the session log>"     --summary "<the session log's first sentence>"     --open    "<comma-separated open threads, or 'none'>"     --next    "<one line: what the next session picks up>"     --status-md "<project STATUS.md>"     --plan      "<active plan file, if any>"     --qmd-collection      # only when the repo lives OUTSIDE the vault
```

**Start it in the background as soon as the session log and the memory files
exist** — right after Step 2d.1, not at the end. The backup and the reindexes are
the long poles and they do not depend on anything you write afterwards, so they
should run *underneath* Steps 3 through 7 rather than after them. Collect the
report before Step 6 and paste its outcome into the confirmation.

Ordering was the single largest cost in this protocol: run serially at the end,
these tasks added 8-9 minutes of pure waiting to every conclude. Run concurrently
and overlapped with the writing work, they add close to nothing.

Add `--dry-run` first if you have changed the protocol: it copies sessions.db to a
temp file, inserts against the copy, and prints every external command instead of
running it.

**Never write these by hand.** In particular, never use a `python3 - <<'PYEOF'`
heredoc: `python3` does not exist on this Windows box, and the `python` fallback
drops into the interactive REPL and hangs until timeout. That single pattern cost
two minutes on 2026-08-01. Never use the Edit tool on the global STATUS.md either
— `update-global-status.py` owns that file and preserves its hardlink.

#### When `validering` or `global STATUS.md` reports FAIL

Two of the tasks check the session's claims instead of just recording them, and
they are the only ones you must act on before finishing:

- **`global STATUS.md` exits 2** when the `--open` string names a project whose
  hub says it is parked or reference-only. Nothing was written. Either drop that
  project from the open threads, or reactivate it by setting `status: active` in
  `wiki/projects/<slug>/<slug>.md` if it really is running again. This gate
  exists because the `Open:` field is read back into *every* new session as
  OPEN ELSEWHERE — a parked project named there makes agents propose work on it.

- **`validering` fails** when the project's status contradicts itself somewhere,
  when a watched file was silently replaced with an older version, when the hub's
  `updated:` was not bumped today, or when `GOALS.md` and `goals_updated:` are
  both missing. Each problem is printed as a full sentence saying what to do.

Fix the cause, then re-run only the affected tasks — the other five have already
completed and must not run twice:

```bash
python ~/.agents/scripts/conclude-finalize.py <same arguments> --only validate,global-status
```

Neither failure is fatal by design: a session must never lose its log because a
check complained. But a conclude that ends with an unaddressed FAIL has written
something untrue into the state every later session reads.

#### Where the `--open` string should come from

For projects with a `.beads` graph, generate it instead of composing prose:

```bash
python ~/.agents/scripts/render-status.py --open <workspace>
```

It reads the actual work graph, and it returns "none (projektet ar parkerat)"
for parked projects rather than listing their stale items.

What the script does, and why each piece exists:

- **sessions.db row** — what makes `/recall --sessions` work across every agent
  and session. Deduplicates on `session_id`, so re-running is safe.
- **global STATUS.md** — the navigable cross-agent index. Session logs stay the
  authoritative record; this points at them. Keeps 3 entries per agent.
- **memory mirror** into `~/.agents/memory/<slug>/` (`sessions/`, `plans/`,
  `handoffs/`, `decisions/`, `indexes/`) — derived data only. Local project files
  remain canonical, and a failed mirror never fails the conclude or rolls back a
  local write.
- **vault backup**, **qmd**, **gbrain**, **chorus** — see Steps 8 and 8b for what
  each one guarantees.

Every task is non-fatal and reports its own status. A missing CLI or a failed
backup must never cost a session its log. Report any failures in the session log
and in the confirmation rather than retrying blindly.

### Step 3: Update STATUS.md

Open `STATUS.md` and update every section that this session's work affects:

- **"Last updated" line** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Update the date
- **Priority list** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Update priorities, reorder if needed, mark completed items
- **Open decisions** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Add new decisions as resolved, add new open decisions
- **Any status tables or trackers** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Update statuses that changed
- **Key metrics** ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â Update any numbers that changed

Do not skip sections that weren't affected ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â leave them as-is. But do check each one. A decision made this session might resolve an open item logged sessions ago.

### Step 3b: Sync Agent Configs

If CLAUDE.md or AGENTS.md was modified this session, sync the counterpart now:

```powershell
# Claude sessions — source is CLAUDE.md
& "C:\Python314\python.exe" "{{USER_HOME}}\.claude\hooks\sync-configs-hook.py" --source CLAUDE.md

# Codex sessions — source is AGENTS.md
& "C:\Python314\python.exe" "{{USER_HOME}}\.claude\hooks\sync-configs-hook.py" --source AGENTS.md
```

The script applies agent-name substitutions (`--agent claude` ↔ `--agent codex`, provider paths, titles) and writes the counterpart only if content differs. Report the one-line output (`synced` or `no diff`) in the session log.

### Step 3c: Upstream Sync Check (super-intelligence)

**Infrastructure work ALWAYS reaches the installer.** If this session changed
global agent infrastructure — skills, hooks, routers, CARL config, installer
scripts, templates, workflows — the change MUST be applied to the
super-intelligence package before the session closes. `.carl/upstream.json`
gates the *automated* sync below, but its absence never excuses shipping an
infra change that only exists on this machine. If the file is missing and infra
changed, say so explicitly and apply the change to the package by hand.

Remember the package's own trap: `install.mjs`'s `deployTemplate()`/`wf()`
**skip** writing when the destination already exists. New hooks or config that
must reach *existing* users need an explicit additive merge in both
`install.mjs` and `upgrade.mjs`, not just a file drop.

If `.carl/upstream.json` exists, audit the session for changes to **global agent
infrastructure** — anything that should reach other installs via the
super-intelligence package:

- Skills added or modified in `~/.agents/skills/`
- CARL changes: domains/rules/decisions in `~/.carl/carl.json`, or `~/.claude/hooks/carl-hook.py`
- MCP server configs, hooks, or installer-relevant templates/docs

If nothing global changed, note "upstream: no changes" in the session log and move on.

If anything changed, execute the sync now (per CONCLUDE CARL rule):

```powershell
# 1. Skills (copy new + newer; never deletes)
robocopy "{{USER_HOME}}\.agents\skills" "{{USER_HOME}}\super-intelligence\skills" /E /XO /XD node_modules .git
# 2. CARL config + hook
Copy-Item "{{USER_HOME}}\.carl\carl.json" "{{USER_HOME}}\super-intelligence\carl\carl.json" -Force
Copy-Item "{{USER_HOME}}\.claude\hooks\carl-hook.py" "{{USER_HOME}}\super-intelligence\carl\carl-hook.py" -Force
```

**Verify the copy landed — robocopy fails quietly here.** Its exit codes are a
bitfield, not a status: 0-7 are success variants and ≥8 is failure, so a shell
that treats non-zero as an error reports a working copy as broken, and a shell
that ignores the code misses a real one. On 2026-08-01 it returned 16 and copied
nothing; the miss was caught only because the files were diffed afterwards. Always
confirm with `git status` in the package repo before believing the sync happened:

```bash
cd "{{USER_HOME_FWD}}/super-intelligence" && git status --short -- skills/ hooks/
```

An empty result after a session that changed skills means the copy did **not**
happen. Fall back to `cp -r "<source>/." "<dest>/"` and check again.

Then in the super-intelligence repo: bump `VERSION` (semver — patch for skill
updates, minor for new capabilities/workflow changes), add a `CHANGELOG.md`
entry listing what was added/updated, and **commit locally**. Stage the files you
actually touched rather than `git add -A` — this repo collects unrelated drift
between sessions and a blanket add sweeps it into your commit. Present the commit
summary to the user. **NEVER push without explicit instruction.**

### Step 3d: Vault Project Hub Doc (MANDATORY for infrastructure work)

**A hub is never created alone.** Every new active project gets two files, not
one: the hub (`<repo>/<slug>.md`, the short catalogue entry) and the goals
document (`<repo>/GOALS.md`, copied from
`wiki/projects/_templates/goals-template.md`). The hub says the project exists
and how it ranks; the goals document says what it is for, what "done" means, and
which sub-goals come in what order. Agents ground their suggestions in the
second one — without it they can only guess, and a guess phrased confidently is
worse than an honest gap.

Fill what you can derive, and put everything you inferred yourself under
"Föreslaget — ej beslutat". Never invent a milestone: write "inte bestämt än"
and put the question under "Öppna frågor till {{USER_NAME}}".

`project-registrar.py` warns about active projects with no GOALS.md, and the
`validate` task in `conclude-finalize.py` checks that the file was either
updated today or consciously skipped.

Any session that changed **architecture or infrastructure** must leave behind a
current, single-document explanation of how the project works — written so an
agent or a person can orient in one read and then drill into the right file.

1. **Look for the existing hub doc first. Do not create a duplicate.** A stale
   second copy is worse than no copy, because the vault agent may read the old
   one. Search before writing:
   ```bash
   ls <repo>/<project-slug>.md                      # the conventional location
   find "<vault>/wiki" -iname "*<project-slug>*"
   grep -rl "<distinctive-term>" "<vault>/wiki/concepts" "<vault>/wiki/entities" "<vault>/wiki/sources"
   ```
   Convention: the hub doc lives at `<repo-root>/<project-slug>.md` and surfaces
   in the vault through the project junction. Frontmatter: `title`, `type: project`,
   `status`, `project_slug`, `repo`, `updated`.

2. **If it exists, update it. If not, create it.**

3. **It must contain**, at minimum:
   - What the project is, in one paragraph
   - The core mechanics / decision flow, as a scannable table or diagram
   - **A document map** — every significant project file, one line each on what it
     carries, so the reader can jump straight to what they need
   - Invariants and gotchas that bite if broken
   - How to verify the system
   - Current status and open threads

4. **Mark superseded docs as stale** in the map rather than deleting them.

Report in the conclude summary whether you found and updated an existing hub doc
or created a new one, and confirm you searched for duplicates.


### Step 4: Update Other Affected Docs

If the session changed something that lives in a doc other than STATUS.md, update it now.

If you already updated these docs during the session, verify they're current ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â don't re-update, but do confirm. If this step has no entries configured, skip it.

### Step 5: Cross-Project Handoffs

Review the cross-project implications identified in Step 1.

If any findings from this session are relevant to another project:

1. Create the `Outgoing/` directory if it doesn't exist
2. Write a handoff doc to `Outgoing/YYYY-MM-DD-to-{target-project}-{topic}.md`:

```markdown
# Cross-Project Handoff ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â {Topic}
### 2026-05-21 Destructive Action Guard
After the OneDrive/vault deletion incident, conclude must not perform automatic deletion cleanup. A hygiene sweep may list suspected temp/build artifacts, but it must not delete, trash, prune, mirror-delete, `git rm`, `git clean`, or run recursive removal. Any cleanup requires a separate exact-path deletion manifest and explicit {{USER_NAME}} approval.
**From:** [This project] session {date}
**To:** {Target project}
**Source session log:** session-logs/{session-log-filename}

## What Changed
[What happened this session]

## What It Means For {Target Project}
[Implications, new capabilities enabled, actions required]

## Actionable Items
- [Specific things the target project can/should do now]
```

3. Reference the handoff in the session log's "Cross-Project Handoffs" section
4. Tell the user: "Handoff written to Outgoing/ for {target}. Route it to {target}/Incoming/ when ready."

If no cross-project implications: skip, and note "None this session." in the log.

### Step 5b: Skill-Creation Evaluation (Hermes pattern)

Review the session. Count distinct tool calls made. If the session involved **5 or more tool
calls** completing a non-trivial, repeatable workflow (i.e., not just "read a file and answer"),
prompt the user:

> "This session used a repeatable procedure ([brief description]). Should I capture it as a
> SKILL.md for future sessions? (yes / patch existing / no)"

- **yes** â†’ call `/skill create <name>` inline before the commit in Step 7.
- **patch existing** â†’ call `/skill patch <name>` with the specific improvement.
- **no** â†’ skip.

Skills are written to `~/.agents/skills/<name>/SKILL.md` — flat, no category subdirectory.
`~/.agents/skills/` is a junction to `KB\.agents\skills\`. Commit in the KB vault root with
`-c user.email={{USER_EMAIL}} -c user.name={{USER_NAME}}`.

Only prompt if the procedure was genuinely reusable. Don’t create skills for one-off tasks.

### Step 6: Confirm With User

Present a summary of everything that was captured:

- Session log filename and location
- Key items in the log (decisions count, open threads count, files changed)
- List of docs updated beyond the session log, including the active plan file if it was created or updated
- Any handoffs written to Outgoing/
- Any open threads being carried forward
- **Shutdown status:** Note that an automatic commit will happen in Step 7 unless the user declines. State whether it is safe to shut down the conversation after the commit.
- **Suggested task name:** Based on the session's primary focus and outcomes, suggest a concise, descriptive name for the conversation/task (e.g., "API Integration & Auth Setup", "Database Schema Redesign", "Q1 Roadmap Planning Session"). Keep it specific enough to distinguish from other sessions ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â avoid generic names like "Work Session" or "Project Updates."

This is the user's chance to say "you missed X" or correct something before the session ends. If they provide corrections, update the relevant doc and confirm again.

### Step 7: Commit

After the user confirms the conclude output, stage and commit all session artifacts â€” the session log, updated plan, STATUS.md, handoff docs, and any hygiene findings that were documented (but never auto-deleted).

**Default: always commit.** Only skip if:
- The user explicitly says not to commit
- Nothing has changed (clean working tree)
- The repo is in a conflicted or broken state

Do **not** push â€” that remains a separate, explicit action.

Use a descriptive commit message following the project's commit conventions. If no conventions are configured, default to:

```
conclude: session YYYY-MM-DD
```

After committing (or deciding not to), report the final shutdown status:
- `committed` â€” artifacts saved to git, safe to close
- `not committed â€” user declined` â€” artifacts written to disk but not committed
- `not committed â€” nothing to commit` â€” working tree was already clean

### Steps 8 / 8b: Backup and reindex — already running

Both are executed by `conclude-finalize.py`, which you started in the background
back at Step 2c. **Collect its report now** and paste the outcome into the
confirmation and the session log. Do not run these commands a second time.

What each one guarantees, so a failure can be judged rather than shrugged at:

- **Vault backup** writes to three destinations every run: the git-tracked
  OneDrive mirror (restorable by commit hash via `restore-vault.ps1`), a local
  non-OneDrive mirror that survives cloud-sync incidents, and a plain copy in
  `Documents
ault-backup` outside OneDrive for the fastest restore. All three
  are append/update-only robocopy — **never** mirror-delete.
  Mid-session, `backup-vault.ps1 -Checkpoint` does a Documents-only save.
- **qmd** reindexes every collection. Note the trap it exists to avoid: a repo
  reached through a vault junction is **not** covered by the `wiki` collection,
  because qmd does not walk outward through a junction. Pass `--qmd-collection`
  for a repo outside the vault and the script creates and names its collection
  the first time. Verify with `qmd collection list`. Indexing that silently
  covers nothing is the failure mode here.
- **gbrain** picks up code, skills and agent guidance. If the project has a
  `sync-gbrain` skill wired, prefer that — it also refreshes the search guidance
  in `CLAUDE.md`.
- **chorus** hands off to the other agents. Skipped silently if the CLI is
  absent; say so rather than implying the handoff happened.

All four are **non-fatal**. An unindexed vault is recoverable; a lost session log
is not. Report failures honestly in the session log (`[index] WARNING: gbrain
sync failed — <reason>`) and never claim the vault is searchable without having
seen the task report come back clean.

### Step 9: Workspace Hygiene Sweep

After all docs are written and confirmed, do a final organizational check. This step is inspection-only unless the user explicitly approves a specific follow-up change:

- **Naming conventions:** Verify all files created this session follow the project's naming conventions (e.g., lowercase-with-hyphens, date prefixes where applicable).
- **File placement:** Check for files sitting in the wrong location ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â temp artifacts in the project root, misplaced docs, build outputs that should be cleaned up.
- **Session log filename:** Confirm it matches the convention `YYYY-MM-DD-session-log.md` (with sequence number if needed).
- **No orphaned artifacts:** Check for temp files, build outputs, or scratch artifacts created during the session that aren't needed going forward. List them explicitly and ask before any cleanup.

If the sweep finds anything, document it in the session log under "What Changed," note it to the user, and only fix it immediately if the user explicitly approves the exact change.

## Important Reminders

- **Capture everything, not just technical progress.** Organizational decisions, priority shifts, corrections to understanding, relationship context ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â if it happened in the session, it goes in the log.
- **Individual logs, not a running doc.** Each session gets its own file. This makes logs portable ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â they can be dropped into any context window for instant continuity.
- **Write for a stranger.** The session log should make sense to someone with zero context about what happened. Future sessions, different tools, or the user themselves weeks later ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â they all need to understand what this session accomplished.
- **Don't rush.** The conclude is the last thing that happens. Doing it thoroughly saves significant reconstruction time in the next session.

