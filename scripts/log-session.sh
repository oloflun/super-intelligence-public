#!/usr/bin/env bash
set -euo pipefail

session_log="${1:-}"
if [ -z "$session_log" ]; then
  echo "Usage: log-session.sh <session_log>"
  exit 1
fi

if [ ! -f "$session_log" ]; then
  echo "Missing session log: $session_log"
  exit 1
fi

project_root="${AGENTS_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
if [ ! -d "$project_root" ]; then
  echo "Error: could not determine project root."
  exit 1
fi

slugify() {
  printf '%s' "$1" \
    | tr '[:upper:] ' '[:lower:]-' \
    | tr -cd 'a-z0-9._-' \
    | sed -E 's/-+/-/g; s/^-+//; s/-+$//'
}

project_slug="${AGENTS_PROJECT_SLUG:-$(slugify "$(basename "$project_root")")}"
agents_home="${AGENTS_HOME:-$HOME/.agents}"
mem_root="$agents_home/memory/$project_slug"

mkdir -p "$mem_root"/{plans,sessions,handoffs,decisions,errors,indexes}

base="$(basename "$session_log")"
cp "$session_log" "$mem_root/sessions/$base"

if [ -f "$project_root/STATUS.md" ]; then
  cp "$project_root/STATUS.md" "$mem_root/indexes/STATUS.md"
fi

"$agents_home/scripts/extract-entities.sh" "$session_log" >/dev/null 2>&1 || true
