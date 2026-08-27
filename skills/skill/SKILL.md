---
name: skill
description: "Hermes-style self-improvement gateway. Manage the shared agent-agnostic skill registry in ~/.agents/skills/. Supports: /skill list, /skill view <name>, /skill create <name>, /skill patch <name>, /skill evolve <name>. Progressive disclosure: list is cheap (names only), view is on-demand."
---

# /skill — Self-Improvement Gateway

Manages the shared skill registry at `~/.agents/skills/` (agentskills.io format). Any agent
(Claude, Codex, Gemini) can read and contribute to this registry.

The existing `~/.claude/skills/` directory holds Claude Code plugin skills — those are not
managed here. This skill manages the **agent-agnostic**, user-owned registry.

## Commands

### `/skill list`

List all skills in `~/.agents/skills/` at progressive-disclosure level 0 (names + descriptions only):

```bash
find ~/.agents/skills/ -name "SKILL.md" | while read f; do
  dir=$(dirname "$f")
  name=$(basename "$dir")
  desc=$(grep -m1 "^description:" "$f" | sed 's/description: *//' | tr -d '"')
  echo "  $name — $desc"
done
```

Also list skills in `~/.claude/skills/` for reference (read-only from this skill's perspective).

### `/skill view <name>`

Read the full SKILL.md for the named skill:

```bash
find ~/.agents/skills/ ~/.claude/skills/ -name "SKILL.md" -path "*/$name/*" 2>/dev/null | head -1
```

Read that file and present it in full.

### `/skill create <name>`

Write a new skill to `~/.agents/skills/<name>/SKILL.md`.

Skills are stored flat — no category subdirectory. Use descriptive names (e.g. `vercel-cicd-setup`, `nextjs-localization`). Category is captured in frontmatter `metadata.category` only.

Use the agentskills.io SKILL.md template:

```markdown
---
name: <name>
description: "<one-line trigger description>"
version: 1.0.0
metadata:
  tags: [tag1, tag2]
  category: <category>
---

# Skill Title

## When to Use
[Trigger conditions — be specific]

## Procedure
[Step-by-step. Be concrete.]

## Pitfalls
[Known failure modes and how to avoid them]

## Verification
[How to confirm the skill worked]

## Changelog
- <date> v1.0.0 — Initial creation
```

After writing: git add + commit in `{{VAULT_PATH}}\`.

### `/skill patch <name>`

Make a targeted correction to an existing skill. Use when:
- Instructions are found to be outdated during a task
- A better approach was discovered
- A pitfall should be documented

```
/skill patch <name> "<old text>" "<new text>"
```

Process:
1. Find the skill file.
2. Apply the edit (old_string → new_string).
3. Append to the `## Changelog` section:
   `- <date> v<bump> — <one-line reason for the change>`
4. Git add + commit.

One skill per task category — evaluate: does this fit an existing skill? If yes, patch.
Only create if genuinely new.

### `/skill evolve <name>`

Trigger the DSPy+GEPA optimization pipeline for one skill:

```powershell
& "{{VAULT_PATH}}\scripts\evolve-skills.sh" <name>
```

This writes a candidate to a review branch. **Never auto-merges.** Review the diff before
applying. This requires `hermes-agent-self-evolution` to be cloned at `~/hermes-agent-self-evolution/`.

For the nightly scheduled run, use the `schedule` skill to set up a cron trigger.

## Skill File Layout

```
~/.agents/skills/          ← junction: {{USER_HOME}}\.agents\skills
                              same as: KB\.agents\skills
└── <name>/                ← flat, no category subfolder
    ├── SKILL.md           # required
    ├── references/        # optional supplementary docs
    ├── templates/         # optional output formats
    └── scripts/           # optional helper scripts
```

## Conditional Activation (frontmatter)

```yaml
metadata:
  requires_tools: [terminal]        # only show if terminal available
  fallback_for_toolsets: [web]      # only show if web tools unavailable
```

## Design Principles

- **Progressive disclosure**: list is ~3k tokens total; view is on-demand. Never load all
  skill content upfront.
- **One skill per task category**: prefer patching over creating.
- **Semantic preservation gate**: when evolving, the mutation must not drift from the
  original purpose. The evolved skill should do the same thing, better.
- **Return errors as data**: skill procedures should guide the agent to return
  `{"error": "..."}` rather than throw, so the LLM can reason about failures.
