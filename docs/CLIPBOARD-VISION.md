# Clipboard Vision MCP (Optional)

Add vision to text-only models (DeepSeek V4, GLM 5.1) by letting them see images directly from your clipboard — no manual file saving.

## The Problem

Text-only models like DeepSeek V4 and GLM 5.1 can't read images. When you paste a screenshot, they ask you to save it to disk and provide a path.

## The Fix

This MCP server sits between your AI client and a free vision model (Groq + Llama-4 Scout). When the LLM needs to see your screenshot, it calls `analyze_clipboard` — the server reads the clipboard image, sends it to the vision model, and returns a text description the text model can reason about.

**Result: paste → ask → done.** No file shuffling.

## Quick Install

```bash
git clone https://github.com/Capetlevrai/clipboard-vision-mcp.git
cd clipboard-vision-mcp
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -e .
```

## Get a Free API Key

Sign up at https://console.groq.com/keys (30 seconds, free tier).

## Wire to Your MCP Client

### Claude Code (~/.claude/.mcp.json or ~/.mcp.json)

```json
{
  "mcpServers": {
    "clipboard-vision": {
      "command": "{{PYTHON_PATH}}",
      "args": ["-m", "clipboard_vision_mcp"],
      "env": {
        "GROQ_API_KEY": "gsk_your_key_here"
      }
    }
  }
}
```

Replace `{{PYTHON_PATH}}` with the absolute path to your venv Python.

### Codex (~/.codex/config.toml)

```toml
[mcp_servers.clipboard-vision]
command = "{{PYTHON_PATH}}"
args = ["-m", "clipboard_vision_mcp"]

[mcp_servers.clipboard-vision.env]
GROQ_API_KEY = "gsk_your_key_here"
```

## Tools Provided

| Tool | What It Does |
|---|---|
| `analyze_clipboard` | Generic description/Q&A on clipboard image |
| `extract_text_from_clipboard` | Pure OCR from clipboard |
| `describe_ui_from_clipboard` | UI/UX review, component inventory |
| `diagnose_error_from_clipboard` | Error screenshot → cause + fix |
| `code_from_clipboard` | Extract code from a screenshot |

## Security

- Local stdio process — no network ports opened
- File type allow-list (only .png .jpg .jpeg .gif .webp .bmp)
- Magic-byte validation before upload
- 20 MB max per image
- Auto-deletes clipboard temp files after analysis
- Never commit your Groq API key

## Requirements

- Python 3.10+
- Groq API key (free)
- OS-specific: Windows (nothing extra), macOS (`brew install pngpaste` optional), Linux (`wl-clipboard` or `xclip`)

## Reference

- [[entities/clipboard-vision-mcp]] — full entity documentation for this tool in the vault wiki
