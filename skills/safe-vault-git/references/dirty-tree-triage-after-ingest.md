# Dirty-tree triage after ingest

Use this when Anton asks which files still need attention after an ingest run or ingest audit.

## Core lesson

Do not report the plain `ingest-pending.sh` output as the true ingest backlog by itself.
In Anton's vault, that queue can include broad markdown/untracked noise such as:
- `plans/*.md`
- `AGENTS*.md`
- sync-conflict copies
- agent/provider docs
- other repo markdown that is discoverable but not unresolved ingest work

## Preferred sequence

1. Run `graph-stray-audit` first for the authoritative unresolved count.
2. Run `ingest-pending.sh --strays` to see the focused actionable queue.
3. Use plain `ingest-pending.sh` only as a secondary discovery signal.
4. Then classify remaining Git dirt separately from ingest backlog.

## Interpretation rule

If broad pending discovery and stray audit disagree:
- treat the stray-audit unresolved count as the real ingest backlog
- describe the broad pending queue as noisy discovery output

## Recommended classification buckets

After the ingest-specific queue is known, group repo dirt into:
- real ingest backlog
- duplicate-delete candidates awaiting confirmation
- duplicate-merge candidates requiring synthesis
- sync-conflict noise
- operational state/log churn (`.agent-chorus/messages`, `.carl/sessions`, mirrors)
- local Obsidian state (`.obsidian/workspace.json`, plugin data)
- meaningful scripts/config/wiki/skill changes for review or commit
- task-specific validation/probe artifacts

## Session example captured

Observed pattern:
- normal pending discovery surfaced a long list including `AGENTS.md`, plans, conflict copies, and raw files
- `graph-stray-audit --dry-run` reduced that to 4 true unresolved candidates
- therefore the right user-facing statement was: actual ingest attention needed = 4 sources

## Bridge-artifact isolation reminder

When the task also involves validation/probe files, isolate those explicitly from the rest of the dirty tree instead of implying all untracked files belong to the validation task.
