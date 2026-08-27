#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  watch-and-route.sh  v2                                          ║
# ║                                                                  ║
# ║  Watches Downloads for auto-exported AI chat files and routes    ║
# ║  them to ~/wiki/raw/conversations/{platform}/.                   ║
# ║                                                                  ║
# ║  v2: Overwrites previous export of the same conversation         ║
# ║      by matching the `url:` field in YAML frontmatter.           ║
# ╚══════════════════════════════════════════════════════════════════╝

set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────
WATCH_DIR="${WATCH_DIR:-$HOME/Downloads}"
WIKI_DIR="${WIKI_DIR:-$HOME/wiki}"
CONV_DIR="$WIKI_DIR/raw/conversations"
LOG_FILE="$WIKI_DIR/scripts/watcher.log"

CLAUDE_DIR="$CONV_DIR/claude"
CHATGPT_DIR="$CONV_DIR/chatgpt"
GEMINI_DIR="$CONV_DIR/gemini"
COPILOT_DIR="$CONV_DIR/copilot"
GROK_DIR="$CONV_DIR/grok"
UNKNOWN_DIR="$CONV_DIR/other"

# ── Setup ──────────────────────────────────────────────────────────
for dir in "$CLAUDE_DIR" "$CHATGPT_DIR" "$GEMINI_DIR" "$COPILOT_DIR" "$GROK_DIR" "$UNKNOWN_DIR"; do
    mkdir -p "$dir"
done
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    local msg="[$(date -Iseconds)] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

# ── Detect platform from filename or frontmatter ──────────────────

detect_platform() {
    local filepath="$1"
    local filename
    filename=$(basename "$filepath")

    # Check filename prefix first (fast path)
    if [[ "$filename" =~ ^claude[_.-] ]]; then echo "claude"; return; fi
    if [[ "$filename" =~ ^chatgpt[_.-] ]]; then echo "chatgpt"; return; fi
    if [[ "$filename" =~ ^gemini[_.-] ]]; then echo "gemini"; return; fi
    if [[ "$filename" =~ ^copilot[_.-] ]]; then echo "copilot"; return; fi
    if [[ "$filename" =~ ^grok[_.-] ]]; then echo "grok"; return; fi

    # Fallback: check YAML frontmatter
    if [[ "$filename" =~ \.md$ ]]; then
        local author
        author=$(head -20 "$filepath" 2>/dev/null | grep -oP '(?<=author: )\S+' || true)
        case "$author" in
            claude)  echo "claude" ;;
            chatgpt) echo "chatgpt" ;;
            gemini)  echo "gemini" ;;
            copilot) echo "copilot" ;;
            grok)    echo "grok" ;;
            *)       echo "unknown" ;;
        esac
    else
        echo "unknown"
    fi
}

# ── Get conversation URL from YAML frontmatter ───────────────────

get_conversation_url() {
    local filepath="$1"
    # Extract the url: field from YAML frontmatter (first 30 lines)
    head -30 "$filepath" 2>/dev/null | grep -oP '(?<=url: )\S+' || true
}

# ── Find and remove previous export of same conversation ──────────

