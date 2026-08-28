#!/usr/bin/env python
"""SessionStart -- reconciles the legacy install.mjs setup with this plugin.

Why this exists: this repo ships two independent ways to get the same content
onto a machine. `install.mjs` writes skills and hook registrations directly
onto disk, once, at install time -- that is how the ORIGINAL live setup on
this machine (and on any teammate's machine who already ran it) came to be.
The Claude Code plugin mechanism is a second, separate distribution path that
auto-updates on every commit via the git-SHA-as-version convention (see
CLAUDE.md's "Updating" section) -- but it knows nothing about install.mjs's
files, and vice versa.

Installing this plugin on a machine that already ran install.mjs therefore
creates real duplication: every hook this plugin declares in hooks/hooks.json
is ALSO already registered directly in that machine's ~/.claude/settings.json
by install.mjs. Without this reconciliation, every one of those hooks fires
TWICE per event -- double CARL injection, double brief-context searches,
double design/marketing gates, double chorus pings, and (the expensive one)
double deepclaude-pretool routing. Measured on the reference machine 2026-08-28:
22 of 22 plugin hooks already present in the live settings.json, 100% overlap.

What this script does, every SessionStart, in two tiers:

  1. FAST PATH (every session, near-zero cost): compare this plugin's current
     CLAUDE_PLUGIN_ROOT against the path recorded from the last run. Claude
     Code's plugin cache directory is named per-version (a semver or a short
     git SHA in the path itself -- confirmed against this machine's real
     installed_plugins.json), so an unchanged path IS an unchanged version.
     Equal -> exit immediately. This is the case on ~every ordinary session.

  2. SLOW PATH (only right after this plugin updates to a new commit):
     a. Remove any LEGACY hook registration from ~/.claude/settings.json whose
        script basename matches one this plugin now also provides -- "legacy"
        meaning its command does not already reference this CLAUDE_PLUGIN_ROOT.
        A one-time backup of settings.json is taken before the first real
        edit, never overwritten on later runs.
     b. Sync this plugin's skills/ into ~/.agents/skills/ (copy-if-newer,
        additive only -- never deletes a hand-authored skill that isn't part
        of this plugin). ~/.agents/skills is the fixed path every other part
        of this stack already reads from (CARL, wake-gate, the pattern
        index) -- syncing INTO it, rather than leaving content sitting only
        in the plugin's own cache directory, is what makes "the rest of the
        stack sees plugin updates" true instead of aspirational.

Both steps are pure-Python (no robocopy dependency) so this stays portable to
macOS/Linux, per this repo's own install.mjs presets. Fail-soft throughout --
a broken sync should never block a session from starting.
"""

import json
import os
import shutil
import sys
import time
from pathlib import Path

if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
    sys.exit(0)

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)
HOME = Path.home()
SETTINGS = HOME / ".claude" / "settings.json"
SETTINGS_BACKUP = HOME / ".claude" / "settings.json.pre-plugin-sync.bak"
SKILLS_DST = HOME / ".agents" / "skills"
MARKER = HOME / ".agents" / ".plugin-sync-root"
LOG = HOME / ".agents" / "logs" / "plugin-sync.jsonl"


def log(**fields):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        rec.update(fields)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass


def already_synced():
    try:
        return MARKER.read_text(encoding="utf-8").strip() == str(PLUGIN_ROOT)
    except OSError:
        return False


def mark_synced():
    try:
        MARKER.parent.mkdir(parents=True, exist_ok=True)
        MARKER.write_text(str(PLUGIN_ROOT), encoding="utf-8")
    except OSError:
        pass


def plugin_hook_basenames():
    """Script filenames this plugin's own hooks.json declares. Read live
    (not hardcoded) so a future commit adding/removing a hook stays correct
    without touching this file.

    Extracts the basename from the quoted path in each command, not from a
    guessed file extension -- an early version matched only `.py`/`.sh` and
    silently missed the three extensionless gstack hooks
    (`question-preference-hook` and friends), which meant 3 of 26 duplicate
    registrations survived dedup untouched. Caught by testing against a real
    isolated copy of the live settings.json before this ever ran for real.
    """
    try:
        data = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    import re
    names = set()
    for groups in (data.get("hooks") or {}).values():
        for g in groups:
            for h in (g.get("hooks") or []):
                m = re.search(r'"([^"]+)"', h.get("command", ""))
                if m:
                    names.add(Path(m.group(1)).name)
    return names


