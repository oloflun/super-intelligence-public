#!/usr/bin/env python
"""Shared infrastructure for the marketing hook family.

A sibling of design_hook_lib.py, not a fork of it. Everything design already
solved -- event parsing, project-root discovery, deny/emit shapes, UI-file
detection -- is imported. What lives here is only what is genuinely marketing:
the `.marketing/` state dir, the design<->marketing baton, the KB frontier,
and the marketing router.

The router is parsed from references/routing.md rather than carried here, for
the same reason design parses component-routing.md: one home per fact. Adding
a skill is a markdown table row, not a code change.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import design_hook_lib as D  # noqa: E402  -- reuse, do not re-implement

HOME = Path(os.path.expanduser("~"))
SKILL = HOME / ".agents" / "skills" / "marketing"
ROUTING_DOC = SKILL / "references" / "routing.md"

KILL_SWITCH = "MARKETING_HOOKS_DISABLED"
BLOCK_SWITCH = "MARKETING_GATE_BLOCKING"
STATE_DIR_NAME = ".marketing"
LEDGER_NAME = "session.jsonl"
BATON_NAME = "handoff.md"

# The KB lives in the vault. Overridable so this is testable off a scratch dir.
KB = Path(os.environ.get(
    "MARKETING_KB",
    str(HOME / "OneDrive" / "Dokument" / "Obsidian" / "Knowledge Base" / "wiki"),
))
KB_DOMAIN = KB / "domains" / "marketing"
KB_SOURCES = KB / "sources"

# Reuse design's plumbing verbatim.
read_event = D.read_event
emit = D.emit
deny = D.deny
tool_name = D.tool_name
tool_input = D.tool_input
target_file = D.target_file
written_content = D.written_content
project_root = D.project_root


def disabled() -> bool:
    if os.environ.get(D.UNIVERSAL_KILL_SWITCH, "").strip() not in ("", "0", "false"):
        return True  # CLAUDE_HOOKS_DISABLED (Fas 6 arm B) -- shared switch, not D's own
    return os.environ.get(KILL_SWITCH, "").strip() not in ("", "0", "false")


def blocking() -> bool:
    """Gate strictness. Default ON -- dropping to advisory is an env flip."""
    return os.environ.get(BLOCK_SWITCH, "1").strip() not in ("", "0", "false")


# --------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------

def state_dir(root: Path) -> Path:
    d = root / STATE_DIR_NAME
    try:
        d.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass
    return d


def log(root: Path, **fields) -> None:
    try:
        rec = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        rec.update({k: v for k, v in fields.items() if v not in (None, "", [])})
        with (state_dir(root) / LEDGER_NAME).open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def read_ledger(root: Path) -> list[dict]:
    try:
        p = state_dir(root) / LEDGER_NAME
        if not p.exists():
            return []
        rows = []
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except Exception:
                    continue
        return rows
    except Exception:
        return []


def _once(root: Path, key: str) -> bool:
    """True the first time this key is seen in the session, False after.

    Design has the same helper, but keyed to its own state dir. A chain
    reminder re-emitted on every edit of the same file is noise, and noise
    gets skipped -- which costs the reminders that do matter.
    """
    try:
        flag = state_dir(root) / (".once-" + re.sub(r"[^a-z0-9]+", "-", key.lower()))
        if flag.exists():
            return False
        flag.write_text("1", encoding="utf-8")
        return True
    except Exception:
        return False


def already_loaded(root: Path) -> tuple[set, set]:
    """What the KB layer has already injected this session. C2/C3 subtract
    these before ranking, which is the whole anti-repetition mechanism."""
    principles, sources = set(), set()
    for row in read_ledger(root):
        for p in row.get("principles") or []:
            principles.add(p)
        for s in row.get("sources") or []:
            sources.add(s)
    return principles, sources


# --------------------------------------------------------------------------
# The baton -- design <-> marketing handoff
# --------------------------------------------------------------------------

_FM = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.S)


def baton_path(root: Path) -> Path:
    return state_dir(root) / BATON_NAME


def read_baton(root: Path) -> dict:
    """Parse the baton's YAML frontmatter. Deliberately a tiny scalar/list
    parser rather than a PyYAML dependency -- the baton has a fixed shape and
    hooks must never fail on a missing import."""
    try:
        p = baton_path(root)
        if not p.exists():
            return {}
        m = _FM.match(p.read_text(encoding="utf-8", errors="replace"))
        if not m:
            return {}
        out = {}
        for line in m.group(1).splitlines():
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if ":" not in line:
                continue
            k, _, v = line.partition(":")
            k = k.strip()
            v = v.split("#")[0].strip()
            if v.startswith("[") and v.endswith("]"):
                out[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
            elif v in ("null", "~", ""):
                out[k] = None
            elif re.fullmatch(r"-?\d+", v):
                out[k] = int(v)
            else:
                out[k] = v.strip("'\"")
        return out
    except Exception:
        return {}


def baton_open(root: Path) -> bool:
    return (read_baton(root).get("status") or "") == "open"


# --------------------------------------------------------------------------
# The KB frontier -- enumerated, never hardcoded, so it grows by itself
# --------------------------------------------------------------------------

_FM_KEYS = ("title", "captured", "ingested", "tags", "priority_themes", "show", "category")


def frontier() -> list[dict]:
    """Every marketing-categorised source, frontmatter only.

    ponytail: a linear scan of ~440 frontmatters, no index to go stale. If the
    marketing frontier ever passes a few hundred files, cache it in state_dir
    keyed on the sources/ mtime.
    """
    out = []
    try:
        for p in sorted(KB_SOURCES.glob("*.md")):
            try:
                head = p.read_text(encoding="utf-8", errors="replace")[:2400]
            except Exception:
                continue
            m = _FM.match(head)
            if not m or "Marknadsf" not in m.group(1):
                continue
            rec = {"path": str(p), "slug": p.stem}
            for line in m.group(1).splitlines():
                k, _, v = line.partition(":")
                k = k.strip()
                v = v.strip()
                if k in _FM_KEYS and v:
                    if v.startswith("[") and v.endswith("]"):
                        rec[k] = [x.strip().strip("'\"") for x in v[1:-1].split(",") if x.strip()]
                    else:
                        rec[k] = v.strip("'\"")
            out.append(rec)
    except Exception:
        pass
    return out


def _tokens(text) -> set:
    """Split on non-letters so hyphenated slugs decompose: `facebook-ads`
    becomes {facebook, ads}. Without this, free-text brief terms never match
    tag slugs and every source scores zero -- which silently degrades C3 into
    a pure recency feed."""
    if isinstance(text, (list, tuple)):
        text = " ".join(str(x) for x in text)
    return {t for t in re.split(r"[^a-zA-ZåäöÅÄÖ]+", str(text or "").lower()) if len(t) >= 3}


def _related(a: str, b: str) -> bool:
    """Prefix match at 4 chars, so ad/ads/advert/advertising relate and
    copy/copywriting relate. Cheap stemming without a stemmer."""
    if a == b:
        return True
    n = min(len(a), len(b))
    return n >= 4 and a[:4] == b[:4]


def rank_sources(brief: str, seen: set | None = None, limit: int = 2,
                 terms: list | None = None) -> list[dict]:
    """C3. Rank by tag/theme overlap, then recency. Anything the ledger
    already used drops out, so a long session broadens.

    `terms` carries the routed skill and branch names. Ranking on the user's
    raw prose alone is too thin -- "a social campaign" shares no token with
    `[cody-schneider, facebook-ads, warehouse]`, while the routed skill names
    (`social`, `ads`, `ad-creative`) do. The router already knows what the
    task is; C3 ranks with that knowledge rather than re-deriving it.
    """
    seen = seen or set()
    want = _tokens(brief) | _tokens(terms or [])
    scored = []
    for rec in frontier():
        if rec["slug"] in seen:
            continue
        bag = _tokens([
            rec.get("tags"), rec.get("priority_themes"),
            rec.get("title"), rec.get("show"),
        ])
        overlap = sum(1 for w in want if any(_related(w, b) for b in bag))
        scored.append((overlap, _source_date(rec), rec))

    # Two channels, not one ranked list. The canon (Ogilvy, Hopkins, Lasker)
    # carries broad tags -- reklam, copywriting, research -- so it wins almost
    # every overlap contest and a single ranked list degenerates into "the
    # classics, every time". That is precisely the locked-content failure this
    # system exists to avoid, and it would also starve the freshness channel.
    # So: one slot for best match, one slot for most recent unused.
    by_match = sorted(scored, key=lambda r: (r[0], r[1]), reverse=True)
    by_date = sorted(scored, key=lambda r: r[1], reverse=True)
    picked, out = set(), []
    for lane in (by_match, by_date):
        for _, _, rec in lane:
            if rec["slug"] not in picked:
                picked.add(rec["slug"])
                out.append(rec)
                break
    for _, _, rec in by_match:  # top up if limit > 2
        if len(out) >= limit:
            break
        if rec["slug"] not in picked:
            picked.add(rec["slug"])
            out.append(rec)
    return out[:limit]


_SLUG_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def _source_date(rec: dict) -> str:
    """The slug's date prefix, not `captured`. A re-ingest bumps `captured`
    -- the Ogilvy corpus all reads 2026-08-14 from its depth pass -- which
    would make 1963 books outrank this month's podcast on recency."""
    m = _SLUG_DATE.match(rec.get("slug") or "")
    return m.group(1) if m else (rec.get("captured") or "")


