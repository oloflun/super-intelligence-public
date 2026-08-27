#!/usr/bin/env bash
# Super-Intelligence Stack — Daily Auto-Update + Health Check
# Called by systemd timer / launchd / crontab / Task Scheduler.
# Idempotent. Read-only health checks run even when no update is pulled.
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_DIR="$HOME/.super-intelligence"
CONFIG_FILE="$CONFIG_DIR/config.json"

# If config missing, nothing to do (install not complete)
if [ ! -f "$CONFIG_FILE" ]; then exit 0; fi

# ── JSON helpers (jq preferred, fallback to grep) ─────────────────────────────
_jq() {
  if command -v jq &>/dev/null; then
    jq -r "$1" "$CONFIG_FILE" 2>/dev/null || echo ""
  else
    # Minimal grep-based JSON extraction (ponytail: jq is better, this is fallback)
    local key="${1#.}"
    grep -oP "\"${key}\"\s*:\s*\K(true|false|\"[^\"]*\"|null|[0-9]+)" "$CONFIG_FILE" 2>/dev/null \
      | head -1 | sed 's/^"//;s/"$//' || echo ""
  fi
}

AUTO_UPDATE=$(_jq ".auto_update")
REPO_PATH=$(_jq ".repo_path")
VAULT_PATH=$(_jq ".vault_path")
LOG_FILE=$(_jq ".update_log")
OWNER_MODE=$(_jq ".owner_mode")

# Defaults if .super-intelligence is missing (before first installer run)
LOG_FILE="${LOG_FILE:-$CONFIG_DIR/update.log}"
AUTO_UPDATE="${AUTO_UPDATE:-true}"

mkdir -p "$CONFIG_DIR"
touch "$LOG_FILE"

# ── Colors ────────────────────────────────────────────────────────────────────
_R='\033[0m' _G='\033[32m' _R2='\033[31m' _Y='\033[33m' _C='\033[36m' _B='\033[1m'

_log()  { echo -e "[$(date -Iseconds)] $1" >> "$LOG_FILE"; }
_ok()   { echo -e "${_G}[ok]${_R} $1"; }
_fail() { echo -e "${_R2}[XX]${_R} $1"; }
_warn() { echo -e "${_Y}[WARN]${_R} $1"; }
_info() { echo -e "${_C}[INFO]${_R} $1"; }

# ── Terminal report ───────────────────────────────────────────────────────────
HEALTH_PASS=0 HEALTH_FAIL=0 HEALTH_WARN=0
_health_ok()   { HEALTH_PASS=$((HEALTH_PASS + 1)); _ok "$1"; }
_health_fail() { HEALTH_FAIL=$((HEALTH_FAIL + 1)); _fail "$1"; }
_health_warn() { HEALTH_WARN=$((HEALTH_WARN + 1)); _warn "$1"; }

# ── Counters (defaults) ──────────────────────────────────────────────────────
PKG_PASS=0 PKG_FAIL=0 INST_PASS=0 INST_FAIL=0
MCP_OK=0 MCP_FAIL=0 MCP_TOTAL=0
DOMAIN_COUNT=0 RULE_COUNT=0 DEC_COUNT=0 ACTIVE_COUNT=0
CARL_JSON_PATH=""
if [ "$AUTO_UPDATE" != "true" ]; then
  _log "auto_update disabled — skipping git fetch, running health check only"
  SKIP_FETCH=true
else
  SKIP_FETCH=false
fi

# ── Validate repo path ────────────────────────────────────────────────────────
if [ -z "$REPO_PATH" ] || [ ! -d "$REPO_PATH/.git" ]; then
  _log "ERROR: repo_path missing or not a git repo: ${REPO_PATH:-unset}"
  echo -e "${_R2}ERROR: repo_path not configured or not a git repo${_R}"
  echo "Check ${CONFIG_FILE} — set repo_path to the super-intelligence clone"
  exit 1
fi

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1: UPDATE CHECK
# ══════════════════════════════════════════════════════════════════════════════
echo ""
DID_UPDATE=false

