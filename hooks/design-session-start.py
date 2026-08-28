#!/usr/bin/env python
"""SessionStart — make session-scoped hook state actually session-scoped.

The chain's dedup flags (.once-*, .design-verb, .stop-signature) were written
once and never cleared, so "once per session" silently meant "once per project,
forever": the inspection floor injected on jul 28 never fired again, and a new
session whose first design verb matched the previous session's last verb got
no intent injection at all. The ledger likewise accumulated across sessions,
turning Stop reports into cross-session mush.

Runs on source=startup and source=clear only — resume and compact continue an
existing conversation, so their state is still live.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import design_hook_lib as L
except Exception:
    sys.exit(0)


def clear_root(root: Path) -> None:
    d = root / L.STATE_DIR_NAME
    if not d.is_dir():
        return
    for flag in d.glob(".once-*"):
        try:
            flag.unlink()
        except Exception:
            pass
    for name in (".design-verb", ".stop-signature", ".stop-blocks", ".linked-roots"):
        try:
            (d / name).unlink()
        except Exception:
            pass
    ledger = d / L.LEDGER_NAME
    try:
        if ledger.exists():
            prev = d / "design-session.prev.jsonl"
            if prev.exists():
                prev.unlink()
            ledger.rename(prev)
    except Exception:
        pass


def main() -> None:
    if L.disabled():
        return
    event = L.read_event()
    if event.get("source") not in ("startup", "clear"):
        return
    clear_root(L.project_root({"cwd": event.get("cwd")}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
