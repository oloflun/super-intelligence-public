---
title: "LLM Wiki setup guide"
type: note
category: [AI-agents, Dev-tools]
---

# LLM Wiki — Complete Setup Guide

## Your Setup: Karpathy's LLM Wiki + Automatic Conversation Ingestion

This guide gives you *exactly* what to do, step by step, to build a personal knowledge base that:

1. Follows Karpathy's three-layer architecture (raw → wiki → schema)
2. Works with **Claude Code, Codex, and any MCP-compatible agent**
3. **Automatically ingests every conversation** from Claude.ai and ChatGPT

---

## Part 1 — Directory Structure

Create this in a location of your choice (e.g. `~/wiki` or an Obsidian vault):

```
~/wiki/
├── CLAUDE.md              # Schema file (Claude Code reads this)
├── AGENTS.md              # Schema file (Codex/OpenCode reads this)
├── raw/                   # Immutable source documents
│   ├── articles/          # Web clips, PDFs, reports
│   ├── conversations/     # ← Auto-ingested chat exports land here
│   │   ├── claude/        # Claude.ai conversations (markdown)
│   │   ├── chatgpt/       # ChatGPT conversations (markdown)
│   │   └── claude-code/   # Claude Code sessions (markdown)
│   └── assets/            # Images, attachments
├── wiki/                  # LLM-maintained knowledge base
│   ├── index.md           # Master index of all wiki pages
│   ├── log.md             # Chronological activity log
│   ├── overview.md        # High-level synthesis
│   ├── entities/          # People, companies, tools
│   ├── concepts/          # Ideas, patterns, techniques
│   ├── sources/           # One summary page per raw source
│   ├── projects/          # Project-specific knowledge
│   └── personal/          # Goals, decisions, preferences
├── scripts/               # Automation scripts
│   ├── export-claude.sh
│   ├── export-chatgpt.sh
│   ├── export-claude-code.sh
│   ├── convert-to-markdown.py
│   └── sync-wiki.sh       # Master sync script
└── .qmd.yaml              # QMD search config (optional)
```

Initialize as a git repo immediately:

```bash
cd ~/wiki
git init
echo "raw/conversations/.tokens" >> .gitignore
git add -A && git commit -m "init: wiki structure"
```

---

## Part 2 — The Schema Files

### `CLAUDE.md` (for Claude Code)

```markdown
# Wiki Knowledge Base — Agent Instructions

You are maintaining a personal knowledge base wiki. Follow these rules precisely.

## Architecture

- `raw/` — Immutable source documents. NEVER modify these.
- `wiki/` — You own this entirely. Create, update, and cross-link pages here.
- This file (`CLAUDE.md`) — The schema. You and I co-evolve this.

## Page Types & Templates

### Source Summary (`wiki/sources/`)
```yaml
---
title: "Source Title"
type: source
source_path: raw/conversations/claude/2026-04-06-topic.md
ingested: 2026-04-06
tags: [tag1, tag2]
confidence: high|medium|low
---
```
Key takeaways, then cross-references to entity/concept pages.

### Entity Page (`wiki/entities/`)
People, tools, companies. Include: what it is, relationship to me, 
key facts, source references with `[[wikilinks]]`.

### Concept Page (`wiki/concepts/`)
Ideas, patterns, techniques. Include: definition, how it relates 
to other concepts, where it came from, my current understanding.

### Project Page (`wiki/projects/`)
Active projects. Include: status, goals, decisions made, 
open questions, related conversations.

### Personal Page (`wiki/personal/`)
Goals, preferences, decisions, self-knowledge derived from 
conversations. Update incrementally.

## Workflows

### Ingest a new source
1. Read the source in `raw/`
2. Create a summary page in `wiki/sources/`
3. Update `wiki/index.md` — add the new page with one-line summary
4. Update or create relevant entity/concept/project pages
5. Append to `wiki/log.md`: `## [YYYY-MM-DD] ingest | Source Title`
6. Cross-link: every page should link to related pages with [[wikilinks]]

### Ingest a conversation
Same as above, but additionally:
1. Extract: decisions made, preferences stated, problems solved, 
   tools/techniques discussed, open questions