if [ "$SKIP_FETCH" = false ]; then
  echo -e "${_B}── Fetching updates ──${_R}"
  cd "$REPO_PATH"

  git fetch origin 2>> "$LOG_FILE" || { _log "git fetch failed"; _warn "git fetch failed — network issue?"; }

  LOCAL=$(git rev-parse HEAD 2>/dev/null || echo "")
  REMOTE=$(git rev-parse origin/main 2>/dev/null || echo "")

  if [ -z "$LOCAL" ] || [ -z "$REMOTE" ]; then
    _warn "Could not determine git SHAs — skipping pull"
    _log "WARN: LOCAL=$LOCAL REMOTE=$REMOTE"
  elif [ "$LOCAL" = "$REMOTE" ]; then
    _ok "Already up to date ($(git log -1 --format=%h 2>/dev/null))"
    _log "INFO: up to date"
  else
    echo -e "${_C}Pulling ${LOCAL:0:7} → ${REMOTE:0:7}${_R}"
    _log "UPDATE: $LOCAL → $REMOTE"

    if git pull --ff-only origin main 2>> "$LOG_FILE"; then
      _ok "git pull succeeded"
      DID_UPDATE=true
    else
      _fail "git pull failed — local diverged from origin/main. Manual intervention needed."
      _log "ERROR: git pull --ff-only failed"
    fi

    # Run upgrade
    if [ "$DID_UPDATE" = true ] && [ -f "upgrade.mjs" ] && command -v node &>/dev/null; then
      echo ""
      echo -e "${_B}── Running upgrade.mjs ──${_R}"
      node upgrade.mjs 2>> "$LOG_FILE" && _ok "upgrade.mjs completed" || _warn "upgrade.mjs had issues (check log)"
      _log "upgrade.mjs executed"
    fi
  fi
else
  _info "auto_update disabled — skipping git fetch/pull"
fi

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2: HEALTH CHECKS
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${_B}── Health Checks ──${_R}"

# ── 2.1 Package Health ───────────────────────────────────────────────────────
echo ""
echo -e "${_B}Package:${_R}"
if [ -f "$REPO_PATH/scripts/health-check.mjs" ] && command -v node &>/dev/null; then
  OUT=$(node "$REPO_PATH/scripts/health-check.mjs" 2>&1) || true
  # Count pass/fail from output
  PKG_PASS=$(echo "$OUT" | grep -c "\[ok\]" || true)
  PKG_FAIL=$(echo "$OUT" | grep -c "\[XX\]" || true)
  if [ "$PKG_FAIL" -eq 0 ]; then
    _health_ok "health-check.mjs: ${PKG_PASS}/${PKG_PASS} passed"
  else
    _health_fail "health-check.mjs: ${PKG_PASS} passed, ${PKG_FAIL} failed"
  fi
else
  _health_warn "health-check.mjs not available (no node or missing script)"
fi

# ── 2.2 Installation Health ──────────────────────────────────────────────────
echo ""
echo -e "${_B}Installation:${_R}"
if [ -f "$REPO_PATH/scripts/verify-install.mjs" ] && command -v node &>/dev/null; then
  OUT=$(node "$REPO_PATH/scripts/verify-install.mjs" 2>&1) || true
  INST_PASS=$(echo "$OUT" | grep -c "\[ok\]" || true)
  INST_FAIL=$(echo "$OUT" | grep -c "\[XX\]" || true)
  if [ "$INST_FAIL" -eq 0 ]; then
    _health_ok "verify-install.mjs: ${INST_PASS}/${INST_PASS} passed"
  else
    _health_fail "verify-install.mjs: ${INST_PASS} passed, ${INST_FAIL} failed"
  fi
else
  _health_warn "verify-install.mjs not available"
fi

# ── 2.3 MCP Health ───────────────────────────────────────────────────────────
echo ""
echo -e "${_B}MCP Servers:${_R}"
MCP_JSON="$HOME/.mcp.json"

