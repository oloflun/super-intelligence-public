#!/usr/bin/env python
"""UserPromptSubmit — projekt-digest + sök valvet, injicera pekare.

Ersätter vault-context.py (samma hook-slot, Fas 2.2 i wondrous-wishing-star.md).
Behåller vault-context.py:s bevisade sökkärna rakt av (tre mätta beslut i dess
historik: qmd search inte query/vsearch, OR-union av termer, BM25-poäng inget
kvalitetsfilter — se git-historiken för den filen om skälen behövs igen).

Nytt i denna version: projektdetektering (cwd + prompttermer mot hubbarnas
`repo:`-fält) injicerar en kompakt digest ur projektets hub-frontmatter INNAN
sökpekarna. v1 av digesten är hubbens egen frontmatter (goal/next_milestone/
milestone_blockers/stage/money_weight) — Fas 3:s Dröm tar över genereringen när
den finns; fram tills dess ÄR hubben den handseedade digesten.

Formatkontrakt: digest + pekare tillsammans ska landa under ~2,5K tokens
(ICM-fyndet i wondrous-wishing-star.md Fas 2.1/2.2). Digesten är ~150-300 tokens;
pekarblocket är oförändrat från vault-context.py (kvot kunskap:2 verktyg:2
arbete:1, några hundra tokens). Gott om marginal.
"""

import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME = r"{{USER_HOME}}"
QMD = os.path.join(os.environ.get("APPDATA", ""), "npm", "qmd.cmd")
VAULT = Path(HOME) / "OneDrive/Dokument/Obsidian/Knowledge Base"
PROJECTS_DIR = VAULT / "wiki/projects"

VERKTYG = {"skills", "claude-config", "buzz"}
ARBETE = {"session-logs"}

MIN_LEN = 25
MAX_TERMS = 3
PER_TERM = 6
QUOTA = [("kunskap", 2), ("verktyg", 2), ("arbete", 1)]

SKIP = re.compile(
    r"^\s*(ok(ej|ay)?|ja|nej|yes|no|y|n|k|tack|thanks|forts(ä|a)tt|continue|"
    r"g(ö|o)r det|do it|k(ö|o)r|k(ö|o)r p(å|a)|proceed|g(å|a) vidare|"
    r"stopp|stop|avbryt|v(ä|a)nta|wait)\b[\s.!]*$",
    re.IGNORECASE,
)

NOISE = re.compile(
    r"\[SYSTEM NOTIFICATION|<task-notification>|<system-reminder>|"
    r"<local-command-|<command-name>|Caveat: The messages below",
    re.IGNORECASE,
)

STOP = set("""
och eller men att som det den där här för med till från utan över under
jag du han hon vi ni dom dem denna detta dessa min din sin vår er ett
vill ska skall kan kunde bör borde måste får fick har hade blir blev är var
inte icke ingen inga något några alla varje man sig själv bara även samt
när hur vad vem vilken vilket vilka varför därför alltså sedan innan efter
gör göra gjort göras skriva skriv fixa fixar lägg lägga ta tar behöver nya
the and but that which this these those from with into over under about
will shall can could should must have has had are was were being been
not none any all each every when how what who why because then before after
make makes made need needs want wants like just also more most some such new
please help write add fix update change create build let get put use using
""".split())

WORD = re.compile(r"[A-Za-zÅÄÖåäö0-9_]{3,}")


def terms_from(prompt):
    out = []
    for w in WORD.findall(prompt.lower()):
        if w in STOP or w in out:
            continue
        out.append(w)
        if len(out) == MAX_TERMS:
            break
    return out


def search(index, query):
    cmd = [QMD]
    if index:
        cmd += ["--index", index]
    cmd += ["search", query, "-n", str(PER_TERM), "--format", "json"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=7)
    except Exception:
        return []
    out = (r.stdout or "").strip()
    i = out.find("[")
    if i < 0:
        return []
    try:
        return json.loads(out[i:])
    except Exception:
        return []


