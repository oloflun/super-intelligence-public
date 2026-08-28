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

# Windows ger stdin i cp1252. Prompten kommer som UTF-8, sa utan den har raden
# blir "frågorna istället" till bytesalladen "frÃ¥gorna istÃ¤llet", och
# ordregexen nedan plockar ut soktermerna "gorna", "ist", "llet". Precis det
# hande 2026-08-26: en fraga om projektmal sokte pa "gorna klartext ist" och
# traffade en Excel-konversation. Varje svensk prompt var tyst forsamrad.
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")

HOME = str(Path.home())
QMD = os.path.join(os.environ.get("APPDATA", ""), "npm", "qmd.cmd")


def resolve_vault():
    """Var ligger valvet? Miljöagnostiskt istället för hårdkodat till en maskin.

    Ordning: 1) explicit env-override (CLAUDE_VAULT), for den som pekar om
    valvet eller kor pa en annan maskin. 2) OneDrive-standardsokvagen om den
    finns pa den har maskinen -- det vanliga fallet. 3) en molnsession som
    klonat sjalva valv-repot som projektkatalog (CLAUDE_PROJECT_DIR pekar da
    pa en katalog med memory/MEMORY.md i roten, valvets eget signatur-innehall).
    Traffar inget av detta anvands anda OneDrive-standardvagen -- resten av
    filen degraderar redan snallt mot icke-existerande sokvagar.
    """
    env_override = os.environ.get("CLAUDE_VAULT")
    if env_override:
        return Path(env_override)
    default = Path(HOME) / "OneDrive/Dokument/Obsidian/Knowledge Base"
    if default.exists():
        return default
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir and (Path(project_dir) / "memory" / "MEMORY.md").exists():
        return Path(project_dir)
    return default


VAULT = resolve_vault()
PROJECTS_DIR = VAULT / "wiki/projects"
PATTERNS = Path(HOME) / ".agents" / "patterns-index.json"

VERKTYG = {"skills", "claude-config", "buzz"}
ARBETE = {"session-logs"}

