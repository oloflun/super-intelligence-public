---
name: tauri-react-visual-verify
description: "Visually verify React/Tauri app UI (a page, a canvas widget like a graph, a design system change) in a plain browser via a mock-IPC harness, when the real desktop app can't be driven headlessly or you need fast screenshot-iterate loops"
version: 1.0.0
metadata:
  tags: [tauri, react, design, screenshot-verification, visual-testing, ipc-mock]
  category: frontend-tooling
  requires_tools: [terminal]
---

# Tauri/React Visual Verification via Browser Mock-IPC Harness

## When to Use
- You're iterating on visual/UI work (design tokens, a canvas widget, page layout) inside a
  Tauri desktop app, and need to *see* the actual rendered result to judge it — not guess.
- The Tauri window can't be screenshotted directly by your tooling (no browser-automation
  access to a native webview), but the app's frontend is a normal React SPA underneath.
- You need a fast edit → screenshot → compare loop, faster than rebuilding the Rust backend
  and relaunching the native app on every change.
- Any time you are about to claim a visual change is "verified" or "matches the reference" —
  this is the mechanism that makes that claim true instead of asserted. See
  [[design-verification-mandate]] (project memory) for why this matters: claiming visual
  verification without actually looking is a trust-destroying failure mode.

Do NOT use this to replace testing the real app — it's a fast design-iteration loop, not a
substitute for a final check in the actual Tauri window with real IPC data.

## Procedure

1. **Build a mock IPC layer** (`src/lib/ipcMock.ts` or similar): export an `isTauri` boolean
   (`typeof window !== "undefined" && "__TAURI_INTERNALS__" in window`) and a `mockInvoke(cmd,
   args)` function returning realistic seed-shaped data for every command your pages call.
   Route the app's real `invoke()` wrapper through it: `isTauri ? tauriInvoke(...) :
   mockInvoke(...)`. This makes every page render correctly in a plain browser tab with zero
   backend.

2. **For a single complex widget** (e.g. a canvas/graph component), also build a standalone
   harness: a tiny `preview/<widget>Preview.tsx` entry that renders just that component with
   inline mock data, plus a matching `<widget>-preview.html` at the project root pointing to
   it via `<script type="module" src="/src/preview/...">`. This isolates iteration on one
   component from the rest of the app (faster reload, simpler DOM to screenshot).

3. **Add a second dev-server launch config** on a different port so it doesn't collide with
   any already-running dev server (e.g. the real app's `tauri dev` occupying port 1420).
   Example `.claude/launch.json` entry:
   ```json
   { "name": "design-preview", "runtimeExecutable": "npm",
     "runtimeArgs": ["--prefix", "app", "run", "dev", "--", "--port", "1425", "--strictPort"],
     "port": 1425 }
   ```

4. **Iterate with the preview tools**: `preview_start` the new config, `preview_eval` to
   navigate (`window.location.href = "http://localhost:PORT/#/route"` or `?query=params` for
   the standalone harness), `preview_screenshot` to actually look, edit source, repeat.
   - Use `preview_eval` to drive interactive state for verification (e.g. call an exposed
     debug hook like `window.__appInstance.emit(...)` to simulate a click/hover/focus state
     that would otherwise require real mouse coordinates).
   - Toggle dark/light and resize the viewport (`preview_resize`) — verify both, not just one.
   - If a change doesn't show up in the screenshot, don't assume HMR applied it — reload
     explicitly and re-screenshot before concluding the fix didn't work.

5. **When judging against a reference image**: open the actual reference file(s) with the
   Read tool BEFORE writing any iteration code, and re-open them when comparing — do not rely
   on a description or memory of what the reference looks like. State explicitly which
   reference element you're targeting for each change.

## Pitfalls
- **Two dev servers on the same port silently reuse the wrong one.** If `preview_start`
  reports "port in use by a non-preview server," don't force it — add a distinct port config
  instead (step 3). Reusing the real app's dev server means you're screenshotting stale HMR
  state, not your latest edit.
- **HMR can lag or fail silently on structural changes** (new files, changed imports). If a
  screenshot looks unchanged after an edit that should have visibly changed something,
  hard-reload (`window.location.reload()` or full navigation) before trusting the screenshot.
- **A mock returning empty/wrong-shaped data makes every page "render" without erroring** —
  which can mask the fact you're looking at an empty state, not the real layout. Make mock
  data realistic in *shape and volume* (e.g. seed hundreds of graph nodes if the real app
  has hundreds), not just type-correct.
- **Screenshotting your own iteration isn't verification against a reference** — it only
  proves internal consistency. Always diff against the actual reference file, opened fresh.
- **Debug globals left in production code** (e.g. `window.__appInstance = sigmaInstance` for
  preview-eval access) should be dev-only guarded (`import.meta.env.DEV`) so they don't ship.

## Verification
- The preview screenshot shows the intended change with the mock data rendering a realistic,
  non-empty state.
- The screenshot has been visually compared against the actual reference file (opened via
  Read this same turn), not asserted from memory.
- Both light and dark mode checked if the app has a theme toggle.
- A final pass happens in the REAL app (real IPC, real data) before calling the work done —
  the mock harness accelerates iteration, it doesn't replace the final check.

## Changelog
- 2026-07-09 v1.0.0 — Initial creation, extracted from an example-app OS (Tauri 2 + React 19)
  session where this pattern (ipcMock.ts + a standalone brain-preview.html harness + a
  second Vite launch config on port 1425) enabled fast screenshot-driven iteration on an
  AI-brain graph visualization and app-wide design tokens without rebuilding the Rust backend
  on every change.