# --------------------------------------------------------------------------
# The router -- parsed from routing.md, never carried here
# --------------------------------------------------------------------------

_JSON_BLOCK = re.compile(r"```json\s*\n(.*?)\n```", re.S)


def routing_table() -> dict:
    """Read the JSON block out of references/routing.md.

    Mirrors design_hook_lib.routing_table(). Returns {} when the doc is
    missing or malformed -- every caller degrades to emitting nothing rather
    than to emitting something wrong.
    """
    try:
        text = ROUTING_DOC.read_text(encoding="utf-8", errors="replace")
        m = _JSON_BLOCK.search(text)
        return json.loads(m.group(1)) if m else {}
    except Exception:
        return {}


# --------------------------------------------------------------------------
# Artifact classification
# --------------------------------------------------------------------------

_ARTIFACT_PATHS = (
    "/content/", ".agents/marketing", "/copy/", "/campaigns/",
    "/marketing/", "/posts/", "/blog/", "/emails/", "/ads/",
)
_COPY_STEM = re.compile(
    r"(?:^|[-_.])(?:copy|strings|messages|content|i18n|locale|sv|en)(?:[-_.]|$)")

_ARTIFACT_STEMS = (
    "copy", "headline", "landing", "campaign", "newsletter", "ad-", "ads",
    "email", "social", "post", "pitch", "positioning", "messaging",
)

