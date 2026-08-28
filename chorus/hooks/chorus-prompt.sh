#!/usr/bin/env bash
# UserPromptSubmit hook — capture the last prompt into this agent's presence.
set -euo pipefail

if [ -n "${CLAUDE_HOOKS_DISABLED:-}" ] && [ "${CLAUDE_HOOKS_DISABLED}" != "0" ] && [ "${CLAUDE_HOOKS_DISABLED}" != "false" ]; then
  exit 0  # Fas 6 assistant-bench arm B: all hooks off, incl. chorus presence capture
fi

VAULT="${CHORUS_VAULT:-$HOME/OneDrive/Dokument/Obsidian/Knowledge Base}"
FORK="${CHORUS_FORK:-$HOME/agent-chorus-fork}"

CHORUS_AGENT_NAME="claude" \
CHORUS_PROJECT_ROOT="$VAULT" \
CHORUS_WORKSPACE="${CLAUDE_PROJECT_DIR:-$PWD}" \
node "$FORK/scripts/local/capture-prompt.mjs" >/dev/null 2>&1 || true

# Surface any un-notified cross-user messages as additionalContext (prints JSON
# on stdout, empty when there's nothing new). Failures must never block a prompt.
CHORUS_PROJECT_ROOT="$VAULT" \
node "$FORK/scripts/local/remote-notify.mjs" 2>/dev/null || true

exit 0
