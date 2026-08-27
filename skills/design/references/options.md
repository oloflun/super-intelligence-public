# Presenting options

**Load when showing the user two or more directions, variations, or riffs.**

> Source: Anthropic's Claude Design "Options" skill, ported at full fidelity with the host-specific bits adapted. Blocks marked **[ours]** are this repo's framing.

---

## Choosing the shape

> *"When showing multiple design options on one page, decide between (a) a single full-size responsive prototype with a tweaks panel, or (b) a vertical stack of anchored option cards. Choose based on how design-y vs prototype-y the ask is, how many options there are, and how big each is."*

Use **(a)** when the question is "how should this behave" and there is essentially one design with parameters. Use **(b)** when the question is "which direction" — that is the format below.

## The turn-stacked format

> *"Present multiple design options as a vertical stack of turns — each turn of options is its own `<section>`, newest turn at the **top**, and every option gets a stable `{turn}{letter}` id (`1a`, `1b`, `2a`…) that the user references back in chat and you cross-link between turns."*

> *"**How to write it** — put one `<style>` block in the head, then one `<section class="dv-turn">` per turn as a **direct child of the root**, no wrapper. When the user asks for another round, **insert the new section ABOVE the existing ones** so the latest work sits at the top; never reorder, renumber, or delete earlier turns."*

**[ours]** The host-provided pan/zoom canvas does not exist here, so the `design_doc_mode` meta and `<helmet>` wrapper are dropped and replaced with a normal `<head>`. Everything else ports unchanged.

```html
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{margin:0;background:#f0eee9;font-family:system-ui,sans-serif}.dv-turn{padding:40px 44px 32px;border-bottom:1px solid rgba(0,0,0,.08);scroll-margin-top:16px}.dv-thd{display:flex;align-items:baseline;gap:10px;margin:0 0 20px}.dv-tid{font:600 10px ui-monospace,Menlo,monospace;padding:3px 7px;background:#1a1a1a;color:#fff;border-radius:4px;text-decoration:none}.dv-tname{font:600 13px/1.2 system-ui,sans-serif;color:#1a1a1a}.dv-opts{display:flex;flex-wrap:wrap;gap:28px;align-items:flex-start}.dv-opt{flex:none;display:flex;flex-direction:column;gap:9px;scroll-margin-top:16px}.dv-oid{font:600 10.5px ui-monospace,Menlo,monospace;padding:3px 7px;background:rgba(0,0,0,.08);color:#1a1a1a;border-radius:5px;text-decoration:none}.dv-olabel{display:flex;align-items:baseline;gap:8px;font:400 11px/1.3 system-ui,sans-serif;color:rgba(0,0,0,.55)}.dv-card{max-width:100%;background:#fff;border:1px solid rgba(0,0,0,.08);border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow:hidden}.dv-opt:target .dv-oid{background:#2a78d6;color:#fff}.dv-next{margin:22px 0 0;font:12px/1.5 system-ui,sans-serif;color:rgba(0,0,0,.5)}</style>
</head>
<section class="dv-turn" id="t2">
<div class="dv-thd"><a class="dv-tid" href="#t2">2</a><span class="dv-tname">Riffs on <a class="dv-oid" href="#1b">1b</a></span></div>
<div class="dv-opts">
<div class="dv-opt" id="2a"><div class="dv-olabel"><a class="dv-oid" href="#2a">2a</a>Tighter spacing</div><div class="dv-card" style="width:360px">…design…</div></div>
<div class="dv-opt" id="2b">…</div>
</div>
<p class="dv-next">Try next: "more like <a class="dv-oid" href="#2a">2a</a> but with the serif from <a class="dv-oid" href="#1c">1c</a>" · "make <a class="dv-oid" href="#2b">2b</a> full-bleed" · "new directions"</p>
</section>
<section class="dv-turn" id="t1">…turn 1, unchanged…</section>
```

## Rules

> *"Turn section ids are `t1`, `t2`, `t3`…; option ids are `1a`, `1b`, `2a`… and go on the option's **outermost** element (`.dv-opt`), never on the badge — so `#1b` scrolls the whole option into view. Ids are stable forever, never reused or renumbered. Options within a turn sit side-by-side in a wrapping row. **Every** option-id reference in the file — turn heading, option label, `.dv-next` line, any prose — is an `<a class="dv-oid" href="#1b">1b</a>` link, never a bare `1b`; in your chat replies, just write `1b`. End each turn with a one-line `.dv-next` of 2–3 plain-English follow-ups the user could paste into chat. Size each `.dv-card` to its content (explicit width is fine); don't use `height:100%`."*

**[ours]** The stable-id rule is what makes the whole thing work: the user says "1b but with 2a's spacing" and both of you mean the same thing three turns later. Renumbering breaks every prior reference in the conversation.

## What to vary

From [`process.md`](process.md) — 3+ variations across several dimensions, mixing by-the-book against novel; some with colour and advanced CSS, some with iconography and some without; basic first, more creative as you go. Remix the brand's own DNA: scale, fills, texture, visual rhythm, layering, novel layouts, type treatments.

**[ours]** At Tiers 0–2 every option stays inside the derived system. Options explore *composition, rhythm, and emphasis*, not alternative brands. Presenting one option in the brand and two in invented palettes is not a choice of three — it is one real option and two distractions.
