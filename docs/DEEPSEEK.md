# DeepSeek Integration via Claudeep (Optional)

Use DeepSeek models as a backend for Claude Code via the Anthropic API proxy bridge.

## What is Claudeep?

[Claudeep](https://socket.dev/npm/package/claudeep) is an npm package that proxies Claude Code's Anthropic API calls to DeepSeek's API. It lets you run Claude Code (with all its tools, hooks, and MCP servers) backed by DeepSeek models instead of Anthropic's — at a fraction of the cost.

## Quick Install

```bash
# Install globally
npm install -g claudeep

# Or use npx
npx claudeep setup
```

The setup script creates `~/.deepseek-claude/env` with the required environment variables.

## Configuration

After setup, configure these environment variables (the setup script guides you):

```bash
export ANTHROPIC_BASE_URL="https://api.deepseek.com/anthropic"
export ANTHROPIC_AUTH_TOKEN="sk-your-deepseek-api-key"
export ANTHROPIC_DEFAULT_SONNET_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_OPUS_MODEL="deepseek-v4-pro[1m]"
export ANTHROPIC_DEFAULT_HAIKU_MODEL="deepseek-v4-flash[1m]"
export CLAUDE_CODE_SUBAGENT_MODEL="deepseek-v4-flash[1m]"
export CLAUDE_CODE_EFFORT_LEVEL="max"
```

## Model Mapping

| Anthropic Model | DeepSeek Equivalent | Context |
|---|---|---|
| Claude Sonnet 4 | `deepseek-v4-pro[1m]` | 1M tokens |
| Claude Opus 4 | `deepseek-v4-pro[1m]` | 1M tokens |
| Claude Haiku | `deepseek-v4-flash[1m]` | 1M tokens |

## How It Works

```
┌──────────────┐   Anthropic API   ┌──────────┐   DeepSeek API   ┌──────────┐
│  Claude Code │ ────────────────▶ │ claudeep │ ────────────────▶ │ DeepSeek │
│  (unchanged) │                   │ (proxy)  │                   │  V4 Pro  │
└──────────────┘                   └──────────┘                   └──────────┘
```

Claude Code thinks it's talking to Anthropic. Claudeep translates and forwards to DeepSeek.

## Limitations

- **No image support:** DeepSeek V4 is text-only. Pair with [clipboard-vision-mcp](CLIPBOARD-VISION.md) for vision via clipboard screenshots.
- **Tool use differences:** Some Claude Code features may behave differently with DeepSeek backend.
- **Rate limits:** DeepSeek API has its own rate limits separate from Anthropic.

## Security

- Never commit `~/.deepseek-claude/env` — it contains your API key
- Store the key in environment variables, not in config files
- Rotate keys regularly at https://platform.deepseek.com/api_keys
- The proxy runs locally — your prompts go directly to DeepSeek, not through a third party

## Pairing with Clipboard Vision

The ideal stack for cost-effective Claude Code:

```
Claude Code + claudeep (DeepSeek V4 backend)
    +
clipboard-vision-mcp (Groq + Llama-4 Scout vision)
    =
Full Claude Code tool suite + vision when needed, at DeepSeek prices
```
