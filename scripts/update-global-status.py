#!/usr/bin/env python
"""
Prepend a new session entry to the global STATUS.md under the correct agent section.
Prunes each agent section to at most 3 entries (newest first).
Writes in-place — hardlinks are preserved.

Usage:
    python update-global-status.py \
        --agent claude \
        --slug global-config \
        --summary "Migrated rules to CARL. Open: DESIGN FP" \
        --open "DESIGN FP, plugin cleanup" \
        --log "{{USER_HOME_ESC}}\\session-logs\\2026-05-25-session-log.md"
"""

import argparse
import platform
import sys
from datetime import date
from pathlib import Path

if platform.system() == "Windows":
    STATUS_PATH = Path(r"{{USER_HOME}}\STATUS.md")
else:
    STATUS_PATH = Path.home() / "STATUS.md"  # ~/STATUS.md via symlink → ~/vault-local/STATUS.md

MAX_ENTRIES = 3


def format_entry(slug: str, summary: str, open_threads: str, log_path: str) -> str:
    today = date.today().isoformat()
    return f"- [{today}] {slug} — {summary}. Open: {open_threads} → {log_path}"


def update_status(agent: str, entry: str) -> None:
    if not STATUS_PATH.exists():
        print(f"[update-global-status] ERROR: {STATUS_PATH} not found", file=sys.stderr)
        sys.exit(1)

    content = STATUS_PATH.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=False)

    header = f"## {agent.capitalize()}"

    # Find agent section start
    start = None
    for i, line in enumerate(lines):
        if line == header:
            start = i
            break
    if start is None:
        print(f"[update-global-status] ERROR: section '{header}' not found", file=sys.stderr)
        sys.exit(1)

    # Find next ## section or EOF
    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break

    # Collect existing bullet entries from section body
    old_bullets = [l for l in lines[start + 1:end] if l.startswith("- [")]

    # Build new section: header + blank + newest-first entries (max 3) + trailing blank
    new_entries = [entry] + old_bullets[:MAX_ENTRIES - 1]
    replacement = [header, ""] + new_entries + [""]

    # Splice: strip any leading blank lines from the post segment (they're
    # already provided by the trailing blank in replacement)
    post = lines[end:]
    while post and post[0] == "":
        post = post[1:]

    new_lines = lines[:start] + replacement + post

    # Update _Updated_ line
    today = date.today().isoformat()
    for i, line in enumerate(new_lines):
        if line.startswith("_Updated:"):
            new_lines[i] = f"_Updated: {today} by {agent}_"
            break

    STATUS_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    print(f"[update-global-status] prepended entry to {header} ({len(new_entries)} entries total)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update global STATUS.md")
    parser.add_argument("--agent", required=True, choices=["claude", "codex", "gemini", "hermes"])
    parser.add_argument("--slug", required=True, help="Project slug or 'global'")
    parser.add_argument("--summary", required=True, help="One-sentence session summary")
    parser.add_argument("--open", required=True, dest="open_threads",
                        help="Comma-separated open threads, or 'none'")
    parser.add_argument("--log", required=True, help="Absolute path to session log file")
    args = parser.parse_args()

    entry = format_entry(args.slug, args.summary, args.open_threads, args.log)
    update_status(args.agent, entry)


if __name__ == "__main__":
    main()
