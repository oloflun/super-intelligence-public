#!/usr/bin/env python
"""PreToolUse Write|Edit|MultiEdit -- the marketing write gate.

Two denials, both narrow on purpose:

  1. No `.agents/product-marketing.md`. Every one of the 40 marketingskills
     reads that file first. Without it they do not fail -- they guess the ICP,
     and the output looks fine. That is the expensive failure this blocks.

  2. Invented proof. A metric, customer count, rating, or multiplier that was
     not supplied. Same rule design enforces at gate 46.

Fires only on marketing artifacts. Source code is not this system's business,
and a false positive here blocks a write the user never asked it to police.

`MARKETING_GATE_BLOCKING=0` downgrades both to warnings without a code change.
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


CONTEXT_PATHS = (
    ".agents/product-marketing.md",
    ".claude/product-marketing.md",
    ".agents/product-marketing-context.md",
    ".claude/product-marketing-context.md",
)


def has_context(root: Path) -> bool:
    return any((root / p).exists() for p in CONTEXT_PATHS)


def main() -> None:
    if M.disabled():
        sys.exit(0)

    event = M.read_event()
    path = M.target_file(event)
    content = M.written_content(event)

    if not M.is_marketing_artifact(path, content):
        sys.exit(0)

    root = M.project_root(event)

    # The context file itself, and the baton, must always be writable --
    # otherwise the gate blocks the only thing that can satisfy it.
    low = (path or "").replace("\\", "/").lower()
    if any(c in low for c in ("product-marketing", "/.marketing/")):
        sys.exit(0)

    problems = []

    if not has_context(root):
        problems.append(
            "MISSING POSITIONING. `.agents/product-marketing.md` does not exist "
            "in this project.\n"
            "  Every marketingskill reads it first. Without it, this copy is "
            "written against a guessed ICP -- it will read fine and say nothing "
            "specific to this product.\n"
            "  Fix: invoke Skill(product-marketing). It can auto-draft from the "
            "repo (README, landing pages, package.json) and then ask you what "
            "to correct."
        )

    hits = M.invented_metrics(content)
    if hits:
        detail = "; ".join(f'"{h}" ({why})' for h, why in hits)
        problems.append(
            "INVENTED PROOF. This content carries claims that were not "
            f"supplied: {detail}.\n"
            "  Fix: use a real number the user gave you, a labelled placeholder "
            '("metric to confirm"), or restructure so the claim is not needed. '
            "Fabricated proof is the fastest way to make good copy unusable."
        )

    if not problems:
        M.log(root, event="gate-pass", file=path)
        sys.exit(0)

    reason = (
        "Marketing gate blocked this write.\n\n"
        + "\n\n".join(problems)
        + "\n\nSee ~/.agents/skills/marketing/SKILL.md. To downgrade this gate "
          "to a warning for the session, set MARKETING_GATE_BLOCKING=0."
    )

    M.log(root, event="gate-deny", file=path,
          reasons=[p.split(".")[0] for p in problems])

    if M.blocking():
        M.deny(reason)
    else:
        M.emit("PreToolUse", "<marketing-gate WARNING>\n" + reason
               + "\n</marketing-gate>")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
