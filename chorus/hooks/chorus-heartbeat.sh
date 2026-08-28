#!/usr/bin/env bash
# Heartbeat/presence hook wrapper for SessionStart and Stop.
set -euo pipefail

if [ -n "${CLAUDE_HOOKS_DISABLED:-}" ] && [ "${CLAUDE_HOOKS_DISABLED}" != "0" ] && [ "${CLAUDE_HOOKS_DISABLED}" != "false" ]; then
  exit 0  # Fas 6 assistant-bench arm B: all hooks off
fi

VAULT="${CHORUS_VAULT:-$HOME/OneDrive/Dokument/Obsidian/Knowledge Base}"
FORK="${CHORUS_FORK:-$HOME/agent-chorus-fork}"

CHORUS_AGENT_NAME="claude" \
CHORUS_PROJECT_ROOT="$VAULT" \
CHORUS_WORKSPACE="${CLAUDE_PROJECT_DIR:-$PWD}" \
node "$FORK/scripts/local/heartbeat.mjs" "${1:-working}" >/dev/null 2>&1 || true

exit 0
