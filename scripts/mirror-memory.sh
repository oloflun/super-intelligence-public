#!/usr/bin/env bash
set -euo pipefail

kind="${1:-}"
source_file="${2:-}"

if [ -z "$kind" ] || [ -z "$source_file" ]; then
  echo "Usage: mirror-memory.sh <kind> <source_file>"
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

if [ ! -f "$source_file" ]; then
  echo "Missing source file: $source_file"
  exit 0
fi

base="$(basename "$source_file")"

case "$kind" in
  session)
    cp "$source_file" "$mem_root/sessions/$base"
    ;;
  plan)
    cp "$source_file" "$mem_root/plans/$base"
    ;;
  handoff)
    cp "$source_file" "$mem_root/handoffs/$base"
    ;;
  decision)
    cp "$source_file" "$mem_root/decisions/$base"
    ;;
  error)
    cp "$source_file" "$mem_root/errors/$base"
    ;;
  status)
    cp "$source_file" "$mem_root/indexes/STATUS.md"
    ;;
  *)
    echo "Unknown kind: $kind"
    exit 1
    ;;
esac
