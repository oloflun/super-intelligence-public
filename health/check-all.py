#!/usr/bin/env python
"""Verify that every layer of the plugin actually works, not just that it exists.

The plugin has no `version` field on purpose, so Claude Code treats each commit as
a new version and installed copies follow the default branch. That convenience is
only safe with a gate in front of it: these checks run in CI on every push, and a
red run is what stops a broken commit from becoming everyone's next auto-update.

Six checks, each independent so one failure still reports the rest:

  1 manifest     -- plugin.json parses and every directory it names exists
  2 skills       -- every SKILL.md has usable frontmatter and matches its folder
  3 hooks        -- hooks.json is valid and every script it points at is present
  4 agents       -- every agent definition parses
  5 portability  -- no absolute home paths, drive letters or MSYS paths shipped
  6 privacy      -- no forbidden identifier survives into a shipped file

Checks 5 and 6 exist because this plugin is extracted from a private repo. Making
sanitization a test rather than a cleanup step is the whole point: a cleanup is
done once and rots, a test runs on every commit.

    python health/check-all.py
    python health/check-all.py --json
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parent.parent)

# Directories a plugin may ship. Claude Code auto-discovers these by name.
COMPONENT_DIRS = ("skills", "hooks", "agents", "commands")

# Event names Claude Code accepts in hooks.json. An unknown name is not an error
# at install time -- the hook simply never fires, which is the worst failure mode
# there is: silent. So it is an error here.
VALID_EVENTS = {
    "SessionStart", "SessionEnd", "UserPromptSubmit", "PreToolUse", "PostToolUse",
    "PermissionRequest", "Notification", "Stop", "SubagentStop", "PreCompact",
    "ConfigChange", "FileChanged", "CwdChanged",
}

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---", re.S)


def field(block, name):
    m = re.search(rf"^{name}:\s*(.+)$", block, re.M)
    return m.group(1).strip().strip('"').strip("'") if m else ""


def shipped_files():
    """Every text file that would end up in a user's install."""
    skip = {".git", ".github", "node_modules", "__pycache__", ".venv"}
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in skip for part in p.parts):
            continue
        if p.suffix.lower() in (".md", ".py", ".json", ".sh", ".ps1", ".cmd",
                                ".txt", ".yml", ".yaml", ".toml"):
            yield p


def read(p):
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


# --- 1: manifest -----------------------------------------------------------

def check_manifest():
    fel = []
    mf = ROOT / ".claude-plugin" / "plugin.json"
    if not mf.exists():
        return ["saknar .claude-plugin/plugin.json"]
    try:
        data = json.loads(read(mf))
    except json.JSONDecodeError as e:
        return [f"plugin.json ar inte giltig JSON: {e}"]

    if not data.get("name"):
        fel.append("plugin.json saknar 'name' (kravs, och ar skill-namespacet)")
    elif not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", data["name"]):
        fel.append(f"plugin-namnet '{data['name']}' ar inte kebab-case")

    # Ett version-falt ar tillatet, men da slutar SHA-baserad autouppdatering att
    # galla och nagon maste komma ihag att bumpa. Sag det hogt.
    if "version" in data:
        fel.append("plugin.json har ett 'version'-falt: autouppdatering foljer da "
                   "inte langre nya commits utan kraver manuell bump")

    mkt = ROOT / ".claude-plugin" / "marketplace.json"
    if mkt.exists():
        try:
            m = json.loads(read(mkt))
            namn = {p.get("name") for p in m.get("plugins", [])}
            if data.get("name") and data["name"] not in namn:
                fel.append("marketplace.json listar inte plugin:ets eget namn")
        except json.JSONDecodeError as e:
            fel.append(f"marketplace.json ar ogiltig JSON: {e}")

    # Komponentkataloger som finns men ar tomma ar en fallucka: de ser ut som
    # kapabilitet och levererar ingenting.
    for d in COMPONENT_DIRS:
        p = ROOT / d
        if p.is_dir() and not any(p.iterdir()):
            fel.append(f"katalogen {d}/ finns men ar tom")
    return fel


