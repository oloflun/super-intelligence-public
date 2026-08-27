---
name: executing-plans
description: Use when you have a written implementation plan to execute in a separate session with review checkpoints
---

# Executing Plans

## Overview

Load plan, review critically, execute all tasks, report when complete.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

**Note:** Tell your human partner that Superpowers works much better with access to subagents. The quality of its work will be significantly higher if run on a platform with subagent support (such as Claude Code or Codex). If subagents are available, use superpowers:subagent-driven-development instead of this skill.

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

### Step 2: Execute Tasks

**CRITICAL: Real-time progress visibility.** Never let a task sit silently — the user must always know what you're working on and what step you're at. If they can see the todo list but it hasn't moved, they're in the dark. That is unacceptable.

For each task:
1. **Announce** what you're about to do BEFORE starting the task
2. Mark as in_progress
3. Follow each step exactly (plan has bite-sized steps)
4. **Report progress** within 30s — if a tool call takes longer, send a status update: "Still working on X, Y is running..."
5. Run verifications as specified
6. Report result: PASS/FAIL + one-line evidence
7. Mark as completed

**Progress reporting rules:**
- Every tool call result → explain what happened and what's next
- Multi-step task → announce each substep before executing
- Background process → poll and report when done
- Timeout or error → **report the blocker IMMEDIATELY**, don't silently retry
- If something is going to take >60s → tell the user and give an ETA
- Never let the user stare at "0/6 Preparing" without knowing what's happening

**Pitfall — Silent stalls:** A task that sits at "Preparing" or "0/6" with no update for minutes is unacceptable. User: "Jag hade ingen insyn i vilket steg den befann sig på. Du får aldrig låta det hända, du måste hålla mig updaterad och om du stöter på något problem ska du meddela mig det." Translation: always show which step is in progress, and report problems immediately — never let the user discover a stall on their own.

**Pitfall — Too many parallel ops:** Running 3+ tool calls in parallel can make progress invisible. The user sees output from all of them at once with no context on which succeeded or failed. Prefer sequential execution for visible tasks, parallel only for truly independent background operations (npm install, git clone).

### Step 3: Complete Development

After all tasks complete and verified:
- Announce: "I'm using the finishing-a-development-branch skill to complete this work."
- **REQUIRED SUB-SKILL:** Use superpowers:finishing-a-development-branch
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- **superpowers:using-git-worktrees** - REQUIRED: Set up isolated workspace before starting
- **superpowers:writing-plans** - Creates the plan this skill executes
- **superpowers:finishing-a-development-branch** - Complete development after all tasks