def load_paths():
    import yaml
    out = {}
    for name in ("index.yml", "projects.yml"):
        try:
            with open(os.path.join(HOME, ".config", "qmd", name),
                      encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            for col, spec in (cfg.get("collections") or {}).items():
                if isinstance(spec, dict) and spec.get("path"):
                    out[col] = spec["path"]
        except Exception:
            pass
    return out


def resolve(uri, roots):
    if not uri.startswith("qmd://"):
        return uri, "?"
    body = uri[6:].split("?", 1)[0]
    col, _, rel = body.partition("/")
    root = roots.get(col)
    if not root:
        return body, col
    full = os.path.join(root, rel.replace("/", os.sep))
    try:
        return os.path.relpath(full, HOME), col
    except ValueError:
        return full, col


def kind(col, from_projects):
    if from_projects:
        return "arbete"
    if col in VERKTYG:
        return "verktyg"
    if col in ARBETE:
        return "arbete"
    return "kunskap"


# ---- Fas 2.2: projekt-digest ----

def load_hubs():
    """Canonical hub = wiki/projects/<slug>/<slug>.md. Same convention as
    generate-portfolio.py -- other .md files in a project dir aren't hubs."""
    import yaml
    hubs = []
    try:
        project_dirs = [p for p in PROJECTS_DIR.iterdir() if p.is_dir()]
    except Exception:
        return hubs
    for d in project_dirs:
        if d.name.startswith("_") or d.name.startswith("."):
            continue
        hub = d / f"{d.name}.md"
        if not hub.exists():
            continue
        try:
            text = hub.read_text(encoding="utf-8")
            fm = yaml.safe_load(text.split("---", 2)[1]) or {}
        except Exception:
            continue
        if fm.get("status") == "redirect":
            continue
        hubs.append(fm)
    return hubs


def norm(p):
    return os.path.normcase(os.path.normpath(p))


def detect_project(cwd, terms, hubs):
    if cwd:
        cwd_n = norm(cwd)
        for fm in hubs:
            repo = fm.get("repo")
            if not repo or repo == "none":
                continue
            repo_n = norm(repo)
            if cwd_n == repo_n or cwd_n.startswith(repo_n + os.sep):
                return fm
    term_set = set(terms)
    matches = [fm for fm in hubs if fm.get("project_slug") in term_set]
    if len(matches) == 1:
        return matches[0]
    return None


def format_digest(fm):
    lines = [f"PROJECT: {fm.get('title', fm.get('project_slug', '?'))} "
             f"(weight {fm.get('money_weight', '-')}, stage {fm.get('stage', '-')})"]
    if fm.get("goal"):
        lines.append(f"GOAL: {fm['goal']}")
    if fm.get("next_milestone"):
        lines.append(f"NEXT MILESTONE: {fm['next_milestone']}")
    blockers = fm.get("milestone_blockers") or []
    if isinstance(blockers, list) and blockers:
        lines.append("BLOCKED BY: " + "; ".join(blockers))
    return lines


def main():
    if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
        return  # Fas 6 assistant-bench arm B: all hooks off, incl. digest+vault pointers

    raw = sys.stdin.read()
    event = json.loads(raw) if raw.strip() else {}
    prompt = (event.get("prompt") or event.get("userInput") or "").strip()
    cwd = event.get("cwd") or os.getcwd()

    if (len(prompt) < MIN_LEN or prompt.startswith("/")
            or SKIP.match(prompt) or NOISE.search(prompt)):
        return

    terms = terms_from(prompt)
    if not terms:
        return

    hubs = load_hubs()
    project_fm = detect_project(cwd, terms, hubs)

    jobs = [(idx, t) for idx in (None, "projects") for t in terms]
    with ThreadPoolExecutor(max_workers=len(jobs)) as ex:
        results = list(ex.map(lambda j: (j[0], search(j[0], j[1])), jobs))

    votes = defaultdict(int)
    best_rank, meta = {}, {}
    for index, hits in results:
        for rank, h in enumerate(hits):
            key = (index, h.get("file", ""))
            votes[key] += 1
            best_rank[key] = min(best_rank.get(key, 99), rank)
            meta[key] = h

    blocks = []

    if project_fm:
        blocks.append("<project-digest>\n" + "\n".join(format_digest(project_fm))
                       + "\n</project-digest>")

    if votes:
        order = sorted(votes, key=lambda k: (-votes[k], k[0] is not None, best_rank[k]))
        roots = load_paths()
        buckets = {"kunskap": [], "verktyg": [], "arbete": []}
        seen = set()
        for key in order:
            index, uri = key
            path, col = resolve(uri, roots)
            if path in seen:
                continue
            seen.add(path)
            title = re.sub(r"\s+", " ", (meta[key].get("title") or "")).strip()[:88]
            buckets[kind(col, index is not None)].append((path, title))

        lines, spare = [], 0
        for sort, want in QUOTA:
            take = buckets[sort][: want + spare]
            spare = max(0, want + spare - len(take))
            for path, title in take:
                lines.append(f"{sort + ':':<9} {path}" + (f" — {title}" if title else ""))
        if lines:
            header = ("Valvet först — sökt på: " + " ".join(terms) + ". Detta finns "
                       "redan om ämnet. Läs det som är relevant innan du börjar, och "
                       "bygg inte om ett verktyg som redan finns.")
            blocks.append("\n".join(["<vault-context>", header, *lines, "</vault-context>"]))

    if not blocks:
        return

    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "UserPromptSubmit",
        "additionalContext": "\n".join(blocks),
    }}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
