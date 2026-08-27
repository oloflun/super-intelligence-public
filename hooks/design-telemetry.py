#!/usr/bin/env python
"""PostToolUse on Skill — attribute every skill invocation to a component.

Without this there is no way to tell whether the router worked or whether a
good result was luck. It answers one question the transcript cannot:

    did the skill the router named actually get loaded?

Correlation is positional: a skill call is attributed to the most recent
`edit` in the ledger. That is right for the normal build rhythm (edit a
component, then load the skill for it) and approximate when the agent loads
several skills up front. Approximate attribution is still far better than
none — the route-vs-invocation gap in the report only counts whether a named
skill was ever invoked, so front-loading does not create false gaps.

Emits nothing into context. Pure instrumentation.
"""

import os
import sys
from pathlib import Path

if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).parent))

try:
    import design_hook_lib as L
except Exception:
    sys.exit(0)


def main() -> None:
    if L.disabled():
        return
    event = L.read_event()
    if L.tool_name(event) != "Skill":
        return

    ti = L.tool_input(event)
    skill = ti.get("skill") or ti.get("name") or ""
    if not skill:
        return

    root = L.project_root(event)

    # Attribute to the component most recently edited.
    component, file_path = "", ""
    for row in reversed(L.read_ledger(root)):
        if row.get("event") == "edit":
            component = row.get("component", "")
            file_path = row.get("file", "")
            break

    L.log(root, event="skill", skill=skill, component=component,
          file=file_path, tier=L.tier(root), detail=ti.get("args", "") or "")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
