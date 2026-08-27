# Super-Intelligence Agent Stack — Architecture

## Overview

The Super-Intelligence Agent Stack is a filesystem-first multi-agent AI infrastructure. It enables multiple AI agents (Claude Code, Codex, Gemini, Hermes/WSL) to share context, skills, memory, and rules through a common Obsidian vault bridged by Syncthing.

### Core Design Principles

1. **Filesystem-first** — Everything is a file. No databases except sessions.db (SQLite FTS5 for search). No running services except Syncthing and optional chorus relay.
2. **CARL is canonical** — All behavioral rules live in `.carl/carl.json`. Agent configs (CLAUDE.md, AGENTS.md) are reference-only.
3. **Write at /conclude, read at /standup** — Memory writes happen only at session end. Memory reads happen only at session start. No mid-session memory mutation.
4. **Junctions over copies** — Windows NTFS junctions and Linux symlinks ensure all agents read/write the same files.
5. **Non-destructive by default** — Backups, syncs, and restores are append/update-only. No mirror-delete operations.

---

## Component Deep Dives

### 1. CARL — Context Augmentation & Reinforcement Layer

**Location:** `.carl/carl.json` (canonical), `~/.claude/hooks/carl-hook.py` (injector)

CARL is a UserPromptSubmit hook that reads the current conversation context and injects relevant rules before the agent processes the prompt.

**How it works:**
1. On every user prompt, `carl-hook.py` receives JSON via stdin with the prompt text, session ID, and context window state
2. It calculates context bracket (FRESH >70%, MODERATE 40-70%, DEPLETED 15-40%, CRITICAL <15%)
3. It matches the prompt against domain recall keywords
4. Always-on domains (GLOBAL) are always loaded
5. Matched domains are loaded based on keyword hits
6. Context deduplication: if the same domain set was injected recently, a short `<carl-status dedup>` tag replaces the full injection
7. On FRESH sessions, `STATUS.md` is auto-injected as `<global-status>`

**Domain structure in carl.json:**
```json
{
  "domains": {
    "GLOBAL": {
      "state": "active",
      "always_on": true,
      "recall": ["universal"],
      "rules": [{ "id": 0, "text": "rule text", "source": "manual" }],
      "decisions": [{ "id": "id", "decision": "text", "rationale": "why" }]
    }
  }
}
```

**Context brackets:**
- FRESH: Full injection + STATUS.md
- MODERATE: Rules to keep focused, avoid exploration
- DEPLETED: Minimize tool calls, batch aggressively, suggest /compact
- CRITICAL: Recommend compact or fresh agent

### 2. Agent Configs (CLAUDE.md / AGENTS.md / GEMINI.md)

**Location:** `~/CLAUDE.md`, `~/AGENTS.md`, `~/GEMINI.md`

Pure reference files. No behavioral rules (those are in CARL). They contain:
- CARL integration notice
- Project registry & junction instructions
- Session protocol table (standup, conclude, recall, ingest, skill)
- Memory topology and tier documentation
- QMD reference (collections, commands)
- Cross-agent chorus coordination commands

**Sync:** `sync-configs-hook.py` keeps CLAUDE.md ↔ AGENTS.md in sync with 6 substitution pairs (agent name, provider path, chorus --agent flag). Runs at /conclude if either file was modified.

### 3. Skills System

**Location:** `~/.agents/skills/` (172 modules, junctioned from vault)

Each skill is a directory with a `SKILL.md` file containing YAML frontmatter (name, description) and markdown instructions. The agent loads skills via `/skill <name>`, which injects the SKILL.md content as context.

**Core skills:**
- `conclude` — Session end protocol (8 steps: audit, log, memory, sessions.db, STATUS.md, handoffs, commit, backup)
- `ingest` — Convert raw conversations → wiki pages, update index, reindex QMD
- `recall` — Unified search (QMD + sessions.db FTS5 + CARL decisions + chorus)
- `standup` — Project-scoped context load at session start
- `safe-vault-git` — Non-destructive vault git operations

**Category distribution:**
- Design: 20+ skills (design-md, extract-design, emil-design-eng, shadcn-ui, etc.)
- Marketing: 25+ skills (ads, seo, cold-email, ab-testing, cro, etc.)
- Development: 15+ skills (next-best-practices, deploy-to-vercel, react-components, etc.)
- Infrastructure: 10+ skills (agent-browser, obsidian-bases, json-canvas, etc.)
- Operations: sync-agent-configs, search-memory, learned, recall, etc.

### 4. Memory System

**Location:** `{{VAULT_PATH}}/memory/`

Three-tier memory with strict capacity management:

