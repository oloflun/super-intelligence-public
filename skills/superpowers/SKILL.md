---
name: superpowers
description: >-
  Namespace for development workflow process skills — brainstorming,
  planning, TDD, debugging, code review, subagent-driven development,
  verification, and related disciplines. Each subdirectory is an
  independently invocable skill (e.g., superpowers:test-driven-development).
---

# Superpowers — Development Workflow Skills

A collection of structured process skills for AI-assisted software development.
Each skill covers one phase of the development lifecycle and is independently
invocable.

## Skills

| Skill | Phase | Purpose |
|---|---|---|
| brainstorming | Design | Explore, design, and spec before implementation |
| writing-plans | Design | Create implementation plans with architectural review |
| using-git-worktrees | Setup | Isolated workspace for parallel work |
| test-driven-development | Implement | Red-Green-Refactor TDD discipline |
| subagent-driven-development | Implement | Fresh subagent per task with two-stage review |
| executing-plans | Implement | Follow a written plan in a separate session |
| dispatching-parallel-agents | Implement | Parallel independent task execution |
| systematic-debugging | Debug | Root-cause-before-fix methodology |
| requesting-code-review | Review | Dispatch review subagents for quality gates |
| receiving-code-review | Review | Process review feedback with technical rigor |
| verification-before-completion | Verify | Evidence-based completion claims |
| finishing-a-development-branch | Release | Complete, merge, and clean up |
| writing-skills | Meta | TDD methodology applied to skill authoring |
| using-superpowers | Meta | Skill discovery and invocation guide |

## Flow

```
brainstorming → writing-plans → using-git-worktrees → subagent-driven-development
                                                           ↓
finishing-a-development-branch ← verification-before-completion ← requesting-code-review
```
