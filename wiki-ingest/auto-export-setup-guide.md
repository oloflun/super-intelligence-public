---
title: "Auto export setup guide"
type: note
category: [AI-agents, Dev-tools]
---

# Auto-Export Pipeline — Setup Guide

## What This Does

Every time you finish a conversation on Claude.ai, ChatGPT, Gemini, Copilot, or Grok and navigate away (click another chat, close the tab, or go to a new conversation), it:

1. **Auto-exports** the conversation as a Markdown file (via the RevivalStack exporter)
2. **Auto-routes** the downloaded file to `~/wiki/raw/conversations/{platform}/`
3. **Auto-commits** to git
4. Marks the file as `status: pending-ingest` so Claude Code knows what to process

No manual clicking. No remembering to export. Every conversation flows into your wiki.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│  Browser (Claude.ai / ChatGPT / Gemini / etc.)       │
│                                                      │
│  ┌─────────────────────┐  ┌────────────────────────┐ │
│  │ RevivalStack Exporter│  │ Auto Wiki Ingest       │ │
│  │ (Tampermonkey)       │  │ (Tampermonkey)         │ │
│  │                      │  │                        │ │
│  │ DOM → Markdown       │  │ Detects navigation     │ │
│  │ Turndown.js          │  │ Clicks "Export MD" btn  │ │
│  │ downloadFile()       │◄─┤ Tracks export history  │ │
│  └──────────┬───────────┘  └────────────────────────┘ │
│             │ .md file downloaded                     │
└─────────────┼────────────────────────────────────────┘
              ▼
    ~/Downloads/claude_my-chat_2026-04-06T14-30-00.md
              │
              ▼
┌─────────────────────────────────────────────────────┐
│  watch-and-route.sh (background daemon)              │
│                                                      │
│  • Watches ~/Downloads for new .md/.json files       │
│  • Routes by platform prefix (claude_ → claude/)     │
│  • Injects status: pending-ingest                    │
│  • Auto-commits to git                               │
└──────────────┬──────────────────────────────────────┘
               ▼
    ~/wiki/raw/conversations/claude/claude_my-chat_....md
               │
               ▼  (you run Claude Code in ~/wiki)
┌─────────────────────────────────────────────────────┐
│  Claude Code / Codex / any agent                     │
│                                                      │
│  "Ingest all pending conversations"                  │
│  • Reads CLAUDE.md schema                            │
│  • Creates wiki/sources/ summary pages               │
│  • Updates entities, concepts, projects              │
│  • Updates index.md and log.md                       │
└─────────────────────────────────────────────────────┘
```

---

## Step-by-Step Setup

### 1. Install Tampermonkey

Install [Tampermonkey](https://www.tampermonkey.net/) for your browser (Chrome, Firefox, or Edge).

### 2. Install RevivalStack AI Chat Exporter

Install from Greasy Fork (the original script — this is the engine):

**https://greasyfork.org/en/scripts/541051**

Or install directly:
**https://raw.githubusercontent.com/revivalstack/chatgpt-exporter/refs/heads/main/ai-chat-exporter.user.js**

After installing, configure the **filename format** by clicking the ⚙️ button on any AI chat page. Set it to:

```
{platform}_{title}_{timestampLocal}
```

This prefix is how the watcher script knows which platform the export came from.

### 3. Install Auto Wiki Ingest (companion script)

In Tampermonkey:
1. Click the Tampermonkey icon → "Create a new script"
2. Delete the template content
3. Paste the entire contents of **`auto-wiki-ingest.user.js`** (provided)
4. Save (Ctrl+S)

### 4. Configure your browser for silent downloads

The auto-export triggers a file download. To avoid the "Save As" dialog every time:

**Chrome/Edge:**
- Settings → Downloads
- Turn OFF "Ask where to save each file before downloading"
- Set default location to `~/Downloads` (or wherever you prefer)

**Firefox:**
- Settings → General → Files and Applications
- Select "Save files to" and pick your Downloads folder

### 5. Set up the file watcher

Copy `watch-and-route.sh` to your wiki:

```bash
cp watch-and-route.sh ~/wiki/scripts/
chmod +x ~/wiki/scripts/watch-and-route.sh
```

**Linux** — install inotify-tools:
```bash
sudo apt install inotify-tools
```

**macOS** — install fswatch:
```bash
brew install fswatch
```

**Windows (Git Bash / WSL)** — no extra install needed (uses polling).

### 6. Run the watcher as a background service

#### Option A: Quick start (foreground)

```bash
~/wiki/scripts/watch-and-route.sh
```

#### Option B: Linux systemd service (persistent)

```bash
mkdir -p ~/.config/systemd/user/