# Gate 46 -- invented proof. Numbers a model reaches for when it has none.
INVENTED = [
    # Bidirectional: the noun sits either side of the number in real copy --
    # "47% increase" and "lifted conversion 47%" are the same claim.
    (r"[+\-]?\s?\d{1,3}(?:[.,]\d+)?\s?%\s+(?:increase|lift|boost|conversion|growth|more|faster|higher|ökning|fler|snabbare|högre)",
     "a percentage improvement claim"),
    (r"\b(?:increase[d]?|lift(?:ed)?|boost(?:ed)?|grew|grow|improve[d]?|reduce[d]?|cut|conversion|revenue|retention|(ö|o)kade|(ö|o)kning|minskade|konverter\w*|int(ä|a)kt\w*|f(ö|o)rs(ä|a)ljning\w*)\b[^.!?\n]{0,40}?[+\-]?\s?\d{1,3}(?:[.,]\d+)?\s?%",
     "a percentage improvement claim"),
    (r"(?:trusted|used|loved|joined)\s+by\s+[\d,\.]+\s?(?:k|m|\+|million|thousand)?\s*\+?\s*(?:teams|companies|customers|users|businesses|developers|brands)",
     "a customer-count claim"),
    (r"\b\d{1,3}\s?[x×]\s+(?:faster|better|more|cheaper|snabbare|bättre|billigare)\b",
     "an Nx multiplier claim"),
    (r"\b(?:over|more than|över|mer än)\s+[\d,\.]+\s?(?:k|m|\+|million|thousand|miljoner|tusen)\b.{0,40}(?:customers|users|teams|kunder|användare)",
     "a scale claim"),
    (r"\b\d{1,3}(?:[.,]\d)?\s?/\s?5\b|\b\d{1,3}(?:[.,]\d)?\s+stars?\b",
     "a rating claim"),
    # A percentage RANGE is almost always a proof claim in marketing copy, and
    # needs no trigger verb near it. Missed live on project-b' shipped
    # "Vi räknar med att ta bort 50-70 % av det repetitiva jobbet": en-dash
    # separator, space before %, and "ta bort" was not a trigger verb.
    (r"\b\d{1,3}\s?[-–—]\s?\d{1,3}\s?%",
     "a percentage range claim"),
    # Swedish removal/saving verbs, which the English trigger list did not cover.
    (r"\b(?:ta bort|tar bort|spara[rt]?|minska[rt]?|kapa[rt]?|halvera[rt]?|frig(ö|o)r\w*)\b[^.!?\n]{0,40}?\d{1,3}\s?%",
     "a saving or reduction claim"),
]


