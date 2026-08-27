# Hermes / WSL Agent Setup

Hermes is the Linux-based agent running in WSL2. It shares the same vault as Windows agents via Syncthing.

## Prerequisites

- WSL2 installed and running
- Syncthing configured (see `../syncthing/README.md`)
- Python 3.10+, Node.js 18+, Git in WSL

## Setup

### 1. Run the Hermes installer in WSL

```bash
# In WSL terminal:
cd /mnt/c/path/to/super-intelligence
node install.mjs --agent hermes
```

The installer detects Linux and:
- Creates `~/.carl` symlink → `~/vault-local/.carl`
- Creates `~/.agents` symlink → `~/vault-local/.agents`
- Deploys `carl-hook.py` with Linux detection
- Sets up Hermes-specific paths

### 2. Configure Syncthing folder

Add the vault as a Syncthing folder shared between Windows and WSL:
- Windows: `C:\Users\<user>\OneDrive\Obsidian\Knowledge Base`
- WSL: `~/vault-local`

### 3. Verify

```bash
# In WSL:
ls -la ~/.carl        # Should show symlink -> ~/vault-local/.carl
ls -la ~/.agents      # Should show symlink -> ~/vault-local/.agents
ls -la ~/STATUS.md    # Should show symlink -> ~/vault-local/STATUS.md

# Check CARL hook detects Linux
python3 ~/.claude/hooks/carl-hook.py --version
```

## HERMES CARL Domain

The HERMES domain in `carl.json` is platform-gated. It only loads on Linux (detected by `platform.system() != "Windows"` in carl-hook.py).

**Rules:**
1. STATUS.md is auto-injected (not part of /standup)
2. Write rules to CARL, not AGENTS.md/SOUL.md
3. Deduplicate AGENTS.md/SOUL.md rules at /standup
4. Project-specific rules go to MEMORY-FULL.md, not CARL
5. Use Hermes-specific paths: `python3`, `~/vault-local/`
6. Check relay inbox at session start
7. Chorus messages use WSL vault path

## Hermes-Specific Paths

| Context | Path |
|---|---|
| Python | `python3` |
| Vault | `~/vault-local/` |
| CARL | `~/.carl/` (→ `~/vault-local/.carl/`) |
| Agents | `~/.agents/` (→ `~/vault-local/.agents/`) |
| STATUS | `~/STATUS.md` (→ `~/vault-local/STATUS.md`) |
| QMD | `~/.hermes/scripts/qmd-hermes` |
| Chorus cwd | `/mnt/c/Users/<user>/OneDrive/.../Knowledge Base` |
| Relay inbox | `~/.hermes/inbox/*.msg` |

## Memory System (from Hermes)

Hermes uses the same memory topology as Windows agents but writes to `~/vault-local/memory/` which Syncthing syncs back.

**/conclude from Hermes:**
1. Write session log to `~/vault-local/session-logs/`
2. Write memory nudges to `~/vault-local/memory/MEMORY.md` and `USER.md`
3. Write sessions.db row
4. Run `update-global-status.py --agent hermes`
5. Send chorus handoffs
