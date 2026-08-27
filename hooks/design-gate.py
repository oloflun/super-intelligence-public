#!/usr/bin/env python
"""PreToolUse on Write|Edit|MultiEdit — contract enforcement.

Denies a write that violates the locked design system, so the agent sees the
correction *before* the bad value lands rather than after.

Scope is deliberately narrow. It only fires when:
  * the project has a DESIGN.md (no lock, no contract, no opinion), AND
  * the target is a UI file, AND
  * the incoming content trips a contract rule.

Everything softer — taste, rhythm, structure — is advisory and belongs to
design-route.py. A gate that denies on judgment calls stalls long sessions,
which costs more than the drift it prevents.

Two enforcement modes:
  advisory (default)  warn in context, allow the write
  blocking            deny the write
Promote with DESIGN_GATE_BLOCKING=1 once a clean run is on record.
Kill entirely with DESIGN_HOOKS_DISABLED=1.
"""

import os
import re
import sys
from pathlib import Path

if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
    sys.exit(0)

sys.path.insert(0, str(Path(__file__).parent))

try:
    import design_hook_lib as L
except Exception:
    sys.exit(0)


WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}

# Contract rules only. These read DESIGN.md directly and are unambiguous.
CONTRACT_RULES = {
    "design-system-color",
    "design-system-font",
    "design-system-font-size",
    "design-system-radius",
}

HEX_RE = re.compile(r"#[0-9a-fA-F]{6}\b")


def blocking() -> bool:
    return os.environ.get("DESIGN_GATE_BLOCKING", "").strip() not in ("", "0", "false")


def main() -> None:
    if L.disabled():
        return
    event = L.read_event()
    if L.tool_name(event) not in WRITE_TOOLS:
        return

    path = L.target_file(event)
    if not path or not L.is_ui_file(path):
        return

    root = L.project_root(event)
    if not L.design_md(root):
        return  # no locked system — nothing to enforce against

    content = L.written_content(event)
    if not content.strip():
        return

    violations = []

    # Gate 60 — demoted-skill palette. Pattern-matched, no detector needed.
    for skill, hx in L.trap_hits(content):
        violations.append((
            "gate-60",
            f"{hx} is {skill}'s hardcoded palette. This project has a locked "
            f"DESIGN.md — use its token instead."
        ))
        L.log(root, event="trap", file=path, component=L.component_of(path),
              skill=skill, detail=hx, signal="pre" if blocking() else "post")

    # Contract rules — run the real detector against a shadow copy of the
    # incoming content so we check what is about to land, not what is on disk.
    # Runs even when gate 60 already fired: one denial should name everything
    # wrong with the write, or the agent burns a round trip per violation.
    if True:
        shadow = None
        try:
            sd = L.state_dir(root) / "shadow"
            sd.mkdir(parents=True, exist_ok=True)
            shadow = sd / Path(path).name
            shadow.write_text(content, encoding="utf-8")
            findings = L.detect([str(shadow)], root, timeout=20)
            # Hand the full result to design-route.py so the detector runs once
            # per write instead of once per hook.
            L.cache_detect(root, content, findings)
            for f in findings:
                rid = f.get("antipattern", "")
                if rid in CONTRACT_RULES:
                    violations.append((rid, f.get("snippet") or f.get("name") or rid))
        except Exception:
            pass
        finally:
            try:
                if shadow and shadow.exists():
                    shadow.unlink()
            except Exception:
                pass

    if not violations:
        L.log(root, event="gate-pass", file=path,
              component=L.component_of(path), tier=L.tier(root))
        return

    tokens = L.design_tokens(root)
    hint_parts = []
    if tokens.get("colors"):
        hint_parts.append("colors: " + ", ".join(
            f"{k}={v}" for k, v in list(tokens["colors"].items())[:8]))
    if tokens.get("fonts"):
        hint_parts.append("fonts: " + ", ".join(tokens["fonts"][:4]))
    if tokens.get("radii"):
        hint_parts.append("radii: " + ", ".join(tokens["radii"][:6]))

    body = [f"DESIGN.md contract violation in {Path(path).name}:"]
    for rid, detail in violations[:6]:
        body.append(f"  · [{rid}] {detail}")
    if hint_parts:
        body.append("Locked tokens — " + " | ".join(hint_parts))
    body.append(
        "Use the locked token. If the value is genuinely new, add it to "
        "DESIGN.md first, then reference it — do not inline it."
    )
    msg = "\n".join(body)

    for rid, detail in violations[:6]:
        L.log(root, event="gate-deny", file=path, component=L.component_of(path),
              signal=rid, detail=str(detail)[:160], tier=L.tier(root))

    if blocking():
        L.deny(msg)
    else:
        L.emit("PreToolUse", "[design-gate · advisory] " + msg +
               "\n(Set DESIGN_GATE_BLOCKING=1 to make this a hard denial.)")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
