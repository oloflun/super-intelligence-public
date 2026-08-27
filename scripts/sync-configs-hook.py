#!/usr/bin/env python
"""
Sync CLAUDE.md <-> AGENTS.md with agent-name substitutions.

Usage:
    python sync-configs-hook.py --source CLAUDE.md
    python sync-configs-hook.py --source AGENTS.md
"""

import sys
import argparse
from pathlib import Path

BASE = Path(r"{{USER_HOME}}")
CLAUDE_MD = BASE / "CLAUDE.md"
AGENTS_MD = BASE / "AGENTS.md"

# Ordered substitution pairs: (claude_token, agents_token)
# str.replace — no regex, so partial-word false positives are impossible
# (e.g. "codex-config", "--source codex", "Agent: codex" are untouched)
PAIRS = [
    ("# Claude Code – Global Configuration", "# Codex – Global Configuration"),
    ("agent-chorus:claude:", "agent-chorus:codex:"),
    ("providers\\claude.md", "providers\\codex.md"),
    ("--agent claude", "--agent codex"),
    ("--from claude", "--from codex"),
    ("--to codex", "--to claude"),    # Claude sends TO codex → Codex sends TO claude
]


def transform(content: str, *, to_agents: bool) -> str:
    for claude_token, codex_token in PAIRS:
        src, dst = (claude_token, codex_token) if to_agents else (codex_token, claude_token)
        content = content.replace(src, dst)
    return content


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, choices=["CLAUDE.md", "AGENTS.md"])
    args = parser.parse_args()

    if args.source == "CLAUDE.md":
        src_path, dst_path, to_agents = CLAUDE_MD, AGENTS_MD, True
    else:
        src_path, dst_path, to_agents = AGENTS_MD, CLAUDE_MD, False

    if not src_path.exists():
        print(f"[sync-configs] ERROR: source not found: {src_path}", file=sys.stderr)
        sys.exit(1)

    src_content = src_path.read_text(encoding="utf-8")
    derived = transform(src_content, to_agents=to_agents)

    if dst_path.exists():
        current = dst_path.read_text(encoding="utf-8")
        if current == derived:
            print(f"[sync-configs] no diff — {dst_path.name} already in sync")
            return

    dst_path.write_text(derived, encoding="utf-8")
    print(f"[sync-configs] synced {src_path.name} -> {dst_path.name}")


if __name__ == "__main__":
    main()