remove_previous_export() {
    local dest_dir="$1"
    local new_url="$2"
    local new_filename="$3"

    if [[ -z "$new_url" ]]; then
        return 0
    fi

    local removed=0

    # Search all .md files in the destination directory for matching URL
    for existing in "$dest_dir"/*.md; do
        [[ -f "$existing" ]] || continue

        # Don't compare with ourselves
        if [[ "$(basename "$existing")" == "$new_filename" ]]; then
            continue
        fi

        local existing_url
        existing_url=$(get_conversation_url "$existing")

        if [[ -n "$existing_url" && "$existing_url" == "$new_url" ]]; then
            log "  OVERWRITE: Removing old export $(basename "$existing")"
            log "             Same conversation URL: $new_url"
            rm -f "$existing"
            removed=$((removed + 1))
        fi
    done

    return 0
}

# ── Main routing function ─────────────────────────────────────────

route_file() {
    local filepath="$1"
    local filename
    filename=$(basename "$filepath")

    # Skip non-markdown/json files
    if [[ ! "$filename" =~ \.(md|json)$ ]]; then
        return
    fi

    # Skip partial downloads
    if [[ "$filename" =~ \.(crdownload|part|tmp)$ ]]; then
        return
    fi

    # Wait for the file to finish writing
    sleep 1

    # Verify file still exists
    if [[ ! -f "$filepath" ]]; then
        return
    fi

    # Detect platform
    local platform
    platform=$(detect_platform "$filepath")

    local dest_dir=""
    case "$platform" in
        claude)  dest_dir="$CLAUDE_DIR" ;;
        chatgpt) dest_dir="$CHATGPT_DIR" ;;
        gemini)  dest_dir="$GEMINI_DIR" ;;
        copilot) dest_dir="$COPILOT_DIR" ;;
        grok)    dest_dir="$GROK_DIR" ;;
        *)       dest_dir="$UNKNOWN_DIR" ;;
    esac

    # ── KEY CHANGE: Check for previous export of same conversation ──
    if [[ "$filename" =~ \.md$ ]]; then
        local conv_url
        conv_url=$(get_conversation_url "$filepath")

        if [[ -n "$conv_url" ]]; then
            remove_previous_export "$dest_dir" "$conv_url" "$filename"
        fi
    fi

    # Move the file
    mv -f "$filepath" "$dest_dir/$filename"
    log "ROUTED: $filename → $platform/"

    # Add pending-ingest status if missing
    if [[ "$filename" =~ \.md$ ]]; then
        if ! grep -q "status:" "$dest_dir/$filename" 2>/dev/null; then
            if head -1 "$dest_dir/$filename" | grep -q "^---$"; then
                # Insert status after the opening ---
                sed -i'' '2a\status: pending-ingest' "$dest_dir/$filename" 2>/dev/null || true
            fi
        else
            # If status exists, reset it to pending-ingest (conversation was updated)
            sed -i'' 's/^status: .*/status: pending-ingest/' "$dest_dir/$filename" 2>/dev/null || true
        fi
    fi

    # Auto-commit to git
    if [[ -d "$WIKI_DIR/.git" ]]; then
        (
            cd "$WIKI_DIR"
            git add -A
            if ! git diff --cached --quiet 2>/dev/null; then
                git commit -m "auto: ${platform} conversation $(echo "$filename" | sed 's/\.[^.]*$//')" --no-verify 2>/dev/null
            fi
        ) || true
    fi
}

# ── Detect OS ─────────────────────────────────────────────────────

detect_os() {
    case "$(uname -s)" in
        Linux*)  echo "linux" ;;
        Darwin*) echo "macos" ;;
        MINGW*|MSYS*|CYGWIN*) echo "windows" ;;
        *)       echo "unknown" ;;
    esac
}

OS=$(detect_os)

# ── Startup ───────────────────────────────────────────────────────

log "=== Watch & Route v2 starting ==="
log "OS: $OS | Watching: $WATCH_DIR | Wiki: $WIKI_DIR"

# Process any existing exports
for f in "$WATCH_DIR"/*.md "$WATCH_DIR"/*.json; do
    [[ -f "$f" ]] || continue
    fname=$(basename "$f")
    if [[ "$fname" =~ ^(claude|chatgpt|gemini|copilot|grok)[_.-] ]]; then
        route_file "$f"
    fi
done

# ── Watch loop ────────────────────────────────────────────────────

case "$OS" in
    linux)
        if ! command -v inotifywait &>/dev/null; then
            echo "ERROR: Install inotify-tools: sudo apt install inotify-tools"
            exit 1
        fi
        log "Watching with inotifywait..."
        inotifywait -m -e close_write -e moved_to --format '%w%f' "$WATCH_DIR" | \
        while read -r filepath; do
            route_file "$filepath"
        done
        ;;

    macos)
        if ! command -v fswatch &>/dev/null; then
            echo "ERROR: Install fswatch: brew install fswatch"
            exit 1
        fi
        log "Watching with fswatch..."
        fswatch -0 --event Created --event MovedTo "$WATCH_DIR" | \
        while IFS= read -r -d '' filepath; do
            route_file "$filepath"
        done
        ;;

    *)
        log "Watching with polling (5s interval)..."
        declare -A known_files
        for f in "$WATCH_DIR"/*.md "$WATCH_DIR"/*.json; do
            [[ -f "$f" ]] && known_files["$f"]=1
        done
        while true; do
            for f in "$WATCH_DIR"/*.md "$WATCH_DIR"/*.json; do
                [[ -f "$f" ]] || continue
                if [[ -z "${known_files[$f]+x}" ]]; then
                    known_files["$f"]=1
                    route_file "$f"
                fi
            done
            sleep 5
        done
        ;;
esac
