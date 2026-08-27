---
name: recall
description: "Two-phase search: QMD search (vault + federated project index) for fetching, a synthesis subagent for interpretation (citations, gap analysis, conflict detection). v3 adds trigger-aware skill boosting. Use /recall <query> [--synthesis|--wiki|--raw|--sessions|--decisions|--chorus]."
optimized_by: "SIA run_6 gen_3 — 2026-06-27"
updated: 2026-08-25
---

# /recall — Two-Phase Unified Search (v3.1 — gbrain decommissioned)

**Fas 1: Hämta** — QMD (valv + federerat projektindex), behåll träffar ≥50%. Visa råa resultat.
**Fas 2: Tolka** — en syntes-subagent tolkar de kombinerade resultaten (citat, gap-analys, konfliktdetektion).

> gbrain avvecklat 2026-08-25 (0.55 recall@5 @ 12,6s mot qmds 0.90 @ 4,6s; strukturellt
> PGLite-haveri). Alla `gb search`/`gb think`-anrop nedan är ersatta. Se
> `wondrous-wishing-star.md` Fas 0.1.

## v3 Improvements (from SIA gen_3, 98.4% term coverage)

### 1. Skill Trigger Awareness
Before search, scan `.agents/skills/*/SKILL.md` for `triggers:` in YAML frontmatter. Build trigger→skill mapping. If query matches a known trigger keyword, **boost matching skills by +0.3** above semantic results. This ensures `/design` master router ranks #1 for "design system" queries.

Swedish triggers included: `designa` → `/design`, `återkalla` → `/recall`, etc.

### 2. Cross-Source Federation
QMD's projektindex (`~/.cache/qmd/projects.sqlite`) redan federerar valvet med **varje
git-repo i `~`** (`super-design`, `project-a-next`, `project-c-next`, `designpowers`,
`example-analysis`, `project-b`, …) — en kollektion per repo, keyword/AST-baserad.
`qmdv.py` slår ihop valv + projekt automatiskt i ett anrop. Inget separat käll-flagg
eller extern graf-backend behövs längre.

### 3. Two-Pass Retrieval for Ambiguous Queries
- **Pass 1:** Semantic + keyword search (current behavior)
- **Pass 2:** If query contains known trigger keywords, search for skills that trigger on those keywords
- **Merge:** Trigger-matched skills get +0.3 score boost. Sort merged results by adjusted score.

### 4. Project ↔ Skill Linking
Om en fråga matchar en skill, sök skillens namn/nyckelord i projektindexet (via `qmdv`)
för att hitta projekt skapade från den skillen (t.ex. `/design` → `super-design`). Den
tidigare grafbaserade traverseringen (`gb think --follow skill-to-project`) finns inte
längre — syntes-subagenten (Fas 2) noterar kopplingar den ser i sökträffarna, men gör
ingen strukturerad graf-traversal.

---

## Protokoll

### Fas 1 — Fetch (RAW RESULTS)

```bash
python ~/.agents/scripts/qmdv.py "<query>" --json
# eller direkt MCP-åtkomst:
mcp_qmd_query(searches=[{"type":"lex","query":"<query>"},{"type":"vec","query":"<question>"}], limit=8, rerank=false)
```

**Filtrering:** Behåll endast träffar med ≥50% (QMD). Bredare spridning endast om användaren explicit ber om det ("visa alla", "ge mig allt", "wider spread").

**v3 Boost:** Before presenting, check query against trigger map. If match, add boosted skill hits at top with `[TRIGGER BOOST]` label.

**Presentation:** Visa kombinerade råa träffar sorterade efter score. Format:

```
| # | Source | Score | Hit |
|---|--------|-------|-----|
| 1 | QMD | 100% | file-path.md — snippet |
| 2 | TRIGGER | BOOST | .agents/skills/design/SKILL.md — /design master router |
```

**Viktigt:** Presentera råa resultat som de är. Ingen syntes, ingen beskrivning av vad resultaten "betyder". Användaren vill se vad varje verktyg hittade.

