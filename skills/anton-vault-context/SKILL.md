---
name: anton-vault-context
description: "Fires on any question about Anton's own projects, status, priorities, history or next steps — 'vad ligger öppet', 'hur går det med X', 'vad gjorde vi senast', 'vad ska jag prioritera', 'status', 'sammanfatta läget', 'var lämnade vi', 'what's open', 'where did we leave off', 'what should I work on'. Also fires before answering any broad question whose answer depends on knowing Anton's current situation across projects. Establishes WHERE to look and IN WHAT ORDER, so answers are grounded in the vault instead of guessed. Does NOT fire for general knowledge questions unrelated to Anton's work, or for pure code questions inside a single repo where the repo itself is the source."
---

# Anton's vault context

The knowledge base is the private repo `oloflun/anton-vault`, branch `vault-main`.
In chat and on any surface without a local filesystem, read it through the GitHub
connector. On Anton's own machine and in Cowork it is on disk at
`~/OneDrive/Dokument/Obsidian/Knowledge Base/`, and local reads are faster —
prefer disk when it exists, the paths below are identical either way.

## The one rule that matters: survey only when the target is unknown

Anton's instruction (2026-08-30): go vault-first on **broad** questions, and go
**straight to the source** when he has already named it. Both failure modes are
real — answering a broad question without looking costs him a wrong answer, and
surveying the portfolio when he asked for one specific document wastes his time
and buries the thing he asked for.

**Broad question** — "vad ligger öppet", "vad ska jag prioritera", "hur går det",
"sammanfatta läget", or any business/strategy question where his actual situation
changes the answer. Read in this order, and stop as soon as you can answer:

1. `wiki/projects/_index/portfolio.md` — every project, status and weight, in one
   file. This is the cheapest way to know what exists and what is parked.
2. `wiki/projects/<slug>/<slug>.md` — the hub for each project that turned out to
   be relevant. Frontmatter carries `goal`, `next_milestone`, `milestone_blockers`,
   `status` and `updated`. A hub whose `updated` is old is a warning, not a fact.
3. The most recent session log for those projects:
   `.agents/memory/<slug>/sessions/<YYYY-MM-DD>-session-log.md` (mirrors of every
   project's own logs, so they are reachable without cloning each repo). Read the
   `## Open Threads` and `## Current State` sections first — that is where the
   live work is. The vault's own logs are in `session-logs/`.
4. `memory/MEMORY.md`, `memory/USER.md`, `memory/BLOCKS.md` — environment facts,
   his preferences, and why work was parked. `BLOCKS.md` is the one that explains
   *why* something is not being worked on; check it before proposing that he
   start something that was deliberately stopped.

**Named target** — "gräv i senaste sessionen", "läs X-dokumentet", "vad står i
planen för Y", "djupdyk i hubben för <projekt>". Go directly to that file. Do
**not** run the survey first. If the exact filename is unclear, list the one
directory it must be in rather than walking the tree from the top.

## Parked projects

A hub whose frontmatter `status:` is anything other than `active` is not
available work, no matter how interesting its open threads look. Never present
such a project as something to pick up; say plainly that it is parked if it comes
up. The portfolio index carries the same status field, so one read is enough to
know which projects are eligible before proposing any work at all.

## Handing a plan from chat to a Claude Code cloud session

When a plan has been worked out in chat and Anton wants it executed, do not
retype it into a session prompt — the prompt is ephemeral and the plan is worth
keeping. Instead:

1. **Write the plan into the vault** via the GitHub connector:
   `plans/<YYYY-MM-DD>-<slug>.md`, using the structure in the `conclude` skill's
   plan template (Scope / Completed / In Progress / Remaining / Deferred /
   Blockers / Next Steps). Everything the next agent needs to act without asking
   Anton anything goes in this file — repo, branch, acceptance check, and what it
   must not touch.
2. **Start the cloud session** through the Claude Code Remote connector, with the
   relevant project repo *and* `oloflun/anton-vault` attached as sources, and a
   short prompt that points at the file rather than restating it: *"Läs
   `plans/<file>` i anton-vault. Den är skriven av Anton och är din uppgift.
   Genomför den och rapportera utfallet."*
3. **State the branch and the push rule in the prompt.** Never push to `main`
   without Anton saying so; work on the project's own default branch.

The plan file being a real artifact is the point: it survives the session, Anton
can read and correct it before it runs, and a failed run can be resumed from it.

## What this skill does not do

It does not decide business questions — for those, load the foreman framework
first and then `Skill(business-principles-integration)`, per those skills' own
load order. This skill only establishes where the facts live.