if [ -f "$MCP_JSON" ]; then
  # Parse server names and commands
  if command -v jq &>/dev/null; then
    MCP_SERVERS=$(jq -r '.mcpServers // {} | to_entries[] | "\(.key)\t\(.value.command // "")"' "$MCP_JSON" 2>/dev/null || echo "")
    if [ -n "$MCP_SERVERS" ]; then
      while IFS=$'\t' read -r name cmd; do
        MCP_TOTAL=$((MCP_TOTAL + 1))
        if [ -z "$cmd" ] || [ "$cmd" = "null" ]; then
          _health_warn "${name}: no command configured"
        elif command -v "$cmd" &>/dev/null || command -v "$(basename "$cmd")" &>/dev/null; then
          _health_ok "${name}: $(basename "$cmd")"
          MCP_OK=$((MCP_OK + 1))
        elif [ -f "$cmd" ] && [ -x "$cmd" ]; then
          _health_ok "${name}: ${cmd}"
          MCP_OK=$((MCP_OK + 1))
        else
          _health_fail "${name}: command not found — ${cmd}"
          MCP_FAIL=$((MCP_FAIL + 1))
        fi
      done <<< "$MCP_SERVERS"
    fi
  else
    # Fallback: grep for server names (ponytail: jq is better, this counts servers at least)
    MCP_COUNT=$(grep -c '"command"' "$MCP_JSON" 2>/dev/null || echo "0")
    MCP_TOTAL=$MCP_COUNT
    MCP_OK=$MCP_COUNT
    _health_ok "${MCP_COUNT} server(s) configured (install jq for deep MCP check)"
  fi
fi

if [ "$MCP_TOTAL" -eq 0 ]; then
  _health_warn "No MCP servers configured in ~/.mcp.json"
else
  echo -e "  ${MCP_OK} OK, ${MCP_FAIL} failed out of ${MCP_TOTAL} total"
fi

# ── 2.4 CARL Deep Health ─────────────────────────────────────────────────────
echo ""
echo -e "${_B}CARL:${_R}"
CARL_JSON_PATH=""
for cand in "$HOME/.carl/carl.json" "$VAULT_PATH/.carl/carl.json"; do
  if [ -f "$cand" ]; then CARL_JSON_PATH="$cand"; break; fi
done

if [ -z "$CARL_JSON_PATH" ]; then
  _health_fail "carl.json not found at ~/.carl/ or vault .carl/"
else
  if command -v jq &>/dev/null; then
    # Validate structure
    HAS_VER=$(jq -r '.version // "missing"' "$CARL_JSON_PATH" 2>/dev/null || echo "error")
    HAS_CFG=$(jq -r '.config // "missing"' "$CARL_JSON_PATH" 2>/dev/null || echo "error")
    DOMAIN_COUNT=$(jq -r '.domains | length // 0' "$CARL_JSON_PATH" 2>/dev/null || echo "0")
    RULE_COUNT=$(jq -r '[.domains[].rules | length] | add // 0' "$CARL_JSON_PATH" 2>/dev/null || echo "0")
    DEC_COUNT=$(jq -r '[.domains[].decisions | length] | add // 0' "$CARL_JSON_PATH" 2>/dev/null || echo "0")
    ACTIVE_COUNT=$(jq -r '[.domains[] | select(.state == "active")] | length' "$CARL_JSON_PATH" 2>/dev/null || echo "0")

    if [ "$HAS_VER" != "missing" ] && [ "$HAS_CFG" != "missing" ] && [ "$DOMAIN_COUNT" -gt 0 ]; then
      _health_ok "carl.json valid: ${DOMAIN_COUNT} domains, ${RULE_COUNT} rules, ${DEC_COUNT} decisions (${ACTIVE_COUNT} active)"

      # Domain summary
      if [ "$DOMAIN_COUNT" -gt 0 ]; then
        jq -r '.domains | to_entries[] | "  \(.key): \(.value.rules | length) rules, state=\(.value.state // "unknown")"' "$CARL_JSON_PATH" 2>/dev/null | while read -r line; do
          echo -e "    ${_C}${line}${_R}"
        done
      fi

      # Check for domains missing rules array
      BAD=$(jq -r '.domains | to_entries[] | select(.value.rules == null or (.value.rules | type) != "array") | .key' "$CARL_JSON_PATH" 2>/dev/null || echo "")
      if [ -n "$BAD" ]; then
        _health_fail "Domains missing rules array: $BAD"
      fi
    else
      _health_fail "carl.json invalid or empty: ver=$HAS_VER cfg=$HAS_CFG domains=$DOMAIN_COUNT"
    fi
  else
    # Fallback: basic check without jq
    if [ -f "$CARL_JSON_PATH" ]; then
      DOMAIN_COUNT=$(grep -c '"state"' "$CARL_JSON_PATH" 2>/dev/null || echo "0")
      _health_ok "carl.json present: ~${DOMAIN_COUNT} domains (install jq for deep CARL check)"
    else
      _health_fail "carl.json missing"
    fi
  fi
