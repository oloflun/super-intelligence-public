#!/usr/bin/env bash
# scripts/hooks/chorus-session-end.sh
#
# Claude Code SessionEnd hook — fires when the CLI session terminates,
# whether via clean exit, crash, or window close.
#
# INSTALL: Add to ~/.claude/settings.json (global) or .claude/settings.json (project):
#
#   "hooks": {
#     "SessionEnd": [{
#       "hooks": [{
#         "type": "command",
#         "command": "bash /path/to/chorus-session-end.sh",
#         "timeout": 10
#       }]
#     }]
#   }
#
# PURPOSE: Call `chorus checkpoint --from claude` on session end so other
# agents always receive a lightweight state broadcast (branch, uncommitted
# count, last commit) even when an interactive `/conclude` was not run.
#
# SAFETY: The `.agent-chorus/` guard in `chorus checkpoint` means this is
# safe to install globally; it no-ops on projects without chorus wiring.

set -euo pipefail

# Killswitch guard, added here to match every other hook in this repo (see
# chorus-prompt.sh / chorus-heartbeat.sh) -- neither the agent-chorus-fork
# source nor the public fork's copy of this file had it.
if [ -n "${CLAUDE_HOOKS_DISABLED:-}" ] && [ "${CLAUDE_HOOKS_DISABLED}" != "0" ] && [ "${CLAUDE_HOOKS_DISABLED}" != "false" ]; then
  exit 0  # Fas 6 assistant-bench arm B: all hooks off
fi

# Canonicalize to prevent env-var-based path traversal. Fallback to cwd.
CWD="$(realpath "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || printf '%s' "$PWD")"

# Cheap early exit when there's nothing to do.
[ -d "$CWD/.agent-chorus" ] || exit 0

# Background so a hanging chorus process doesn't pin the CLI exit past the
# settings.json timeout. `disown` detaches from the parent's job table.
(
  cd "$CWD" || exit 0
  chorus checkpoint --from claude 2>/dev/null || true
) &
disown 2>/dev/null || true

exit 0
