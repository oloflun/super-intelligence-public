#!/usr/bin/env python
"""UserPromptSubmit -- detect business-judgment intent and inject the load order.

A sibling of marketing-intent.py / design-intent.py: same reasoning, same
fail-open shape. What this one exists for is Anton's rule that foreman
(frameworks/leadership/negotiation/storytelling/game-theory/stoic/people/
creative/thinking/decisions/writing/ai-leadership), business-principles
(sections 1-8) and the coaching protocols must NEVER need to be named --
every prompt that carries a business-judgment component gets routed to the
right grounding without the user saying "business-principles-integration" or
"§2" or "load foreman".

Deliberately lean compared to marketing-intent.py: no baton, no ledger, no KB
frontier scan. Pure regex plus one lazy json load (foreman-index.json, only
read when the gate actually fires). No LLM calls, no qmd calls -- the
10s hook budget is not a real constraint here, but nothing here does slow
work anyway.
"""

import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOME = Path(os.path.expanduser("~"))


def resolve_foreman_index() -> Path:
    """Prefer the live, growing local index on Anton's own machine; fall back
    to the bundled snapshot shipped in data/ (this file's ../../data/) so
    foreman-name lookups still work in Cowork/cloud where ~/.agents doesn't
    exist. Bundled path resolves relative to this hook's own location, which
    is CLAUDE_PLUGIN_ROOT/hooks/ wherever the plugin is installed."""
    live = HOME / ".agents" / "foreman-index.json"
    if live.exists():
        return live
    return Path(__file__).resolve().parent.parent / "data" / "foreman-index.json"


FOREMAN_INDEX = resolve_foreman_index()

KILL_SWITCH = "BUSINESS_HOOKS_DISABLED"
UNIVERSAL_KILL_SWITCH = "CLAUDE_HOOKS_DISABLED"  # shared with every other hook family


def disabled() -> bool:
    if os.environ.get(UNIVERSAL_KILL_SWITCH, "").strip() not in ("", "0", "false"):
        return True
    return os.environ.get(KILL_SWITCH, "").strip() not in ("", "0", "false")


def read_event() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def emit(context: str) -> None:
    if not context:
        return
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Exclusions -- stripped from the copy every pattern runs against, so a hit
# inside one of these spans can never count as a signal. Kept narrow on
# purpose: a false negative here just means the gate stays silent on an edge
# case, a false positive would mean legitimate words never fire at all.
# ---------------------------------------------------------------------------
NOT_BUSINESS = re.compile(
    r"\bprisv(ä|a)rd\w*"                       # "prisvärd" (good value) shares the pris stem
    r"|\b\w*_(id|ids)\b"                        # customer_id, user_ids -- identifiers
    r"|\b(customer|kund|team|user)[_-]\w+",     # customer_service, kund_id style identifiers
    re.I,
)

# A prompt dominated by code-shaped content (stack traces, file:line refs,
# function defs, shell/git/sql invocations) must not fire on a WEAK pair --
# "team" and "beslut" both show up in ordinary engineering prose. STRONG
# terms are unambiguous enough to still fire even inside a code-heavy prompt
# (e.g. "ska jag höja priset OCH refaktorera checkout-koden" is legitimately
# both), so the guard only suppresses the WEAK path.
CODE_SHAPED = re.compile(
    r"Traceback \(most recent call last\)|SyntaxError|TypeError|ImportError|"
    r"ModuleNotFoundError|ReferenceError|NullPointerException|"
    r"\b\w+\.(py|ts|tsx|js|jsx|go|rs|java|cs|cpp|c|rb|php):\d+|"
    r"\bdef \w+\(|\bfunction \w+\(|=>\s*\{|"
    r"\bgit (rebase|merge|commit|push|pull|checkout)\b|"
    r"\bnpm (run|install|test)\b|"
    r"\bSELECT\b.{0,60}\bFROM\b|"
    r"\b(CI|build|pipeline)[- ]?(bygget)?\s*(fail|failar|misslyckas)",
    re.I,
)

