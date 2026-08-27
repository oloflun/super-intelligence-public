# Auto-Export Pipeline Setup

Automatically exports AI conversations from browsers into your Obsidian vault.

## Architecture

```
Browser (Claude.ai / ChatGPT / Gemini)
    ↓ Tampermonkey auto-exports on navigation
Downloaded .md file
    ↓ watch-and-route-v2.sh (polling every 5s)
raw/conversations/{platform}/
    ↓ git commit (auto)
    ↓ /ingest (manual or scheduled by agent)
wiki/sources/ + entity/concept/project pages
```

## Setup

### 1. Install Tampermonkey

Install the Tampermonkey browser extension:
- Chrome: https://chrome.google.com/webstore/detail/tampermonkey/
- Firefox: https://addons.mozilla.org/en-US/firefox/addon/tampermonkey/

### 2. Install the Auto-Export Script

1. Open Tampermonkey dashboard
2. Create new script
3. Copy contents of `auto-wiki-ingest-v2.user.js`
4. Configure `DOWNLOAD_DIR` to your preferred location
5. Save

### 3. Install the File Watcher

```bash
# Make executable
chmod +x watch-and-route-v2.sh

# Configure paths in the script:
#   WATCH_DIR  -> where Tampermonkey downloads files
#   VAULT_RAW  -> vault/raw/conversations/

# Run (or set up as a service)
./watch-and-route-v2.sh
```

### 4. Configure Git Auto-Commit

The watcher auto-commits new files. Configure git in the vault:

```bash
cd {{VAULT_PATH}}
git config user.email "{{USER_EMAIL}}"
git config user.name "{{USER_NAME}}"
```

### 5. Test

1. Open a conversation in Claude.ai
2. Navigate to another page (triggers export)
3. Check that the .md file appears in `raw/conversations/claude/`
4. Run `/ingest` from any agent to convert it to wiki pages

## Troubleshooting

- **No files appearing:** Check Tampermonkey console for errors
- **Watcher not running:** Check process with `ps aux | grep watch-and-route`
- **Ingest failing:** Check `.wiki-ingest-ledger.json` for error entries
