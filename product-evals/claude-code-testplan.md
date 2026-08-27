# Nivå 1 — Testkörning i Claude Code

Kopiera varje sektion nedan och klistra in i Claude Code. Kör i ordning.
Varje test tar ~30 sekunder. Totalt ~5 minuter för alla.

---

## TEST 1: ponytail (aktiv nu — testa direkt)

```
/ponytail-review
```

Förväntat: Agenten granskar din nuvarande diff och pekar ut över-engineering.

```
/ponytail-audit
```

Förväntat: Agenten granskar hela repot och listar förenklingsmöjligheter.

```
/ponytail ultra
```

Förväntat: Agenten byter till ultra-läge. Fråga sedan: "Lägg till en date picker i detta projekt" — agenten ska svara `<input type="date">`.

```
/ponytail full
```

Återställ till standardläge.

---

## TEST 2: last30days-skill (research)

```
/last30days "AI agent frameworks June 2026"
```

Förväntat: Multi-source resultat från Reddit, X, HackerNews, webben — med källhänvisningar.

```
/last30days hn "show hn claude code"
```

Förväntat: HackerNews-poster om Claude Code.

---

## TEST 3: Agent-Reach (CLI — kör i terminal)

Gå till mappen först:
```bash
cd {{USER_HOME_FWD}}/AppData/Local/hermes/eval-sandboxes/Agent-Reach
```

```bash
python -c "import agent_reach; print('v' + agent_reach.__version__)"
```
Förväntat: `v1.5.0`

```bash
python -m agent_reach.cli --help
```
Förväntat: Hjälptext med tillgängliga kommandon.

```bash
python -m agent_reach.cli github info NousResearch/hermes-agent
```
Förväntat: Repo-metadata (stars, forks, description, license).

---

## TEST 4: sia (benchmark)

```bash
cd {{USER_HOME_FWD}}/AppData/Local/hermes/eval-sandboxes/sia
```

```bash
python -c "from sia import __version__; print('v' + __version__)"
```
Förväntat: `v0.5.1`

Kör en snabb evaluering:
```bash
python -m sia evaluate --help
```
Förväntat: Hjälptext för evaluate-kommandot.

---

## BLOCKERADE — kräver manuell fix

### agentsview (ladda .exe)
1. Gå till https://github.com/kenn-io/agentsview/releases/latest
2. Ladda ner `agentsview_Windows_x86_64.exe`
3. Lägg i `{{USER_HOME}}\AppData\Local\hermes\eval-sandboxes\`
4. Kör: `agentsview.exe --help`

### hivemind (saknar tree-sitter)
```bash
cd {{USER_HOME_FWD}}/AppData/Local/hermes/eval-sandboxes/hivemind
npm install tree-sitter
npm install
```

### cua (kräver sandbox)
Plan finns: `wiki/projects/super-intelligence/plans/2026-05-13-cua-clean-product-evaluation-plan.md`