# ---------------------------------------------------------------------------
# Vocabulary. Every group is tagged with the business-principles section(s)
# (§1-§8, per anton-principles/skills/business-principles-integration's
# routing table) it most plausibly grounds. STRONG fires alone. WEAK needs a
# second distinct WEAK group, or one WEAK group plus a decision-framing
# "surface" phrase ("borde jag", "ska jag", "hur vet jag om...").
# ---------------------------------------------------------------------------
STRONG_GROUPS = [
    (re.compile(r"\bprissätt\w*|\bpricing\w*", re.I), ("§2",)),
    (re.compile(r"\bstrategi\w*|\bstrategy\w*|\bstrategisk\w*", re.I), ("§2",)),
    (re.compile(r"\bkonkurrent\w*|\bcompetitor\w*", re.I), ("§2",)),
    (re.compile(r"\bf(ö|o)rhandl\w*|\bnegotiat\w*", re.I), ("§2", "§3")),
    (re.compile(r"\bpivot\w*", re.I), ("§2",)),
    (re.compile(r"\bkapital\b|\bkapitalet\b|\bfunding\w*|\binvesterare\w*|\binvestor\w*", re.I), ("§2",)),
    (re.compile(r"\baff(ä|a)rsmodell\w*|\bbusiness\s*model\w*", re.I), ("§2",)),
    (re.compile(r"\bmarginal(en|er)?\b", re.I), ("§2",)),
    (re.compile(r"\banst(ä|a)ll\w*|\bhiring\b|\bhire[sd]?\b|\brekryter\w*|"
                r"\bavsked\w*|\bsparka\w*|\bfire (someone|him|her|them)\b", re.I), ("§3",)),
    (re.compile(r"\btillv(ä|a)xt\w*|\bgrowth\b", re.I), ("§5",)),
    (re.compile(
        r"prioritera\s+mellan|"
        r"\btv(å|a)\s+(projekt|uppgifter|alternativ|options?)\b.{0,60}\bvilket\b|"
        r"\bvilket\s+(projekt|alternativ)\s+ska jag\b",
        re.I), ("§4", "§7")),
]

# (protocol letter, pattern). See business-coaching-protocols/SKILL.md:
# A = stuck, B = big decision, C = team question, D = mindset/frustration.
COACHING_TRIGGERS = [
    ("A", re.compile(r"\bjag (ä|a)r fast\b|\bfast i (det|detta|beslutet)\b|"
                      r"\bk(ä|a)nns tungt\b|\bv(ä|a)rt att forts(ä|a)tta\b|"
                      r"\bvet inte (om|vad) jag (ska|borde)\b|\bstuck\b", re.I)),
    ("B", re.compile(r"\bstort beslut\b|\bbig decision\b", re.I)),
    ("D", re.compile(r"\btappat gnistan\b|\benergi\w* (ä|a)r (helt )?slut\b|"
                      r"\bhelt slut\b|\borkar inte l(ä|a)ngre\b|\btappat motivationen\b", re.I)),
]
COACHING_DOMAINS = ("§1", "§7")

WEAK_GROUPS = [
    (re.compile(r"\bpris\b|\bpriset\b|\bpriser\b|\bpriserna\b", re.I), ("§2",)),
    (re.compile(r"\brabatt\w*", re.I), ("§2",)),
    (re.compile(r"\bkund\w*|\bcustomer\w*", re.I), ("§5",)),
    (re.compile(r"\bteam\w*\b", re.I), ("§3",)),
    (re.compile(r"\bdel(ä|a)gare\w*|\bmedgrundare\w*|\bco-?founder\w*", re.I), ("§3",)),
    (re.compile(r"\bbeslut\w*|\bdecision\w*", re.I), ("§1",)),
    (re.compile(r"\bs(ä|a)lj\w*|\bsell\w*|\bsale\w*", re.I), ("§5",)),
    (re.compile(r"\bprodukt\w*|\bproduct\w*", re.I), ("§6",)),
    (re.compile(r"\blansera\w*|\blaunch\w*", re.I), ("§2",)),
    (re.compile(r"\bm(å|a)l(et|en)?\b|\bgoals?\b", re.I), ("§1",)),
    (re.compile(r"\benergi\w*|\bmotivation\w*", re.I), ("§1",)),
    (re.compile(r"\bledarskap\w*|\bleadership\b", re.I), ("§3",)),
    (re.compile(r"\bdelegera\w*|\bdelegat\w*", re.I), ("§3",)),
    (re.compile(r"\bber(ä|a)tta\w*|\bstory\b|\bstories\b", re.I), ("§6",)),
    (re.compile(r"\brisk\w*", re.I), ("§5",)),
    (re.compile(r"\bprocess\w*", re.I), ("§4",)),
    (re.compile(r"\bnyfiken\w*", re.I), ("§6",)),
    (re.compile(r"\bv(ä|a)xa\b|\bv(ä|a)xer\b|\bv(ä|a)xte\b", re.I), ("§5",)),
]

# A decision-framing preamble. On its own it proves nothing (every question
# could be phrased this way), but paired with one WEAK business term it is
# exactly the shape of a judgment call: "hur vet jag om appen är redo att
# växa?", "borde jag ta in en delägare?".
SURFACE = re.compile(
    r"\bborde jag\b|\bska jag\b|\bb(ö|o)r jag\b|\bshould i\b|"
    r"\bhur vet jag om\b|\bvet jag om\b", re.I)

