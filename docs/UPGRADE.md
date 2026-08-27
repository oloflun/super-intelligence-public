# Upgrade Guide

## Automatic Daily Updates (Recommended)

The installer sets up a daily health check and auto-update that runs at 09:00 (with a randomized ±1h delay).

**What it does every day:**

1. `git fetch origin` — checks for new commits
2. If updates exist: `git pull --ff-only origin main`
3. Runs `node upgrade.mjs` — non-destructive sync of skills, CARL, hooks
4. Runs a full health check:
   - Package integrity (npm, skills, subsystems)
   - Installation health (paths, configs, junctions)
   - MCP servers (configured, reachable)
   - CARL (domain integrity, hook wiring, version)
   - Repos (git status, ahead/behind)
5. Prints a terminal report
6. Logs to `~/.super-intelligence/update.log`

**Config:** `~/.super-intelligence/config.json`

```json
{
  "auto_update": true,
  "repo_path": "~/super-intelligence",
  "vault_path": "~/Obsidian/Knowledge Base",
  "last_check": "2026-07-22T09:02:00Z",
  "update_log": "~/.super-intelligence/update.log"
}
```

**Disable:** Set `"auto_update": false` in the config, or run:
```bash
bash ~/super-intelligence/scripts/remove-auto-update.sh   # POSIX
powershell ~/super-intelligence/scripts/remove-auto-update.ps1  # Windows
```

**Run manually:**
```bash
bash ~/super-intelligence/scripts/auto-update.sh   # POSIX
powershell ~/super-intelligence/scripts/auto-update.ps1  # Windows
```

**Health check only (no git pull):**
```bash
node ~/super-intelligence/scripts/health-check.mjs --installed
node ~/super-intelligence/scripts/verify-install.mjs
```

## Manual Upgrade

```bash
cd super-intelligence
git pull
node upgrade.mjs
```

The upgrade script:
1. Reads your current `VERSION`
2. Compares against the latest templates
3. Applies non-destructive updates to:
   - `carl.json` (merges new domains/rules/decisions by text — never overwrites existing)
   - Skills (copies new, overwrites changed, never deletes user-local)
   - Scripts (same content-aware sync)
   - `carl-hook.py` (updated if version changed)
4. Reports what was changed (`+added / ~updated / unchanged`)
5. Never touches your personal data (memory, sessions, STATUS.md)

### If the auto-update fails

The scheduler task logs to `~/.super-intelligence/update.log`. Check there first.
Common issues:

- **Local diverged from origin:** `git pull --ff-only` refuses. `git reset --hard origin/main` (if no local changes) or `git stash && git pull && git stash pop`
- **Node.js not in scheduler PATH:** Edit the scheduler task to include the full PATH or use absolute paths in the update script
- **jq not installed:** CARL deep health falls back to basic checks. Install `jq` for full diagnostics.

## Manual Upgrade Steps (if automatic fails)

1. **Skills:** Copy `skills/` from the package to your vault's `.agents/skills/`
2. **Scripts:** Copy `scripts/` to `.agents/scripts/`
3. **CARL:** Review `carl/carl.json` for new domains/rules and merge into your `.carl/carl.json`
4. **Hook:** Update `.claude/hooks/carl-hook.py` if the version changed
5. **Configs:** Review template changes and apply to your `CLAUDE.md`/`AGENTS.md`

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for detailed version history.

## Breaking Changes

Breaking changes are rare and always documented in the release notes. The installer
and upgrade script are designed to be non-destructive:

- Personal memory (MEMORY.md, USER.md, sessions.db) is never touched
- Session logs are never modified
- STATUS.md entries are preserved
- CARL domains you've customized are preserved (new ones are added by text match)
