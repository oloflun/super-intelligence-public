#!/usr/bin/env bash
set -euo pipefail

query=""
scope="all"
project_root="${AGENTS_PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

usage() {
  cat <<USAGE
Usage: search-memory.sh <query> [--plans|--sessions|--handoffs|--decisions|--errors|--indexes|--all]
USAGE
}

while [ $# -gt 0 ]; do
  case "$1" in
    --plans|--sessions|--handoffs|--decisions|--errors|--indexes|--all)
      scope="${1#--}"
      ;;
    -*)
      usage
      exit 1
      ;;
    *)
      if [ -z "$query" ]; then
        query="$1"
      else
        query="$query $1"
      fi
      ;;
  esac
  shift
done

if [ -z "$query" ]; then
  usage
  exit 1
fi

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

normalize_query() {
  printf '%s' "$1" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/\b(show|me|the|current|progress|status|of|plan|please|for|on)\b/ /g; s/[[:space:]]+/ /g; s/^ //; s/ $//'
}

plan_progress_requested() {
  local lowered
  lowered="$(printf '%s' "$query" | tr '[:upper:]' '[:lower:]')"
  case "$lowered" in
    *"current progress"*|*"plan progress"*|*"progress of the plan"*|*"current status"*|*"status of the plan"*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

latest_file() {
  local dir="$1"
  [ -d "$dir" ] || return 0
  find "$dir" -maxdepth 1 -type f -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
}

matching_plan_file() {
  local plans_dir="$mem_root/plans"
  local subject
  subject="$(normalize_query "$query")"
  [ -d "$plans_dir" ] || return 0

  if [ -n "$subject" ]; then
    grep -R -i -l -- "$subject" "$plans_dir" 2>/dev/null | head -n 1 && return 0
  fi

  latest_file "$plans_dir"
}

extract_markdown_section() {
  local file="$1"
  local heading="$2"
  awk -v target="$heading" '
    function lower_trim(s) {
      gsub(/^[[:space:]#]+|[[:space:]]+$/, "", s)
      return tolower(s)
    }
    /^###[[:space:]]/ || /^##[[:space:]]/ {
      current=$0
      sub(/^###[[:space:]]*/, "", current)
      sub(/^##[[:space:]]*/, "", current)
      if (in_section) exit
      if (lower_trim(current) == lower_trim(target)) {
        in_section=1
        next
      }
    }
    in_section { print }
  ' "$file" | sed '/^[[:space:]]*$/d'
}

first_heading() {
  local file="$1"
  grep -m 1 '^# ' "$file" 2>/dev/null | sed 's/^# //' || true
}

first_non_empty_line() {
  local file="$1"
  awk 'NF { print; exit }' "$file" 2>/dev/null || true
}

first_non_empty_lines() {
  local file="$1"
  local limit="${2:-12}"
  awk -v limit="$limit" 'NF { print; count++; if (count >= limit) exit }' "$file" 2>/dev/null || true
}

print_progress_block() {
  local label="$1"
  local body="$2"
  if [ -n "$body" ]; then
    echo "$label:"
    printf '%s\n' "$body"
    echo
  fi
}

print_plan_progress() {
  local file="$1"
  local title modified completed_count pending_count
  local scope_section completed_section progress_section remaining_section deferred_section blockers_section next_steps_section

  [ -f "$file" ] || return 0

  title="$(first_heading "$file")"
  if [ -z "$title" ]; then
    title="$(first_non_empty_line "$file")"
  fi
  modified="$(date -r "$file" '+%Y-%m-%d %H:%M:%S' 2>/dev/null || echo 'unknown')"
  completed_count="$(grep -Ec '^[[:space:]]*[-*][[:space:]]*\[[xX]\]' "$file" 2>/dev/null || true)"
  pending_count="$(grep -Ec '^[[:space:]]*[-*][[:space:]]*\[[[:space:]]\]' "$file" 2>/dev/null || true)"

  scope_section="$(extract_markdown_section "$file" "Scope")"
  completed_section="$(extract_markdown_section "$file" "Completed")"
  progress_section="$(extract_markdown_section "$file" "In Progress")"
  remaining_section="$(extract_markdown_section "$file" "Remaining")"
  deferred_section="$(extract_markdown_section "$file" "Deferred")"
  blockers_section="$(extract_markdown_section "$file" "Blockers")"
  next_steps_section="$(extract_markdown_section "$file" "Next Steps")"

  echo "=== Current Plan Progress ==="
  echo "Plan File: $file"
  echo "Last Modified: $modified"
  if [ -n "$title" ]; then
    echo "Title: $title"
  fi
  echo "Checklist Progress:"
  echo "- Completed items: $completed_count"
  echo "- Remaining items: $pending_count"
  echo

  print_progress_block "Scope" "$scope_section"
  print_progress_block "Completed" "$completed_section"
  print_progress_block "In Progress" "$progress_section"
  print_progress_block "Remaining" "$remaining_section"
  print_progress_block "Deferred" "$deferred_section"
  print_progress_block "Blockers" "$blockers_section"
  print_progress_block "Next Steps" "$next_steps_section"

  if [ -z "$scope_section$completed_section$progress_section$remaining_section$deferred_section$blockers_section$next_steps_section" ]; then
    echo "Structured Sections:"
    grep -E '^#' "$file" 2>/dev/null || true
    echo
    echo "Excerpt:"
    first_non_empty_lines "$file" 12
    echo
  fi
}

print_scope() {
  local label="$1"
  local dir="$2"
  local hits
  hits="$(grep -R -n -i -C 2 --binary-files=without-match -- "$query" "$dir" 2>/dev/null || true)"
  if [ -n "$hits" ]; then
    echo "=== $label ==="
    printf '%s\n' "$hits"
    echo
  fi
}

case "$scope" in
  sessions)
    print_scope "Sessions" "$mem_root/sessions"
    ;;
  plans)
    if plan_progress_requested; then
      plan_file="$(matching_plan_file)"
      if [ -n "${plan_file:-}" ]; then
        print_plan_progress "$plan_file"
      fi
    else
      print_scope "Plans" "$mem_root/plans"
    fi
    ;;
  handoffs)
    print_scope "Handoffs" "$mem_root/handoffs"
    ;;
  decisions)
    print_scope "Decisions" "$mem_root/decisions"
    ;;
  errors)
    print_scope "Errors" "$mem_root/errors"
    ;;
  indexes)
    print_scope "Indexes" "$mem_root/indexes"
    ;;
  all)
    if plan_progress_requested; then
      plan_file="$(matching_plan_file)"
      if [ -n "${plan_file:-}" ]; then
        print_plan_progress "$plan_file"
        exit 0
      fi
    fi
    print_scope "Plans" "$mem_root/plans"
    print_scope "Sessions" "$mem_root/sessions"
    print_scope "Handoffs" "$mem_root/handoffs"
    print_scope "Decisions" "$mem_root/decisions"
    print_scope "Errors" "$mem_root/errors"
    print_scope "Indexes" "$mem_root/indexes"
    ;;
  *)
    echo "Unknown scope: $scope"
    exit 1
    ;;
esac