# Compact copy of marketing-intent.py's STRONG_INTENT -- the discriminating
# GTM-only terms. Not imported (business-intent.py must not depend on
# marketing_hook_lib), duplicated deliberately so this file has zero import
# surface beyond the stdlib. Coordination rule: business yields when one of
# these fires and business has no STRONG (or coaching) signal of its own --
# i.e. the prompt is GTM-only. A prompt with both fires both hooks; that's
# by design.
MARKETING_STRONG_COMPACT = re.compile(
    r"\b(marketing|marknadsf(ö|o)ring|campaign|kampanj|reklam|annons(er|ering)?|"
    r"copywriting|tagline|slogan|seo|serp|aso|content\s*strategy|"
    r"inneh(å|a)llsstrategi|newsletter|nyhetsbrev|cold\s*email|kallmail|"
    r"ppc|roas|cpa|retarget|ad\s*creative|cro|funnel|tratt|paywall|"
    r"positioning|positionering|icp|jtbd|customer\s*research|kundresearch|"
    r"lead\s*magnet|gtm|go.to.market)\w*",
    re.I,
)

SECTION_FILES = {
    "§1": "01-1-mindset-det-inre-spelet",
    "§2": "02-2-strategi-hur-man-tanker-om-affarer",
    "§3": "03-3-talang-manniskor-och-team",
    "§4": "04-4-exekvering-hur-man-far-saker-gjorda",
    "§5": "05-5-tillvaxt-skala-och-uthallighet",
    "§6": "06-6-skapande-produkt-och-innovation",
    "§7": "07-7-implementering-fran-insikt-till-handling",
    "§8": "08-8-lokal-ai-affarsmodeller-i-agent-eran",
}

# Which foreman-index.json categories to search per § domain, for the
# "1-2 best matching foreman skill names" the brief block points at.
FOREMAN_CATEGORY_BY_DOMAIN = {
    "§1": ("stoic", "decisions", "thinking"),
    "§2": ("frameworks", "negotiation", "game-theory"),
    "§3": ("leadership", "people", "negotiation"),
    "§4": ("frameworks", "decisions"),
    "§5": ("frameworks", "leadership"),
    "§6": ("creative", "thinking", "storytelling"),
    "§7": ("decisions", "frameworks"),
    "§8": ("ai-leadership", "frameworks"),
}

_WORD = re.compile(r"[a-zA-ZåäöÅÄÖ]{4,}")

# foreman skill names/tags are English. A raw token-overlap score against a
# Swedish prompt is close to always zero, which silently degrades picks to
# alphabetical order. This bridges the handful of concept words that recur in
# the business vocabulary above -- not a translator, just enough to make the
# ranking mean something.
SV_EN_BRIDGE = {
    "beslut": ("decision", "decisions"),
    "fast": ("stuck", "paralysis"),
    "team": ("team",),
    "anst(ä|a)ll": ("hiring",),
    "rekryter": ("hiring", "recruit"),
    "konkurrent": ("competitor", "competition"),
    "f(ö|o)rhandl": ("negotiation", "negotiate"),
    "tillv(ä|a)xt": ("growth",),
    "v(ä|a)x": ("growth",),
    "ledarskap": ("leadership",),
    "produkt": ("product",),
    "risk": ("risk",),
    "strategi": ("strategy", "strategic"),
    "kapital": ("capital", "funding"),
    "marginal": ("margin",),
    "kund": ("customer",),
    "nyfiken": ("curiosity",),
    "energi": ("energy", "motivation"),
    "gnistan": ("motivation", "flow"),
    "del(ä|a)gare": ("partnership", "cofounder"),
    "prissätt": ("pricing",),
}


def clean(prompt: str) -> str:
    return NOT_BUSINESS.sub(" ", prompt or "")


def match_strong(text: str):
    return [domains for rx, domains in STRONG_GROUPS if rx.search(text)]


def match_coaching(text: str):
    return [label for label, rx in COACHING_TRIGGERS if rx.search(text)]


def match_weak(text: str):
    labels, domains = [], set()
    for rx, doms in WEAK_GROUPS:
        m = rx.search(text)
        if m:
            labels.append(m.group(0).lower())
            domains.update(doms)
    return labels, domains


def analyze(prompt: str):
    """-> (fire, domains:set, coaching_labels:list, business_strong:bool)"""
    text = clean(prompt)
    code_dominated = bool(CODE_SHAPED.search(prompt or ""))

    strong_hits = match_strong(text)
    coaching_hits = match_coaching(text)
    business_strong = bool(strong_hits) or bool(coaching_hits)

    domains = set()
    for doms in strong_hits:
        domains.update(doms)
    if coaching_hits:
        domains.update(COACHING_DOMAINS)

    weak_fire = False
    if not code_dominated:
        weak_labels, weak_domains = match_weak(text)
        if len(set(weak_labels)) >= 2 or (len(weak_labels) >= 1 and SURFACE.search(text)):
            weak_fire = True
            domains.update(weak_domains)

    fire = business_strong or weak_fire
    return fire, domains, coaching_hits, business_strong


