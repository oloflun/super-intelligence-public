# Agent Context — {agent_name}

**Agent:** {agent_name}
**Platform:** {platform}
**Vault path:** {vault_path}
**Chorus cwd:** {chorus_cwd}

## Coordination Interface

- Read inbound messages from .agent-chorus/messages/{agent_name}.jsonl
- Send handoffs with explicit project context and next-action summary
- Write checkpoint before significant task blocks to .agent-chorus/CHECKPOINT.md

## Session Protocol

1. **Start:** Check chorus messages (chorus messages --agent {agent_name})
2. **Body:** Write checkpoints before significant tasks
3. **End:** Send handoffs to other agents, update STATUS.md

## CARL Integration

Follow all rules in <carl-rules> blocks. Rules are dynamically injected based on context.

## Skills

Skills are loaded via /skill <name>. Available skills are in .agents/skills/.

## Memory

Memory is read at /standup and written at /conclude. Never write mid-session.
