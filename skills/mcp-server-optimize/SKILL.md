---
name: mcp-server-optimize
description: Optimize an MCP vision server's prompts, parameters, and image analysis pipeline against reference images with a Gemini-quality baseline. Use when an MCP vision server (clipboard-vision, etc.) produces undercounts, misses UI elements, or has poor OCR accuracy.
metadata:
  type: workflow
  triggers:
    - optimize mcp server
    - improve vision prompts
    - fix product undercount
    - match gemini quality
    - clipboard vision accuracy
---

# MCP Server Optimize

Test-and-tune workflow for vision MCP servers backed by weaker vision models
(e.g., Llama-4 Scout). Compensates for model limitations with structured prompts,
PIL metadata tuning, and parameter adjustments. Verifies against a Gemini-quality
baseline and confirms generalization on unrelated images.

## Core Principle

Weaker vision models undercount items and skip UI elements because they need
EXPLICIT enumeration instructions. The fix is always: stronger prompts,
dynamic grid hints from PIL metadata, and lower temperature. Never rewrite
the server from scratch — targeted edits only.

## Steps

### 1. Read the current server.py
Identify: PROMPTS dict, _pil_context_string(), _find_zones() threshold,
VisionClient.analyze() temperature/max_tokens.

### 2. Apply targeted edits
- **describe_ui prompt**: Replace generic "analyze this UI" with numbered
  sections (Browser Chrome → Header → Content Grid → Sidebars → Colors).
  Add "MUST have these sections — do not skip" and "GRID LOCK using PIL metadata."
- **extract_text prompt**: Add product-code pattern awareness, spatial grouping,
  OCR completeness checklist.
- **_pil_context_string()**: Add GRID LOCK mode (uniform column width detection),
  MANDATORY sidebar listing, BROWSER CHROME FIRST instruction.
- **_find_zones() threshold**: Lower from 0.85 to 0.92 to catch narrow gaps
  between product cards (~1.7% width).
- **Model params**: temperature 0.3→0.15, max_tokens 4096→8192.
- **Sidebar prompt**: Widen edge range (0-20% not 0-5%), mention specific
  icon types (arrows, plus signs, letters, chevrons).

### 3. De-overfit check
Grep for hardcoded product data in prompts:
```bash
grep -n "EXACTLY 10\|2 rows x 5\|project-a\|HT-RE[0-9]" server.py
```
If found: replace with dynamic PIL metadata references ("use the column count
from the metadata above" not "EXACTLY 5 columns").

### 4. Test via direct Python import
```python
import sys, json, asyncio, os
sys.path.insert(0, '<path-to-mcp-package>')
from <server_module> import VisionClient, PROMPTS

async def test():
    client = VisionClient(api_key=os.environ['GROQ_API_KEY'])
    resp = await client.analyze('<reference-image>', PROMPTS['describe_ui'])
    data = json.loads(resp)
    # Count product codes, check browser/sidebar/colors presence
    # Compare against Gemini baseline
asyncio.run(test())
```

### 5. Validate against metrics
- Product count: exact match to ground truth
- OCR accuracy: >95% codes and names correct
- Browser chrome: URL bar, bookmarks, tabs described
- Sidebar: all icons listed
- Layout: correct row×column count
- Color palette: dominant colors mentioned

### 6. Generalization test
Test on a completely unrelated image (non-UI photo, different website).
Verify no hardcoded values from step 3 leak into output.

### 7. Score with evaluate.py
If an evaluate.py exists in the task directory, run it:
```bash
python evaluate.py --gen-dir <gen-dir>
```
Target: ≥70/100 (SIA PASS threshold).

## Environment cleanup
- Check for stale `VISION_MODEL` in registry:
  `reg query HKCU\Environment /v VISION_MODEL`
- Kill stale MCP processes if accumulated
- MCP reload requires session restart after process kill.
- **Clipboard tools may not work in all process contexts** — see `references/clipboard-mcp-quirks.md` for diagnosis and workarounds.

## Files modified
- `<mcp-package>/server.py` — prompts, PIL context, zone threshold, model params
- Evaluate with: `evaluate.py` (if available)

## Constraints
- Keep all existing tools intact
- Keep PIL metadata layer (_extract_pil_metadata, _find_zones, _detect_text_regions)
- Keep JSON output format (pixel_analysis + semantic_analysis)
- Backend and Python version must not change