def dedupe_legacy_hooks():
    """Strip legacy (non-plugin-path) registrations of scripts this plugin
    now also owns. Returns the list of removed script basenames, or [] on
    any failure (never raises -- a settings.json this can't safely parse is
    left untouched)."""
    plugin_root_str = str(PLUGIN_ROOT)
    names = plugin_hook_basenames()
    if not names:
        return []
    try:
        raw = SETTINGS.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError) as e:
        log(step="dedupe", error=str(e)[:200])
        return []

    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return []

    removed = []
    changed = False
    for event, groups in list(hooks.items()):
        new_groups = []
        for g in groups:
            new_entries = []
            for h in (g.get("hooks") or []):
                cmd = h.get("command", "")
                is_ours = any(n in cmd for n in names)
                is_legacy_path = plugin_root_str not in cmd
                if is_ours and is_legacy_path:
                    removed.append((event, cmd[:120]))
                    changed = True
                    continue
                new_entries.append(h)
            if new_entries:
                g = dict(g)
                g["hooks"] = new_entries
                new_groups.append(g)
            else:
                changed = True  # whole group emptied out
        hooks[event] = new_groups

    if not changed:
        return []

    try:
        if not SETTINGS_BACKUP.exists():
            SETTINGS_BACKUP.write_text(raw, encoding="utf-8")
        SETTINGS.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                            encoding="utf-8")
    except OSError as e:
        log(step="dedupe_write", error=str(e)[:200])
        return []

    return removed


def sync_skills():
    """Copy-if-MISSING, additive only. Returns count of files copied, or -1
    on failure (source/dest unreadable).

    Deliberately NOT copy-if-newer: ~/.agents/skills is an NTFS junction into
    the Obsidian vault, and vault content gets hand-edited directly (that's
    the whole point of the junction -- Obsidian and this stack share one
    copy). An mtime-based overwrite meant a plugin reinstall could stomp a
    newer hand-edit in the vault just because the plugin's packaged copy
    happened to have a later mtime (e.g. from a fresh git checkout, where
    every file's mtime is "now" regardless of content history). Never
    overwrite something that already exists -- only fill in what's missing.
    """
    src = PLUGIN_ROOT / "skills"
    if not src.is_dir():
        return -1
    try:
        SKILLS_DST.mkdir(parents=True, exist_ok=True)
        n = 0
        for root, _dirs, files in os.walk(src):
            rel = Path(root).relative_to(src)
            target_dir = SKILLS_DST / rel
            for fname in files:
                s = Path(root) / fname
                d = target_dir / fname
                if not d.exists():
                    target_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s, d)
                    n += 1
        return n
    except OSError as e:
        log(step="sync_skills", error=str(e)[:200])
        return -1


def main():
    if already_synced():
        return

    t0 = time.time()
    removed = dedupe_legacy_hooks()
    copied = sync_skills()
    mark_synced()

    log(plugin_root=str(PLUGIN_ROOT), hooks_removed=len(removed),
        removed_detail=removed[:30], skills_copied=copied,
        elapsed_s=round(time.time() - t0, 2))

    if removed or copied > 0:
        lines = ["<plugin-sync>",
                 "super-intelligence-plugin uppdaterades och synkade sig:"]
        if removed:
            lines.append(f"- {len(removed)} dubblettregistrerade hookar "
                         f"borttagna ur ~/.claude/settings.json (backup: "
                         f"{SETTINGS_BACKUP.name})")
        if copied and copied > 0:
            lines.append(f"- {copied} skill-filer synkade till ~/.agents/skills")
        lines.append("</plugin-sync>")
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join(lines),
        }}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(error=f"unhandled: {e!r}"[:300])
    sys.exit(0)
