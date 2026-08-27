# Karpathy Wiki Setup

Adapted from Andrej Karpathy's LLM wiki methodology for the Super-Intelligence Agent Stack.

## Philosophy

> "Treat your AI knowledge base like a personal wiki. Every conversation becomes a page. Entities, concepts, and projects are linked. The wiki grows organically."

## Setup

### 1. Directory Structure

```
{{VAULT_PATH}}/
├── wiki/
│   ├── concepts/       # Reusable ideas (e.g., "token-optimization.md")
│   ├── entities/       # People, tools, systems (e.g., "carl.md")
│   ├── projects/       # Active projects (e.g., "super-intelligence.md")
│   ├── sources/        # Raw conversation exports
│   └── index.md        # Global wiki index
├── raw/
│   └── conversations/  # Auto-exported conversations
│       ├── claude/
│       ├── chatgpt/
│       └── gemini/
└── .wiki-ingest-ledger.json  # Tracks which conversations are ingested
```

### 2. Auto-Export Pipeline

**Tampermonkey Script:** `wiki-ingest/auto-wiki-ingest-v2.user.js`
- Installed in browser via Tampermonkey
- Auto-exports conversations as .md files on navigation
- Downloads to configured directory

**File Watcher:** `wiki-ingest/watch-and-route-v2.sh`
- Polls download directory every 5 seconds
- Routes files to `raw/conversations/{platform}/`
- Auto-commits to git

### 3. Ingestion Workflow

When files appear in `raw/conversations/`:

```bash
# Agent runs /ingest skill:
# 1. Read the raw conversation
# 2. Extract entities, concepts, decisions
# 3. Create/update wiki pages
# 4. Update .wiki-ingest-ledger.json
# 5. Run qmd update
# 6. Commit
```

### 4. Linking Conventions

- Use `[[wikilinks]]` for Obsidian compatibility
- Link concepts first time they appear in each page
- Create stub pages for missing links (let them grow organically)
- Tag pages with `type:` and `status:` in frontmatter

### 5. Search

Once ingested, all wiki content is searchable via:
- `qmd query "topic"` — semantic + keyword
- `/recall <topic>` — multi-source (QMD + sessions.db + CARL + chorus)
- Obsidian graph view — visual navigation

### 6. Maintenance

- Run `qmd update` after bulk ingest
- Review `.wiki-ingest-ledger.json` for failed ingests
- Archive stale conversations to `raw/archive/`
- Prune the wiki periodically (merge small pages, split large ones)

## References

- [Andrej Karpathy on LLM Wiki](https://karpathy.ai/)
- See `llm-wiki-setup-guide.md` for the original full guide
- See `hermes_self_improvement_deep_dive.md` for self-improvement patterns
