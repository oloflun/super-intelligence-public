#!/usr/bin/env python
"""UserPromptSubmit — detect design intent and inject the gate order.

Deliberately a SIBLING of carl-hook.py rather than an edit to it. Claude Code
runs every hook registered for an event, so this achieves the same injection
with zero regression risk to a 921-line file that carries the user's whole
CARL setup.

What it adds that CARL's static DESIGN rules cannot: the *current project's*
state — which tier is in force and what the locked tokens actually are. That
turns "derive from the brand" from advice into a specific instruction naming
specific values.

Turn-boundary injection is the weakest link in the chain by design; the
per-edit hooks are what actually hold across a long session. This exists so
the gate order is in context before the first edit, not to carry the session.
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


# Multilingual. Swedish included because the user works in it.
#
# Signal-gated (idea-2ao): a bare keyword match fired on any prompt containing
# "font", "nav" or "komponent" in any context — architecture plans, orchestration
# reports, backend work. Two tiers now: STRONG words are unambiguous design
# intent and fire alone; WEAK words are common in non-design prose and need at
# least two DISTINCT hits to fire.
STRONG_INTENT = re.compile(
    r"\b("
    r"design|designa|redesign|omdesign|"
    r"ui|ux|frontend|front-end|"
    r"landing\s*page|landningssida|hero|cta|bento|pricing\s*page|"
    r"styling|css|tailwind|"
    r"typograf|typograph|palette|palett|"
    r"premiumk(ä|a)nsla|"
    r"mockup|wireframe|"
    r"bygg en sida|build a (page|site|landing)|make it look"
    r")\b",
    re.I,
)
WEAK_INTENT = re.compile(
    r"\b("
    r"g(ö|o)r om|styl|style|layout|font|f(ä|a)rg|colou?r|"
    r"animation|animera|animate|motion|transition|"
    r"polish|polera|premium|skiss|"
    r"komponent|component|nav|header|footer|modal|drawer|carousel|karusell"
    r")\b",
    re.I,
)


def has_intent(prompt: str) -> bool:
    if STRONG_INTENT.search(prompt):
        return True
    weak = {m.group(0).lower() for m in WEAK_INTENT.finditer(prompt)}
    return len(weak) >= 2


# Verb detection. The pre-2026-07-28 system routed by component but never by
# task type, so build / redesign / audit / polish / study all got identical
# treatment. Order matters: the first match wins, so the more specific and
# more destructive verbs are checked first.
VERBS = [
    ("redesign", re.compile(
        r"\b(redesign|omdesign|rebuild|bygg om|g(ö|o)r om|modernise|modernize|"
        r"overhaul|revamp|refresh the (design|look|site)|nytt utseende)\b", re.I)),
    ("system", re.compile(
        r"\b(design system|designsystem|brand kit|brandkit|design tokens|"
        r"token(s)? for the whole|style guide|styleguide)\b", re.I)),
    ("audit", re.compile(
        r"\b(audit|granska|review the (design|ui|page)|design review|"
        r"what('s| is) wrong with|check (this|the) (ui|design|page))\b", re.I)),
    ("study", re.compile(
        r"\b(study|extract the design|match this|like this site|"
        r"same (style|look) as|h(ä|a)rma|kopiera stilen)\b", re.I)),
    ("explore", re.compile(
        r"\b(options|variants|varianter|explore|brainstorm|"
        r"show me (some )?(directions|ideas|options)|wireframe|skiss)\b", re.I)),
    ("polish", re.compile(
        r"\b(polish|polera|finishing touches|tighten|finputsa|"
        r"feels? (off|slow|wrong)|make it (feel|look) better)\b", re.I)),
    ("verify", re.compile(
        r"\b(verify|screenshot|does it look right|check it renders|"
        r"responsive check|kolla att)\b", re.I)),
]

# One line per verb naming the procedure that owns it. Kept terse on purpose —
# a paragraph here gets skipped by turn three of a long build.
VERB_ROUTE = {
    "redesign": ("REDESIGN — three procedures, run in this order (see "
                 "references/skill-orchestration.md §3):\n"
                 "  1. Mode detection: scope-discipline.md § Redesign protocol "
                 "— greenfield / preserve / overhaul, audit before touching, "
                 "SEO + IA + analytics preservation.\n"
                 "  2. Tier gate: does brand evidence survive? A partial "
                 "rebrand (new name, kept traits) is PRESERVE, not greenfield.\n"
                 "  3. Page shape: verbs/redesign.md — single-page vs "
                 "multi-page split, section rhythm, component voice.\n"
                 "  Mode beats tier beats page shape. Do NOT also run "
                 "redesign-existing-projects (redundant)."),
    "system":   ("SYSTEM — invoke Skill(brand-system). It emits a "
                 "{brand}-design skill plus DESIGN.md via `impeccable "
                 "document`. Only write DESIGN.md through that path."),
    "audit":    ("AUDIT — read-only. references/verbs/audit.md for severity "
                 "grading, stamp-lies and design-system drift. Then "
                 "`impeccable detect` for the mechanical pass. Do NOT edit "
                 "while auditing; fixes are a separate pass."),
    "study":    ("STUDY — Tier 2. references/study.md for the DNA, "
                 "extract-design for hard tokens. Borrow principle, never "
                 "pixel. Mix sources; never clone one."),
    "explore":  ("EXPLORE — low fidelity first: references/wireframe.md "
                 "(3-5 genuinely different approaches), presented via "
                 "references/options.md. Do not write production code yet."),
    "polish":   ("POLISH — direction is already settled; do not re-open it. "
                 "`impeccable polish`, plus emil-design-eng for anything that "
                 "moves. Note: the standalone `polish` skill has a stale "
                 "/teach-impeccable dependency (v3 naming) — prefer "
                 "`impeccable polish`."),
    "verify":   ("VERIFY — invoke Skill(design-verify). Console + network "
                 "before judging the render, all four breakpoints, batched "
                 "probes, never clear storage."),
}


def detect_verb(prompt: str) -> str:
    for name, rx in VERBS:
        if rx.search(prompt):
            return name
    return "build"


def main() -> None:
    if L.disabled():
        return
    event = L.read_event()

    prompt = (event.get("prompt") or event.get("userInput")
              or event.get("message") or event.get("input") or "")
    if not prompt:
        return
    if prompt.startswith("[SYSTEM NOTIFICATION") or "<task-notification>" in prompt:
        return
    if not has_intent(prompt):
        return

    root = L.project_root(event)
    verb = detect_verb(prompt)

    # Re-fire when the task type changes, not merely once per session. A
    # mid-session pivot from "build the hero" to "now audit the whole page"
    # is exactly when the wrong procedure gets used.
    state = L.state_dir(root) / ".design-verb"
    try:
        previous = state.read_text(encoding="utf-8").strip()
    except Exception:
        previous = ""
    first_time = not previous
    changed = previous != verb
    if not (first_time or changed):
        return
    try:
        state.write_text(verb, encoding="utf-8")
    except Exception:
        pass

    lines = ["<design-gate>"]
    if changed and not first_time:
        lines.append(f"Task type changed: {previous} → {verb}.")
    lines.append("Design intent detected. Load Skill(design) before any UI decision.")
    lines.append("")
    lines.append(VERB_ROUTE.get(verb,
                 "BUILD — full flow, SKILL.md Steps 0-6."))
    lines.append("")

    dm = L.design_md(root)
    tier_now = L.tier(root)
    if dm and tier_now == "0-locked":
        tokens = L.design_tokens(root)
        lines.append(f"TIER 0 — LOCKED. {dm.name} exists at the project root.")
        lines.append("Inherit the system. Do not re-derive, do not invent, do not "
                     "rotate a theme. Pages SHARE the system.")
        if tokens.get("colors"):
            lines.append("  colors: " + ", ".join(
                f"{k}={v}" for k, v in list(tokens["colors"].items())[:10]))
        if tokens.get("fonts"):
            lines.append("  fonts : " + ", ".join(tokens["fonts"][:5]))
        if tokens.get("radii"):
            lines.append("  radii : " + ", ".join(tokens["radii"][:8]))
        lines.append("Every colour and face in your output references one of these.")
    elif dm:
        lines.append(f"TIER 0 — PROSE ONLY. {dm.name} exists but carries no "
                     f"machine-readable token frontmatter.")
        lines.append("Treat it as AUTHORITY, but know the contract gate is BLIND "
                     "to it — design-gate.py cannot deny an off-brand write here.")
        lines.append("Read the file in full and obey it yourself. To get "
                     "mechanical enforcement, run `$impeccable document` to "
                     "regenerate it with token frontmatter.")
        lines.append("(This shape is what design-md, gstack's "
                     "design-consultation, and hand-written files produce.)")
    else:
        lines.append("No DESIGN.md — run the gate before picking anything:")
        lines.append("  Tier 1 DERIVE   logo/wordmark, brand hex, deployed site, "
                     "tailwind colours, favicon → derive from that evidence")
        lines.append("  Tier 2 REFERENCE a URL or screenshot was given → study it, "
                     "borrow principle not pixel")
        lines.append("  Tier 3 INVENT    genuinely nothing, or the user said "
                     "'wing it' → only then invent or reach for a theme")
        lines.append("First tier with evidence wins. Say which tier you are in "
                     "before picking a token.")

    lines.append("")
    lines.append("NEVER let minimalist-ui, industrial-brutalist-ui, or "
                 "high-end-visual-design set direction — each hardcodes a full "
                 "palette. Gate 60 denies their hex values in a locked project.")
    lines.append("</design-gate>")

    L.log(root, event="intent", tier=tier_now, signal=verb,
          detail=f"verb={verb}" + (f" (was {previous})" if changed and previous else ""))
    L.emit("UserPromptSubmit", "\n".join(lines))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
