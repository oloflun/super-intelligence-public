#!/usr/bin/env python3
"""
DeepClaude PreToolUse hook — blocks model from undoing backend switches.

When the router auto-falls back from Anthropic to DeepSeek (401/402/403),
the model may still try to execute the echo command from the slash-command
template. This hook intercepts Bash tool calls that write to
.deepclaude-mode and denies them — the UserPromptSubmit hook already
handled the switch before the model call.

ponytail: single-file, stdlib only, one responsibility.
"""
import json
import sys

MODE_FILE_MARKER = '.deepclaude-mode'


def main():
    import os
    if os.environ.get("CLAUDE_HOOKS_DISABLED", "").strip() not in ("", "0", "false"):
        sys.exit(0)  # Fas 6 assistant-bench arm B: all hooks off

    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # pass-through on invalid input

    tool_name = input_data.get('tool_name', '')
    tool_input = input_data.get('tool_input', {})

    if tool_name != 'Bash':
        # Not a bash call — allow
        sys.exit(0)

    command = tool_input.get('command', '')

    # Only block WRITES to .deepclaude-mode — reads are harmless
    is_write = (
        (MODE_FILE_MARKER in command and '>' in command) or
        'Set-Content' in command or
        'Out-File' in command
    )
    # ponytail: explicit allowlist for read-only operations
    is_read = (
        'type ' in command or
        'Get-Content' in command or
        'cat ' in command
    )

    if is_write and not is_read:
        # Model is trying to write to .deepclaude-mode — block it.
        # The UserPromptSubmit hook already handled the switch.
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    "DeepClaude: .deepclaude-mode write blocked. "
                    "Backend switch was already handled by UserPromptSubmit hook "
                    "before this model call. No action needed."
                )
            },
            "systemMessage": (
                "DeepClaude: backend switch already processed — "
                "echo/type command skipped."
            )
        }
        print(json.dumps(output))
        sys.exit(0)

    # Not a mode-file command — allow
    sys.exit(0)


if __name__ == "__main__":
    main()
