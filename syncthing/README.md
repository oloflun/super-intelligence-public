# Syncthing Configuration

Syncthing bridges the Windows Obsidian vault with the WSL `~/vault-local/` directory, enabling Hermes (Linux agent) to share the same files as Windows agents.

## Installation

### Windows
```powershell
winget install Syncthing.Syncthing
```

### WSL/Linux
```bash
sudo apt install syncthing
# or
curl -s https://syncthing.net/release-key.txt | sudo apt-key add -
echo "deb https://apt.syncthing.net/ syncthing stable" | sudo tee /etc/apt/sources.list.d/syncthing.list
sudo apt update && sudo apt install syncthing
```

## Folder Setup

### 1. Share the vault folder

In Syncthing Web UI (http://localhost:8384):

**Windows side:**
- Add Folder: `C:\Users\<user>\OneDrive\Obsidian\Knowledge Base`
- Folder ID: `knowledge-base`
- Share with: WSL device

**WSL side:**
- Add Folder: `~/vault-local`
- Folder ID: `knowledge-base` (same as Windows)
- Share with: Windows device

### 2. Configure .stignore

Create `.stignore` in the vault root:

```
# Syncthing internals
.stfolder
.stversions
.syncthing*

# Node/Obsidian
node_modules
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/cache

# Git internals
.git/objects
.git/index
.git/logs

# Temp files
*.tmp
.cache
.tmp

# Build artifacts
.next
dist
build
out

# Session state (per-agent, don't sync)
.carl/sessions/*
!.carl/sessions/.gitkeep

# Desktop configs (per-machine)
.claude/settings.json
.claude/.credentials.json
.codex/auth.json
```

### 3. Start Syncthing

**Windows:**
```cmd
syncthing-boot.cmd
```
Or configure as a Windows service for auto-start.

**WSL:**
```bash
syncthing serve --no-browser &
```
Or configure systemd service.

### 4. Verify sync

Check Syncthing Web UI that both sides show "Up to Date" and the folder is syncing.

## Safety Rules

1. **Never delete from either side** — deletions propagate bidirectionally
2. **Wait for sync before switching agents** — let Syncthing finish before Hermes reads Windows-agent writes
3. **Check `.stignore`** — make sure personal configs aren't synced
4. **Backup before large operations** — the vault backup script protects against sync incidents
