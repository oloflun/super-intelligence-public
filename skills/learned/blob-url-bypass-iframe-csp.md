---
name: blob-url-bypass-iframe-csp
description: "Open proxied binary content (PDF, image, video) via blob: URL to bypass parent-frame CSP that blocks inline rendering"
user-invocable: false
origin: auto-extracted
---

# Blob-URL bypass for parent-frame CSP that blocks inline rendering

**Extracted:** 2026-05-19
**Context:** Web app proxies binary content (PDF, image, video) from an internal API
route; needs to render it for the user, but runs inside an embedded iframe (Claude Desktop /
Cursor / VS Code preview / Electron WebView / Teams tab / Office add-in) whose CSP blocks
inline rendering of the content type.

## Problem

`<a href="/api/foo/pdf" target="_blank">` works in a normal browser tab, but when the
app is iframed inside a host with strict CSP, the new tab inherits restrictions (or the
host's WebView refuses to render application/pdf inline) and the user sees only a black
viewport. The PDF bytes themselves are valid (`%PDF-1.3` header confirmed) — the issue
is purely the embedding environment's CSP / WebView capabilities.

## Solution

Fetch the binary in the client, wrap in a Blob, open via `URL.createObjectURL`.
`blob:` URLs technically have a separate opaque origin and inherit the *page's* CSP, not
the parent frame's restriction list — so the browser opens them in a clean tab with its
native viewer (Chrome PDF viewer, image viewer, etc.).

```tsx
async function openBinary(endpoint: string) {
  const res = await fetch(endpoint);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.error ?? `Failed (${res.status})`);
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  // Revoke after the new tab has time to load — without this the blob leaks.
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}
```

Server-side route stays normal: returns the binary with correct `Content-Type` and
`Content-Disposition: inline; filename="..."`. No code change there.

## When to Use

Trigger conditions:
- App embeds inside another host (Claude Desktop preview, VS Code Webview, Cursor preview,
  Electron app, Teams/Outlook add-in, mobile in-app browser)
- You proxy binary via your own server route (to keep API keys server-side)
- Direct `<a target="_blank">` to that route shows black/blank/refused-to-render
- The binary is verified valid (PDF magic header, image header, etc.) — so it's an
  environment problem, not corruption

Don't use this when:
- The app is only ever opened in a normal browser tab (use plain `<a>` — saves a fetch)
- The binary is huge (>50 MB) — blob construction blocks the main thread; stream instead
- You need the URL to be shareable (blob URLs are session-scoped)

## Edge Cases

- Always `URL.revokeObjectURL` after a delay — otherwise the blob leaks until page unload
- For repeated use of the same file, cache the blob URL rather than refetching
- Some Electron variants strip `target="_blank"` opens; use `shell.openExternal` instead
- On iOS Safari in-app browsers, blob URLs sometimes still get blocked — fall back to
  `Content-Disposition: attachment` to force download

## Diagnosis Steps (when not sure if this applies)

1. Open DevTools Network tab → click the PDF link → confirm `200 application/pdf` and
   non-zero size
2. Save the response body to disk → `file foo.pdf` should show `PDF document` and
   `head -c 8 foo.pdf` should print `%PDF-1.x`
3. Open the saved file natively → if it renders, the bytes are fine and the embedding
   environment is the culprit. Apply this pattern.
