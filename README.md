<p align="center">
  <h1 align="center">🧠 Super-Intelligence Agent Stack</h1>
  <p align="center"><strong>One command to install a complete multi-agent AI infrastructure.</strong></p>
  <p align="center">
    <a href="#install">Install</a> ·
    <a href="#what-you-get">Components</a> ·
    <a href="#architecture">Architecture</a> ·
    <a href="#quick-start">Quick Start</a> ·
    <a href="#upgrade">Upgrade</a> ·
    <a href="docs/ARCHITECTURE.md">Docs</a>
  </p>
</p>

---

## What Is This?

A **complete, installable AI agent infrastructure** that an AI agent (Claude Code, Codex, Gemini, or any coding agent) can set up in one shot. It wires together:

- **CARL** — Context-aware rule injection (the right rules load automatically based on what you're doing)
- **213 skills** — Reusable `/skill` modules for design, development, marketing, SEO, and system operations
- **Memory system** — Tiered hot/warm/cold memory with FTS5 search that persists across sessions
- **Agent Chorus** — Cross-agent messaging so Claude, Codex, Gemini, and Hermes can hand off tasks
- **QMD search** — Hybrid semantic + keyword search across your entire Obsidian vault
- **Cross-agent STATUS** — Every agent sees what every other agent did recently

And optional extras: Hermes/WSL agent, Syncthing vault bridge, auto-export pipeline, Karpathy wiki methodology, vault backup, DeepSeek backend via claudeep, and clipboard vision for text-only models.

**2,326 files. No personal data, no credentials — enforced by a test that runs on every commit (see [Health](#health)). MIT licensed.**

---

## How It Works

```
You clone this repo.
You tell your AI agent: "Run node install.mjs"
The agent installs everything in one shot.
Your next agent session auto-loads all the rules, skills, and memory.
```

The installer is **interactive** (asks about each component) or **non-interactive** (your agent passes flags). It detects Windows/macOS/Linux, creates all directories and filesystem links, deploys configurations, and initializes the memory database.

---

## <a name="install"></a>Install

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **Git**
- **Obsidian** (for the vault — or any markdown vault)

Optional: WSL2 (for Hermes), Rust/Cargo (for building chorus CLI), Syncthing (for multi-machine sync).

### One Command (Agent-Driven)

Tell your AI agent:

```
Clone https://github.com/oloflun/super-intelligence.git,
cd into it, and run: node install.mjs --yes
```

The `--yes` flag accepts all defaults. For interactive mode (you answer prompts), omit `--yes`.

### Manual Install

```bash
git clone https://github.com/oloflun/super-intelligence.git
cd super-intelligence
node install.mjs
```

The installer asks:
1. Which agent are you? (claude / codex / gemini / hermes)
2. Where is your Obsidian vault?
3. New or existing wiki structure?
4. Which components do you want? (Hermes? Chorus? Syncthing? etc.)
5. Your git username and email for vault commits.

Then it installs everything.

### Presets

Skip the prompts with a preset:

```bash
node install.mjs --preset claude-windows --vault ~/vault --yes
node install.mjs --preset hermes-wsl --vault ~/vault-local --yes
node install.mjs --preset minimal --agent claude --vault ~/vault --yes
```

| Preset | Agent | Hermes | Chorus | Syncthing | Export | QMD | Backup |
|---|---|---|---|---|---|---|---|
| `claude-windows` | Claude | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `codex-windows` | Codex | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `claude-mac` | Claude | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `claude-linux` | Claude | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `hermes-wsl` | Hermes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `minimal` | Claude | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| `full` | Claude | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### Component Flags

Toggle individual components:

```bash
node install.mjs --no-hermes --no-chorus --no-syncthing --yes
```

| Flag | Effect |
|---|---|
| `--no-hermes` | Skip Hermes/WSL agent setup |
| `--no-chorus` | Skip cross-agent messaging |
| `--no-syncthing` | Skip Syncthing bridge config |
| `--no-auto-export` | Skip browser auto-export pipeline |
| `--no-karpathy` | Skip Karpathy wiki methodology |
| `--no-qmd` | Skip QMD search engine |
| `--no-backup` | Skip vault backup scripts |

### Plugin install (the other path)

Everything in `skills/` and `hooks/` is also installable as a native Claude Code
plugin — a second, independent way to get the same content, for people who want
skills and hooks without the full OS-level integration (junctions, npm globals,
vault wiring) that `install.mjs` sets up.

```
/plugin marketplace add oloflun/super-intelligence-public
/plugin install super-intelligence@super-intelligence
```

`plugin.json` carries no `version` field on purpose, so Claude Code tracks the
plugin by git commit SHA — every push to this repo is what "installed" means on
your next session, no manual update step.

**If you already ran `node install.mjs` on this machine** (this is the normal
case for anyone who set this stack up before the plugin existed), installing
the plugin on top would otherwise register every hook a second time — CARL,
brief-context, the design/marketing gates, chorus — each firing twice per
event. The plugin's first `SessionStart` after install runs
`hooks/plugin-sync.py`, which detects and removes exactly those legacy
duplicate registrations from `~/.claude/settings.json` (one-time backup to
`settings.json.pre-plugin-sync.bak` before the first edit) and syncs the
plugin's own `skills/` into `~/.agents/skills/` — additive only, it never
deletes a hand-authored skill. This runs automatically; nothing to do by hand.
On every ordinary session after that it's a single path comparison, no-op.

---

## <a name="what-you-get"></a>What You Get

### CARL — Context Augmentation & Reinforcement Layer

A UserPromptSubmit hook that injects the right rules based on context. On every prompt, CARL reads your message, matches it against 8 domains, and injects relevant rules before the agent responds.

```
You: "fix this bug in the auth flow"
CARL: → loads DEVELOPMENT domain (7 coding rules)
      → loads GLOBAL domain (8 always-on rules)
      → injects STATUS.md (if fresh session)

Agent: operates with all 15 rules active
```

**8 domains:**

| Domain | When It Loads | Rules |
|---|---|---|
| GLOBAL | Always | Paths, parallelism, validation, errors, git, code style, workflow |
| DEVELOPMENT | Coding keywords | TypeScript strict, type-check, checkpoints, Karpathy guidelines |
| PROJECT | New project keywords | Vault junction first |
| SEARCH | Search/lookup keywords | 3-tool search combo, reindex after writes |
| AGENTS | Chorus/agent keywords | Global cwd, chorus-first, Gemini fallback |
| DESIGN | Design/UI keywords | /design master router |
| CONCLUDE | Session-end keywords | Evaluate CARL rules during conclude |
| HERMES | Linux only (auto) | Hermes-specific paths and routines |

### Skills — 213 Reusable Modules

Every skill is a directory with a `SKILL.md` that gets injected as context when you run `/skill <name>`.

**Core session management:**
`conclude` · `ingest` · `recall` · `standup` · `safe-vault-git`

**Design & frontend (27):**
`design` · `design-md` · `shadcn-ui` · `react-components` · `animated-navigation` · `slideshow` · `image-to-code` · `brandkit` · `polish` · `stitch-design` · `stitch-loop` · and more

**Development (15):**
`next-best-practices` · `deploy-to-vercel` · `payload-cms-setup` · `remotion` · `defuddle` · `json-canvas` · `enhance-prompt` · `contributing-to-fork` · and more

**Marketing & SEO (36):**
`ads` · `ai-seo` · `cold-email` · `cro` · `ab-testing` · `customer-research` · `landing-page` · `lead-magnets` · `pricing` · and more

**Source commands (44):**
`source-command-cpp-build` · `source-command-go-review` · `source-command-kotlin-test` · `source-command-rust-build` · `source-command-python-review` · and more

### Memory System

Three-tier memory with strict capacity management. Write only at session end, read only at session start.

```
Hot (loaded every /standup)
├── MEMORY.md     ← 2,200 char cap — active constraints, environment facts
└── USER.md       ← 1,375 char cap — active user preferences

Warm (loaded on demand via /recall)
├── MEMORY-FULL.md ← unbounded — episodic knowledge, dated session blocks
└── USER-FULL.md   ← unbounded — full user profile history

Cold (QMD search only)
└── archive/
    ├── dev-tools.md
    ├── infrastructure.md
    ├── incidents.md
    └── projects.md

Index
└── sessions.db   ← SQLite FTS5 — every concluded session, full-text searchable
```

**Automatic offload:** At `/conclude`, if hot files exceed 80% capacity, entries are classified (keep hot / move warm / move cold) and migrated. Ambiguous entries stay hot.

### Agent Chorus — Cross-Agent Coordination

```
Session end (Claude):
  chorus send --from claude --to codex --message "Session ended. Open: auth bug. Next: fix login."

Session start (Codex):
  chorus messages --agent codex  →  reads Claude's handoff
  "Claude was working on the auth bug. Picking up from there."
```

Each agent has a JSONL inbox. Messages include project context. A shared CHECKPOINT.md lets agents recover if interrupted mid-task.

### QMD — Query My Documents

Hybrid semantic + keyword search over your entire vault:

```bash
qmd query "authentication flow"     # Semantic + reranked
qmd query "api" -c wiki             # Restrict to wiki collection
qmd search "ECONNREFUSED"           # Fast keyword-only
qmd update                          # Reindex after writing new files
```

Wrappers included for Windows (`.ps1`), macOS, and Linux.

### STATUS.md — Cross-Agent Session Index

```markdown
## Claude
- [2026-05-26] global — Wired CARL into shared config. Open: DESIGN FP → log.md

## Codex
- [2026-05-25] my-app — Carousel polish. Open: mobile breakpoints → log.md

## Hermes
(no recent sessions)
```

Auto-injected on fresh sessions via CARL hook. Every agent sees the last 3 sessions of every other agent. Maintained by `update-global-status.py`.

### Optional: DeepSeek Backend (claudeep)

Run Claude Code backed by DeepSeek models at a fraction of the cost:

```bash
npm install -g claudeep
npx claudeep setup
```

See [docs/DEEPSEEK.md](docs/DEEPSEEK.md) for full setup. Pair with clipboard-vision-mcp for vision support (text-only models can't see images).

### Optional: Clipboard Vision MCP

Let text-only models (DeepSeek V4, GLM 5.1) see images directly from your clipboard:

```bash
git clone https://github.com/Capetlevrai/clipboard-vision-mcp.git
cd clipboard-vision-mcp
python -m venv .venv && source .venv/bin/activate && pip install -e .
```

Paste screenshot → ask → done. No file saving. Uses Groq's free tier with Llama-4 Scout vision. See [docs/CLIPBOARD-VISION.md](docs/CLIPBOARD-VISION.md).

### Optional: Hermes / WSL

A Linux-based agent sharing the same vault via Syncthing. The HERMES CARL domain auto-loads on Linux with platform-specific paths and routines. See [hermes/README.md](hermes/README.md).

### Optional: Auto-Export Pipeline

Browser conversations automatically flow into your vault:

```
Browser (Claude.ai / ChatGPT / Gemini)
    ↓ Tampermonkey auto-exports on navigation
Downloaded .md file
    ↓ watch-and-route-v2.sh (polls every 5s)
raw/conversations/{platform}/
    ↓ /ingest (agent converts to wiki pages)
wiki/concepts/ + wiki/entities/ + wiki/projects/
```

### Optional: Vault Backup

Dual-mirror, append-only backup at every `/conclude`:
- OneDrive mirror (git-tracked, restorable by commit hash)
- Local mirror (survives cloud sync incidents)

Never uses destructive operations (no `robocopy /MIR`, no `rsync --delete`).

---

## <a name="architecture"></a>Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Obsidian Vault                            │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────────────┐  │
│  │  .carl/  │  │ .agents/ │  │  memory/                   │  │
│  │ carl.json│  │ skills/  │  │  HOT: MEMORY.md, USER.md   │  │
│  │ sessions/│  │ scripts/ │  │  WARM: *-FULL.md           │  │
│  └────┬─────┘  └────┬─────┘  │  COLD: archive/            │  │
│       │             │        │  sessions.db (FTS5)         │  │
│  ┌────┴─────────────┴────────┴───────────────────────────┐  │
│  │           Syncthing (optional, bidirectional)          │  │
│  └────────────────────────┬──────────────────────────────┘  │
└───────────────────────────┼──────────────────────────────────┘
                            │
                 ┌──────────┴──────────┐
                 │                     │
     ┌───────────┴───────┐  ┌─────────┴──────────┐
     │   Windows / macOS  │  │   WSL2 / Linux      │
     │                    │  │   (Hermes)          │
     │  ~/.carl ──> vault │  │  ~/.carl ──> vault  │
     │  ~/.agents ─>vault │  │  ~/.agents ─> vault │
     │                    │  │                     │
     │  Claude / Codex    │  │  carl-hook.py       │
     │  / Gemini          │  │  HERMES domain auto │
     │                    │  │                     │
     │  carl-hook.py      │  │                     │
     │  (UserPromptSubmit)│  │                     │
     └────────┬───────────┘  └─────────┬───────────┘
              │                        │
              └────────────┬───────────┘
                           │
               ┌───────────┴───────────┐
               │   Agent Chorus        │
               │  claude.jsonl         │
               │  codex.jsonl          │
               │  gemini.jsonl         │
               │  hermes.jsonl         │
               └───────────────────────┘
```

### Session Lifecycle

```
SESSION START
  carl-hook fires → calculates context bracket (FRESH/MODERATE/DEPLETED)
  → injects GLOBAL + matched domain rules
  → injects STATUS.md (if fresh)
  → agent reads chorus inbox
  → /standup loads project context + hot memory

SESSION BODY
  → CARL rules guide behavior
  → /skill loads specialized workflows
  → /recall searches vault + sessions + CARL decisions
  → checkpoints written before significant tasks

SESSION END (/conclude)
  1. Audit session (files, decisions, open threads)
  2. Write session log
  3. Update active plan
  4. Memory nudges (MEMORY.md, USER.md)
  5. Hot-memory audit & offload (if >80% cap)
  6. Write sessions.db row
  7. Update global STATUS.md
  8. Sync agent configs (CLAUDE.md ↔ AGENTS.md)
  9. Send chorus handoffs to other agents
  10. Git commit session artifacts
  11. Vault backup (dual mirror)
```

---

## <a name="quick-start"></a>Quick Start

```bash
# 1. Clone
git clone https://github.com/oloflun/super-intelligence.git
cd super-intelligence

# 2. Install (interactive)
node install.mjs
# → Answer prompts for agent, vault path, components, git user

# 3. Index your vault
qmd update

# 4. Start your agent — CARL auto-injects on fresh sessions
# Run /standup to load project context
# Run /conclude when done
```

After installation, your agent's first session will:
1. Auto-load GLOBAL rules (always on)
2. Match your prompt against domain keywords and load relevant rules
3. Auto-inject STATUS.md (fresh session context)
4. Be ready with 213 skills available via `/skill <name>`

---

## <a name="upgrade"></a>Upgrade

```bash
git pull
node upgrade.mjs
```

The upgrade script:
- Merges new CARL domains/rules (preserves your customizations)
- Updates skills and scripts (newer files only)
- Creates `.bak-*` backups before any change
- **Never touches** your personal data (memory, sessions, STATUS.md)

---

## File Topology After Install

```
~ (home)
├── CLAUDE.md              ← Agent reference config (rules live in CARL)
├── AGENTS.md              ← Codex variant (auto-synced)
├── GEMINI.md              ← Gemini variant
├── STATUS.md              ← Hardlink → vault/STATUS.md
├── .carl/                 ← Junction → vault/.carl
├── .agents/               ← Junction → vault/.agents
├── .claude/
│   ├── settings.json      ← Claude Code settings (hooks, plugins)
│   └── hooks/
│       ├── carl-hook.py   ← CARL injector (fires on every prompt)
│       └── sync-configs-hook.py ← CLAUDE.md ↔ AGENTS.md sync
└── session-logs/          ← Local session logs (personal, gitignored)

{{VAULT_PATH}} (Obsidian vault)
├── .carl/carl.json        ← 8 domains, all behavioral rules
├── .agents/
│   ├── skills/            ← 213 skill modules
│   ├── scripts/           ← Utility scripts (15)
│   └── memory/            ← Memory mirrors per project
├── .agent-chorus/
│   ├── messages/          ← Agent inboxes (JSONL)
│   ├── providers/         ← Provider contracts
│   └── CHECKPOINT.md      ← Shared recovery checkpoint
├── memory/
│   ├── MEMORY.md          ← Hot memory (2,200 cap)
│   ├── USER.md            ← Hot preferences (1,375 cap)
│   ├── MEMORY-FULL.md     ← Warm episodic memory
│   ├── USER-FULL.md       ← Warm user history
│   ├── sessions.db        ← FTS5 session index
│   └── archive/           ← Cold storage
├── STATUS.md              ← Cross-agent session index (3 per agent)
├── .qmd.yaml              ← QMD search config
├── .stignore              ← Syncthing exclusion rules
└── scripts/               ← Vault scripts
```

---

## Requirements

| Component | Minimum | Purpose |
|---|---|---|
| Node.js | 18+ | Installer, QMD, MCP servers |
| Python | 3.10+ | CARL hook, scripts |
| Git | Any | Version control |
| Obsidian | Any version | Vault (or any markdown directory) |

**Optional:**

| Component | For |
|---|---|
| WSL2 | Hermes (Linux agent) |
| Syncthing | Windows ↔ WSL vault sync |
| Rust/Cargo | Building chorus CLI from source |
| Groq API key | Clipboard vision MCP (free tier) |
| DeepSeek API key | Claudeep (DeepSeek backend) |

---

## Documentation

| Document | Content |
|---|---|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Full system design — every component in detail |
| [QUICKSTART.md](docs/QUICKSTART.md) | 5-minute setup guide |
| [UPGRADE.md](docs/UPGRADE.md) | How to upgrade, what's preserved |
| [DEEPSEEK.md](docs/DEEPSEEK.md) | DeepSeek backend via claudeep |
| [CLIPBOARD-VISION.md](docs/CLIPBOARD-VISION.md) | Vision for text-only models |
| [hermes/README.md](hermes/README.md) | Hermes/WSL setup |
| [syncthing/README.md](syncthing/README.md) | Syncthing bridge config |
| [karpathy/wiki-setup.md](karpathy/wiki-setup.md) | Karpathy wiki methodology |
| [wiki-ingest/README.md](wiki-ingest/README.md) | Auto-export pipeline |

---

## Security

- **No credentials in the package** — All `.env`, `auth.json`, `credentials.json` patterns are gitignored
- **Personal paths are placeholders** — Templates use `{{VAULT_PATH}}`, `{{USER_HOME}}` — never real paths
- **Memory is never committed** — Personal memory files (MEMORY.md, USER.md, sessions.db) are always local
- **Backups are append-only** — No destructive sync operations, no `robocopy /MIR`, no `rsync --delete`
- **Clipboard MCP is hardened** — File type allow-list, magic-byte validation, size cap, auto-delete temp files
- **Claudeep runs locally** — No third-party proxy, prompts go directly to DeepSeek

---

## License

MIT — Build your own super-intelligence.

---

<p align="center">
  <sub>680 files · 4.8 MB · 213 skills · 8 CARL domains · 7 install presets · zero personal data</sub>
</p>