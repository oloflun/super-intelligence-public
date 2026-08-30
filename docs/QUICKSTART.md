# Quick Start

## 5-Minute Setup

```bash
# 1. Clone
git clone https://github.com/oloflun/super-intelligence-public.git
cd super-intelligence-public

# 2. Install
node install.mjs
# → Enter your vault path when prompted (any folder; a git repo is
#   recommended -- see karpathy/vault-repo-setup.md)
# → Enter your git username and email

# 3. Index
qmd update

# 4. Start using
# Your next agent session will auto-load CARL rules via carl-hook.py
# Run /standup to load project context
# Run /conclude when done
```

## What Just Happened

The installer created:

| File/Link | Location | Purpose |
|---|---|---|
| `carl.json` | vault `.carl/` | All behavioral rules (9 domains) |
| `carl-hook.py` | `~/.claude/hooks/` | Auto-injects rules on every prompt |
| `CLAUDE.md` | `~/` | Agent reference config |
| `AGENTS.md` | `~/` | Codex variant (auto-synced) |
| Skills (70+) | vault `.agents/skills/` | Reusable `/skill` modules |
| Scripts | vault `.agents/scripts/` | Utility scripts |
| `MEMORY.md` | vault `memory/` | Hot memory (loaded at /standup) |
| `sessions.db` | vault `memory/` | FTS5 session index |
| `STATUS.md` | vault root | Cross-agent session index |
| `~/.carl` | junction → vault | CARL accessible from home |
| `~/.agents` | junction → vault | Skills/scripts accessible from home |
| `~/.claude/settings.json` | Claude config | Hook + plugin configuration |

## First Session

Start any agent (Claude Code, Codex, etc.) in your home directory or a project directory.

The agent will:
1. Auto-load GLOBAL CARL rules (always on)
2. Auto-inject STATUS.md on fresh sessions
3. Match your prompt against CARL domains and load relevant rules

Try these:
- `/standup` — loads project context
- `/recall <topic>` — searches your vault, sessions, and CARL decisions
- `/skill design` — loads the design master router
- `/conclude` — wraps up the session properly

## Next: Set Up Cross-Agent

To enable multi-agent coordination:

1. **Syncthing** — Bridge Windows ↔ WSL vault (see `syncthing/README.md`)
2. **Hermes** — Linux agent in WSL (see `hermes/README.md`)
3. **Auto-Export** — Browser → vault pipeline (see `wiki-ingest/README.md`)
4. **Karpathy Wiki** — Knowledge management methodology (see `karpathy/wiki-setup.md`)

## Troubleshooting

**CARL rules not loading:**
- Check `~/.claude/settings.json` has the hook configured
- Verify `python` is in PATH
- Run `python ~/.claude/hooks/carl-hook.py` manually to test

**Skills not found:**
- Verify `~/.agents/skills/` junction points to vault `.agents/skills/`
- Run `/skill list` to see available skills

**QMD search not working:**
- Run `qmd update` to index your vault
- Check `.qmd.yaml` exists in vault root

## Automatic Updates

Your install includes a daily health check and auto-update system:

- **Runs daily at 09:00** (randomized ±1h)
- **Fetches latest stack** from GitHub (`git pull --ff-only`)
- **Applies updates** (`node upgrade.mjs`) — non-destructive, never touches your data
- **Runs full health check** — package, installation, MCPs, CARL, repos
- **Logs everything** to `~/.super-intelligence/update.log`

**Disable:** edit `~/.super-intelligence/config.json` → `"auto_update": false`

**Run manually:**
```bash
bash ~/super-intelligence/scripts/auto-update.sh   # POSIX
powershell ~/super-intelligence/scripts/auto-update.ps1  # Windows
```

**Health check only:** `node ~/super-intelligence/scripts/health-check.mjs --installed`
