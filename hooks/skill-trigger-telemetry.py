#!/usr/bin/env python
"""PostToolUse on Skill -- append every skill invocation to a telemetry log.

Fas 2.4 (wondrous-wishing-star.md): measures under-triggering of the skill
router (Anthropic pattern: skills exist but don't fire often enough). This is
the capture side only -- it emits nothing into context, just logs. Analysis
(which skills fire vs. which SKILL.md triggers: keywords appeared in the
prompt but never got invoked) is a separate pass over this file, not done here
-- ponytail: don't build the analyzer before there's a week of real data to
analyze.

Domain-specific telemetry (design-telemetry.py, marketing-telemetry.py)
already covers those two skills in more depth (component attribution). This
is the general, all-skills counterpart they don't provide.
"""

import json
import os
import sys
import time
from pathlib import Path

LOG = Path.home() / ".agents/memory-probe/skill-trigger-telemetry.jsonl"


def main() -> None:
    if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
        return  # Fas 6 assistant-bench arm B: don't pollute telemetry with bench data

    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    if (event.get("tool_name") or event.get("toolName")) != "Skill":
        return

    ti = event.get("tool_input") or event.get("toolInput") or {}
    if not isinstance(ti, dict):
        return
    skill = ti.get("skill") or ti.get("name") or ""
    if not skill:
        return

    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "skill": skill,
        "args": ti.get("args", ""),
        "cwd": event.get("cwd", ""),
    }
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