# Writing *about* marketing is not writing marketing. Skill files, references,
# plans and docs quote bad copy as counter-examples -- a file explaining why
# "+47% conversion" is slop would otherwise be blocked for containing it.
# Found the hard way: this gate blocked the edit to design's own copy-gate.md.
_DOC_PATHS = (
    "/.agents/", "/.claude/", "/skills/", "/references/", "/reference/",
    "/docs/", "/doc/", "/node_modules/", "/.git/",
    "readme", "changelog", "contributing", "/plans/", "/session-logs/",
    # Working notes are not shipped copy. Caught live: a headline-exploration
    # file in the scratchpad was blocked for missing positioning, because
    # project_root() resolves from the target file and a temp dir belongs to
    # no project at all.
    "/scratchpad/", "/scratch/", "/tmp/", "/temp/", "/appdata/local/temp/",
)


def is_marketing_artifact(path: str, content: str = "") -> bool:
    """Marketing copy, not source code and not documentation about marketing.
    Deliberately narrow -- a false positive here blocks a write the user did
    not ask this system to police."""
    if not path:
        return False
    low = path.replace("\\", "/").lower()
    stem = Path(low).stem

    # A copy module is a marketing artifact whatever its extension. project-b
    # keeps every user-facing string in components/marketing/copy.ts and
    # copy-sections.ts -- the exact files this gate exists for, and the
    # extension filter below was silently skipping all of them.
    # Token-boundary rather than exact stem: `landing-copy.ts`, `copy-sections.ts`
    # and `pricing-copy.ts` are all copy modules, and an exact list silently
    # misses every naming variant a project actually uses. `copyright.ts` does
    # not match, which is the case the boundary exists for.
    is_copy_module = (
        low.endswith((".ts", ".tsx", ".js", ".jsx", ".mjs"))
        and _COPY_STEM.search(stem.split(".")[0])
        and any(d in low for d in ("/marketing/", "/content/", "/copy/",
                                   "/locales/", "/i18n/", "/messages/"))
    )

    if not is_copy_module and not low.endswith(
            (".md", ".mdx", ".txt", ".html", ".json", ".yaml", ".yml")):
        # Other UI files carry copy too, but those belong to design's Step 6,
        # which delegates here explicitly rather than being intercepted here.
        return False
    if any(frag in low for frag in _DOC_PATHS):
        return False
    if is_copy_module:
        return True
    if any(frag in low for frag in _ARTIFACT_PATHS):
        return True
    stem = Path(low).stem
    return any(s in stem for s in _ARTIFACT_STEMS)


def invented_metrics(content: str) -> list:
    hits = []
    for rx, label in INVENTED:
        for m in re.finditer(rx, content or "", re.I):
            hits.append((m.group(0).strip(), label))
    return hits[:6]


# --------------------------------------------------------------------------
# Entry condition -- new surfaces only
# --------------------------------------------------------------------------

