#!/usr/bin/env python
"""PostToolUse matcher=Skill -- the ledger, and the baton return.

Two jobs:

  1. Record which marketing skill fired, under which branch. The ledger is what
     C2 and C3 subtract against, so this hook is what makes the KB layer
     broaden across a session instead of returning the same principles.

  2. Emit the return instruction when the copy chain reaches its end against
     an open design baton. This is the second of the three return mechanisms
     -- the baton file is the state, this is the nudge, marketing-stop.py is
     the backstop.
"""

import sys
from pathlib import Path

# Kill-switchen ar inte valfri: utan den gar lagret inte att mata mot sig sjalvt,
# och en assistant-bench som kor med hookarna igang i bada armarna mater ingenting.
import os
if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).parent))

try:
    import marketing_hook_lib as M
except Exception:
    sys.exit(0)


# The skills that end the copy chain. Reaching one of these against an open
# baton means stage 5 is next, and stage 6 hands the turn back.
TERMINAL = {"humanizer", "humanizer-svenska", "copy-editing"}


def branch_of(skill: str, table: dict) -> str:
    for bid, meta in table.get("branches", {}).items():
        if skill in meta.get("skills", []):
            return bid
    return ""


def main() -> None:
    if M.disabled():
        sys.exit(0)

    event = M.read_event()
    skill = (M.tool_input(event).get("skill") or "").strip()
    if not skill:
        sys.exit(0)

    root = M.project_root(event)
    table = M.routing_table()
    bid = branch_of(skill, table)

    if not bid and skill not in TERMINAL and skill != "marketing":
        sys.exit(0)

    pin = table.get("pins", {}).get(skill)
    M.log(root, event="skill", skill=skill, branch=bid,
          principles=[pin] if pin else [])

    if skill not in TERMINAL:
        sys.exit(0)

    baton = M.read_baton(root)
    if (baton.get("status") or "") != "open":
        sys.exit(0)

    langs = baton.get("languages") or ["en"]
    want = {"humanizer-svenska" if x == "sv" else "humanizer" for x in langs}
    ran = {r.get("skill") for r in M.read_ledger(root) if r.get("event") == "skill"}
    outstanding = sorted(want - ran)

    if outstanding:
        M.emit("PostToolUse",
               "<marketing-chain>\n"
               f"Baton languages are {langs}. Still to run: "
               f"{', '.join(outstanding)}.\n"
               "One run per language actually present -- running one and "
               "assuming the other is covered is skipping a step.\n"
               "</marketing-chain>")
        return

    M.emit("PostToolUse",
           "<marketing-chain>\n"
           "Humanizer done for every language on the baton. Next, in order:\n"
           "  1. copy-chain.md stage 5 -- audit against the stage-2 output. "
           "Five checks: no claim changed meaning, no invented proof, voice "
           "held, zero em-dashes, no translation.\n"
           f"  2. On pass: fill artifact + audit in .marketing/handoff.md, flip "
           f"status to `returned`, invoke Skill(design) verb=verify.\n"
           f"     On fail: back to stage 2 with the findings, cycle "
           f"{(baton.get('cycle') or 1) + 1}. Hard cap at 2.\n"
           "</marketing-chain>")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
