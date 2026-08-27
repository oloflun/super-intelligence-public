# Gemini / Antigravity â€” Global Configuration

## Session Protocol
Every session starts with /standup — reads project-local STATUS.md first, then the mirrored latest session log in ~/.agents/memory/<project-slug>/sessions/ when available, with fallback to project-local session-logs/.

**First action at standup:** check for incoming messages from other agents and factor them into context:
```
chorus messages --agent gemini --cwd <project-path> --clear --json
```
If messages are empty and this is a recovery standup (previous session may have been interrupted),
also check the shared checkpoint file for the last known in-progress state:
```
cat "<project-path>/.agent-chorus/CHECKPOINT.md" 2>/dev/null || echo "No checkpoint."
```

**When starting a significant task block** (new feature, migration, fix spanning multiple files),
write current state to the shared checkpoint file so other agents can recover if you're interrupted:
```bash
cat > "<project-path>/.agent-chorus/CHECKPOINT.md" << 'EOF'
# Agent Checkpoint
**Agent:** gemini
**Timestamp:** $(date -u +%Y-%m-%dT%H:%M:%SZ)
**Branch:** $(git branch --show-current 2>/dev/null || echo unknown)
**Uncommitted files:** $(git status --short 2>/dev/null | wc -l | tr -d ' ')
**Current task:** [one-line description of what you are about to do]
**Files being modified:** [list key files]
**Status:** in-progress — do not overwrite without reading this
EOF
```

At ~80% context or session end: /conclude — writes the local session log, updates local STATUS.md, prepares handoff, then mirrors derived session artifacts into ~/.agents/memory/<project-slug>/ without making global memory authoritative.

**Last action before closing:** send a handoff message to each other agent AND write a Chorus-discoverable JSONL stub:
```
chorus send --from gemini --to claude --message "Session ended. Open threads: [bullet list]. Next focus: [one line]." --cwd <project-path>
chorus send --from gemini --to codex --message "Session ended. Open threads: [bullet list]. Next focus: [one line]." --cwd <project-path>
```
Then write a JSONL stub so `chorus read --agent gemini` can discover this session:
```bash
mkdir -p ~/.gemini/tmp && \
echo "{\"agent\":\"gemini\",\"session\":\"$(date +%Y-%m-%dT%H:%M:%S)\",\"cwd\":\"$(pwd)\",\"content\":\"Session concluded. See session-logs/ for full log.\"}" \
  >> ~/.gemini/tmp/$(date +%Y-%m-%d-%H-%M).jsonl
```
## Project Registry & Symlinks

> **HARD RULE — enforced for all agents (Claude, Codex, Gemini):**
> When starting or creating any new project, the FIRST action is to create a junction in the vault.
> Failure to do this means the project is invisible to Obsidian and other agents.

All active project folders are junction-linked into the Obsidian vault for universal access:
- **Vault Projects dir:** `{{VAULT_PATH}}\wiki\projects\`
- **Skills/agents dir:** `{{VAULT_PATH}}\.agents\` ← junction from `~\.agents`

**MANDATORY — when starting or creating a new project:**
```powershell
# Step 1: Create the project directory at home (if new)
# New-Item -ItemType Directory -Path "{{USER_HOME}}\<project-name>"

# Step 2: Create junction in wiki/projects (ALWAYS — even for existing projects without one)
New-Item -ItemType Junction -Path "{{VAULT_PATH}}\wiki\projects\<project-name>" -Target "{{USER_HOME}}\<project-name>"

# Step 3: Update "Current linked projects" list in CLAUDE.md
```

**Verify a junction exists before working in any project:**
```powershell
Get-Item "{{VAULT_PATH}}\wiki\projects\<project-name>" | Select-Object LinkType, Target
# Must show LinkType=Junction and Target pointing to home dir
```

Current linked projects: `example-design-system`, `example-os`, `designpowers`, `example-analysis`, `hermes-agent-self-evolution`, `hermes-onboarding`, `project-d`, `project-b`, `super-design`, `super-intelligence`, `project-c`, `project-c-next`, `wiki-ingest-daemon`

## Deployment Rules
- **NEVER push to `main` unless the user explicitly instructs it.** Default branch for all work is `development`.
- Vercel deploys automatically from every branch push â€” preview URLs are generated per branch.
- Supabase Edge Functions deploy via GitHub Actions on changes to `supabase/functions/`.
- Always confirm branch before any `git push`: `git branch --show-current`.

## Persistent Rules
- TypeScript strict mode always. No `any`, no `ts-ignore` without explanation.
- Prefer editing existing files over creating new ones.
- Show code, not explanation â€” unless asked.
- Run type-check after implementation changes.
- Vercel auto-deploys on push to main â€” no manual deployment needed.
- Supabase Edge Functions deploy via GitHub Actions on changes to `supabase/functions/`.

## Search Rule — Always Use QMD

**When the user asks to search, find, look up, check, recall, or query anything — always run `qmd query` before responding.** Never answer from memory alone. Trigger phrases: "search for", "find", "look up", "what do you know about", "have we discussed", "check if", "recall", or any variant.

## Documentation Search
Prefer `qmd query` over reading files directly.

**Available collections:** `claude-config`, `gemini-config`, `codex-config`, `agents-config`, `skills`, `user-root`, `wms`, `obsidian`

```bash
qmd query "what you're looking for"          # Best â€” hybrid + reranking
qmd search "exact term or identifier"        # Fast keyword-only
qmd query "topic" -c wms                     # Restrict to one project
```

## Cross-Agent Coordination
<!-- agent-chorus:gemini:start -->
This project is wired for cross-agent coordination via `chorus`.
Provider snippet: `.agent-chorus\providers\gemini.md`
When a user asks for another agent status (for example "What is Claude doing?"),
run Agent Chorus commands first and answer with evidence from session output.
Session routing and defaults:
1. Start with `chorus read --agent <target-agent> --cwd <project-path> --json` (omit `--id` for latest).
2. "past session" means previous session: list 2 and read the second session ID.
3. "past N sessions" means exclude latest: list N+1 and read the older N session IDs.
4. "last N sessions" means include latest: list N and read/summarize those sessions.
5. Ask for a session ID only after an initial read/list attempt fails or when exact ID is requested.
Support commands:
- `chorus list --agent <agent> --cwd <project-path> --json`
- `chorus search "<query>" --agent <agent> --cwd <project-path> --json`
- `chorus compare --source codex --source gemini --source claude --cwd <project-path> --json`
If command syntax is unclear, run `chorus --help`.
Gemini/Antigravity fallback: `chorus read --agent gemini` returns NOT_FOUND because Antigravity
stores sessions as protobuf at `~/.gemini/antigravity/conversations/`. When this happens, read the
most recently modified `.md` file in `~/.agents/memory/project-c-next/sessions/` instead.
Note: the JSONL stub written at /conclude will eventually make `chorus read --agent gemini` work.
<!-- agent-chorus:gemini:end -->

