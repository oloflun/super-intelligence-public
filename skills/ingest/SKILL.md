---
name: ingest
description: "Process vault files into wiki pages — new files or the full vault. Extraction-first: pull knowledge across 7 dimensions (Problem, Solution, What Worked, What Didn't, Key Insight, Applicability, Valid As Of). Runs a connection pre-scan before writing, then weaves every note bidirectionally into the graph. Use /ingest for new/pending files, /ingest --reindex to retroactively apply connection weaving and extraction updates to ALL previously indexed files."
---

# /ingest — Wiki Ingestion Pipeline

Processes any new or changed source file in the vault into structured wiki knowledge — then weaves that knowledge bidirectionally into the existing graph so nothing is left isolated.

## ⚠️ CRITICAL RULES (2026-06-12) — LOAD FIRST

These rules override any conflicting instructions elsewhere in this skill or in older skill versions. Every agent must read this section before touching any source file.

### Language Rules

| Source Type | Language Rule |
|-------------|---------------|
| AI conversations, articles, web clippings, project files (non-Snipd) | **Preserve source language.** Never translate. |
| Snipd: Books, personal development, general podcasts | Translate to Swedish. Quotes stay in original language. |
| Snipd: Finance/investment episodes (Fill or Kill, Market Makers, Thoughts on the Market, Bloomberg Daybreak, Veckans Trade, Prof G Markets) | **Do NOT translate snips.** Keep ALL snips and bullet points in original language. Write summary/insights in source language for consistency. |
| Quotes (`> ...`) | **Always in original language.** Never translate quotes. |

### Content-Type Router (MANDATORY before extraction)

Before applying any extraction framework, determine the source's content type:

| Source | Pipeline | Skill to Load | Extraction Method |
|--------|----------|---------------|-------------------|
| `Snipd/Data/Fill or Kill/` | Investment | `snipd-ingest` + `investment-intelligence` | Mode 1 (full snips, original language) + structured extraction |
| `Snipd/Data/Market Makers/` | Investment | `snipd-ingest` + `investment-intelligence` | Mode 1 + structured extraction |
| `Snipd/Data/Thoughts on the Market/` | Investment | `snipd-ingest` + `investment-intelligence` | Mode 1 + structured extraction |
| `Snipd/Data/Bloomberg Daybreak/` | Investment | `snipd-ingest` + `investment-intelligence` | Mode 1 + structured extraction |
| `Snipd/Data/Veckans Trade/` | Investment | `snipd-ingest` + `investment-intelligence` | Mode 1 + structured extraction |
| `Snipd/Data/Prof G Markets/` | Investment | `snipd-ingest` + `investment-intelligence` | Mode 1 + structured extraction, original language (English) |
| `Snipd/Data/The Startup Ideas Podcast/` | AI Analysis + Entrepreneurship | `snipd-ingest` + `ai-analysis` + `business-coach` | Mode 1 + segment routing: AI-tech → AI-agents concept pages, business insights → [[entrepreneurship/business-principles]] |
| `Snipd/Data/Founders/` | Book/Longform | `snipd-ingest` | Mode 2 (curated, Swedish) |
| `Snipd/Data/Skit om AI/` | AI/Entreprenörskap (Svensk) | `snipd-ingest` + `business-coach` | Mode 1, Swedish. Segment routing: AI-tech → AI-agents, business → [[entrepreneurship/business-principles]] |
| `Snipd/Data/Veckans AI/` | AI-nyheter (Svensk) | `snipd-ingest` + `ai-analysis` | Mode 1, Swedish. AI news → AI-agents |
| `Snipd/Data/The Lean Startup/` | Book/Entreprenörskap | `snipd-ingest` | Mode 2 (curated, Swedish). Audiobook merge rule → ALL tracks on ONE page. Segment routing → [[entrepreneurship/business-principles]] |
| `Snipd/Data/<audiobook>/` | Book/Longform | `snipd-ingest` | Mode 2 (curated, Swedish) |
| `raw/conversations/` | Conversation | Inline 7-dimension | Problem → Solution → What Worked/Didn't → Key Insight → Applicability |
| `raw/articles/` | Article | Inline 7-dimension | Same as conversation |
| `Clippings/`, `Web Clippings/` | Article | Inline 7-dimension | Same as conversation |

### Show Auto-Discovery (MANDATORY — 2026-07-02)

**Problem:** The routing table is static. New shows added to `Snipd/Data/` are silently skipped because they don't match any known source path.

**Solution:** Before EVERY ingest run (including cron), scan `Snipd/Data/` for directories NOT in the routing table. For each unknown show:

1. List all `.md` files in the directory
2. Read the first episode's AI description (lines 26-28 of the Snipd file)
3. Determine: language (Swedish/English), content type (investment/AI/entrepreneurship/book)
4. Add to routing table ON THE FLY (patch this SKILL.md)
5. Emit: `[ingest][discovery] NEW SHOW: "<name>" — N episodes, <type>, routing: <pipeline>`
6. Process immediately — do not defer

**Detection command:**
```bash
# Find all show directories NOT in the routing table
for dir in "$VAULT/Snipd/Data/"*/; do
    show=$(basename "$dir")
    if ! grep -q "$show" "$VAULT/.agents/skills/ingest/SKILL.md"; then
        count=$(ls "$dir"*.md 2>/dev/null | wc -l)
        echo "NEW_SHOW: $show ($count episodes)"
    fi
done
```