2. Update `wiki/personal/` pages with any new self-knowledge
3. Update project pages if the conversation touched active projects
4. File insights — don't just summarize the chat, extract the *knowledge*

### Answer a query
1. Read `wiki/index.md` to find relevant pages
2. Read those pages
3. Synthesize an answer with [[wikilink]] citations
4. If the answer is substantial, file it as a new wiki page

### Lint
Run periodically. Check for:
- Orphan pages (no inbound links)
- Stale claims contradicted by newer sources
- Concepts mentioned but lacking their own page
- Missing cross-references
- Pages with no source citations

## Conventions
- All wiki pages use Obsidian-compatible `[[wikilinks]]`
- Frontmatter YAML on every page
- One page per entity/concept — don't duplicate
- Every claim should trace back to a source
- Separate fact from interpretation — mark opinions as "My take:" or "Analyst view:"
- Swedish content is fine — don't translate unless asked
```

### `AGENTS.md` (for Codex / OpenCode / other agents)

Same content as above. Just copy `CLAUDE.md` to `AGENTS.md`:

```bash
cp CLAUDE.md AGENTS.md
```

---

## Part 3 — Exporting Conversations

### 3A. Claude.ai (web conversations like this one)

**Method: Built-in data export + conversion script**

1. Go to **claude.ai → Settings → Privacy → Export Data**
2. You'll receive a ZIP via email containing JSON
3. Run the conversion script (below) to produce markdown files

**For ongoing/automated exports**, install the Chrome extension:

```
socketteer/Claude-Conversation-Exporter
```
- GitHub: https://github.com/socketteer/Claude-Conversation-Exporter
- Supports bulk export as JSON, Markdown, or Plain Text
- Can export all conversations or filter by search

**Alternative — Tampermonkey (works for Claude + ChatGPT + Gemini + Grok):**

```
revivalstack/ai-chat-exporter
```
- GitHub: https://github.com/revivalstack/ai-chat-exporter
- Exports as Markdown with YAML frontmatter — perfect for the wiki
- Keyboard shortcuts: `Alt+M` (Markdown), `Alt+J` (JSON)
- **This is the recommended single tool** since it covers multiple platforms

### 3B. ChatGPT

**Method 1: Built-in export (all conversations at once)**
1. ChatGPT → Settings → Data Controls → Export Data
2. Receive ZIP via email with JSON files
3. Run conversion script (below)

**Method 2: CLI tool for incremental exports (recommended)**

```bash
npx chatgpt-exporter backup \
  --token "YOUR_SESSION_TOKEN" \
  --incremental \
  --download-files
```

Get your token from: `chatgpt.com/api/auth/session` (copy the `accessToken` value from browser DevTools → Network tab)

GitHub: https://github.com/FdezRomero/chatgpt-exporter

This produces markdown files per conversation, supports incremental backups, and downloads attachments.

**Method 3: Console script (one-click, all conversations)**

```bash
# Run in browser console at chatgpt.com:
# Paste contents of: https://gist.github.com/ocombe/1d7604bd29a91ceb716304ef8b5aa4b5
# Downloads a ZIP with JSON + Markdown + HTML
```

### 3C. Claude Code sessions

Claude Code stores sessions locally in `~/.claude/projects/` as JSONL files.

```bash
# Install the extractor
pipx install claude-conversation-extractor

# Export all sessions as markdown
claude-extract --all --format md --output ~/wiki/raw/conversations/claude-code/

# Export recent sessions
claude-extract --recent 10 --format md --output ~/wiki/raw/conversations/claude-code/
```

GitHub: https://github.com/ZeroSumQuant/claude-conversation-extractor

---

## Part 4 — The Conversion Script

This script converts the JSON exports from Claude.ai and ChatGPT into clean markdown files suitable for wiki ingestion.

### `scripts/convert-to-markdown.py`

```python
#!/usr/bin/env python3
"""Convert Claude.ai and ChatGPT JSON exports to markdown files."""

import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path


