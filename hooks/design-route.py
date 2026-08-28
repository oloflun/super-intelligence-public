#!/usr/bin/env python
"""PostToolUse on Write|Edit|MultiEdit — the component router.

This is the fix for the original failure: guidance arrived once per *turn*,
but design decisions happen once per *edit*. This hook fires after every UI
file write and names the skill for what was just written.

Advisory by design. It never blocks; design-gate.py owns denial.

Output is deliberately terse — one line per route. A paragraph here would be
ignored by turn three of a long build.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import design_hook_lib as L
except Exception:
    sys.exit(0)


WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit", "apply_patch"}


def main() -> None:
    if L.disabled():
        return
    event = L.read_event()
    if L.tool_name(event) not in WRITE_TOOLS:
        return

    path = L.target_file(event)
    if not path or not L.is_ui_file(path):
        return

    content = L.written_content(event)
    root = L.project_root(event)
    component = L.component_of(path)
    tier = L.tier(root)

    # Cross-project registry: a session whose cwd is one repo often builds in
    # another (site scaffolds, worktrees). Edits land in the FILE's root ledger
    # while design-stop.py reads the CWD root's — without this pointer the Stop
    # report and the exit-bar check are blind to the whole build.
    cwd_root = L.project_root({"cwd": event.get("cwd")})
    if root != cwd_root:
        try:
            reg = L.state_dir(cwd_root) / ".linked-roots"
            existing = reg.read_text(encoding="utf-8").splitlines() if reg.exists() else []
            if str(root) not in existing:
                reg.write_text("\n".join([*existing, str(root)]) + "\n", encoding="utf-8")
        except Exception:
            pass

    routes = L.match_routes(path, content)
    signals = ",".join(r.get("id", "") for r in routes)
    L.log(root, event="edit", file=path, component=component,
          signal=signals, tier=tier)

    lines = []

    # Gate 60 — the instrumented trap. Advisory here; design-gate.py denies
    # pre-write once it is promoted to blocking.
    traps = L.trap_hits(content)
    if traps and tier != "ungated":
        for skill, hx in traps[:4]:
            L.log(root, event="trap", file=path, component=component,
                  skill=skill, detail=hx, tier=tier)
        listed = ", ".join(f"{hx} ({skill})" for skill, hx in traps[:4])
        lines.append(
            f"GATE 60 — demoted-skill palette in a locked project: {listed}. "
            f"Replace with the DESIGN.md token."
        )

    for rule in routes:
        skill = rule.get("skill", "")
        why = rule.get("why", "")
        if not skill:
            continue
        if skill == "copy-gate":
            lines.append("→ copy gate (user-facing strings) — copywriting, then humanizer")
        else:
            lines.append(f"→ {skill} ({why})")
        L.log(root, event="route", file=path, component=component,
              skill=skill, signal=rule.get("id", ""), tier=tier)

    # Deterministic rules. Reuse design-gate.py's verdict on these exact bytes
    # when it already ran this write; only pay for the detector when it didn't
    # (unlocked projects, where the gate is a no-op). The full sweep is Stop.
    findings = L.cached_detect(root, content)
    if findings is None:
        findings = L.detect([path], root)
    if findings:
        seen, shown = set(), []
        for f in findings:
            rid = f.get("antipattern") or f.get("id") or "?"
            if rid in seen:
                continue
            seen.add(rid)
            shown.append(f"{rid}: {f.get('snippet') or f.get('name') or ''}".strip())
            if len(shown) >= 5:
                break
        lines.append("detector: " + " · ".join(shown))
        contract = [f for f in findings
                    if str(f.get("antipattern", "")).startswith("design-system-")]
        if contract:
            lines.append(
                f"{len(contract)} of these are DESIGN.md contract violations — "
                f"fix against the locked token, do not add a new one."
            )

    if not lines:
        return

    header = f"[design · {component}]"
    if tier == "0-locked":
        header += " tier 0 — inherit the locked system, do not re-derive"
    L.emit("PostToolUse", header + "\n" + "\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