**Auto-classification heuristics:**
| Markers | Classification |
|---------|---------------|
| Swedish episode titles + "AI", "Claude", "agent" in AI description | AI/Entreprenörskap (Svensk) — Mode 1, Swedish |
| "track" in filenames, multiple numbered tracks | Audiobook — Mode 2, combined tracks |
| Tickers ($AAPL), "Fed", "inflation", "earnings", "market" | Investment — Mode 1, original language |
| "Founders", biography names, "how to", entrepreneurial keywords | Book/Longform — Mode 2, Swedish |
| Default (can't classify) | Flag for user: `[ingest][discovery] UNCLASSIFIED: "<name>" — please categorize` |

**After classification:** Process at least ONE episode from the new show immediately as proof of routing. The rest can follow in normal batch order.

### Business Ideas & Implementation Plans Extractor (MANDATORY — 2026-07-02)

**Regel:** Varje gång AI- eller entreprenörskaps-innehåll ingestas (oberoende av källa), MÅSTE konkreta affärsidéer, implementationstips och verksamhetstillämpningar extraheras UTÖVER all övrig processing.

**Process:**
1. Efter att wiki-page + segment-routing + bidirektionella länkar är klara:
2. Läs `wiki/entrepreneurship/ai-implementation-plans.md` för att se befintliga idéer
3. Extrahera ur källan:
   - Konkreta affärsidéer (produkter, tjänster, modeller)
   - Implementationstips (exakta steg, verktyg, workflows)
   - Tillämpningar för {{USER_NAME}}s specifika verksamheter (enskil firma, SaaS-projekt, agent-setup)
4. För varje ny idé:
   - Lägg till i §1 (🚀 Affärsidéer) med status, problem, lösning, tillämpning
   - Om idén är mogen → skapa implementeringsplan i §2 (🛠 Implementeringsplaner)
5. Uppdatera registry-uppdateringsloggen
6. Om implementeringsplanen har konkreta steg → skapa todos

**Valideringsregel:** Om källan har ≥2 AI-markörer eller ≥2 entreprenörskaps-markörer och INGEN ny idé extraherades → flagga: `[ingest][WARN] källa <titel> gav inga affärsidéer — verifiera manuellt`

**Keyword reinforcement:** If the source contains ≥3 markers from another domain, flag for review but route by keywords.

### Snipd Content: NEVER use 7-dimension framework

The 7-dimension extraction framework (Problem, Solution, What Worked, etc.) is for AI conversations, articles, and project files. **If the source is under `Snipd/Data/`, STOP.** Load `skill_view("snipd-ingest")`. Producing generic filler like "Källan gav för lite strukturerat underlag" for Snipd content is a hard failure.

### Book/Audiobook Content: Mode 2 only

Books use Mode 2 from `snipd-ingest`: 2-3 strongest examples per thematic section with expanded context (3-5 sentences each). Model after `2026-06-01-the-7-habits-of-highly-effective-people.md`. Never list 30+ one-line compressed examples.

### Investment Content: Memory System

After episode processing, update `wiki/investments/market-intelligence.md` (living document) and `wiki/investments/host-credibility.json` (host track record). These auto-load for all finance-related tasks.

### AI Content: Feature Analysis + Telegram

After episode processing, run Curiosity Gate analysis: extract ALL features → QMD cross-reference → evaluate improvement potential → implementation plans for HIGH priority candidates → Telegram delivery with clickable artifact.

Detection covers the **entire vault** via three mechanisms:
1. `status: pending-ingest` frontmatter (conversation exports from the auto-watcher)
2. Untracked/new `.md` files (Snipd, Web Clippings, anything synced from apps to vault root)
3. `.md` files committed since the last ingest (project files, manually added content)

**Core principles:**
- **Extraction > summary.** Pull the actual knowledge — problem, solution, failures — not a description of what the source is about.
- **Connection > isolation.** Every note must link outward AND update existing notes to link back. A note with no inbound links is invisible to the graph and useless to an agent searching by topic.
- **Timestamp everything.** Staleness is real. Every insight gets a date.
- **One source at a time, end-to-end.** Do not load multiple sources simultaneously. Process source N completely (extract → write → weave → coverage assert → mark completed in state) before opening source N+1. Between sources, drop reading buffers — only the state file (`wiki/.ingest-batch.json`) persists context. This is how the batch survives context compactions: a fresh agent reads the state file, skips completed entries, and resumes at the next pending one.
- **Never rewrite a complete page — in normal mode.** If a `wiki/sources/` page already exists with frontmatter + ≥3 content sections + `## Källa`, mark it completed in state and continue. Do not regenerate it — every regeneration after a compaction degrades the content. **`--reindex` mode is the explicit exception:** that mode rebuilds the entire wiki from the ground up against the current rules, so previously-complete pages ARE re-evaluated and rewritten (with the old version backed up first, see §1 reindex overrides). Use `--reindex` when global rules change and the whole knowledge base should be re-applied; use the regular `/ingest <path>` for targeted re-runs of one source with new instructions or a better model.

**⚠️ SNIPD CONTENT: For Snipd podcast and audiobook formatting, load the `snipd-ingest` skill (`skill_view("snipd-ingest")`). It is the authoritative single source of truth for Snipd format. The old inline Snipd template was removed — use `snipd-ingest` instead.**

## Usage

### Architecture Guardrails

### 2026-05-21 Deletion Freeze
Cron or unattended ingest must never delete, trash, prune, mirror-delete, or run duplicate-delete helpers with `--apply`. Any proposed deletion count greater than zero stops the run and reports exact paths. Before scheduled writes, verify the expected roots exist: `wiki/`, `raw/`, `Clippings/`, `Web Clippings/`, `Snipd/`, `.agents/`, and `memory/`.
- On Hermes/WSL, `~/vault-local` is the canonical writable mirror. Avoid `/mnt/c/...` for ingest writes or copy-back; Syncthing mirrors changes to the Windows OneDrive vault.
- A failed `/mnt/c` stat/copy/PowerShell attempt does not prove sync failed. Verify Syncthing or check the Windows vault after a moment.
- For `/ingest --reindex`, initialize/resume the batch in `reindex` mode and discover candidates with `bash "$SCRIPTS/ingest-pending.sh" --reindex`. Do not silently downgrade to `all`; that only processes pending/new files.
- After ingest, run QMD update/status only. Treat `qmd embed` as optional deep mode on Hermes/WSL because Vulkan/glslc may fail or hang. Do not block or retry endlessly.


```
/ingest                  # normal: process new/pending files; never rewrite complete pages
/ingest --recent N       # only the N most recently modified pending files
/ingest <path>           # one specific file or directory (use this when a single source
                         # needs re-running with new instructions / a better model)
/ingest --reindex        # GROUND-UP REBUILD of the entire knowledge base
/ingest --reindex-recent N # soft reingest: rewrite latest N discovered sources only
/ingest --reingest N       # alias for --reindex-recent N
/ingest --strays [N]       # stray rescue: only weak/grey/unclassified/duplicate-looking nodes
```

**Three distinct modes — pick the right one:**

| Mode | When to use | Lock-existing rule | Backup before rewrite |
|------|-------------|-------------------|----------------------|
| `/ingest` (normal) | New/pending files; never disturb existing pages | **APPLIES** — complete pages skipped | N/A |
| `/ingest <path>` | Re-run ONE source with better instructions/model | Override per-file: rewrite that one | Yes (auto, just for that file) |
| `/ingest --reindex` | **Global rule change** — apply new rules to whole wiki | **DOES NOT APPLY** — every page re-evaluated | Yes — all old pages copied to `wiki/.reindex-backup/<batch-id>/` first |
| `/ingest --reindex-recent N` / `/ingest --reingest N` | Soft reingest after improved prompts/model/scripts | **DOES NOT APPLY** for selected files | Yes — selected old pages copied to `wiki/.reindex-backup/<batch-id>/` first |
| `/ingest --strays [N]` | Raw coverage repair — process every raw/source file missing a complete wiki write-up, footer, category/project, or duplicate decision | **APPLIES to resolved unchanged raw** — unresolved raw always re-enters the queue | Report-first; duplicate deletion requires separate confirmation |

**`--reindex` is the "rebuild the whole wiki from scratch with the current rules" command.** Run it when the SKILL.md rules change (new extraction dimensions, new connection requirements, new coverage thresholds) and you want every existing page to reflect the new standard. It does not trust prior page content as "good enough" — every source goes through §2 → §5.5 again, with the previous version preserved in `wiki/.reindex-backup/<batch-id>/` so no work is lost if the rebuild produces something worse.

The state file (`.ingest-batch.json`) still gates resumption: a `--reindex` run that crashes mid-batch resumes at the next pending entry. Within ONE `--reindex` batch, completed entries are not redone. Starting a fresh `--reindex` invocation (no existing batch state) re-evaluates everything.

**`--strays` is the raw-source coverage command.** It starts from `scripts/graph-stray-audit.mjs`, which scans every raw/source markdown file under `raw/`, `Snipd/Data/`, `Clippings/`, and `Web Clippings/`. A raw file is not resolved until it has a complete processed wiki page, category/project placement, an append-only raw coverage footer, and an entry in `wiki/.raw-coverage-index.json`. Grey raw nodes are useful diagnostics: do not hide them just to make the graph cleaner.

**Raw mutation rule:** raw/source files may only be changed by adding or replacing the managed footer between `<!-- ingest:raw-coverage:start -->` and `<!-- ingest:raw-coverage:end -->` at the bottom of the file. Never edit, reorder, normalize, or delete original raw content.

**Duplicate deletion rule (UPDATED 2026-06-12):** `/ingest --strays` may write `wiki/.duplicate-delete-candidates.json`, but it must never delete files itself. **OneDrive `*(1)*` sync artifacts are auto-processed** by `scripts/vault-dedup.py` (see `vault-auto-dedup` skill): identical content = auto-delete, different content = auto-merge (append only). Non-`(1)` duplicates still require separate action-time confirmation.

## Platform Detection

Resolve the vault path before running any scripts. Check which environment you are in:

```bash
# Windows (native or Git Bash)
VAULT="{{VAULT_PATH_FWD}}"

# WSL / Hermes
VAULT="$HOME/vault-local"
[ -d "$VAULT" ] || VAULT="$HOME/Knowledge Base"

# Last-resort Windows mount fallback only; do not use for normal Hermes write-back.
[ -d "$VAULT" ] || VAULT="{{WSL_VAULT_PATH}}"

SCRIPTS="$VAULT/scripts"
```

Use `$VAULT` and `$SCRIPTS` for all paths throughout this skill. Never hardcode a platform-specific path inline.

## Per-File Algorithm

For each source file, execute these steps in order:

### 0.5 Boot — resume or initialize batch state

This step ALWAYS runs first, on every `/ingest` invocation. The batch state file
(`wiki/.ingest-batch.json`) is what makes the skill resumable across context
compactions and agent restarts.

```bash
# Does a batch already exist? (set by a prior run that didn't finish)
if bash "$SCRIPTS/ingest-state.sh" exists; then
    echo "[ingest] resuming existing batch:"
    bash "$SCRIPTS/ingest-state.sh" status
else
    # Fresh batch — feed the source list from §1 into state init
    # MODE is "normal" or "reindex"
    bash "$SCRIPTS/ingest-state.sh" init "$MODE"
fi
```

**Resume semantics:**
- `completed` entries are skipped immediately — never re-extracted, never re-written.
- `in_progress` entries (a prior run crashed mid-source) are picked up first,
  but the lock-existing check in §4 still applies: if the wiki page is already
  fully written, the entry is upgraded to `completed` without rewrite.
- `pending` entries are processed in list order (most-recent first from §1).
- After every source, the state file is written to disk **before** moving on.
  This is non-negotiable — it's the only thing standing between a compaction
  and a degraded re-write.

**Per-source loop (drives §2 → §5.5):**
```
while next=$(bash "$SCRIPTS/ingest-state.sh" next); do
    bash "$SCRIPTS/ingest-state.sh" mark "$next" in_progress
    process_one_source "$next"   # §2 → §4 → §5 → §5.5
    bash "$SCRIPTS/ingest-state.sh" mark "$next" completed \
        --wiki-page="$wiki_page" --coverage="$concepts,$entities,$inbound"
    emit_checkpoint "$next" "$wiki_page" "$backlinks"
done
```

**Checkpoint output (after each source — emit to chat):**
```
[ingest] ✓ <title> → wiki/sources/<slug>.md
[ingest] backlinks: categories/<X>, entities/<Y>, concepts/<Z>
```

When the loop exits, run §6 (index/log update) and §7 (architectural batch summary).

### 1. Identify pending files

```bash
# Normal run — new/pending files only:
bash "$SCRIPTS/ingest-pending.sh" [all|recent N|<path>]

# Full-vault reindex — ALL files including previously indexed:
bash "$SCRIPTS/ingest-pending.sh" --reindex

# Soft reingest of latest N discovered sources:
bash "$SCRIPTS/ingest-pending.sh" --reindex-recent N

# Stray rescue — raw coverage audit + unresolved source queue:
bash "$SCRIPTS/graph-stray-audit.mjs" --dry-run
bash "$SCRIPTS/ingest-pending.sh" --strays [N]
```

Returns a deduplicated list. Process most-recent first.

**Skip rules (normal mode):**
- Already indexed: check `wiki/sources/` for an existing entry with the same source path — skip if present
- `status: too-short` — fewer than 3 meaningful entries
- `status: duplicate` — same URL/content already ingested
- Files in output dirs (wiki/, memory/, scripts/, .agents/, session-logs/) — never re-ingest
- Files in build artifacts (node_modules/, .next/, dist/, build/, out/) — never ingest
- Files that are already wiki pages (`type:` frontmatter field exists)

**Coverage rules (`--strays` mode):**
- First full run audits all raw/source roots, regardless of git status or mtime.
- Later runs use `wiki/.raw-coverage-index.json` to skip only unchanged files whose coverage status is `resolved`.
- A changed hash, missing footer, missing category/project, missing wiki page, incomplete extraction, or duplicate/merge decision brings the source back into the queue.
- `Snipd/Data/Thoughts on the Market/**`, `Fill or Kill/**`, `Market Makers/**`, and `Bloomberg Daybreak*/**` default to `Investering` unless the source clearly belongs to a more specific existing category.
- If `wiki/.duplicate-delete-candidates.json` contains candidates, report them to the user with proof. Do not delete until the user confirms the exact paths in a separate attended action; unattended ingest must only report candidates.

**Skip rules (`--reindex` mode) — overrides (GROUND-UP REBUILD):**

The whole point of `--reindex` is to apply the *current* SKILL.md rules to every page in the wiki. Anything written under earlier rules is suspect by default.

- ✅ "Already indexed" check is **disabled** — every file is processed.
- ✅ The lock-existing-pages check (§4) is **disabled** — every existing wiki/sources/ page is rewritten from the source against the *current* §3 extraction framework, §5 bidirectional weaving, and §5.5 coverage assertion.
- ✅ **Backup before rewrite (mandatory).** Before overwriting any existing wiki page, copy the previous version to `wiki/.reindex-backup/<batch-id>/<original-relative-path>`. This is non-negotiable — if the rebuild produces something worse, the user can recover. Use the batch_id from `.ingest-batch.json` to namespace each rebuild's backups.
- ✅ Concept, entity, and category pages are **also re-validated**. For each, re-run the inbound-link pass (§5 step 2–4) so they pick up backlinks from sources that were ingested AFTER they were created. A page written six months ago should reference every source written since.
- ✅ For pages that the rebuilt extraction reveals as still-good: the rewrite simply reproduces them. No special-case "looks fine, leave it" logic — that's what created the v1 connection gaps.
- ❌ `status: too-short` and `status: duplicate` still apply — these files have nothing to offer.
- ❌ Build artifacts still excluded — no legitimate knowledge there.

**State-file behavior in `--reindex` mode:**
- A fresh `--reindex` invocation (no existing `.ingest-batch.json`) starts a clean batch and re-evaluates EVERY source.
- A resumed `--reindex` invocation (state file exists with `mode: reindex`) honors the in-batch `completed` marks — entries already rewritten in THIS batch aren't redone after a compaction-restart. This makes the rebuild interruptible without redoing work that was already updated to current rules.
- To genuinely "start over from scratch", run `bash "$SCRIPTS/ingest-state.sh" clear` first.

### 2. Read and classify the source

Read the raw file. Do not modify original raw/source content. In `--strays` mode only, after a source is fully covered, append or replace the managed coverage footer at the bottom of the raw/source file. Do not add frontmatter to app-managed files.

Classify by location and frontmatter:

| Location | Type | Primary extraction signal |
|----------|------|--------------------------|
| `raw/conversations/<platform>/` | AI conversation | Decisions, preferences, problems solved, failures, open questions |
| `raw/articles/` | Article / Web Clipper | Thesis, key arguments, what worked / didn't work, actionable points |
| `Snipd/Data/<show>/` | Podcast episode | **MUST delegate to `snipd-ingest` skill.** Never apply the generic 7-dimension extraction framework to Snipd content. The `snipd-ingest` skill (`skill_view("snipd-ingest")`) is the authoritative single source of truth for ALL Snipd formatting — podcast episodes use Mode 1 (full snip preservation with Swedish translation), audiobooks/books use Mode 2 (curated thematic sections with 2-3 strongest examples). Producing generic filler like "Källan gav för lite strukturerat underlag" for Snipd content is a hard failure — Snipd files contain rich, structured data from the app. Read the actual snips.
|  |
|  **Show → Pipeline Routing:** See `references/show-pipeline-routing.md` for the canonical mapping of every show to its correct extraction pipeline, language rule, and memory system. |
| `Clippings/` | Web Clipping | Title, key paragraph, actionable insight |
| Project dir | Project-specific | Decisions, architecture choices, failures, open questions |
| Other | Generic | Use judgment — see extraction framework below |

### 2.5 Connection Pre-scan

**Before writing anything**, scan the existing wiki to build a hit list. This determines what links the new note will contain AND which existing notes will be updated with a backlink.

```
For each source being ingested, collect:

A. PROJECT MEMBERSHIP
   Does this source relate to a known project?
   → Scan wiki/projects/ for index files. Check: does the source mention a
     project name, its tech stack, or its category tag (e.g. Projekt-WMS)?
   → Hits: wiki/projects/<slug>/index.md
            all sources already in wiki/projects/<slug>/conversations/
            all sources tagged with the project's category

   IMPORTANT — vault layout (post-migration):
     wiki/projects/<slug>/ holds KNOWLEDGE only:
       index.md, conversations/, plans/, logs/, agents/, decisions.md
     Project SOURCE CODE lives at ~/projects/<slug>/ (outside the vault).
     Never look for package.json, src/, node_modules/ inside the vault — those
     directories should not exist in wiki/projects/. If you find them, run
     scripts/migrate-projects-out.sh to clean up before continuing.

B. TECH / DOMAIN TAG OVERLAP
   What tools, frameworks, services, or domains appear in this source?
   (Next.js, Supabase, Vercel, MCP, git, Python, Claude, Obsidian, etc.)
   → Hits: all wiki/ pages whose frontmatter tags include any of those terms

C. PROBLEM KEYWORD OVERLAP
   What errors, failure modes, or problem types appear?
   (disk full, gc, authentication, rate limit, timeout, CORS, migration, etc.)
   → Hits: all wiki/ pages that contain those keywords in ## Problem sections

D. CONCEPT PAGE GAP CHECK
   For each technology/pattern identified in (B):
   → Does wiki/concepts/<slug>.md already exist?
   → If NO and 2+ sources share this technology → mark for concept page creation
     (create the concept page as part of this ingest run)

Record the full hit list as a working note.
Every hit will receive a backlink in §5 after the source page is written.
```

### 3. Extract knowledge — 7-dimension framework

**⚠️ SNIPD GUARD: If the source is under `Snipd/Data/`, STOP. Do not proceed with this section.** Load `skill_view("snipd-ingest")` and follow its Mode 1 or Mode 2 format. The 7-dimension extraction framework is for AI conversations, articles, web clippings, and project files — never for Snipd content. If you find yourself writing "Extraherade insikter" or "Problem / Lösning" headings for a Snipd file, you have already failed. Go back, load `snipd-ingest`, and use the correct format.

This step determines the quality of the wiki page. Go through **all 7 dimensions** for every source. Mark `N/A` if a dimension genuinely does not apply — never silently skip.

| Dimension | What to extract | Required? |
|-----------|----------------|-----------|
| **Problem** | The specific challenge, error message, failure mode, or question being addressed | Conditional |
| **Solution** | The concrete fix: exact commands, config values, code snippets, architecture | Conditional |
| **What Worked** | Specific techniques that succeeded — include *why* they worked | Conditional |
| **What Didn't Work** | Approaches that failed and *why* — often more valuable than the solution | Conditional |
| **Key Insight** | The non-obvious takeaway. What would you tell an agent researching this cold? | Always |
| **Applicability** | When/where to use this. Prerequisites. When it does NOT apply. | Always |
| **Valid As Of** | Date for any time-sensitive claim (versions, prices, market data, API behaviour) | When present |

**Timestamp rule:** Every extracted insight gets a date so staleness can be assessed:
- Snipd snip → use `episode_publish_date`
- Conversation → use `created_at` or `exported_at` from frontmatter
- Article → use publication date if known, export date otherwise
- Time-sensitive content (prices, rates, version behaviour) → add `valid_as_of: YYYY-MM-DD` to frontmatter AND inline: *(valid as of YYYY-MM-DD)*

#### Density assessment

Before extracting, assess the source:

**Dense source** (>500 words of substantive content, OR 3+ distinct actionable concepts):
- Keep most content — restructure for clarity, not for brevity
- Use the full 7-dimension framework as section headings
- **Bold** the single most critical insight in each section
- If a technology or pattern is central and no concept page exists → create one now (see §2.5 D)

**Diluted source** (<500 words useful content, OR mostly high-level opinion without specifics):
- Extract only the useful kernel
- Add this note immediately after the title:
  ```
  > *Sammanfattning: <N> nyckelmeningar extraherade från ~<M> ord källa — resterande var kontext, repetition eller utan konkret insikt.*
  ```
- Keep the synthesis under 400 words total

#### Source-type extraction rules — Snipd (MANDATORY DELEGATION)

**ALL Snipd content MUST be processed with `skill_view("snipd-ingest")`.** The `snipd-ingest` skill is the authoritative single source of truth for Snipd formatting. It has been updated (2026-06-12) with:

- **Language rule:** Depends on content type — see CRITICAL RULES at top of this skill. Finance/investment: original language. Books/personal development: Swedish. Non-Snipd: preserve source language. Quotes always in original.
- **Mode 1 (podcasts):** Full snip preservation, all bulletpoints verbatim. Finance episodes: original language throughout. Other podcasts: Swedish translation of snips/bullets, quotes in original.
- **Mode 2 (books/audiobooks):** Curated thematic sections with 2-3 strongest examples per section, expanded context (3-5 sentences each), insights tied to examples. Swedish throughout, quotes in original. Model after `2026-06-01-the-7-habits-of-highly-effective-people.md`.
- **Investment episodes:** Present market analysis, data, and reasoning as-is — never apply AI/research extraction questions. After processing, update investment-intelligence memory system.
- **AI episodes:** After Mode 1 processing, run Curiosity Gate feature analysis with stack cross-reference. Create implementation plans for HIGH priority candidates. Deliver via Telegram.

**Do not attempt to process Snipd content with the generic extraction framework.** If you find yourself writing "Extraherade insikter" or "Problem / Lösning / Vad fungerade" for a Snipd file, you are using the wrong format. Load `snipd-ingest` and follow its modes.

For `--strays`, Snipd episodes still need a processed wiki page. A raw Snipd file with no matching `source_path` wiki page is unresolved even if it appears in the graph.

**Conversations (Tier 2 — extract yourself):**
For each meaningful exchange: what decision was made, what was learned, what problem was solved, what failed, what was explicitly stated as a preference or constraint. Ignore pleasantries, filler, and context-setting.

**Articles and Web Clippings (Tier 2):**
Identify the thesis in one sentence. Extract: key claims with supporting logic, novel frameworks or models introduced, actionable conclusions. Skip examples used to illustrate points already captured.

**Project files (Tier 2):**
Focus on: architecture decisions and their rationale, approaches that were rejected and why, open questions, integration patterns.

### 4. Create the source wiki page

Write to `wiki/sources/YYYY-MM-DD-<slug>.md` (or `wiki/projects/<slug>/conversations/` for project-routed files).

In `--strays` mode, the target page must include:
- frontmatter `source_path` matching the raw/source file;
- `category: [...]` or a category wikilink;
- the existing 7-dimension extraction framework, or the Snipd `## Insikter` structure when the source is a Snipd episode;
- `## Källa` linking back to the raw/source file;
- category/project links used by the graph and MOCs.

After the wiki page is complete, append or replace this footer at the very end of the raw/source file:

```md
<!-- ingest:raw-coverage:start -->
## Processed Wiki Coverage

- Processed page: [[wiki/sources/<slug>]]
- Category: [[wiki/categories/<category>]]
- Project: [[wiki/projects/<project>/<project>]]
- Coverage status: complete
- Source hash: <hash from graph-stray-audit>
- Last checked: <ISO timestamp>
<!-- ingest:raw-coverage:end -->
```

For exact duplicates covered by a canonical source, use `Coverage status: duplicate-covered` and include `Duplicate of: [[<canonical raw file>]]`. Do not delete the duplicate unless the user has confirmed the exact path from `wiki/.duplicate-delete-candidates.json`.

**Lock-existing-pages check (anti-degradation, RUN FIRST — but mode-dependent):**

This check is the single most important defense against compaction-induced degradation in normal mode. It is also the rule that gets explicitly *inverted* in `--reindex` mode.

```bash
target="$VAULT/wiki/sources/$DATE-$SLUG.md"
MODE=$(bash "$SCRIPTS/ingest-state.sh" mode)   # "normal" or "reindex"

if [ "$MODE" = "reindex" ]; then
    # Ground-up rebuild: backup the previous version, then rewrite using current rules
    if [ -f "$target" ]; then
        backup_dir="$VAULT/wiki/.reindex-backup/$BATCH_ID"
        mkdir -p "$backup_dir/$(dirname "wiki/sources/$DATE-$SLUG.md")"
        cp -p "$target" "$backup_dir/wiki/sources/$DATE-$SLUG.md"
        echo "[ingest][reindex] backed up $target -> $backup_dir/"
    fi
    # Fall through to full re-extraction + write
else
    # Normal mode: lock-existing check
    if [ -f "$target" ]; then
        has_frontmatter=$(head -1 "$target" | grep -c "^---$")
        section_count=$(grep -cE "^## " "$target")
        has_source=$(grep -c "^## Källa" "$target")
        if [ "$has_frontmatter" = "1" ] && [ "$section_count" -ge 4 ] && [ "$has_source" -ge 1 ]; then
            echo "[ingest] ⊙ $SLUG already complete, skipping"
            bash "$SCRIPTS/ingest-state.sh" mark "$SRC" completed --wiki-page="wiki/sources/$DATE-$SLUG.md"
            return 0
        fi
        # Page exists but is incomplete: fill in missing sections only,
        # do not rewrite prose that's already there.
    fi
fi
```

**Why two behaviors?**

- **Normal mode:** During the v1 test run, after a context compaction the agent regenerated already-written pages with progressively worse content (a good long Swedish version was overwritten by a generic boilerplate on the third attempt). The lock-existing check prevents that. In normal `/ingest` runs, anything already written is assumed correct.

- **`--reindex` mode:** The whole purpose is to apply *new* rules to *old* pages. Skipping complete pages defeats the purpose. So the rule inverts: every page is rewritten against current rules, and the previous version is preserved in `wiki/.reindex-backup/<batch-id>/` so nothing is lost. Within ONE reindex batch, the state file's `completed` mark still prevents re-processing already-rewritten entries — that's the compaction defense for `--reindex`.

**Targeted single-file re-runs** (`/ingest <path>`): treated as `--reindex` for that one file. Backup first, rewrite with current rules.

**Frontmatter:**

```yaml
---
title: "<episode/article/conversation title>"
type: source
source_path: <relative path from vault root>
source_url: <direct URL if available — episode_url, article URL, etc.>
captured: YYYY-MM-DD          # when it was snipped/exported/clipped
ingested: YYYY-MM-DD          # today
valid_as_of: YYYY-MM-DD       # only for time-sensitive content (markets, versions)
tags: [tag1, tag2]
category: [Category1]
confidence: high|medium|low
platform: snipd|claude|web-clip|chatgpt|article|etc
show: <podcast show name>     # Snipd only
---
```

**Body — use the dimensions that apply. For debugging/implementation sources use the full Problem→Solution structure. For podcast/article sources use Nyckelinsikter as the primary section:**

```markdown
## Problem
[What challenge, error, or question this addresses. Include exact error messages if present.
Skip this section entirely only if the source has no problem-solving content.]

## Lösning / Approach
[The concrete fix or method. Include exact commands, config values, code snippets.
Skip only if no solution is provided.]

## Vad fungerade ✓
[Specific techniques that succeeded. Explain *why* they worked where non-obvious.
Skip if absent from source.]

## Vad fungerade inte ✗
[Approaches that failed and why. Never omit if the source mentions failed attempts —
this is often the most valuable part for a future agent hitting the same wall.]

## Nyckelinsikter
[The non-obvious takeaways. What would you tell an agent researching this from scratch?
Always present — minimum one bullet.]

## Tillämplighet
[When and where to use this. Any prerequisites or version requirements.
Explicitly note when this does NOT apply.]

## Källa

- Originalfil: [[relative/path/to/source]]
- Direktlänk: [Öppna källan](URL)  <!-- Always include — lets agent navigate back -->
- Publicerad: YYYY-MM-DD
- Exporterad: YYYY-MM-DD

## Relaterade sidor

[Populated from §2.5 hit list — see §5 for exact format]
```

### 4.5 Update category MOC pages

For each category assigned in the frontmatter, append a link to the new source page in `wiki/categories/<Name>.md`:

```markdown
- [[sources/YYYY-MM-DD-slug]] — one-line summary (captured: YYYY-MM-DD)
```

### 4.6 Deduplication within the source

Before writing the wiki page, scan the extracted content for repetition. Apply:

- **Keep the most information-dense version.** If two snips cover the same insight, use the one with more precise data, clearer framing, or stronger quote. Drop the weaker one entirely.
- **Merge when both have unique parts.** If the weaker snip adds one fact the stronger doesn't, fold that addition as a sub-bullet, then discard the redundant body.
- **Result:** one clean, non-redundant insight block per distinct idea. Never two bullets saying the same thing in different words.

### 4.7 Architectural/systematic concept check (MANDATORY)

After extraction, scan for **structural, architectural, or systematic concepts** — patterns, workflows, principles, or configurations that could improve the agent/wiki setup. This step is **mandatory and produces required output even when no candidates are found**.

For each candidate:
1. State the concept in one sentence.
2. Compare against current system (read relevant parts of `wiki/concepts/`, `CLAUDE.md`, skill files).
3. Gate on significance: only flag if the improvement is substantial and conflict risk is low.
4. Append to `wiki/.ingest-arch-pending.json` (a list of candidates accumulating across batches for periodic user review):

```
[ingest] Architectural candidate found in "<source title>":
Concept: <one-sentence description>
Relevance: <what aspect of our setup this touches>
Current approach: <how we do it now>
Conflict risk: low | medium | high — <brief reason>
Verdict: recommend | investigate | ignore
```

**Required end-of-batch output (ALWAYS emit, even if zero candidates):**

```
[ingest][batch] architectural candidates: N
  1. <concept> — verdict: recommend|investigate|ignore — relevance: <one-line>
  ... or, if N=0:
  (no architectural candidates found in this batch — content was domain knowledge with no transferable system-level patterns)
```

The "no candidates found" line is **not optional**. Silence is not an acceptable substitute. If a source is purely domain content (e.g. market analysis, podcast episode about a specific company) with no agent/wiki applicability, explicitly say so. Domain knowledge for a *future* project (e.g. market analysis when no example-app project is active yet) should be flagged as `verdict: investigate — store for future <project>` rather than ignored.

### 5. Bidirectional Connection Weaving

This is the step that turns isolated notes into a connected graph. Execute **both outbound and inbound** linking.

**Outbound links (from new note → hit list pages):**

Structure `## Relaterade sidor` by relationship type for readability:

```markdown
## Relaterade sidor

**Projekt:** [[projects/project-a/index]], [[projects/example-app/index]]
**Koncept:** [[concepts/supabase]], [[concepts/agent-skill-architecture]]
**Entiteter:** [[entities/vercel]], [[entities/carl]]
**Källrelationer:** [[sources/2026-03-15-related-slug]], [[sources/2026-02-10-other-slug]]
**Kategorier:** [[categories/Dev-tools]], [[categories/AI-agents]]
```

Include every page from the §2.5 hit list. Do not truncate.

**Inbound links (existing pages → new note) — the critical step:**

Go through each page in the hit list and append a reference back to the new source:

1. **Project index** (`wiki/projects/<slug>/index.md`):
   Append under `## Relevanta källor` (create the section if missing):
   ```markdown
   - [[sources/YYYY-MM-DD-slug]] — one-line summary (captured: YYYY-MM-DD)
   ```

2. **Concept pages** (`wiki/concepts/<name>.md`):
   Append under `## Källor om detta` (create section if missing):
   ```markdown
   - [[sources/YYYY-MM-DD-slug]] — one-line summary (captured: YYYY-MM-DD)
   ```

3. **Entity pages** (`wiki/entities/<name>.md`):
   Append dated reference under relevant section:
   ```markdown
   - [[sources/YYYY-MM-DD-slug]] — one-line summary (captured: YYYY-MM-DD)
   ```

4. **Top-3 most related source pages** (highest tag/keyword overlap from §2.5):
   Append to their `## Relaterade sidor`:
   ```markdown
   - [[sources/YYYY-MM-DD-new-slug]] — one-line reason for connection
   ```

5. **Cross-project concept bridges** (if §2.5 D flagged a missing concept page):
   Create `wiki/concepts/<tech>.md`:
   ```markdown
   ---
   title: "<Technology/Pattern Name>"
   type: concept
   tags: [tag1, tag2]
   created: YYYY-MM-DD
   updated: YYYY-MM-DD
   ---

   # <Technology/Pattern Name>

   [1-paragraph explanation of what this is and why it matters]

   ## Används i projekten

   - [[projects/<slug1>/index]] — how/why this project uses it
   - [[projects/<slug2>/index]] — how/why this project uses it

   ## Nyckelinsikter

   [Key cross-project insights about this technology]

   ## Källor om detta

   - [[sources/YYYY-MM-DD-slug]] — one-line summary (captured: YYYY-MM-DD)
   ```
   Then update BOTH project index pages to link to the new concept page.

### 5.5 Coverage assertion (MANDATORY before marking source completed)

After §5 completes, count what was actually linked and emit a coverage line. This is a fail-loud check — sources that came out under-connected are flagged before the agent moves on.

```
[ingest][source: <slug>] coverage:
  concepts:  N created/linked  (e.g. created: great-work; linked: agent-skill-architecture)
  entities:  N created/linked  (e.g. created: paul-graham, mike-wilson)
  inbound:   N pages updated   (e.g. categories/Entreprenörskap, entities/paul-graham, concepts/great-work)
  arch_check: <verdict from §4.7> (e.g. "0 candidates" or "1 candidate: investigate")
```

**Fail-loud rules:**

- If `concepts == 0` AND `entities == 0`:
  emit `[ingest][WARN] no concept or entity links — re-running pre-scan` and re-attempt §2.5 with broader keyword extraction.
  If still zero on second pass, log the source as `low_connectivity` in state, append a `[ingest][WARN] low_connectivity: <slug>` line to `wiki/log.md`, and continue (don't block the batch).

- If `inbound == 0`:
  emit `[ingest][WARN] no backlinks created` and force at least the category MOC update (every source has ≥1 category, so `categories/<X>.md` is the floor).

The coverage block is **also written to `wiki/log.md`** so coverage history is auditable across batches:
```
## [YYYY-MM-DD] ingest | <source title>
coverage: concepts=1 entities=2 inbound=3 arch_check=0_candidates
```

Only after the coverage assertion passes (or has been logged as a warning) does the agent mark the source `completed` in `.ingest-batch.json` and move to the next.

### 5.6 Assign topical categories

Read `wiki/categories/_taxonomy.md`. For each source, pick 1–3 categories:
- Strong fit → assign silently
- No good fit → add to end-of-batch proposal list (see §6b)

**Heuristics:**
| Content | Categories |
|---------|-----------|
| Fill or Kill, Market Makers, stocks, markets, portfolio strategy | `Investering` |
| Thoughts on the Market, Bloomberg Daybreak, macro/central banks/credit/rates/equities/portfolio risk | `Investering` |
| Startup Ideas Podcast: AI agents, LLM tools | `AI-agents`, `Entreprenörskap` |
| Conversations: agent setup, coding tools | `AI-agents`, `Dev-tools` |
| Swedish tax, enskild firma | `Skatt-juridik` (future broader bucket: `Ekonomi`) |
| Business decisions, company building | `Entreprenörskap` |
| Personal goals, preferences | `Personligt` |

Every new source must explicitly decide: existing category, existing project, or category proposal. Silence is a bug. If no existing category/project fits, append to `wiki/.ingest-category-feedback.md` with source path, proposed category/project, reason, confidence, and the prompt `approve / rename / map to existing`.

After adding a category page or project hub, run `node "$VAULT/scripts/update-graph-colors.mjs"` so both `.obsidian/graph.json` and `.obsidian/graph-{{USER_NAME}}.json` receive deterministic color groups.

### 6. Update index and log

Append to `wiki/index.md` under the correct section:
```
- [YYYY-MM-DD] [[sources/<slug>]] — one-sentence summary (captured: YYYY-MM-DD)
```

Append to `wiki/log.md`:
```
## [YYYY-MM-DD] ingest | <source title> (captured: YYYY-MM-DD)
```

### 6b. End-of-batch: category proposals

After processing all files, present any "no fit" proposals as a single block:

```
[ingest] New category proposals — please review:

1. "Hälsa" — Träning, kost, välmående. Fits: <source title>
   Approve? (y / rename / pick existing / skip)
```

For each approval: create `wiki/categories/<Name>.md`, append to `_taxonomy.md`, register in `wiki/index.md` and `CLAUDE.md`.

### 7. Mark as ingested

**Files in `raw/`:** set `status: ingested` + `ingested: YYYY-MM-DD` in frontmatter.
**Files outside `raw/`** (Snipd, Web Clippings etc.): do NOT modify — managed by external apps. Ingest state is tracked via `wiki/.ingest-state.json`.

### 8. After the batch

```bash
# Update QMD search index. Use wrappers so every shell uses the intended index path.
if [ -x "$HOME/.hermes/scripts/qmd-hermes" ]; then
    "$HOME/.hermes/scripts/qmd-hermes" update
    "$HOME/.hermes/scripts/qmd-hermes" status
else
    powershell -ExecutionPolicy Bypass -File "$HOME/.agents/scripts/qmd-win.ps1" update
fi

# Do NOT run qmd embed as a required ingest step on Hermes/WSL. It is optional deep mode
# and may fail/hang because of the Vulkan/glslc toolchain. Ingest success is based on
# wiki writes + graph links + qmd update/search visibility.

# Commit when operating in a git-backed vault and the mount is healthy. On Hermes, prefer
# Syncthing for Windows propagation; do not copy back through /mnt/c as part of normal ingest.
cd "$VAULT" && git add -A && git commit -m "ingest: <N> sources - <brief description>" || true

# Advance ingest baseline (MUST run after successful writes; commit may be skipped on Hermes).
bash "$SCRIPTS/ingest-pending.sh" --mark-ingested
```

## Conventions

- **Extraction > summary.** Pull the actual insight across all 7 dimensions — not a description of what the source is about.
- **Bidirectional linking is not optional.** If the new note links to a project/concept/entity, that page must link back. One-way links produce isolated graph nodes.
- **Connection before creation.** Run §2.5 pre-scan before writing §4. The hit list determines the content of `## Relaterade sidor` on first write.
- **Timestamp everything.** `captured:` in frontmatter; *(captured: YYYY-MM-DD)* inline for time-sensitive claims.
- **"What Didn't Work" is first-class knowledge.** A failed approach documented with a reason is often more useful to a future agent than the successful one.
- **Always link back to source.** Every wiki page must have `## Källa` with both a wikilink and a direct URL.
- **`valid_as_of:`** on any claim about prices, rates, tool versions, market conditions, or API behaviour. Absence means "likely still valid"; presence is a staleness flag.
- One wiki page per entity/concept — check `index.md` before creating.
- **Preserve source language.** Do not translate content. A Swedish source stays Swedish, an English source stays English. Never translate quotes, bullet points, or body text from their original language. Write summaries and insights in the source's language for consistency.
- Mark opinions: "Min bedömning:" or "Analytikerns syn:".
- Conversations with <3 meaningful exchanges: mark `status: too-short`.
- Duplicates: mark `status: duplicate`. This includes conversations that are purely a recap of already-ingested knowledge — if the entire content is a rephrasing of what's already in the wiki, skip it.
- `category:` = controlled topical axis (from taxonomy). `tags:` = free-form descriptors.

## Notes

- The auto-export watcher deposits AI conversations to `raw/` with `status: pending-ingest`.
- Snipd syncs directly to `Snipd/Data/<show>/` — no routing needed.
- Web Clippings land wherever the browser extension places them — git-untracked detector catches them.
- Build artifacts (node_modules, dist, .next) are excluded by both the detection script and Obsidian's vault settings. If new artifact directories appear in graph view, add them to `.obsidian/app.json` → `userIgnoreFilters`.
- You are the synthesis step. No watcher understands content — only you can.

## Ingest v3 Addendum

These rules close the gaps found on 2026-04-26 after the first Hermes reindex attempt.

### Canonical Paths

- Windows vault: `{{VAULT_PATH_FWD}}`
- Hermes vault: `{{WSL_HOME}}/Knowledge Base`
- `{{WSL_HOME}}/vault-local` is legacy only. Do not make new scripts depend on it unless the canonical folder is missing.

### Hard Reindex Discovery

`--reindex` must discover the whole knowledge base, not just pending raw files. It must include raw conversations, raw articles, Snipd, Clippings, Web Clippings, existing `wiki/sources`, and project knowledge pages such as `wiki/projects/*/index.md`, `conversations/`, `plans/`, `logs/`, and `decisions.md`. If discovery returns fewer than 50 files, warn loudly before continuing because that usually means path drift.

### Soft Reingest

`--reindex-recent N` and `--reingest N` are soft reingest modes. Use them when the previous ingestion quality was unsatisfactory and the user has changed instructions, changed model, or patched scripts. They rewrite only the latest N discovered sources, with the same backup-before-rewrite rule as hard reindex.

### Cross-Source Duplicate Check

Before writing a source page, search existing `wiki/sources` for same title, same source path, same URL, or near-duplicate body. Keep the richest/newest page as canonical. If an older page contains facts missing from the richer page, merge those facts into the canonical page under a dated note and add a comment explaining source recency. Do not silently discard context. Existing duplicate cleanup is report-first; destructive cleanup requires explicit user approval.

### Category Consolidation

`Investering` is the canonical category for market, portfolio, stock, and investment content. Do not assign new sources to `Finans`. Reserve a future `Ekonomi` category for broader personal finance, tax-adjacent, and economic-structure material if the user approves it later.

### Graph Hygiene

Project index pages must remain visible in Obsidian graph view. Build/package clutter should be filtered by path rules, not by hiding all orphans. Category and project color groups should be maintained in `.obsidian/graph-{{USER_NAME}}.json` and `.obsidian/graph.json`.

Raw evidence folders (`raw/`, `Snipd/Data/`, `Clippings/`, `Web Clippings/`) should not be the primary graph surface. They remain preserved on disk, but the graph should prefer structured wiki summaries in `wiki/sources/` and project/category hubs. Use `scripts/graph-stray-audit.mjs` to find raw files that still need summaries or category/project rescue.

Run `node "$VAULT/scripts/update-graph-colors.mjs"` after category/project changes. The script assigns deterministic colors to every project/category and keeps both graph configs aligned.

### Bulk Processing Pattern (added 2026-06-12)

When re-processing many episodes (50+), **do not use delegate_task for the full scope.** Subagents time out at 600s when the scope is too large. Instead:

1. **Write a Python batch script** (see `scripts/master-reprocess.py`) that processes files sequentially with state tracking (`--vault` flag, progress log, `.reprocess-state.json` for resume capability).
2. **Run it via terminal with `background=true` and `notify_on_complete=true`.**
3. **Books/Founders require manual Mode 2 curation** — batch scripts can handle Mode 1 (investment/AI episodes) but Mode 2 needs per-episode reasoning. Process these via delegate_task in small batches (3-4 episodes per subagent) or let the auto-ingest cron handle them one at a time.
4. **After batch processing, always run QMD update** (`qmd-win.ps1 update` on Windows, `qmd-hermes update` on WSL).

**Cron delivery gotcha:** When creating or updating a cron job that should reach the user, always set `deliver: "telegram:<chat_id>"`. The default `deliver: "local"` saves output silently — the user never sees it. Verify with `cronjob action='list'` after creating/updating.

Use the platform wrapper so all agents share the intended QMD index:
- Windows: `powershell -ExecutionPolicy Bypass -File "$HOME/.agents/scripts/qmd-win.ps1" <qmd args>`
- Hermes: `{{WSL_HOME}}/.hermes/scripts/qmd-hermes <qmd args>`
