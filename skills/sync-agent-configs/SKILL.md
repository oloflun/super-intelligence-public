---
name: sync-agent-configs
description: Keep CLAUDE.md and AGENTS.md in sync so Claude and Codex operate under identical rules, differing only in agent-specific identifiers. Use when either config changes, or when the two have drifted apart.
---

# sync-agent-configs

Keeps `CLAUDE.md` (Claude's config) and `AGENTS.md` (Codex's config) in sync so both agents operate with identical rules, reference, and procedures — differing only in agent-specific identifiers.

CARL rules are already shared via `carl.json` (both agents use the same MCP). This skill syncs the reference and procedure sections of the config files.

## Source of truth

**`CLAUDE.md` is canonical.** `AGENTS.md` is derived from it with substitutions applied.

## Files

| File | Agent | Path |
|------|-------|------|
| `CLAUDE.md` | Claude | `{{USER_HOME}}\CLAUDE.md` |
| `AGENTS.md` | Codex | `{{USER_HOME}}\AGENTS.md` |

## Sections

### Shared — copy verbatim
These sections should be byte-for-byte identical (after substitution) in both files:
- `## Project Registry & Symlinks`
- `## Deployment Reference`
- `## QMD Reference`
- Memory Topology block
- Memory Tiers table

### Agent-substituted — apply transformation rules
| CLAUDE.md token | AGENTS.md token |
|-----------------|-----------------|
| `--agent claude` | `--agent codex` |
| `--from claude` | `--from codex` |
| `providers\claude.md` | `providers\codex.md` |
| `chorus messages --agent claude` | `chorus messages --agent codex` |
| `# Claude Code` (title) | `# Codex` (title) |
| `<!-- agent-chorus:claude:` | `<!-- agent-chorus:codex:` |

Affected sections:
- `## Cross-Agent Coordination` (provider snippet path, agent name)
- `## Session Protocol` (standup/conclude chorus commands)

### Codex-only — preserve, do not overwrite
AGENTS.md may have Codex-specific content that has no Claude equivalent. Do not remove these.

## Execution steps

1. Read `CLAUDE.md` fully.
2. Read `AGENTS.md` fully.
3. Parse both into named sections (split on `## ` headings).
4. For each section in CLAUDE.md:
   a. Apply substitution rules to get the Codex version.
   b. Compare against the equivalent section in AGENTS.md (if it exists).
   c. If missing or different: update AGENTS.md with the substituted version.
5. For sections in AGENTS.md not present in CLAUDE.md: leave them untouched (Codex-specific).
6. Check CARL domains: run `carl_v2_list_domains` and confirm both agents share the same carl.json (they do if both are rooted at `{{USER_HOME}}\.carl\`). No sync needed for CARL — it's already shared.
7. Report: list every section that was updated, and every section left untouched (with reason).

## What to check beyond file content

- Both agents use the same skills dir (`{{USER_HOME}}\.agents\skills\`) — verify junction exists.
- If a new CARL domain was added since the last sync, confirm AGENTS.md has no redundant hard-coded version of that rule (it should be removed since CARL injects it).
- If a new section appears in AGENTS.md that isn't in CLAUDE.md and isn't agent-specific, promote it to CLAUDE.md and re-derive for AGENTS.md.

## Automation

Sync runs automatically at `/conclude` via `sync-configs-hook.py`. Manual invocation of this skill is only needed for:
- A forced full re-sync after a large structural change to the shared sections
- Diagnosing a suspected drift between the files mid-session

## After syncing

Tell the user:
- Which sections were updated in AGENTS.md
- Which sections were left untouched (and why)
- Whether any content in AGENTS.md looks like it should be promoted to CLAUDE.md instead
- Any CARL rules that are now redundant as hard-coded text in either file