# Copy work asked for in so many words. Without one of these, a design task on
# a surface that already has copy leaves that copy alone.
COPY_REQUESTED = re.compile(
    r"\b(?:copy|copywriting|text(?:en|er|erna)?|wording|budskap|"
    r"rubrik(?:en|er)?|headline|tagline|slogan|"
    r"skriv(?:a|er|om)?|formulera|omformulera|texta|"
    r"rewrite|reword|rephrase|messaging|"
    r"nyt?t?\s+(?:text|copy|budskap))\w*", re.I)

# A user-facing string in a component or a copy module. Deliberately loose --
# this only has to answer "does this surface already say something to a
# reader", not extract the strings correctly.
_VISIBLE_STRING = re.compile(
    r'\b(?:sv|en)\s*:\s*"[^"]{8,}"'          # localized copy modules
    r'|>[A-ZÅÄÖ][a-zåäöA-ZÅÄÖ ,\'-]{12,}<'   # literal JSX text
    r'|(?:title|alt|placeholder|aria-label)\s*=\s*"[^"]{8,}"',
)

MIN_STRINGS_FOR_EXISTING = 3


def surface_has_copy(path: str, content: str | None = None) -> bool:
    """Does this surface already say something to a reader?

    The rule this supports: the marketing chain runs on NEW surfaces. Design
    work on a page that already has copy leaves that copy alone unless copy
    was explicitly asked for. Rewriting copy that already tested well is a
    real cost -- Ogilvy's rule against killing winners for novelty -- and
    firing the chain on every polish pass guarantees it.

    A file that does not exist yet, or an empty scaffold, is new.
    """
    try:
        if content is None:
            p = Path(path)
            if not p.exists():
                return False
            content = p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return False
    return len(_VISIBLE_STRING.findall(content or "")) >= MIN_STRINGS_FOR_EXISTING


COPY_FLAG = ".copy-requested"


def mark_copy_requested(root: Path) -> None:
    """Recorded by marketing-intent.py, which is the only hook that sees the
    user's prompt. Later hooks read the flag instead of trying to reconstruct
    intent from tool arguments."""
    try:
        (state_dir(root) / COPY_FLAG).write_text("1", encoding="utf-8")
    except Exception:
        pass


def copy_was_requested(root: Path) -> bool:
    try:
        return (state_dir(root) / COPY_FLAG).exists()
    except Exception:
        return False


def surface_had_copy_before(root: Path, path: str) -> bool:
    """Did this surface already carry copy BEFORE the current edit?

    Asked of git, not of disk. At PostToolUse the write has already landed, so
    reading the file answers the wrong question -- it would call every
    freshly-written surface "existing" and disable the rule entirely.
    """
    try:
        rel = str(Path(path).resolve().relative_to(root.resolve())).replace("\\", "/")
    except Exception:
        return False
    try:
        import subprocess
        out = subprocess.run(
            ["git", "-C", str(root), "show", "HEAD:" + rel],
            capture_output=True, timeout=8)
        if out.returncode != 0:
            return False  # not tracked yet == new surface
        return surface_has_copy(path, out.stdout.decode("utf-8", "replace"))
    except Exception:
        return False


def chain_applies(root: Path, path: str) -> tuple:
    """(should_run, why). The single home for the entry decision.

    The chain runs on NEW surfaces, or when copy was explicitly asked for.
    Design work over a page that already has copy leaves the words alone.
    """
    if copy_was_requested(root):
        return True, "copy explicitly requested this session"
    if not surface_had_copy_before(root, path):
        return True, "new surface, no copy in HEAD"
    return False, ("surface already had copy and no copy work was requested "
                   "-- preserve it verbatim")


_SV = re.compile(
    r"[åäöÅÄÖ]"
    r"|\b(?:och|för|att|inte|som|med|den|det|är|kan|ska|dig|din|vi)\b"
)


def languages(content: str) -> list:
    """Which humanizer has to run. Both, when both are present."""
    out = []
    if _SV.search(content or ""):
        out.append("sv")
    if re.search(r"\b(?:the|and|for|with|your|you|our|is|are|to)\b", content or "", re.I):
        out.append("en")
    return out or ["en"]