fi

# Hook version
CARL_HOOK="$HOME/.claude/hooks/carl-hook.py"
if [ -f "$CARL_HOOK" ]; then
  HOOK_VER=$(grep -oP 'CARL_HOOK_VERSION=\K[\d.]+' "$CARL_HOOK" 2>/dev/null || echo "unknown")
  _health_ok "carl-hook.py v${HOOK_VER}"
else
  _health_fail "carl-hook.py missing at ~/.claude/hooks/"
fi

# Hook wiring
SETTINGS="$HOME/.claude/settings.json"
if [ -f "$SETTINGS" ]; then
  if grep -q "carl-hook.py" "$SETTINGS" 2>/dev/null; then
    _health_ok "carl-hook.py wired in settings.json"
  else
    _health_fail "carl-hook.py NOT wired in settings.json"
  fi
else
  _health_warn "~/.claude/settings.json not found"
fi

# ── 2.5 Repos Health ─────────────────────────────────────────────────────────
echo ""
echo -e "${_B}Repos:${_R}"
for repo in "$REPO_PATH"; do
  name=$(basename "$repo")
  if [ -d "$repo/.git" ]; then
    cd "$repo"
    DIRTY=$(git status --porcelain 2>/dev/null | wc -l || echo "0")
    BEHIND=$(git rev-list --count HEAD..origin/main 2>/dev/null || echo "0")
    AHEAD=$(git rev-list --count origin/main..HEAD 2>/dev/null || echo "0")
    BRANCH=$(git branch --show-current 2>/dev/null || echo "?")
    COMMIT=$(git log -1 --format=%h 2>/dev/null || echo "????")

    STATUS=""
    [ "$DIRTY" -gt 0 ] && STATUS="${_Y}${DIRTY} dirty files${_R} " && HEALTH_WARN=$((HEALTH_WARN + 1))
    [ "$BEHIND" -gt 0 ] && STATUS="${STATUS}${_Y}${BEHIND} behind${_R} " && HEALTH_WARN=$((HEALTH_WARN + 1))
    [ "$AHEAD" -gt 0 ] && STATUS="${STATUS}${_Y}${AHEAD} ahead${_R} " && HEALTH_WARN=$((HEALTH_WARN + 1))
    [ -z "$STATUS" ] && STATUS="${_G}clean${_R}" && HEALTH_PASS=$((HEALTH_PASS + 1))

    echo -e "  ${_B}${name}${_R} ${COMMIT} (${BRANCH}): ${STATUS}"
  else
    _health_warn "${name}: not a git repo"
  fi
done

# ══════════════════════════════════════════════════════════════════════════════
# TERMINAL REPORT
# ══════════════════════════════════════════════════════════════════════════════
echo ""
echo -e "${_B}╔══════════════════════════════════════════╗${_R}"
echo -e "${_B}║${_R}  Super-Intelligence Daily Health        ${_B}║${_R}"
printf "${_B}║${_R}  %-38s ${_B}║${_R}\n" "$(date '+%Y-%m-%d %H:%M')"
echo -e "${_B}╠══════════════════════════════════════════╣${_R}"

# Package line
if [ "${PKG_FAIL:-0}" -eq 0 ]; then
  printf "${_B}║${_R}  Package:    ${_G}✓${_R} ${PKG_PASS:-?}/${PKG_PASS:-?} passed %$((24 - ${#PKG_PASS}*2))s${_B}║${_R}\n" ""
