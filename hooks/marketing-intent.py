#!/usr/bin/env python
"""UserPromptSubmit -- detect marketing intent and inject the load order.

A sibling of design-intent.py, same reasoning: Claude Code runs every hook
registered for an event, so this injects alongside the design gate with zero
regression risk to a file carrying the whole design system.

What it adds that a skill description cannot: the *routed* branch set for this
specific prompt, what the session ledger already pulled (so the KB layer
broadens instead of repeating), and whether a design baton is open.

Turn-boundary injection is the weakest link by design; the per-edit and Stop
hooks are what hold across a long session. This exists so the route is in
context before the first tool call.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import marketing_hook_lib as M
except Exception:
    sys.exit(0)


# Multilingual. Swedish included because the user works in it.
#
# Signal-gated (idea-2ao, same fix as design-intent): a bare keyword match
# fired on any prompt containing "post", "email" or "launch" in any context —
# orchestration reports, infrastructure work, plain conversation. STRONG words
# are unambiguous marketing intent and fire alone; WEAK words are common in
# non-marketing prose and need at least two DISTINCT hits.
#
# Trailing \w* rather than \b: Swedish compounds are written solid, so
# "konverteringsflödet", "marknadsföringsplan" and "reklamkampanj" all fail a
# trailing word boundary. The leading \b still blocks mid-word matches.
STRONG_INTENT = re.compile(
    r"\b("
    r"marketing|marknadsf(ö|o)ring|"
    r"campaign|kampanj|reklam|annons(er|ering)?|"
    r"copywriting|tagline|slogan|"
    r"seo|serp|aso|"
    r"content\s*strategy|inneh(å|a)llsstrategi|"
    r"newsletter|nyhetsbrev|cold\s*email|kallmail|"
    r"ppc|roas|cpa|retarget|ad\s*creative|"
    r"cro|funnel|tratt|paywall|"
    r"positioning|positionering|icp|jtbd|"
    r"customer\s*research|kundresearch|"
    r"lead\s*magnet|gtm|go.to.market"
    r")\w*",
    re.I,
)
WEAK_INTENT = re.compile(
    r"\b("
    r"copy|headline|rubrik|keyword|s(ö|o)kord|blogg|blog\s*post|"
    r"email|mejl|utskick|"
    r"social(\s*media)?|linkedin|instagram|tiktok|reels|inl(ä|a)gg|post(a|ar|ning)?|publicera|"
    r"ads|conversion|konvertering|signup|onboarding|popup|"
    r"pricing|priss(ä|a)ttning|launch|lansering|"
    r"competitor|konkurrent|m(å|a)lgrupp|persona|"
    r"referral|churn|retention|community|"
    r"growth|tillv(ä|a)xt"
    r")\w*",
    re.I,
)


def has_intent(prompt: str) -> bool:
    if STRONG_INTENT.search(prompt):
        return True
    weak = {m.group(1).lower() for m in WEAK_INTENT.finditer(prompt)}
    if len(weak) >= 2:
        return True
    # One weak word IS a signal when a new customer-facing surface is named:
    # "skriv copy till nya landningssidan" must reach the chain.
    return len(weak) >= 1 and bool(NEW_SURFACE.search(prompt))

# Words that share a prefix with an intent term but are not marketing.
# Cheaper than tightening every alternation above.
NOT_MARKETING = re.compile(r"\bcopyright|copyleft\b", re.I)

VERBS = [
    ("audit", re.compile(
        r"\b(audit|granska|review the (copy|campaign|funnel|marketing)|"
        r"what.s wrong with (the|our) (copy|campaign|page)|kolla igenom)\b", re.I)),
    ("research", re.compile(
        r"\b(customer research|kundresearch|interview|intervju|icp|persona|jtbd|"
        r"voice of customer|review mining|research (the|our) (customers|market)|"
        r"competitor (research|profil)|konkurrentanalys)\b", re.I)),
    ("measure", re.compile(
        r"\b(analytics|attribution|a/?b test|ab.test|significance|conversion rate|"
        r"m(ä|a)t|m(ä|a)tning|track(ing)?|instrument|roas|cpa)\b", re.I)),
    ("launch", re.compile(
        r"\b(launch|lansering|go.to.market|gtm|ship (the|our) (product|feature) to)\b", re.I)),
    ("plan", re.compile(
        r"\b(strategy|strategi|plan|roadmap|calendar|kalender|"
        r"what should (i|we) (write|post|make)|vad ska vi (skriva|posta)|"
        r"content plan|topic cluster|ideas|id(é|e)er)\b", re.I)),
]


def detect_verb(prompt: str) -> str:
    for name, rx in VERBS:
        if rx.search(prompt):
            return name
    return "create"


def match_surfaces(prompt: str, table: dict) -> list:
    """Match on a leading word boundary, never raw substring.

    Raw `in` matching routed "redo the copy on the leads app" to `paid-ads`,
    because "leads" contains "ads". Short terms are common substrings of
    unrelated words and a confident wrong route is worse than no route.

    Trailing \\w* is kept deliberately: Swedish compounds are solid, so
    "social media" must still hit "social media-reklamkampanj" and
    "konvertering" must hit "konverteringsflodet".
    """
    low = prompt.lower()
    hits = []
    for s in table.get("surfaces", []):
        for m in s.get("match", []):
            if re.search(r"\b" + re.escape(m) + r"\w*", low):
                hits.append(s)
                break
    return hits


# A design build that will CONTAIN customer-facing text. These prompts carry
# no marketing vocabulary, but the copy on a NEW surface still needs the chain
# (Antons regel 2026-08-25): nytt kundfaceande innehall => copy-kedjan MASTE
# kora via batonen; befintlig text => bevaras ordagrant, ingen kedja.
NEW_SURFACE = re.compile(
    r"\b(landing\s*page|landningssida|"
    r"bygg en (sida|hemsida|site|webbplats)|build a (page|site|landing)|"
    r"ny (sida|hemsida|webbplats)|designa en (sida|site|hemsida)|"
    r"pricing\s*page|prissida|hemsida|webbplats|website|"
    r"hero|onboarding)\w*", re.I)


def secondary_block() -> str:
    return (
        "<marketing SECONDARY>\n"
        "Design owns this turn. Marketing is not primary.\n"
        "NEW customer-facing text on this surface => the copy chain MUST run: "
        "/design Step 6 opens the baton (.marketing/handoff.md) and the chain "
        "(positioning -> write -> sweep -> humanizer per language -> stage-5 "
        "audit) delivers the copy. Never ship placeholder or first-draft copy "
        "on a new surface.\n"
        "EXISTING copy with no copy work asked for => PRESERVE IT VERBATIM -- "
        "do not rewrite, do not open a baton, do not 'improve' it in passing. "
        "Copy that already tested well is a winner, and rewriting it for "
        "novelty costs real quality.\n"
        "</marketing SECONDARY>"
    )


DESIGN_CLAIM = re.compile(
    r"\b(design|designa|redesign|omdesign|ui|ux|frontend|layout|"
    r"typograf|palette|palett|animation|animera|motion|"
    r"bygg en sida|build a (page|site|landing)|component|komponent|"
    r"hero|bento|mockup|wireframe|css|tailwind)\b", re.I)


def main() -> None:
    if M.disabled():
        sys.exit(0)

    event = M.read_event()
    prompt = (event.get("prompt") or "").strip()
    if not prompt:
        sys.exit(0)
    if prompt.startswith("[SYSTEM NOTIFICATION") or "<task-notification>" in prompt:
        sys.exit(0)

    root = M.project_root(event)
    table = M.routing_table()

    # The only hook that sees the user's prompt, so it is the only one that can
    # decide whether copy was asked for. Later hooks read the flag rather than
    # reconstructing intent from tool arguments -- an earlier version tried
    # that and matched "copy" in the FILE PATH, which made the rule inert.
    if M.COPY_REQUESTED.search(prompt):
        M.mark_copy_requested(root)

    # ---- Step 0: an open baton beats every other consideration -------------
    baton = M.read_baton(root)
    if (baton.get("status") or "") == "open":
        M.emit("UserPromptSubmit", (
            "<marketing-baton>\n"
            "An OPEN copy baton exists at .marketing/handoff.md.\n"
            f"  caller: {baton.get('caller')}  surface: {baton.get('surface')}  "
            f"cycle: {baton.get('cycle')}  languages: {baton.get('languages')}\n"
            "Skill(marketing) owns this turn. Run references/copy-chain.md stages 1-6.\n"
            "Do NOT re-derive the brand -- tier is inherited from the baton.\n"
            "The chain ends by flipping the baton to `returned` and invoking "
            "Skill(design) verb=verify.\n"
            "</marketing-baton>"
        ))
        return

    if not has_intent(prompt) or NOT_MARKETING.search(prompt):
        # A pure design prompt has no marketing words, but a NEW surface still
        # ships customer-facing copy -- hand design the baton rule so the copy
        # chain runs exactly when new text gets written.
        if NEW_SURFACE.search(prompt) and not NOT_MARKETING.search(prompt):
            M.emit("UserPromptSubmit", secondary_block())
        sys.exit(0)

    # ---- Entry precedence: design owns its own builds ----------------------
    # Only demote when design's claim is the STRONGER read. "landing page copy"
    # is marketing; "build a landing page" is design.
    if DESIGN_CLAIM.search(prompt) and not M.COPY_REQUESTED.search(prompt):
        M.emit("UserPromptSubmit", secondary_block())
        return

    verb = detect_verb(prompt)
    surfaces = match_surfaces(prompt, table)

    branches = []
    for s in surfaces:
        for b in s.get("branches", []):
            if b not in branches:
                branches.append(b)
    if "00" not in branches:
        branches.insert(0, "00")
    branches.sort()

    lines = ["<marketing>", f"Marketing intent detected. Verb: {verb.upper()}."]
    lines.append(table.get("verbs", {}).get(verb, ""))

    if not surfaces:
        lines.append(
            "SURFACE AMBIGUOUS -- no routing surface matched. Read "
            "references/brief.md and ask ONE round (max 4 questions) before "
            "loading anything."
        )
    else:
        lines.append("Surfaces: " + ", ".join(s["id"] for s in surfaces))

    lines.append("")
    lines.append("LOAD ORDER (branch 00 first, always):")
    kb_groups, skills = [], []
    for b in branches:
        meta = table.get("branches", {}).get(b)
        if not meta:
            continue
        lines.append(f"  {b} {meta['title']}: references/{meta['file']}")
        lines.append("     skills: " + " · ".join(meta["skills"]))
        for g in meta.get("kb", []):
            if g not in kb_groups:
                kb_groups.append(g)
        skills.extend(meta["skills"])
        if meta.get("missing"):
            lines.append("     GAP (not installed): " + ", ".join(meta["missing"]))

    lines.append("")
    lines.append("KB -- references/kb-retrieval.md, all three channels:")
    lines.append("  C1 spine: wiki/domains/marketing/CONTEXT.md + the Cite index "
                 "table only. NEVER the whole principles file.")
    lines.append("  C2 groups (rank subsections inside these, do not pin): "
                 + " · ".join(kb_groups))
    pins = {k: v for k, v in table.get("pins", {}).items() if k in skills}
    if pins:
        lines.append("  C2 pins (load in ADDITION to the ranked picks): "
                     + " · ".join(f"{k} -> {v}" for k, v in pins.items()))

    seen_p, seen_s = M.already_loaded(root)
    if seen_p or seen_s:
        lines.append("  ALREADY LOADED this session -- subtract before ranking:")
        if seen_p:
            lines.append("     principles: " + ", ".join(sorted(seen_p)))
        if seen_s:
            lines.append("     sources: " + ", ".join(sorted(seen_s)))

    picks = M.rank_sources(prompt, seen=seen_s, terms=skills, limit=2)
    if picks:
        lines.append("  C3 candidates (best match + most recent unused):")
        for p in picks:
            lines.append(f"     {p['slug']}"
                         + (f"  themes: {', '.join(p.get('priority_themes') or [])}"
                            if p.get("priority_themes") else ""))

    if any(s in skills for s in ("copywriting", "copy-editing", "social", "emails",
                                 "cold-email", "ad-creative")):
        lines.append("")
        lines.append("COPY CHAIN applies -- references/copy-chain.md. Positioning "
                     "-> write -> sweep -> humanizer PER LANGUAGE -> stage-5 audit.")

    lines.append("</marketing>")
    M.emit("UserPromptSubmit", "\n".join(x for x in lines if x is not None))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