# --- 2: skills -------------------------------------------------------------

def check_skills():
    fel = []
    root = ROOT / "skills"
    if not root.is_dir():
        return fel
    for sk in sorted(root.glob("*/SKILL.md")):
        rel = sk.relative_to(ROOT).as_posix()
        fm = FRONTMATTER.match(read(sk))
        if not fm:
            fel.append(f"{rel}: saknar frontmatter")
            continue
        block = fm.group(1)
        namn = field(block, "name")
        if not field(block, "description"):
            fel.append(f"{rel}: saknar description (den avgor nar skillen laddas)")
        if namn and namn != sk.parent.name:
            fel.append(f"{rel}: name '{namn}' matchar inte katalogen "
                       f"'{sk.parent.name}' -- anropet blir da fel")
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if not (d / "SKILL.md").exists():
            fel.append(f"skills/{d.name}/: katalog utan SKILL.md")
    return fel


# --- 3: hooks --------------------------------------------------------------

def check_hooks():
    fel = []
    hf = ROOT / "hooks" / "hooks.json"
    if not hf.exists():
        return fel
    try:
        data = json.loads(read(hf))
    except json.JSONDecodeError as e:
        return [f"hooks/hooks.json ar ogiltig JSON: {e}"]

    for event, grupper in (data.get("hooks") or {}).items():
        if event not in VALID_EVENTS:
            fel.append(f"hooks.json: okand handelse '{event}' -- hooken kommer "
                       f"aldrig att fira, tyst")
        for g in grupper or []:
            for h in g.get("hooks") or []:
                cmd = h.get("command", "")
                for m in re.finditer(r"\$\{CLAUDE_PLUGIN_ROOT\}([^\"'\s]+)", cmd):
                    mal = ROOT / m.group(1).lstrip("/\\")
                    if not mal.exists():
                        fel.append(f"hooks.json ({event}): pekar pa "
                                   f"{m.group(1)} som inte finns")
                if "CLAUDE_PLUGIN_ROOT" not in cmd and (
                        cmd.startswith("/") or re.match(r"^[A-Za-z]:", cmd)):
                    fel.append(f"hooks.json ({event}): absolut sokvag i kommandot "
                               f"-- anvand ${{CLAUDE_PLUGIN_ROOT}}")

    # Kill-switchen ar inte valfri: utan den gar lagret inte att mata mot sig sjalv.
    for script in sorted((ROOT / "hooks").glob("*.py")):
        if "CLAUDE_HOOKS_DISABLED" not in read(script):
            fel.append(f"hooks/{script.name}: hedrar inte CLAUDE_HOOKS_DISABLED")
    return fel


# --- 4: agents -------------------------------------------------------------

def check_agents():
    fel = []
    root = ROOT / "agents"
    if not root.is_dir():
        return fel
    for a in sorted(root.glob("*.md")):
        fm = FRONTMATTER.match(read(a))
        if not fm:
            fel.append(f"agents/{a.name}: saknar frontmatter")
        elif not field(fm.group(1), "description"):
            fel.append(f"agents/{a.name}: saknar description")
    return fel


# --- 5: portability --------------------------------------------------------

HOME_PAT = re.compile(r"C:\\Users\\[A-Za-z]|/c/Users/|/home/[a-z]|/Users/[A-Za-z]")


