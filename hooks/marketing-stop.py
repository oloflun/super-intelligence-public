#!/usr/bin/env python
"""Stop -- the backstop that keeps a handoff from being silently abandoned.

The turn cannot end while a copy baton is open. This is the third of the three
return mechanisms and the only one that does not depend on the model noticing
anything: the baton is state on disk, and this reads it.

Capped at 2 blocks per session, exactly as design-stop.py caps its exit-bar
block. A backstop that can never be escaped is a trap, not a guardrail -- if
two blocks do not resolve it, something is wrong that blocking will not fix,
and the user needs to see the problem rather than fight the hook.
"""

import json
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

MAX_BLOCKS = 2


def main() -> None:
    if M.disabled():
        sys.exit(0)

    event = M.read_event()
    root = M.project_root(event)
    baton = M.read_baton(root)

    if (baton.get("status") or "") != "open":
        sys.exit(0)

    counter = M.state_dir(root) / ".stop-blocks"
    try:
        n = int(counter.read_text(encoding="utf-8").strip() or "0")
    except Exception:
        n = 0

    if n >= MAX_BLOCKS:
        # Degrade to a visible warning rather than trapping the session.
        M.log(root, event="stop-giveup", surface=baton.get("surface"))
        print(
            "marketing: a copy baton at .marketing/handoff.md is still open "
            f"for {baton.get('surface')} after {MAX_BLOCKS} blocks. Not "
            "blocking again. Either finish the chain, or delete the baton if "
            "it is stale.",
            file=sys.stderr,
        )
        sys.exit(0)

    try:
        counter.write_text(str(n + 1), encoding="utf-8")
    except Exception:
        pass

    cycle = baton.get("cycle") or 1
    langs = baton.get("languages") or ["en"]
    hz = ", ".join("humanizer-svenska" if x == "sv" else "humanizer" for x in langs)

    M.log(root, event="stop-block", surface=baton.get("surface"), cycle=cycle)

    reason = (
        "A copy baton is still OPEN -- the turn cannot end mid-handoff.\n\n"
        f"  .marketing/handoff.md\n"
        f"    caller:    {baton.get('caller')}\n"
        f"    surface:   {baton.get('surface')}\n"
        f"    languages: {langs}\n"
        f"    cycle:     {cycle}\n\n"
        "Finish references/copy-chain.md:\n"
        "  1. Stages 1-4 if not done -- positioning, write, sweep, then "
        f"{hz}.\n"
        "  2. Stage 5 audit against the stage-2 output.\n"
        "  3. Stage 6: on pass, fill artifact + audit, flip status to "
        "`returned`, invoke Skill(design) verb=verify. On fail, back to "
        f"stage 2 at cycle {cycle + 1} (hard cap 2).\n\n"
        "If this baton is stale, delete .marketing/handoff.md and say so."
    )
    print(json.dumps({"decision": "block", "reason": reason}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
