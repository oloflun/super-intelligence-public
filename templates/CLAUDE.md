# Claude Code – Global Configuration

<!-- CARL-MANAGED: Do not remove this section -->
## CARL Integration
Follow all rules in <carl-rules> blocks from system-reminders.
These are dynamically injected based on context and MUST be obeyed.
<!-- END CARL-MANAGED -->

## Delegation — build with Sonnet, judge yourself

When this session runs on a top-tier model (Opus, Fable), **always do the building
work through Sonnet subagents** — the `Agent` tool with `model: sonnet` — never
through subagents on the same tier. Two things stay with you and are not delegable:

**Orchestration.** Give each subagent one bounded goal, state the invariants it
may not break, and name the check that decides whether it succeeded. Vague
delegation costs more to review than doing the work yourself would have.

**Review.** Read the files the subagent produced and run the verification. A
subagent's report is a claim, not evidence. In practice nearly every round
contains at least one defect that only surfaces on inspection: a timeout set just
below the measured runtime, a path pointing at the author's own machine, a
validation pattern that fires on the correct answer.

**Visual review is always yours.** Screenshots, rendered UI, diagrams, layout,
spacing, colour. A subagent may capture the image; judging how something *looks*
is a first-person act and never delegated.

Exceptions: trivial mechanical edits and plain conversational answers are done
directly — spinning up an agent for a one-line change is pure overhead.

## Project Registry & Symlinks

All active project folders are junction-linked into the Obsidian vault:
- **Vault Projects dir:** `{{VAULT_PATH}}\wiki\projects\`
- **Skills/agents dir:** `{{VAULT_PATH}}\.agents\` ← junction from `~\.agents`

Junction command:
```powershell
New-Item -ItemType Junction -Path "{{VAULT_PATH}}\wiki\projects\<name>" -Target "{{USER_HOME}}\<name>"
```

Verify: `Get-Item "...\wiki\projects\<name>" | Select-Object LinkType, Target` — must show `LinkType=Junction`.

Current linked projects: `example-design-system`, `example-os`, `designpowers`, `example-analysis`, `hermes-agent-self-evolution`, `hermes-onboarding`, `project-d`, `project-b`, `super-design`, `super-intelligence`, `project-c`, `project-c-next`, `wiki-ingest-daemon`

## Deployment Reference

- Vercel deploys automatically from every branch push — preview URLs are generated per branch. No manual deployment needed.
- Supabase Edge Functions deploy via GitHub Actions on changes to `supabase/functions/`.

## Automatic Updates

A daily health check runs at 09:00 (with randomized delay) that:
1. `git fetch` + `git pull --ff-only` the super-intelligence repo
2. Runs `node upgrade.mjs` to sync new skills, CARL rules, and hooks
3. Runs full health check: package, installation, MCP servers, CARL integrity
4. Logs to `~/.super-intelligence/update.log`

**Config:** `~/.super-intelligence/config.json` — set `auto_update: false` to disable.
**Manual run:** `bash ~/super-intelligence/scripts/auto-update.sh` (or `.ps1` on Windows).
**Health check only:** `node ~/super-intelligence/scripts/health-check.mjs --installed`

## Session Protocol

| Skill | When | What it does |
|---|---|---|
| `STATUS.md` | Session start (auto) | Last 3 sessions per agent across all projects — auto-injected by carl-hook on fresh sessions |
| `/standup` | Session start, manually | Project-scoped context load (STATUS.md + last session log + global memory). Never auto-fires globally. |
| `/conclude` | Session end / ~80% context | Session log, memory nudges, sessions.db row, chorus handoffs, skill-creation eval. |
| `/recall <query>` | Anytime | Unified search: QMD wiki/raw, sessions.db FTS5, CARL decisions, chorus. |
| `/ingest` | After export pipeline deposits files | Convert raw conversations → wiki pages, update index/log, reindex QMD. |
| `/skill` | After complex tasks / on demand | Create, patch, view, list, evolve skills in `~/.agents/skills/`. |

### Standup procedure

First action: check incoming messages from other agents:
```bash
chorus messages --agent claude --cwd "{{VAULT_PATH}}" --clear --json
```

On recovery standup (previous session may have been interrupted), also read the shared checkpoint:
```bash
cat "<project-path>/.agent-chorus/CHECKPOINT.md" 2>/dev/null || echo "No checkpoint."
```

Last action before closing (`/conclude`): send handoffs:
```bash
chorus send --from claude --to codex --message "Session ended. Open threads: [list]. Next focus: [one line]." --cwd "{{VAULT_PATH}}"
chorus send --from claude --to gemini --message "Session ended. Open threads: [list]. Next focus: [one line]." --cwd "{{VAULT_PATH}}"
chorus send --from claude --to hermes --message "Session ended. Open threads: [list]. Next focus: [one line]." --cwd "{{VAULT_PATH}}"
```

### Memory Topology

```
canonical:  ~/OneDrive/Dokument/Obsidian/Knowledge Base/memory/{MEMORY.md, USER.md, sessions.db}
            ~/OneDrive/Dokument/Obsidian/Knowledge Base/STATUS.md  ← global cross-agent status (hardlinked ~/STATUS.md)
mirror:     ~/.agents/memory/<project-slug>/
local:      <repo>/STATUS.md + session-logs/
```

Only `/conclude` writes to canonical memory. Only `/standup` reads it. Never write mid-session.

### Memory Tiers

| Tier | File | Cap | Load | Purpose |
|------|------|-----|------|---------|
| Hot | `memory/MEMORY.md` | 2,200 chars | Every standup | Blocking facts — active quirks, open threads, system paths |
| Hot | `memory/USER.md` | 1,375 chars | Every standup | Active user preferences |
| Warm | `memory/MEMORY-FULL.md` | Unbounded | On demand | Episodic knowledge, dated session blocks |
| Warm | `memory/USER-FULL.md` | Unbounded | On demand | Full user profile history |
| Cold | `memory/archive/*.md` | Unbounded | QMD only | Resolved facts, stable reference, old decisions |

Cold archive categories: `dev-tools.md` · `infrastructure.md` · `incidents.md` · `projects.md`

Retrieval from cold: `qmd query "<topic>"` or `/recall <topic>`. Never load archive files directly.

## QMD Reference

Collections: `wiki`, `conversations`, `articles`, `claude-config`, `gemini-config`, `codex-config`, `agents-config`, `skills`, `user-root`, `wms`, `obsidian`

```bash
qmd query "topic"              # hybrid + reranking across all collections
qmd query "topic" -c wiki      # restrict to wiki
qmd search "exact term"        # fast keyword-only
qmd update                     # reindex after writing new vault files
```

Use `mcp__qmd__query` when MCP is available. `/recall` for multi-source dives (wiki + sessions.db + CARL + chorus).

## Cross-Agent Coordination

Wired via `chorus`. Provider snippet: `.agent-chorus\providers\claude.md`

```bash
chorus read --agent <agent> --cwd "{{VAULT_PATH}}" --json
chorus list --agent <agent> --cwd "{{VAULT_PATH}}" --json
chorus search "<query>" --agent <agent> --cwd "{{VAULT_PATH}}" --json
chorus compare --source codex --source gemini --source claude --cwd "{{VAULT_PATH}}" --json
```