def sanitize_filename(name: str, max_len: int = 80) -> str:
    """Create a filesystem-safe filename from a conversation title."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', '-', name.strip())
    name = name[:max_len].rstrip('-')
    return name or 'untitled'


def convert_claude_export(zip_path: str, output_dir: str):
    """Convert Claude.ai data export (ZIP with JSON) to markdown."""
    import zipfile

    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as z:
        # Find the conversations JSON file
        json_files = [f for f in z.namelist() if f.endswith('.json')]
        
        for jf in json_files:
            with z.open(jf) as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    continue

            # Handle both list-of-conversations and single-conversation formats
            conversations = data if isinstance(data, list) else [data]

            for conv in conversations:
                if not isinstance(conv, dict):
                    continue
                
                title = conv.get('name', conv.get('title', 'Untitled'))
                created = conv.get('created_at', conv.get('create_time', ''))
                uuid = conv.get('uuid', conv.get('id', ''))
                
                # Parse date for filename prefix
                date_prefix = ''
                if created:
                    try:
                        dt = datetime.fromisoformat(created.replace('Z', '+00:00'))
                        date_prefix = dt.strftime('%Y-%m-%d')
                    except (ValueError, TypeError):
                        date_prefix = 'undated'

                safe_title = sanitize_filename(title)
                filename = f"{date_prefix}-{safe_title}.md"
                filepath = os.path.join(output_dir, filename)

                # Build markdown
                lines = [
                    '---',
                    f'title: "{title}"',
                    f'source: claude.ai',
                    f'type: conversation',
                    f'date: {created}',
                    f'id: {uuid}',
                    f'status: pending-ingest',
                    '---',
                    '',
                    f'# {title}',
                    '',
                ]

                # Extract messages - Claude export format
                messages = conv.get('chat_messages', conv.get('messages', []))
                for msg in messages:
                    if isinstance(msg, dict):
                        sender = msg.get('sender', msg.get('role', 'unknown'))
                        # Handle nested content
                        content = msg.get('text', '')
                        if not content:
                            content_list = msg.get('content', [])
                            if isinstance(content_list, list):
                                parts = []
                                for part in content_list:
                                    if isinstance(part, dict):
                                        parts.append(part.get('text', ''))
                                    elif isinstance(part, str):
                                        parts.append(part)
                                content = '\n'.join(parts)
                            elif isinstance(content_list, str):
                                content = content_list

                        ts = msg.get('created_at', '')
                        header = f"**{sender.title()}**"
                        if ts:
                            header += f" ({ts})"
                        
                        lines.append(f"## {header}")
                        lines.append('')
                        lines.append(content)
                        lines.append('')

                with open(filepath, 'w', encoding='utf-8') as out:
                    out.write('\n'.join(lines))
                
                print(f"  ✓ {filename}")


def convert_chatgpt_export(zip_path: str, output_dir: str):
    """Convert ChatGPT data export (ZIP with conversations.json) to markdown."""
    import zipfile

    os.makedirs(output_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as z:
        # ChatGPT exports have conversations.json at the root
        with z.open('conversations.json') as f:
            conversations = json.load(f)

    for conv in conversations:
        title = conv.get('title', 'Untitled')
        created = conv.get('create_time', 0)
        conv_id = conv.get('id', '')

        if isinstance(created, (int, float)) and created > 0:
            dt = datetime.fromtimestamp(created)
            date_prefix = dt.strftime('%Y-%m-%d')
            date_iso = dt.isoformat()
        else:
            date_prefix = 'undated'
            date_iso = ''

        safe_title = sanitize_filename(title)
        filename = f"{date_prefix}-{safe_title}.md"
        filepath = os.path.join(output_dir, filename)

        lines = [
            '---',
            f'title: "{title}"',
            f'source: chatgpt',
            f'type: conversation',
            f'date: {date_iso}',
            f'id: {conv_id}',
            f'model: {conv.get("default_model_slug", "unknown")}',
            f'status: pending-ingest',
            '---',
            '',
            f'# {title}',
            '',
        ]

        # ChatGPT uses a tree structure — walk the linear path
        mapping = conv.get('mapping', {})
        
        # Build the linear conversation by following parent->child
        ordered = []
        for node_id, node in mapping.items():
            msg = node.get('message')
            if msg and msg.get('content', {}).get('parts'):
                ordered.append(msg)
        
        # Sort by create_time
        ordered.sort(key=lambda m: m.get('create_time', 0) or 0)

        for msg in ordered:
            role = msg.get('author', {}).get('role', 'unknown')
            if role == 'system':
                continue
            
            parts = msg.get('content', {}).get('parts', [])
            content = '\n'.join(
                p if isinstance(p, str) else json.dumps(p) 
                for p in parts
            )
            
            if not content.strip():
                continue

            ts = msg.get('create_time', '')
            if isinstance(ts, (int, float)) and ts > 0:
                ts = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M')
            
            role_display = 'Human' if role == 'user' else 'Assistant'
            lines.append(f"## {role_display} ({ts})")
            lines.append('')
            lines.append(content)
            lines.append('')

        with open(filepath, 'w', encoding='utf-8') as out:
            out.write('\n'.join(lines))
        
        print(f"  ✓ {filename}")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print("Usage: convert-to-markdown.py <claude|chatgpt> <input.zip> <output_dir>")
        sys.exit(1)
    
    platform, input_path, output_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    
    if platform == 'claude':
        convert_claude_export(input_path, output_dir)
    elif platform == 'chatgpt':
        convert_chatgpt_export(input_path, output_dir)
    else:
        print(f"Unknown platform: {platform}")
        sys.exit(1)
```

---

## Part 5 — The Sync Script

### `scripts/sync-wiki.sh`

This is the master script you run periodically (or via cron) to pull in new conversations and trigger ingestion.

```bash
#!/bin/bash
set -euo pipefail

WIKI_DIR="$HOME/wiki"
SCRIPTS_DIR="$WIKI_DIR/scripts"
RAW_CONV="$WIKI_DIR/raw/conversations"

echo "=== Wiki Sync — $(date -Iseconds) ==="

# ── 1. Export Claude Code sessions ──
echo "→ Exporting Claude Code sessions..."
if command -v claude-extract &>/dev/null; then
    claude-extract --recent 20 --format md \
        --output "$RAW_CONV/claude-code/" 2>/dev/null || true
    echo "  Done."
else
    echo "  claude-conversation-extractor not installed. Skipping."
fi

# ── 2. Convert any new ZIP exports dropped in raw/ ──
echo "→ Checking for new ZIP exports..."
for zip in "$WIKI_DIR/raw/"*.zip; do
    [ -f "$zip" ] || continue
    basename=$(basename "$zip")
    
    if echo "$basename" | grep -qi "claude"; then
        echo "  Converting Claude export: $basename"
        python3 "$SCRIPTS_DIR/convert-to-markdown.py" claude "$zip" "$RAW_CONV/claude/"
        mv "$zip" "$WIKI_DIR/raw/.processed/"
    elif echo "$basename" | grep -qi "chatgpt\|openai"; then
        echo "  Converting ChatGPT export: $basename"
        python3 "$SCRIPTS_DIR/convert-to-markdown.py" chatgpt "$zip" "$RAW_CONV/chatgpt/"
        mv "$zip" "$WIKI_DIR/raw/.processed/"
    fi
done

# ── 3. List pending ingestions ──
echo ""
echo "→ Conversations pending ingestion:"
pending=$(grep -rl "status: pending-ingest" "$RAW_CONV/" 2>/dev/null | wc -l)
echo "  $pending files with status: pending-ingest"
echo ""

if [ "$pending" -gt 0 ]; then
    echo "  Files:"
    grep -rl "status: pending-ingest" "$RAW_CONV/" 2>/dev/null | \
        while read f; do echo "    - $(basename "$f")"; done
fi

# ── 4. Update QMD index (if installed) ──
if command -v qmd &>/dev/null; then
    echo ""
    echo "→ Updating QMD search index..."
    qmd update
    echo "  Done."
fi

# ── 5. Git commit ──
echo ""
echo "→ Committing changes..."
cd "$WIKI_DIR"
git add -A
if ! git diff --cached --quiet; then
    git commit -m "sync: $(date +%Y-%m-%d) — $pending new conversations"
    echo "  Committed."
else
    echo "  No changes."
fi

echo ""
echo "=== Sync complete ==="
echo ""
echo "Next step: Open Claude Code in ~/wiki and run:"
echo '  "Ingest all pending conversations in raw/conversations/"'
```

Make it executable and optionally add a cron job:

```bash
chmod +x ~/wiki/scripts/sync-wiki.sh

# Optional: run daily at 9am
crontab -e
# Add: 0 9 * * * /home/anton/wiki/scripts/sync-wiki.sh >> /home/anton/wiki/sync.log 2>&1
```

---

## Part 6 — Search with QMD (Karpathy's recommendation)

QMD gives your agents a proper search engine over the wiki via MCP.

### Install

```bash
npm install -g @tobilu/qmd
```

### Configure — `~/wiki/.qmd.yaml`

```yaml
collections:
  wiki:
    path: ./wiki
    mask: "**/*.md"
    context: "Personal knowledge base wiki pages — entities, concepts, projects, sources"
  conversations:
    path: ./raw/conversations
    mask: "**/*.md"
    context: "Raw conversation exports from Claude.ai, ChatGPT, and Claude Code"
  articles:
    path: ./raw/articles
    mask: "**/*.md"
    context: "Web clippings, articles, reports"
```

### Build the index

```bash
cd ~/wiki
qmd collection add ./wiki --name wiki
qmd collection add ./raw/conversations --name conversations
qmd collection add ./raw/articles --name articles

# Create embeddings (requires ~2GB VRAM for the default model)
qmd embed
```

### Start the MCP server

```bash
# As a background daemon
qmd mcp --http --daemon

# Verify
qmd status
```

### Connect to Claude Code

Add to `~/.claude/settings.json` (or your project's `.claude/settings.json`):

```json
{
  "mcpServers": {
    "qmd": {
      "type": "url",
      "url": "http://localhost:8181/mcp"
    }
  }
}
```

Now Claude Code can search your entire wiki and all your conversations.

### Connect to Codex / other agents

For agents that support MCP over HTTP, point them at `http://localhost:8181/mcp`.

For agents that support stdio MCP:

```json
{
  "mcpServers": {
    "qmd": {
      "command": "qmd",
      "args": ["mcp"]
    }
  }
}
```

---

## Part 7 — The Ingestion Workflow (What You Actually Do)

### One-time: Backfill old conversations

1. **Claude.ai**: Go to Settings → Privacy → Export Data. Download the ZIP when emailed. Drop it in `~/wiki/raw/`. Run `sync-wiki.sh`.

2. **ChatGPT**: Go to Settings → Data Controls → Export Data. Same process.

3. **Claude Code**: Run `claude-extract --all --format md --output ~/wiki/raw/conversations/claude-code/`

4. Open Claude Code in `~/wiki/`:
   ```
   cd ~/wiki && claude
   ```
   Then tell it:
   > "Ingest all pending conversations in raw/conversations/. For each, create a source summary, update relevant entity/concept/project pages, and update the index and log. Process them one at a time, starting with the most recent."

### Ongoing: New conversations

**Option A — Manual (recommended to start)**
- After an important Claude.ai or ChatGPT session, use the Tampermonkey script (`Alt+M`) to export as markdown
- Drop the file in `~/wiki/raw/conversations/claude/` or `chatgpt/`
- Run `sync-wiki.sh` or just open Claude Code and say "ingest the latest conversation"

**Option B — Semi-automated**
- Run `sync-wiki.sh` daily (cron or manually)
- Periodically do full exports from Claude.ai and ChatGPT (monthly)
- Claude Code sessions are auto-exported by the sync script

**Option C — Browser extension (most automated)**
- Install `revivalstack/ai-chat-exporter` Tampermonkey script
- Configure it to save to `~/wiki/raw/conversations/` (requires a helper that watches Downloads and moves files — see below)

### File watcher (for Option C)

```bash
# scripts/watch-downloads.sh
#!/bin/bash
# Watches Downloads folder for exported conversations and moves them

WATCH_DIR="$HOME/Downloads"
CLAUDE_DIR="$HOME/wiki/raw/conversations/claude"
CHATGPT_DIR="$HOME/wiki/raw/conversations/chatgpt"

inotifywait -m -e create "$WATCH_DIR" | while read -r dir event file; do
    if echo "$file" | grep -qi "claude.*\.md$"; then
        mv "$WATCH_DIR/$file" "$CLAUDE_DIR/"
        echo "Moved $file → claude/"
    elif echo "$file" | grep -qi "chat.*with.*chatgpt\|chatgpt.*\.md$"; then
        mv "$WATCH_DIR/$file" "$CHATGPT_DIR/"
        echo "Moved $file → chatgpt/"
    fi
done
```

```bash
# Install inotify-tools (Linux) or use fswatch (macOS):
# Linux: sudo apt install inotify-tools
# macOS: brew install fswatch
```

---

## Part 8 — Obsidian Setup (The Visual Layer)

Open `~/wiki` as an Obsidian vault. Configure:

1. **Settings → Files and links → Attachment folder path**: `raw/assets/`
2. **Settings → Files and links → New link format**: Shortest path
3. **Install plugins**:
   - **Dataview** — query frontmatter across pages
   - **Graph View** (built-in) — see connections
   - **Obsidian Web Clipper** — clip articles directly to `raw/articles/`
   - **Templater** — create templates matching your schema

4. **Dataview query for pending ingestions** (put in any note):
   ````
   ```dataview
   TABLE date, source
   FROM "raw/conversations"
   WHERE status = "pending-ingest"
   SORT date DESC
   ```
   ````

---

## Part 9 — Complete Checklist

### First-time setup (do once)

- [ ] Create `~/wiki/` directory structure (Part 1)
- [ ] `git init` the wiki
- [ ] Write `CLAUDE.md` and `AGENTS.md` (Part 2)
- [ ] Create `scripts/convert-to-markdown.py` (Part 4)
- [ ] Create `scripts/sync-wiki.sh` (Part 5)
- [ ] `chmod +x` both scripts
- [ ] Install `pipx install claude-conversation-extractor`
- [ ] Install `npm install -g @tobilu/qmd`
- [ ] Install the Tampermonkey script from `revivalstack/ai-chat-exporter`
- [ ] Open `~/wiki` as an Obsidian vault, install Dataview plugin
- [ ] Create initial `wiki/index.md`, `wiki/log.md`, `wiki/overview.md`

### Backfill (do once)

- [ ] Export all Claude.ai data (Settings → Privacy → Export Data)
- [ ] Export all ChatGPT data (Settings → Data Controls → Export Data)
- [ ] Export all Claude Code sessions (`claude-extract --all`)
- [ ] Run `sync-wiki.sh` to convert and prepare
- [ ] Open Claude Code in `~/wiki`, batch-ingest conversations

### Ongoing (regular habit)

- [ ] After important chats: `Alt+M` to export, drop in `raw/conversations/`
- [ ] Run `sync-wiki.sh` (daily or weekly)
- [ ] Monthly: full re-export from Claude.ai and ChatGPT
- [ ] Periodically: ask Claude Code to "lint the wiki"
- [ ] Commit and push: `cd ~/wiki && git add -A && git commit -m "update"`

---

## Key Design Decisions

**Why markdown, not a database?** Git-versioned markdown is agent-agnostic. Any LLM that can read files can work with this wiki. No vendor lock-in. Obsidian gives you the visual layer for free.

**Why QMD over embeddings-only RAG?** QMD combines BM25 keyword search with vector search and LLM re-ranking, all running locally. The MCP server means any agent can search your wiki natively. At wiki scale (hundreds of pages), the index.md approach Karpathy describes works fine too — QMD is for when you outgrow it.

**Why not fully automate ingestion?** Karpathy's key insight: the human should stay involved in ingestion, at least initially. You want to read the summaries, check the updates, and guide what to emphasize. Once you're comfortable with the LLM's judgment, you can automate more.

**Why separate raw/ from wiki/?** Raw sources are immutable truth. The wiki is the LLM's synthesis. If the LLM gets something wrong, you can always go back to the raw source. This separation is fundamental to the pattern.
