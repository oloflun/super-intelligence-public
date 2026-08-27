#!/usr/bin/env python
"""UserPromptSubmit -- cheap capture of correction-shaped prompts for Drömmen.

Fas 3.4 (wondrous-wishing-star.md): zero-LLM-cost capture at the moment a
correction happens; the dream pipeline (02_distill) does the actual distillation
the next night. This hook only detects and logs -- it never judges whether the
correction mattered.

No direct "previous assistant message id" is available at this hook layer (it only
sees the incoming prompt, not the prior turn's content) -- session_id + timestamp is
logged instead, and stage 01_gather correlates that against the full transcript in
~/.claude/projects/** (which has the real turn-by-turn history) to find what was
actually being corrected.

Emits nothing into context -- pure capture, like skill-trigger-telemetry.py.
"""

import json
import os
import re
import sys
import time
from pathlib import Path

LOG = Path.home() / ".agents/inbox/corrections.jsonl"

NOISE = re.compile(
    r"\[SYSTEM NOTIFICATION|<task-notification>|<system-reminder>|"
    r"<local-command-|<command-name>|Caveat: The messages below",
    re.IGNORECASE,
)

CORRECTION = re.compile(
    r"^\s*(nej|no|fel|inte s[åa]|inte det|jag sa (ju|redan)|det (var|är) inte|"
    r"sluta (med|göra)|stop doing|that'?s wrong|not (like )?that|don'?t do that|"
    r"you misunderstood|missförstod|det stämmer inte)\b",
    re.IGNORECASE,
)


def main() -> None:
    if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
        return  # Fas 6 assistant-bench arm B: don't pollute corrections.jsonl with bench prompts

    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    prompt = (event.get("prompt") or event.get("userInput") or "").strip()

    if not prompt or NOISE.search(prompt) or not CORRECTION.search(prompt):
        return

    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": os.environ.get("CLAUDE_CODE_SESSION_ID", ""),
        "cwd": event.get("cwd", ""),
        "prompt": prompt[:2000],
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