else
  printf "${_B}║${_R}  Package:    ${_R2}✗${_R} ${PKG_PASS:-0} ok, ${PKG_FAIL:-0} fail %$((20 - ${#PKG_PASS} - ${#PKG_FAIL}))s${_B}║${_R}\n" ""
fi

# Install line
if [ "${INST_FAIL:-0}" -eq 0 ]; then
  printf "${_B}║${_R}  Install:    ${_G}✓${_R} ${INST_PASS:-?}/${INST_PASS:-?} passed %$((24 - ${#INST_PASS}*2))s${_B}║${_R}\n" ""
else
  printf "${_B}║${_R}  Install:    ${_R2}✗${_R} ${INST_PASS:-0} ok, ${INST_FAIL:-0} fail %$((20 - ${#INST_PASS} - ${#INST_FAIL}))s${_B}║${_R}\n" ""
fi

# MCP line
if [ "$MCP_FAIL" -eq 0 ] && [ "$MCP_TOTAL" -gt 0 ]; then
  printf "${_B}║${_R}  MCP:        ${_G}✓${_R} ${MCP_OK}/${MCP_TOTAL} servers ok %$((20 - ${#MCP_OK} - ${#MCP_TOTAL}))s${_B}║${_R}\n" ""
elif [ "$MCP_TOTAL" -eq 0 ]; then
  echo -e "${_B}║${_R}  MCP:        ${_Y}─${_R} none configured              ${_B}║${_R}"
else
  printf "${_B}║${_R}  MCP:        ${_R2}✗${_R} ${MCP_FAIL}/${MCP_TOTAL} failed %$((20 - ${#MCP_FAIL} - ${#MCP_TOTAL}))s${_B}║${_R}\n" ""
fi

# CARL line
if [ "${CARL_JSON_PATH:-}" != "" ] && [ "${DOMAIN_COUNT:-0}" -gt 0 ]; then
  printf "${_B}║${_R}  CARL:       ${_G}✓${_R} ${DOMAIN_COUNT:-?} domains, ${RULE_COUNT:-?} rules %$((14 - ${#DOMAIN_COUNT} - ${#RULE_COUNT}))s${_B}║${_R}\n" ""
else
  echo -e "${_B}║${_R}  CARL:       ${_R2}✗${_R} missing or invalid          ${_B}║${_R}"
fi

# Repos line
echo -e "${_B}╠══════════════════════════════════════════╣${_R}"

# Verdict
TOTAL_FAIL=$HEALTH_FAIL
[ "$PKG_FAIL" -gt 0 ] && TOTAL_FAIL=$((TOTAL_FAIL + 1))
[ "$INST_FAIL" -gt 0 ] && TOTAL_FAIL=$((TOTAL_FAIL + 1))
[ "$MCP_FAIL" -gt 0 ] && TOTAL_FAIL=$((TOTAL_FAIL + 1))
TOTAL_WARN=$HEALTH_WARN
if [ "$TOTAL_FAIL" -eq 0 ] && [ "$TOTAL_WARN" -eq 0 ]; then
  echo -e "${_B}║${_R}  VERDICT: ${_G}ALL CLEAN${_R}                      ${_B}║${_R}"
elif [ "$TOTAL_FAIL" -eq 0 ]; then
  echo -e "${_B}║${_R}  VERDICT: ${_Y}${TOTAL_WARN} WARNING(S)${_R}                 ${_B}║${_R}"
else
  echo -e "${_B}║${_R}  VERDICT: ${_R2}${TOTAL_FAIL} FAIL${_R}, ${_Y}${TOTAL_WARN} WARN${_R}               ${_B}║${_R}"
  echo -e "${_B}║${_R}  Fix: run \`node install.mjs --force\`     ${_B}║${_R}"
fi
echo -e "${_B}╚══════════════════════════════════════════╝${_R}"
echo ""

# ── Update last_check in config ───────────────────────────────────────────────
if command -v jq &>/dev/null; then
  NOW=$(date -Iseconds)
  jq --arg ts "$NOW" '.last_check = $ts' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" 2>/dev/null && \
    mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE" || true
fi

_log "auto-update complete: $TOTAL_FAIL failures, $TOTAL_WARN warnings"
