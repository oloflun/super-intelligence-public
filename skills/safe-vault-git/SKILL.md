---
name: safe-vault-git
description: Use when committing or reviewing changes in the Knowledge Base vault, especially after ingest, raw coverage repair, Obsidian graph updates, or any large batch that could trigger OneDrive/Syncthing/Git status polling.
---

# Safe Vault Git

## Overview
The Knowledge Base vault is not a normal small repo. It is a live Obsidian + OneDrive + Syncthing workspace with junctioned projects and background Git status pollers. Broad Git operations can freeze the machine.

## When To Use
Use this before any commit, diff, status summary, cleanup commit, or conclude commit in the vault.

## Incident Hard Stops
After the 2026-05-21 OneDrive/vault deletion incident, no agent may approve or run broad deletion, trash, prune, cleanup, or mirror-delete operations in this vault.

- Stale cleanup may only target generated/cache files from an explicit manifest: nested `node_modules`, `.cache`, `dist`, `build`, `out`, `__pycache__`, or temp/log/pyc artifacts.
- Protected roots are never deletion candidates: `raw`, `wiki/sources`, `memory`, `.obsidian`, `Clippings`, `Snipd`, `Web Clippings`, `.agent-chorus`, `scripts`, and backup folders.
- Forbidden unless Anton names exact paths in the same message: `git clean`, `git rm`, `git worktree remove`, `rm -rf`, `Remove-Item -Recurse`, mirror-delete copy flags, `rsync --delete`, and duplicate-delete helpers with `--apply`.
- Any deletion approval involving more than 10 paths must stop and produce a manifest with path, reason, generated/protected classification, and recovery source.
- If a stale-git sweep reports protected paths, restore or quarantine those exact paths first; never treat them as stale cleanup.
## Rules
- Never run `git add -A`, `git add .`, `git clean`, `git rm`, full-vault `git diff --stat`, or full-vault `git status`.
- Stage only explicit files listed in a pathspec manifest.
- Keep commits grouped by concern: scripts/config, wiki docs, raw coverage footers, duplicate deletions.
- Exclude Obsidian workspace/plugin state unless the user specifically asked to save it.
- Exclude Syncthing conflict files, nested project dirty states, `node_modules`, build outputs, and cache directories.
- Run QMD `update/status` outside the commit phase. Do not run `qmd query` or unrestricted `qmd embed` while committing.

## Standard Command

Create a manifest file with one relative path per line, then run:

```bash
node scripts/safe-vault-commit.mjs .git/safe-commit-manifest.txt "chore: describe batch"
```

The helper stages only those files, shows scoped status/stat, and commits only that manifest.

## Preflight
- Check for runaway `git.exe` processes with `node scripts/identify-git-pollers.mjs` on Windows.
- If many read-only Git pollers are active, pause and ask before killing them.
- Confirm `wiki/projects/wiki-ingest-daemon/node_modules/sql.js` remains present; it should be hidden from Obsidian, not deleted.

