#!/usr/bin/env python
"""PostToolUse on Read — record that pixels actually entered context.

The chain had no way to know whether a render was ever LOOKED at, so the Stop
report could not flag its absence and nothing could enforce the exit bar.
This hook logs a `vision` event whenever an image file is Read. design-stop.py
compares the last vision timestamp against the last UI edit: an edit nobody
looked at afterwards blocks the stop.

Logs to the session cwd's ledger and, when the image lives in another project
tree (a shots dir inside the site being built), to that root's ledger too, so
cross-project sessions stay visible from both sides.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import design_hook_lib as L
except Exception:
    sys.exit(0)

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")


def main() -> None:
    if L.disabled():
        return
    event = L.read_event()
    if L.tool_name(event) != "Read":
        return
    path = L.target_file(event)
    if not path or not path.lower().endswith(IMAGE_EXTS):
        return

    cwd_root = L.project_root({"cwd": event.get("cwd")})
    file_root = L.project_root(event)
    L.log(cwd_root, event="vision", file=path)
    if file_root != cwd_root:
        L.log(file_root, event="vision", file=path)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