MIN_LEN = 25
MAX_TERMS = 5
MAX_PATTERNS = 3
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
upp ner ut in satt satta stall stalla igang klart klar redan finns fanns
sak saker sant sadan del delar bit bitar plats stallet stalle vis satt
kanske typ liksom alltsa ju val nog forst sist bara enbart endast mest
sätt sätta sätts ställ ställa ställs gör göra görs går gå gått får få fått
när där här över under från för är två tre många något några själv sådan
även än åt åter alltså så vad hur vilken vilket vilka därför eftersom
igen redan bara endast enbart precis mest minst mycket lite väl nog kanske
del delar sak saker gång gånger ställe stället plats vis alla varje
ligger ligga ligg lagg satter stalls halls kommer kom tagit
""".split())

WORD = re.compile(r"[A-Za-zÅÄÖåäö0-9_]{3,}")


FOLD = str.maketrans("åäöé", "aaoe")

# Bestamd form och vanliga bojningar. BM25 matchar exakt: "assistentlagret"
# hittar INTE dokument som skriver "assistentlager", "nycklarna" hittar inte
# "nycklar". Uppmatt 2026-08-26: fyra av evalsvitens missar berodde enbart pa
# detta. En variant per ord racker -- langsta matchande suffix vinner.
SUFFIX = ("arna", "erna", "orna", "aste", "ande", "ende",
          "et", "en", "na", "ar", "er", "or", "an", "a", "t", "n")


def stem_of(w):
    """En avbojd variant av ordet, eller None om ingen suffix passar."""
    for s in SUFFIX:
        if w.endswith(s) and len(w) - len(s) >= 4:
            return w[: -len(s)]
    return None


def informativity(word, rarity):
    """Hur mycket sarskiljer ordet? Hogre ar battre.

    Den forsta versionen tog helt enkelt de tre forsta orden som inte stod i
    stopplistan. For prompten "Satt upp ett system i 2 delar for att forhindra
    att felet uppstar igen" blev soktermerna "upp system delar" -- tre av de
    mest intetsagande orden i meningen -- och traffen blev en konversation om
    Excel. Ordningen i en mening sager ingenting om vilka ord som bar amnet.

    Tre signaler, alla gratis: langd (langre ord ar mer specifika i svenskan,
    dar sammansattningar bar innehallet), identifierarform (bindestreck,
    understreck eller siffror betyder nastan alltid ett egennamn eller en
    teknisk term), och sallsynthet mott monsterindexets ordbok -- ett ord som
    bara forekommer i nagra fa dokument sarskiljer mer an ett som finns i alla.
    """
    score = min(len(word), 14)
    if any(c.isdigit() for c in word) or "-" in word or "_" in word:
        score += 6
    n = rarity.get(word)
    if n is None:
        score += 3          # okant for indexet: ofta ett egennamn, ofta bra
    elif n <= 3:
        score += 5
    elif n > 25:
        score -= 4
    return score


def terms_from(prompt, rarity=None):
    rarity = rarity or {}
    seen, cands = set(), []
    for w in WORD.findall(prompt.lower()):
        if w in STOP or w in seen or len(w) < 3:
            continue
        seen.add(w)
        cands.append(w)
    cands.sort(key=lambda w: -informativity(w, rarity))

    # Blanda in medellanga ord med flit. Svenskan bildar sammansattningar, och
    # BM25 har ingen ordledsdelning: "designresultatet" och "intetsagande" ger
    # noll traffar i indexet trots att de ar meningens mest innehallsrika ord.
    # En ren topprankning pa informativitet valde alltsa systematiskt de ord som
    # inte KAN matcha nagot, och tre av trettio fragor i evalsviten fick darfor
    # ingen valvtraff alls. Halften av platserna gar till ord i det langdspann
    # som brukar sta obojt i dokumenten.
    top = cands[:MAX_TERMS - 2]
    vanliga = [w for w in cands if w not in top and 4 <= len(w) <= 9]
    return (top + vanliga)[:MAX_TERMS] or cands[:MAX_TERMS]


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


# ---- Snabbkoppling mot tidigare loste problem ----

# Vilka monstertyper som ar vard att avbryta nagon for, hogst forst. Ett LOST
# block ar den vardefullaste posten som finns: nagon har redan statt i exakt
# den har situationen och skrivit ner vad som faktiskt fungerade.
# "kunskap" ar ingestade kallor (wiki/sources). De vager tungt: en genomarbetad
# kalla som redan svarat pa fragan ar nastan lika vardefull som ett lost block,
# och det var precis den kopplingen som saknades 2026-08-27 (skillsmaxxing-
# avsnittet fanns ingestat men syntes aldrig).
PATTERN_WEIGHT = {"block": 3.0, "kunskap": 2.4, "strategi": 2.0, "dokument": 2.0,
                  "skill": 1.4, "delmal": 1.2, "funktion": 1.0}


def load_patterns():
    try:
        return json.loads(PATTERNS.read_text(encoding="utf-8"))
    except Exception:
        return {"poster": [], "ord": {}}


def match_patterns(prompt, index, project_slug=None):
    """Rena ordboksslagningar, ingen modell, under 10 ms.

    Poangen med den har funktionen ar att gora kopplingen mekanisk. En agent
    som maste komma pa att den ska soka efter tidigare liknande problem gor det
    ibland; en uppslagning som alltid kors gor det varje gang.
    """
    words = {w.translate(FOLD) for w in WORD.findall(prompt.lower())
             if w not in STOP and len(w) >= 4}
    extra = set()
    for w in words:
        if len(w) > 7:
            extra.add(w[:6])
        s = stem_of(w)
        if s:
            extra.add(s)
    words |= extra
    if not words:
        return []

    posts, lookup = index.get("poster", []), index.get("ord", {})
    scores = defaultdict(float)
    for w in words:
        ids = lookup.get(w)
        if not ids:
            continue
        # Ett ord som pekar pa manga poster sarskiljer mindre an ett som pekar
        # pa fa -- samma logik som BM25:s inversa dokumentfrekvens, i miniatyr.
        share = 1.0 / (1.0 + len(ids) * 0.35)
        for i in ids:
            scores[i] += share

    ranked = []
    for i, raw in scores.items():
        p = posts[i]
        # Ingen langdnormalisering har. Den provades (dela med log10 av postens
        # ordantal, som BM25 gor) och matningen sagde nej: hooken foll fran 87 %
        # till 70 % och kopplingsklassen fran 90 % till 60 %. Skalet ar att aven
        # BLOCKS-poster och strategier ar ordrika -- normaliseringen straffade
        # alltsa precis de poster blocket finns for. Trangseln fran kallsidor loses
        # strukturellt i stallet, av taket pa en kunskapspost per block nedan.
        s = raw * PATTERN_WEIGHT.get(p["typ"], 1.0)
        if p.get("lost"):
            s *= 1.5           # loste problem bar facit
        if project_slug and p.get("projekt") == project_slug:
            s *= 0.75          # egna projektets poster ar man oftast medveten om
        ranked.append((s, i, p))
    ranked.sort(key=lambda x: -x[0])

    # Kravet pa minsta poang finns for att ett svagt monster ar samre an inget:
    # det larlar agenten att blocket ar brus och da slutar den lasa det.
    # Ett monster som bara delar ETT ord med fragan ar nastan alltid brus --
    # "satt" i "satt upp ett system" traffade delmalet "Satt priser och paket".
    # Krav: minst tva skilda ord, eller ett ord sa sallsynt att det i sig ar ett
    # egennamn. Ett svagt monster ar samre an inget: det lar agenten att blocket
    # ar brus, och da slutar den lasa aven de traffar som ar ratt.
    word_hits = defaultdict(set)
    for w in words:
        for i in lookup.get(w, []):
            word_hits[i].add(w)

    # Kallsidorna ar 426 av 1183 poster. Utan tak fyllde de hela blocket och
    # trangde ut precis det som blocket finns for: ett last block med facit,
    # eller verktyget som redan loser uppgiften. Hogst en kallsida per block --
    # den far plats, men tar inte over.
    MAX_KUNSKAP = 1
    kunskap_kvar = MAX_KUNSKAP

    out, seen_titles = [], set()
    for s, idx, p in ranked:
        if p["typ"] == "kunskap" and kunskap_kvar <= 0:
            continue
        hits_here = word_hits.get(idx, set())
        # Ett ord som pekar pa EXAKT en post ar maximalt sarskiljande --
        # "nycklar" -> /api-key-setup. Sadana traffar slapps igenom aven
        # ensamma och med lagre poangkrav; det ar breda ord i manga poster
        # som behover tva-ordsregeln och den hoga troskeln.
        unique_hit = any(len(lookup.get(w, [])) <= 1 for w in hits_here)
        rare = unique_hit or any(len(lookup.get(w, [])) <= 4 and len(w) >= 7
                                 for w in hits_here)
        if len(hits_here) < 2 and not rare:
            continue
        if s < (0.6 if unique_hit else 1.2) or p["rubrik"] in seen_titles:
            continue
        seen_titles.add(p["rubrik"])
        out.append(p)
        # Racknas forst nar posten faktiskt kom med -- en kallsida som foll pa
        # troskeln ska inte ha atit upp platsen for nasta.
        if p["typ"] == "kunskap":
            kunskap_kvar -= 1
        if len(out) >= MAX_PATTERNS:
            break
    return out


def format_patterns(matches):
    lines = ["<mönster>",
             "Detta liknar saker som redan finns eller redan lösts. Läs innan "
             "du bygger något nytt:"]
    for p in matches:
        proj = p.get("projekt") or "-"
        if p["typ"] == "block":
            lead = f"Samma form dök upp i {proj}"
            body = p.get("losning") or p.get("form") or ""
            verb = "löstes så" if p.get("lost") else "är öppet, formen är"
            lines.append(f"- {lead} och {verb}: {body[:260]}")
        elif p["typ"] == "strategi":
            lines.append(f"- Erfarenhet från {proj}: {p['rubrik']} — "
                         f"{p.get('losning', '')[:200]}")
        elif p["typ"] == "skill":
            lines.append(f"- Verktyget {p['rubrik']} täcker redan detta: "
                         f"{p.get('losning', '')[:180]}")
        elif p["typ"] == "kunskap":
            # Tom losning gav raden "... — " med ingenting efter tankstrecket.
            kropp = (p.get("losning") or p.get("form") or "").strip()
            lines.append(f"- Redan ingestat och läst: {p['rubrik'][:120]}"
                         + (f" — {kropp[:200]}" if kropp else ""))
        elif p["typ"] == "dokument":
            # Hamnade tidigare i else-grenen nedan och renderades som
            # "Det har beror -, dar det redan avklarat: Blocks" -- fel projekt
            # (tomt), fel verb (ingenting ar avklarat) och ingen upplysning.
            lines.append(f"- Det står redan skrivet i {p['kalla']}: "
                         f"{p['rubrik'][:160]}")
        else:
            klar = "redan avklarat" if p.get("lost") else "står på färdplanen"
            var = f" i {proj}" if proj and proj != "-" else ""
            lines.append(f"- Det här{var} är {klar}: {p['rubrik'][:180]}")
        lines.append(f"  ({p['kalla']})")
    lines.append("</mönster>")
    return "\n".join(lines)


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


def next_subgoal(repo):
    """Forsta obockade delmalet i projektets GOALS.md, eller None."""
    try:
        text = (Path(repo) / "GOALS.md").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^\s*-\s*\[ \]\s*(?:\d+\.\s*)?(.+)$", text, re.M)
    if not m:
        return None
    # Delmalen ar skrivna for manniskor: fetstil och flerradiga beskrivningar.
    # Digesten vill ha rubrikmeningen, inte hela stycket.
    steg = m.group(1).replace("**", "").strip()
    punkt = steg.find(". ")
    return (steg[:punkt + 1] if 0 < punkt < 180 else steg[:180]).strip()


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
    # Malbilden ar det som gor forslag mojliga att forankra. Nasta obockade
    # delmal star har sa att VARJE prompt bar riktningen -- det ar den
    # mekaniska halvan av "agenten foreslar alltid nasta steg sjalv": den kan
    # inte glomma att titta, for raden ligger redan i kontexten.
    repo = fm.get("repo")
    if repo and repo != "none":
        goals = Path(repo) / "GOALS.md"
        if goals.exists():
            steg = next_subgoal(repo)
            if steg:
                lines.append(f"NASTA DELMAL: {steg}")
            lines.append(f"MALBILD: {goals} -- las den innan du foreslar arbete; "
                         f"varje forslag ska peka pa ett delmal dar")
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

    # NB: inte 'index' -- det namnet anvands redan som loopvariabel for
    # qmd-indexet langre ner, och kollisionen gjorde att monsterblocket fick en
    # strang i stallet for uppslagsverket och tyst slutade fungera.
    patterns = load_patterns()
    rarity = {w: len(ids) for w, ids in patterns.get("ord", {}).items()}
    terms = terms_from(prompt, rarity)
    if not terms:
        return

    hubs = load_hubs()
    project_fm = detect_project(cwd, terms, hubs)

    # Sok bade ordet och dess stam: "lagersystemet" OCH "lagersystem". Unionen
    # nedan viktar anda pa antal termer som pekar pa samma dokument, sa en stam
    # som traffar brett drunknar inte ut en exakt traff.
    variants = list(terms)
    for w in terms:
        s = stem_of(w)
        if s and s not in variants:
            variants.append(s)
    jobs = [(idx, t) for idx in (None, "projects") for t in variants]
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

    matches = match_patterns(prompt, patterns,
                             (project_fm or {}).get("project_slug"))
    if matches:
        blocks.append(format_patterns(matches))

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