### Fas 2 — Interpret (SYNTHESIS)

Spawna en syntes-subagent (Agent-verktyget) med Fas 1:s kombinerade råa träffar +
användarens ursprungliga fråga i kontext. Instruera den att producera:

- Syntetiserat svar med citerade källor (filsökväg + rad)
- Gap-analys (vad som saknas / inte täcks av träffarna)
- Konflikt-detektion (motsägande källor — flagga båda, ta inte automatiskt ställning)

**v3:** Om ett skill-match hittades i Fas 1, be subagenten även notera relaterade
projekt den ser i träffarna (ersätter `--follow skill-to-project`).

**Timeout:** inget hårt timeout-anrop, men om subagenten tar orimligt lång tid (upplevs
som >120s väntan), avbryt och fall tillbaka till Fas 1-resultaten och summera manuellt.

## Anrop

```
/recall <query>                  # Fas 1 + Fas 2 (full pipeline, v3 trigger boost active)
/recall <query> --fetch          # Endast Fas 1 (råa resultat)
/recall <query> --synthesis      # Endast Fas 2 (syntes-subagent)
/recall <query> --wiki           # Endast QMD wiki
/recall <query> --raw            # Endast QMD raw/conversations
/recall <query> --sessions       # Endast sessions.db
/recall <query> --decisions      # Endast CARL
/recall <query> --chorus         # Endast chorus
/recall <query> --no-boost       # Skip trigger boost (raw semantic search only)
```

## Trigger Map (Built at Init)

Scan `.agents/skills/*/SKILL.md` frontmatter. Key triggers:

| Trigger | Skill |
|---------|-------|
| `design`, `designa`, `design system`, `redesign`, `build a page`, `polish`, `animation`, `visual direction`, `mockup`, `hero`, `CTA`, `pricing page` | `/design` master router |
| `recall`, `återkalla`, `sök`, `search`, `hitta`, `find` | `/recall` |
| `skill`, `create skill`, `patch skill` | `/skill` |
| `standup`, `status`, `what are we doing` | `/standup` |
| `conclude`, `wrap up`, `avsluta` | `/conclude` |
| `ingest`, `process raw` | `/ingest` |

## Detaljerade käll-regler

### QMD — `mcp_qmd_query`

**ALLTID `rerank: false`.** Utan rerank används RRF-scoring (~1s). Med rerank: 133s+ → överskrider 120s timeout.

```bash
mcp_qmd_query(searches=[...], limit=8, rerank=false)
```

### sessions.db — `session_search`

```bash
session_search(query="<query>", limit=3)
```

### CARL — `carl_search_decisions`

```bash
mcp_carl-mcp_carl_search_decisions(query="<query>")
```

### chorus

```bash
chorus search "<query>" --agent <agent> --cwd <cwd> --json
```

## Felhantering

- **Timeout (>120s):** hoppa över källan, notera `[TIMEOUT]`
- **Källfel:** logga `[ERROR] <källa>: <orsak>`, fortsätt med övriga
- **Inga träffar ≥50%:** "Inga signifikanta träffar. Vill du sänka tröskeln?"
- **Alla källor nere:** "Alla minneskällor otillgängliga."
- **Syntes-subagent misslyckas/timeout:** Fall tillbaka till Fas 1-resultaten, summera manuellt
- **Trigger map build fails:** Skip boost, proceed with normal semantic search

## Noter

- Skillen har inga sidoeffekter — endast läsning (Fas 2:s subagent är också read-only: sök + syntetisera, ingen filskrivning).
- QMD måste vara igång för wiki/raw-sökningar.
- sessions.db FTS5 fungerar utan server.
- gbrain avvecklat 2026-08-25 — inga `gb`/`gbrain`-anrop kvar i denna skill.
- Trigger map uppdateras vid varje `/recall`-anrop för att fånga nya skills.
- Cross-source federation sker automatiskt via qmdv:s projektindex, inget explicit källflagg behövs.
