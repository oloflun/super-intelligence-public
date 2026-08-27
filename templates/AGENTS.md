# Codex – Global Configuration

<!-- CARL-MANAGED: Do not remove this section -->
## CARL Integration
Follow all rules in <carl-rules> blocks from system-reminders.
These are dynamically injected based on context and MUST be obeyed.
<!-- END CARL-MANAGED -->

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
chorus messages --agent codex --cwd "{{VAULT_PATH}}" --clear --json
```

On recovery standup (previous session may have been interrupted), also read the shared checkpoint:
```bash
cat "<project-path>/.agent-chorus/CHECKPOINT.md" 2>/dev/null || echo "No checkpoint."
```

Last action before closing (`/conclude`): send handoffs:
```bash
chorus send --from codex --to claude --message "Session ended. Open threads: [list]. Next focus: [one line]." --cwd "{{VAULT_PATH}}"
chorus send --from codex --to gemini --message "Session ended. Open threads: [list]. Next focus: [one line]." --cwd "{{VAULT_PATH}}"
chorus send --from codex --to hermes --message "Session ended. Open threads: [list]. Next focus: [one line]." --cwd "{{VAULT_PATH}}"
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

Wired via `chorus`. Provider snippet: `.agent-chorus\providers\codex.md`

```bash
chorus read --agent <agent> --cwd "{{VAULT_PATH}}" --json
chorus list --agent <agent> --cwd "{{VAULT_PATH}}" --json
chorus search "<query>" --agent <agent> --cwd "{{VAULT_PATH}}" --json
chorus compare --source codex --source gemini --source claude --cwd "{{VAULT_PATH}}" --json
```