def check_portability():
    fel = []
    # Vendorerade trad ar andras kod som vi speglar. De innehaller sina egna
    # forfattares sokvagar i changeloggar och historikfiler ("extracted from
    # /Users/jesse/..."), och att skriva om dem vore att radera attributionen och
    # skapa drift mot uppstroms vid varje uppdatering. De sokvagarna kor inte
    # heller nagot -- de star citerade i prosa. Var egen kod har inget undantag.
    VENDORERAT = ("skills/gstack/", "skills/superpowers/", "skills/ecc/",
                  "skills/source-command-", "skills/vercel-", "skills/anthropic-skills/")

    for p in shipped_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("health/"):
            continue  # checkarna maste sjalva kunna namna monstren de letar efter
        if any(rel.startswith(v) for v in VENDORERAT):
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            if not HOME_PAT.search(line):
                continue
            # En rad som redan bar en platshallare ar losningen, inte problemet --
            # `/mnt/c/Users/{{USER_NAME}}/...` ar korrekt templatad och ska inte
            # larma. Detsamma galler en glob (`/mnt/c/Users/*/AppData/...`), som
            # ar portabel av konstruktion. Utan de har tva undantagen bestod
            # kontrollens utdata till storsta delen av ratt svar.
            if "{{" in line or "*" in line:
                continue
            # `<user>`, `/Users/you/`, `/home/username/` ar redan det generiska
            # exemplet en laser dokumentation for att hitta. Att larma pa dem
            # sager at forfattaren att skriva en riktig sokvag i stallet, vilket
            # ar tvartemot vad kontrollen finns for.
            if re.search(r"<[^>]+>|/(?:Users|home)/(?:you|user|username|me|"
                         r"your-?name|someone)\b", line, re.I):
                continue
            fel.append(f"{rel}:{i}: absolut hemkatalogsokvag -- "
                       f"anvand en platshallare eller ${{CLAUDE_PLUGIN_ROOT}}")
            break
    return fel


# --- 6: privacy ------------------------------------------------------------

def check_privacy():
    fel = []
    lista = ROOT / "health" / "forbidden-patterns.txt"
    if not lista.exists():
        return ["health/forbidden-patterns.txt saknas -- sanitiseringsgrinden "
                "ar da avstangd och privat innehall kan publiceras obemarkt"]
    monster = []
    for rad in read(lista).splitlines():
        rad = rad.strip()
        if rad and not rad.startswith("#"):
            try:
                monster.append((rad, re.compile(rad, re.I)))
            except re.error as e:
                fel.append(f"forbidden-patterns.txt: ogiltigt monster {rad!r}: {e}")
    for p in shipped_files():
        rel = p.relative_to(ROOT).as_posix()
        if rel.startswith("health/"):
            continue
        text = read(p)
        for raw, rx in monster:
            m = rx.search(text)
            if m:
                rad = text[:m.start()].count("\n") + 1
                fel.append(f"{rel}:{rad}: forbjudet monster {raw!r}")
    return fel


# --- 7: placeholders -------------------------------------------------------

PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def check_placeholders():
    """Varje {{X}} maste vara en som installeraren faktiskt ersatter.

    Det har ar sanitiseringens andra halva. Att byta en personlig sokvag mot
    {{VAULT_PATH}} loser ingenting om ingen ersatter den sedan: filen ser ren ut,
    passerar integritetskontrollen, och installeras med tva klammerparenteser dar
    sokvagen skulle sta. En felstavad platshallare ({{VAULTPATH}}) ar samma fel,
    och tyst pa exakt samma satt.

    Sanningen om vad som gar att ersatta star i install.mjs rpl(), sa den lases
    har i stallet for att listan skrivs av for hand och glider isar.
    """
    fel = []
    inst = ROOT / "install.mjs"
    if not inst.exists():
        return ["install.mjs saknas -- platshallarna kan da inte verifieras"]
    kanda = set(re.findall(r'replaceAll\("\{\{([A-Z0-9_]+)\}\}"', read(inst)))
    if not kanda:
        return ["hittade inga replaceAll(\"{{...}}\") i install.mjs -- har rpl() "
                "skrivits om? kontrollen ar da blind och maste uppdateras"]
    # Vendorerade delar har egna mallsystem med egna klammerord (gstack bygger
    # sina SKILL.md ur .tmpl-filer med {{COMMAND_REFERENCE}} och ett fyrtiotal
    # till). De har ingenting med installeraren att gora, och att larma pa dem
    # gor kontrollen till brus -- vilket ar hur en kontroll slutar lasas.
    #
    # Det som faktiskt ar farligt ar en FELSTAVNING av installerarens egna ord:
    # {{VAULTPATH}} eller {{USER_PATH}} ser rätt ut, ersätts aldrig, och skickas
    # vidare med klammerparenteser kvar. De delar alltid en stam med nagot kant,
    # sa det ar stammen vi larmar pa.
    stammar = set()
    for k in kanda:
        stammar.update(d for d in k.split("_") if len(d) >= 4)

    for p in shipped_files():
        rel = p.relative_to(ROOT).as_posix()
        # gstack bygger sina egna filer ur .tmpl och har ett eget klammersprak.
        if (rel.startswith("health/") or rel == "install.mjs"
                or rel.startswith("skills/gstack/")):
            continue
        for i, line in enumerate(read(p).splitlines(), 1):
            for namn in PLACEHOLDER.findall(line):
                if namn in kanda:
                    continue
                delar = set(namn.split("_"))
                if delar & stammar:
                    fel.append(f"{rel}:{i}: {{{{{namn}}}}} liknar en av "
                               f"installerarens platshallare men ersatts inte -- "
                               f"felstavad? kanda: {', '.join(sorted(kanda))}")
    return fel


# --- 8: installer ----------------------------------------------------------

def check_installer():
    """Installeraren och dess JSON-mallar maste parsa.

    En trasig mall upptacks annars forst nar nagon kor installationen, och da
    halvvags igenom -- med halva stacken utlagd pa disk.
    """
    import subprocess
    fel = []
    for namn in ("install.mjs", "upgrade.mjs"):
        p = ROOT / namn
        if not p.exists():
            fel.append(f"{namn} saknas")
            continue
        try:
            r = subprocess.run(["node", "--check", str(p)], capture_output=True,
                               text=True, timeout=60)
            if r.returncode != 0:
                fel.append(f"{namn}: {(r.stderr or '').strip().splitlines()[0][:120]}")
        except FileNotFoundError:
            fel.append("node saknas -- kan inte syntaxkontrollera installeraren")
            break
        except Exception as e:
            fel.append(f"{namn}: {e!r}")

    tpl = ROOT / "templates"
    if tpl.is_dir():
        for j in sorted(tpl.rglob("*.json")):
            try:
                json.loads(read(j))
            except json.JSONDecodeError as e:
                fel.append(f"templates/{j.name}: ogiltig JSON: {e}")
    return fel


CHECKS = [
    ("manifest", check_manifest),
    ("skills", check_skills),
    ("hooks", check_hooks),
    ("agents", check_agents),
    ("portability", check_portability),
    ("privacy", check_privacy),
    ("placeholders", check_placeholders),
    ("installer", check_installer),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    resultat, trasiga = {}, 0
    for namn, fn in CHECKS:
        try:
            fel = fn()
        except Exception as e:                      # en trasig check ar ett fel
            fel = [f"kontrollen kraschade: {e!r}"]
        resultat[namn] = fel
        trasiga += bool(fel)

    if a.json:
        print(json.dumps({"ok": trasiga == 0, "checks": resultat},
                         ensure_ascii=False, indent=1))
        return 1 if trasiga else 0

    for namn, fel in resultat.items():
        print(f"{'FAIL' if fel else 'ok  '}  {namn}")
        for f in fel[:20]:
            print(f"        {f}")
        if len(fel) > 20:
            print(f"        ... och {len(fel) - 20} till")
    print(f"\n{len(CHECKS) - trasiga}/{len(CHECKS)} kontroller grona")
    return 1 if trasiga else 0


if __name__ == "__main__":
    sys.exit(main())
