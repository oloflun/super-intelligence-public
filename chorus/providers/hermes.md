# Hermes provider contract

- Agent name: hermes
- Default project scope for shared infra coordination: canonical Knowledge Base vault cwd
- Read inbound coordination from `.agent-chorus/messages/hermes.jsonl`
- Send handoffs with explicit project context and next-action summary
- STATUS.md bridge is read from `~/STATUS.md`
- Global conclude/status updates use `~/.agents/scripts/update-global-status.py`