| Tier | Files | Cap | When Loaded | Purpose |
|---|---|---|---|---|
| **Hot** | MEMORY.md | 2,200 chars | Every /standup | Active constraints, environment facts, open threads |
| **Hot** | USER.md | 1,375 chars | Every /standup | Active user preferences |
| **Warm** | MEMORY-FULL.md | Unbounded | On demand | Episodic knowledge, dated session blocks |
| **Warm** | USER-FULL.md | Unbounded | On demand | Full user profile history |
| **Cold** | archive/*.md | Unbounded | QMD only | Resolved facts, stable reference |

**sessions.db:** SQLite database with FTS5 full-text search. One row per concluded session (agent, cwd, timestamp, summary, log path). Powers `/recall --sessions`.

**Audit & offload:** At /conclude, if hot files exceed 80% capacity, entries are classified and moved to warm or cold tiers. Ambiguous entries stay hot.

### 5. Agent Chorus

**Location:** `.agent-chorus/` (in vault)

Cross-agent coordination via JSONL message inboxes. Each agent has a dedicated inbox file.

**Message flow:**
```
Claude concludes → chorus send → messages/codex.jsonl
                                 → messages/gemini.jsonl
                                 → messages/hermes.jsonl

Codex starts → chorus messages --agent codex → reads inbox → clears
```

**Provider contracts:** `.agent-chorus/providers/<agent>.md` — each agent's coordination interface.

**Checkpoint:** `.agent-chorus/CHECKPOINT.md` — shared recovery checkpoint. Any agent writes current state before a significant task block.

**Relay:** Optional relay for async message delivery. Configured via `relay-config.json`.

**CLI:** Rust binary (`chorus`) for send/read/list/search/compare operations.

### 6. QMD — Query My Documents

**Location:** npm package `@tobilu/qmd`

Hybrid semantic + keyword search engine with SQLite-backed index. Configured via `.qmd.yaml` in the vault root.

**Collections:** wiki, conversations, articles, claude-config, agents-config, skills, obsidian

**Usage:**
- `qmd query "topic"` — hybrid search with reranking
- `qmd query "topic" -c wiki` — restrict to collection
- `qmd search "exact term"` — fast keyword-only
- `qmd update` — reindex after writing new vault files

**Wrapper scripts:** `qmd-win.ps1` (Windows), `qmd` (Linux) set environment variables and invoke the npm global binary.

### 7. STATUS.md — Cross-Agent Session Index

**Location:** `{{VAULT_PATH}}/STATUS.md` (hardlinked to `~/STATUS.md`)

Maintained by `update-global-status.py`. Each agent section holds the 3 most recent sessions (newest first).

**Format:**
```markdown
## Claude
- [2026-05-25] global-config — Migrated rules to CARL. Open: DESIGN FP → session-log.md
```

**Injection:** `carl-hook.py` reads `~/STATUS.md` and injects it as `<global-status>` on FRESH sessions.

### 8. Syncthing Bridge

**Purpose:** Bidirectional sync between Windows vault and WSL `~/vault-local/`

**Configuration:** `.stignore` for exclusion rules (node_modules, .git internals, workspace files)

**Startup:** `syncthing-boot.cmd` (Windows) or systemd service (Linux)

### 9. Hermes / WSL

**Agent type:** Linux-based AI agent running in WSL2

**Setup:**
- `~/.carl` → symlink to `~/vault-local/.carl`
- `~/.agents` → symlink to `~/vault-local/.agents`
- `~/STATUS.md` → symlink to `~/vault-local/STATUS.md`
- CARL hook auto-detects Linux and force-loads HERMES domain

**HERMES domain rules:** Platform-gated. Contains Hermes-specific paths (python3, ~/vault-local/, qmd-hermes), relay inbox check, chorus message path.

### 10. Auto-Export Pipeline

**Flow:**
```
Browser (Claude.ai / ChatGPT / Gemini)
    ↓ Tampermonkey auto-exports on navigation
Downloaded .md file
    ↓ watch-and-route-v2.sh (polls every 5s)
raw/conversations/{platform}/
    ↓ git commit (auto)
    ↓ /ingest (manual or scheduled)
wiki/sources/ + entity/concept/project pages
```

### 11. Karpathy Wiki

Andrej Karpathy's LLM wiki methodology: treat your AI knowledge base like a personal wiki. Each conversation becomes a wiki page. Entities, concepts, and projects are linked. The wiki grows organically through /ingest.

**Setup:** See `karpathy/wiki-setup.md` for the full guide adapted for this stack.

### 12. Backup System

**Script:** `backup-vault.ps1` — runs at /conclude

**Two mirrors:**
1. OneDrive mirror (git-tracked, restorable by commit hash)
2. Local mirror (survives cloud sync incidents)

**Safety:** Append/update-only robocopy. No mirror-delete flags. No rsync --delete.

---

## File Topology

```
~ (home directory)
├── CLAUDE.md                    # Agent config (reference only)
├── AGENTS.md                    # Codex variant (synced from CLAUDE.md)
├── GEMINI.md                    # Gemini variant
├── STATUS.md                    # Hardlink → vault/STATUS.md
├── .carl/                       # Junction → vault/.carl
├── .agents/                     # Junction → vault/.agents
├── .agent-chorus/               # Junction → vault/.agent-chorus
├── .claude/
│   ├── settings.json            # Claude Code settings (hooks, plugins)
│   ├── hooks/
│   │   ├── carl-hook.py         # CARL injector (UserPromptSubmit)
│   │   └── sync-configs-hook.py # CLAUDE.md ↔ AGENTS.md sync
│   ├── skills/                  # Symlink → .agents/skills
│   └── plugins/                 # Plugin cache
├── .codex/
│   ├── config.toml              # Codex settings
│   └── skills/                  # Codex skill cache
├── session-logs/                # Local session logs
└── <project>/                   # Individual project repos

{{VAULT_PATH}} (Obsidian vault)
├── .carl/
│   ├── carl.json                # Canonical CARL configuration
│   └── sessions/                # Session state files
├── .agents/
│   ├── skills/                  # 172 skill modules
│   ├── scripts/                 # Utility scripts
│   └── memory/                  # Memory mirrors per project
├── .agent-chorus/
│   ├── messages/                # Agent inboxes (JSONL)
│   ├── providers/               # Provider contracts
│   ├── relay-config.json        # Relay configuration
│   └── CHECKPOINT.md            # Shared recovery checkpoint
├── memory/
│   ├── MEMORY.md                # Hot memory (2,200 char cap)
│   ├── USER.md                  # Hot user profile (1,375 char cap)
│   ├── MEMORY-FULL.md           # Warm episodic memory
│   ├── USER-FULL.md             # Warm user history
│   ├── sessions.db              # FTS5 session index
│   └── archive/                 # Cold storage
├── STATUS.md                    # Cross-agent session index
├── .qmd.yaml                    # QMD configuration
├── .stignore                    # Syncthing exclusion rules
├── scripts/
│   └── backup-vault.ps1         # Vault backup script
├── wiki/                        # Wiki pages
├── raw/                         # Raw conversation exports
└── wiki/projects/               # Project junctions
```

---

## Session Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                   SESSION START                          │
│                                                         │
│  1. carl-hook.py fires on UserPromptSubmit              │
│  2. Context bracket calculated (FRESH/MODERATE/...)     │
│  3. GLOBAL domain loaded (always_on)                    │
│  4. Prompt matched against domain recall keywords       │
│  5. Matched domains injected as <carl-rules>            │
│  6. STATUS.md injected on FRESH sessions                │
│  7. Agent reads chorus messages (standup procedure)     │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   SESSION BODY                           │
│                                                         │
│  - CARL rules guide all behavior                        │
│  - /skill loads specialized workflows                   │
│  - /recall searches vault + sessions.db + CARL          │
│  - Checkpoints written before significant tasks         │
│  - No memory writes during session                      │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                   SESSION END (/conclude)                │
│                                                         │
│  1. Session audit (files created/modified/deleted)      │
│  2. Write session log (session-logs/YYYY-MM-DD.md)      │
│  3. Update active plan                                  │
│  4. Memory nudges (MEMORY.md, USER.md)                  │
│  5. Hot-memory audit & offload                          │
│  6. Write sessions.db row                               │
│  7. Update global STATUS.md                             │
│  8. Mirror to global memory                             │
│  9. Sync agent configs (CLAUDE.md ↔ AGENTS.md)         │
│ 10. Cross-project handoffs                              │
│ 11. Skill-creation evaluation                           │
│ 12. Git commit                                          │
│ 13. Vault backup                                        │
│ 14. Chorus handoff messages                             │
│ 15. Workspace hygiene sweep                             │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Security & Privacy

- **No credentials in the package** — All `.env`, `auth.json`, `credentials.json` are gitignored
- **Personal paths replaced** — Templates use `{{USER_HOME}}`, `{{VAULT_PATH}}` placeholders
- **Memory isolation** — Personal memory (MEMORY.md, USER.md, sessions.db) is never committed
- **Backup safety** — Append-only, no destructive mirror operations
- **CARL decisions** — Historical decisions reference "the user" not personal names
