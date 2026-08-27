#!/usr/bin/env bash
set -euo pipefail

session_log="${1:-}"
if [ -z "$session_log" ]; then
  echo "Usage: extract-entities.sh <session_log>"
  exit 1
fi

if [ ! -f "$session_log" ]; then
  echo "Missing session log: $session_log"
  exit 0
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

stem="$(basename "$session_log" .md)"
decisions_out="$mem_root/decisions/${stem}-decisions.md"
handoffs_out="$mem_root/handoffs/${stem}-handoffs.md"
errors_out="$mem_root/errors/${stem}-errors.md"
index_out="$mem_root/indexes/${stem}-index.md"

extract_section() {
  local heading="$1"
  awk -v heading="$heading" '
    $0 ~ "^## " heading "$" { in_section=1; next }
    in_section && $0 ~ "^## " { exit }
    in_section { print }
  ' "$session_log"
}

decisions_block="$(extract_section "Decisions Made" | sed '/^[[:space:]]*$/d')"
handoffs_block="$(extract_section "Cross-Project Handoffs" | sed '/^[[:space:]]*$/d')"
open_threads_block="$(extract_section "Open Threads" | sed '/^[[:space:]]*$/d')"

error_lines="$(grep -iE 'error|failed|exception|bug|broken|crash|timeout' "$session_log" || true)"

if [ -n "$decisions_block" ]; then
  {
    echo "# Decisions - ${stem}"
    echo
    echo "Source: \`$(basename "$session_log")\`"
    echo
    printf '%s\n' "$decisions_block"
  } > "$decisions_out"
fi

if [ -n "$handoffs_block" ] && ! printf '%s' "$handoffs_block" | grep -qi 'None this session'; then
  {
    echo "# Handoffs - ${stem}"
    echo
    echo "Source: \`$(basename "$session_log")\`"
    echo
    printf '%s\n' "$handoffs_block"
  } > "$handoffs_out"
fi

if [ -n "$error_lines" ]; then
  {
    echo "# Errors - ${stem}"
    echo
    echo "Source: \`$(basename "$session_log")\`"
    echo
    printf '%s\n' "$error_lines"
  } > "$errors_out"
fi

{
  echo "# Index - ${stem}"
  echo
  echo "- Source: \`$(basename "$session_log")\`"
  echo "- Decisions file: $( [ -f "$decisions_out" ] && echo "yes" || echo "no" )"
  echo "- Handoffs file: $( [ -f "$handoffs_out" ] && echo "yes" || echo "no" )"
  echo "- Errors file: $( [ -f "$errors_out" ] && echo "yes" || echo "no" )"
  echo
  echo "## Open Threads"
  printf '%s\n' "$open_threads_block"
} > "$index_out"