def foreman_picks(domains, prompt: str):
    if not domains:
        return []
    try:
        idx = json.loads(FOREMAN_INDEX.read_text(encoding="utf-8"))
    except Exception:
        return []
    cat_rank = {}
    for d in domains:
        for i, c in enumerate(FOREMAN_CATEGORY_BY_DOMAIN.get(d, ())):
            cat_rank[c] = min(i, cat_rank.get(c, 99))
    if not cat_rank:
        return []

    low = (prompt or "").lower()
    tokens = {w.lower() for w in _WORD.findall(prompt or "")}
    for stem, bridged in SV_EN_BRIDGE.items():
        if re.search(stem, low, re.I):
            tokens.update(bridged)

    scored = []
    for s in idx.get("skills", []):
        cat = s.get("category")
        if cat not in cat_rank:
            continue
        bag = {w.lower() for w in _WORD.findall(
            s.get("name", "") + " " + " ".join(s.get("tags") or []))}
        overlap = len(bag & tokens)
        scored.append((-overlap, cat_rank[cat], s["name"]))
    scored.sort()
    return [name for _, _, name in scored[:2]]


def build_block(domains, coaching_labels, foreman_names) -> str:
    """Order matters: foreman is the FOUNDATION (Anton, 2026-08-28) -- the
    framework grounding loads first, business-principles-integration fills
    in on top of it, never the other way round.

    foreman_names are invoked as Skill(foreman:<name>) -- the plugin skill,
    not a local script. `python ~/.agents/scripts/foreman-core.py` only
    exists on Anton's own machine; Skill() resolves identically local,
    Cowork, and cloud once the foreman plugin is installed (see
    cloud-plugin-bootstrap.sh / repo .claude/settings.json enabledPlugins).
    """
    dom_list = sorted(domains, key=lambda d: int(d.lstrip("§")))
    lines = ["<business-brief>"]
    lines.append("Business-judgment intent detected. Domains: "
                 + (", ".join(dom_list) if dom_list else "unmatched -- scan KB headings") + ".")
    lines.append("1. Foreman first (the framework foundation): load "
                 + (", ".join(f"Skill(foreman:{n})" for n in foreman_names) if foreman_names
                    else "the closest matching foreman framework skill (see /foreman)")
                 + ". Reason with it BEFORE touching the KB -- it is the analytical base, "
                 "not an afterthought.")
    step = 2
    lines.append(f"{step}. Load Skill(business-principles-integration) -- check your "
                 "available-skills list for the exact name, it may be namespaced e.g. "
                 "super-intelligence:business-principles-integration. This layer fills in "
                 "on top of the foreman framework, it does not replace it.")
    step += 1
    if coaching_labels:
        proto = ", ".join(sorted(set(coaching_labels)))
        lines.append(f"{step}. Coaching trigger matched (Protocol {proto}) -- also load "
                     "Skill(business-coaching-protocols).")
        step += 1
    lines.append(f"{step}. Synthesize: foreman framework result FIRST, THEN 1-3 KB principles "
                 "cited by name + source + one-sentence application on top of it. Never "
                 "quote-dump; never force-fit if nothing fits.")
    step += 1
    lines.append(f"{step}. MARKNAD: svensk som default. Konkurrenter, prisnivaer, kanaler, "
                 "regelverk och EXEMPEL ska vara svenska/nordiska om inget annat anges -- "
                 "amerikanska bolag namns bara nar de faktiskt konkurrerar om samma svenska "
                 "kund, och da uttryckligen. Frameworken ar marknadsneutrala; kalibreringen "
                 "ar det inte. Anta aldrig amerikansk kontext tyst.")
    for d in dom_list:
        fname = SECTION_FILES.get(d)
        if fname:
            lines.append(f"   KB section for {d}: wiki/entrepreneurship/bp-sections/{fname}.md")
    lines.append("</business-brief>")
    return "\n".join(lines)


def main() -> None:
    if disabled():
        return

    event = read_event()
    prompt = (event.get("prompt") or "").strip()
    if not prompt:
        return
    if prompt.startswith("[SYSTEM NOTIFICATION") or "<task-notification>" in prompt:
        return

    fire, domains, coaching_hits, business_strong = analyze(prompt)
    if not fire:
        return

    # Coordination with marketing-intent.py: yield on a GTM-only prompt --
    # marketing's STRONG signal present, and nothing of business's own
    # STRONG/coaching vocabulary justifies firing independently.
    if MARKETING_STRONG_COMPACT.search(clean(prompt)) and not business_strong:
        return

    names = foreman_picks(domains, prompt)
    emit(build_block(domains, coaching_hits, names))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        sys.exit(0)
