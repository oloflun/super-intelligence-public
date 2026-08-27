#!/usr/bin/env python
"""PostToolUse Write|Edit|MultiEdit -- name the next link in the chain.

A marketing artifact is almost never finished when it is written. Copy needs
its sweeps and its humanizer; ad creative needs a winner pass; a social post
needs its asset. This emits one line naming what comes next.

The chain table lives in references/routing.md and is parsed, not duplicated
here -- same contract design's component-routing.md declares. Editing the
sequence is a markdown edit.
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


# Which chain rules a written artifact plausibly sits after. Path and content
# shape decide, since the hook cannot see which skill produced the file.
SIGNALS = {
    # `creative` and `email` are here as well as in their own rules: ad and
    # email copy is still copy, and still needs the sweeps and the humanizer.
    "copy": ("copy", "headline", "landing", "hero", "page", "messaging",
             "positioning", "creative", "email", "newsletter", "social", "post"),
    "ad": ("ad-", "ads", "creative", "campaign"),
    "social": ("social", "post", "linkedin", "instagram", "tiktok", "thread"),
    "landing": ("landing", "hero", "pricing", "home"),
}


def main() -> None:
    if M.disabled():
        sys.exit(0)

    event = M.read_event()
    path = M.target_file(event)
    content = M.written_content(event)

    if not M.is_marketing_artifact(path, content):
        sys.exit(0)

    root = M.project_root(event)
    table = M.routing_table()
    stem = Path((path or "").replace("\\", "/")).stem.lower()

    fired = {cid for cid, frags in SIGNALS.items() if any(f in stem for f in frags)}
    if not fired:
        sys.exit(0)

    # The chain runs on new surfaces. A design pass over a page that already
    # has copy must not be nudged into rewriting it -- the reminder itself is
    # what turns "I changed the layout" into "while I was here I improved the
    # headline". Content is checked as it was BEFORE this write where possible.
    run, why = M.chain_applies(root, path)
    if not run:
        M.log(root, event="chain-skip", file=path, reason=why)
        sys.exit(0)

    langs = M.languages(content)
    lines = []
    for rule in table.get("chain", []):
        if rule["id"] not in fired:
            continue
        nxt = []
        for step in rule["then"]:
            if step == "humanizer-per-language":
                nxt.extend("humanizer-svenska" if lang == "sv" else "humanizer"
                           for lang in langs)
            else:
                nxt.append(step)
        lines.append(f"  -> {' then '.join(nxt)}  ({rule['why']})")

    if not lines:
        sys.exit(0)

    # Once per file per session. A chain reminder on every keystroke of a long
    # edit session is noise, and noise gets skipped.
    key = f"route-{stem}"
    if not M._once(root, key):
        sys.exit(0)

    baton = M.read_baton(root)
    tail = ""
    if (baton.get("status") or "") == "open":
        tail = ("\n  Baton is OPEN -- after the chain, run copy-chain.md stage 5 "
                "(audit), then flip to `returned` and invoke Skill(design) "
                "verb=verify.")

    M.log(root, event="route", file=path, languages=langs)
    M.emit("PostToolUse",
           "<marketing-chain>\n"
           f"{Path(path).name} written. Not finished:\n"
           + "\n".join(lines) + tail
           + "\n</marketing-chain>")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
