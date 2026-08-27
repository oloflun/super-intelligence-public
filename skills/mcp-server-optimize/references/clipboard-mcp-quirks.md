# Clipboard-Vision MCP Quirks

## Clipboard Access Limitation

The MCP server's `analyze_clipboard` tool uses `PIL.ImageGrab.grabclipboard()` which requires
the Python process to run in an interactive Windows GUI session. When Hermes spawns the MCP
subprocess in certain contexts (service mode, background gateway), the clipboard is NOT accessible.

**Symptom:** `analyze_clipboard` returns "No image found in clipboard" even when an image IS
on the clipboard.

**Workaround:** Use the file-based tools (`analyze_image`, `describe_ui`, `extract_text`) with
absolute paths instead. The file-based tools have no clipboard dependency.

**Diagnosis:** Run `python -c "from PIL import ImageGrab; print(type(ImageGrab.grabclipboard()).__name__)"` —
if it returns `NoneType`, clipboard access is unavailable in the current process context.

## MCP Reload Requires Session Restart

Editing `server.py` (prompts, parameters, PIL layer) does NOT take effect until the MCP server
process is restarted. `hermes mcp test` spawns a fresh process for the TEST but tool calls
through the gateway may use a cached process.

**User-facing commands:** `/reload-plugins` and `/reload-skills` exist but `/reload-mcp`
does NOT. The only way to reload the MCP server is a full session restart (`/reset` or new session).

**Workaround:** After editing server.py, tell the user to `/reset` then test immediately.

## Stale VISION_MODEL in Registry

A `VISION_MODEL=gemini-2.5-flash` entry in `HKCU\Environment` (Windows Registry) overrides
the `.mcp.json` env block and causes Groq 404 errors.

```powershell
# Check:
reg query HKCU\Environment /v VISION_MODEL
# Clear if present:
reg delete HKCU\Environment /v VISION_MODEL /f
```

## Verification Before/After Changes

Always run the MCP test to confirm tools are discovered:
```bash
hermes mcp test clipboard-vision
```

Then test with a real image:
```
mcp__clipboard-vision__describe_ui({"image_path": "<path>"})
```

Compare output against the Gemini baseline from the wiki doc:
`{{VAULT_PATH}}\wiki\tools\clipboard-vision-mcp.md`