cat > ~/.config/systemd/user/wiki-watcher.service << 'EOF'
[Unit]
Description=Wiki Auto-Ingest File Watcher
After=network.target

[Service]
Type=simple
ExecStart=%h/wiki/scripts/watch-and-route.sh
Restart=on-failure
RestartSec=5
Environment=WATCH_DIR=%h/Downloads
Environment=WIKI_DIR=%h/wiki

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable wiki-watcher
systemctl --user start wiki-watcher
systemctl --user status wiki-watcher
```

#### Option C: macOS launchd (persistent)

```bash
cat > ~/Library/LaunchAgents/com.wiki.watcher.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wiki.watcher</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>${HOME}/wiki/scripts/watch-and-route.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>WATCH_DIR</key>
        <string>${HOME}/Downloads</string>
        <key>WIKI_DIR</key>
        <string>${HOME}/wiki</string>
    </dict>
    <key>StandardOutPath</key>
    <string>${HOME}/wiki/scripts/watcher.log</string>
    <key>StandardErrorPath</key>
    <string>${HOME}/wiki/scripts/watcher.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.wiki.watcher.plist
```

#### Option D: Windows (Task Scheduler or startup script)

Add to your startup folder or create a scheduled task that runs:
```
bash.exe -c "$HOME/wiki/scripts/watch-and-route.sh"
```

### 7. Verify the pipeline

1. Open Claude.ai and have a short conversation
2. Navigate to a different chat (click another conversation in the sidebar)
3. Check `~/Downloads` — a `.md` file should appear briefly
4. Check `~/wiki/raw/conversations/claude/` — the file should be there
5. Check `~/wiki/scripts/watcher.log` for routing confirmation

---

## Controls & Shortcuts

| Action | How |
|--------|-----|
| Force export current chat | `Alt+Shift+E` |
| Toggle auto-export on/off | Click the 📚 indicator (bottom-right) |
| Manual export (RevivalStack) | `Alt+M` (Markdown) or `Alt+J` (JSON) |
| Check watcher status (Linux) | `systemctl --user status wiki-watcher` |
| View watcher log | `tail -f ~/wiki/scripts/watcher.log` |

---

## Tuning

In the companion script's `CONFIG` object:

- **`MIN_USER_MESSAGES: 1`** — Increase to 2 or 3 to skip trivial chats
- **`SETTLE_DELAY_MS: 2000`** — Increase if exports trigger mid-conversation
- **`SHOW_NOTIFICATIONS: true`** — Set to false to disable desktop notifications
- **`DEBUG: false`** — Set to true to see detailed console logs

---

## FAQ

**Q: What if I update/continue a conversation after it was exported?**
A: The companion script tracks exported URLs. Same URL won't re-export automatically. Use `Alt+Shift+E` to force a re-export, which will create a new file (the watcher won't overwrite existing files with the same name — the timestamp in the filename ensures uniqueness).

**Q: Does this work on mobile?**
A: No. Tampermonkey and file watchers are desktop-only. For mobile conversations, use the periodic bulk export approach (Settings → Export Data) from the first guide.

**Q: What about Claude Code sessions?**
A: Claude Code sessions are stored locally in `~/.claude/projects/`. Use `claude-conversation-extractor` for those — the sync script from the first guide handles it.

**Q: Can I change where files are routed?**
A: Edit the directory variables at the top of `watch-and-route.sh`.
