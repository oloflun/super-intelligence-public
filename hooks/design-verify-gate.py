#!/usr/bin/env python
"""PreToolUse on mcp__Claude_Browser__* — inject the inspection discipline.

Fires once per session, before the first browser call, so the batching rules
and the breakpoint list are in context at the moment inspection starts rather
than in a skill the agent may not have loaded.

Never blocks. Verification is the one place where friction is pure cost — the
failure mode this addresses is inefficient inspection, not dangerous
inspection.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import design_hook_lib as L
except Exception:
    sys.exit(0)


REMINDER = """[design-verify] First browser call this session. The inspection floor:

1. Read console + network BEFORE judging the render — a layout critique of a
   page that threw on load is wasted work.
   read_console_messages · read_network_requests
2. Batch probes. ONE javascript_tool snippet returning an object, not N calls
   answering one question each. N serial calls are N full round-trips.
3. Sweep 320 / 375 / 414 / 768 via resize_window. Not "it looks responsive."
4. JUDGE FROM PIXELS. Every visual claim rests on a screenshot that was
   actually Read into context — read_page verifies text and structure but
   never looks; it is a supplement, not a substitute. If the pane cannot
   produce a screenshot, fall back to Playwright → PNG → Read (Skill(design)
   Step 5); never downgrade to DOM or computed-style assertions.
5. Never clear localStorage / sessionStorage / indexedDB — that storage is
   shared with the user's live view and may hold their work.
6. javascript_tool is for inspection only. Never implement UI changes through
   it; a fix that exists only in the live DOM vanishes on reload.
7. Iterate until a full pass finds NOTHING — every round that finds a defect
   obliges another round. Then say plainly that the pass came back clean, and
   whether the result honestly beats the references named before the build.

Full checklist: Skill(design-verify)."""


def main() -> None:
    if L.disabled():
        return
    event = L.read_event()
    name = L.tool_name(event)
    if not (name.startswith("mcp__Claude_Browser__")
            or name.startswith("mcp__claude-in-chrome__")):
        return

    root = L.project_root(event)
    if not L.once_per_session(root, "verify-discipline"):
        return

    L.log(root, event="verify", tier=L.tier(root), detail="discipline injected")
    L.emit("PreToolUse", REMINDER)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
