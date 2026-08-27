# Show → Pipeline Routing (Canonical)

This is the single source of truth for which Snipd show routes to which extraction pipeline.
The ingest skill's §2 classification table delegates to this reference for routing decisions.

## Routing Table

| Snipd Show | Pipeline | Skills to Load | Language Rule | Memory System |
|------------|----------|---------------|---------------|---------------|
| Fill or Kill | Investment | snipd-ingest, investment-intelligence | Original (finance exception) | market-intelligence.md |
| Market Makers | Investment | snipd-ingest, investment-intelligence | Original (finance exception) | market-intelligence.md |
| Thoughts on the Market | Investment | snipd-ingest, investment-intelligence | Original (finance exception) | market-intelligence.md |
| Bloomberg Daybreak | Investment | snipd-ingest, investment-intelligence | Original (finance exception) | market-intelligence.md |
| Veckans Trade | Investment | snipd-ingest, investment-intelligence | Original (finance exception) | market-intelligence.md |
| Prof G Markets | Investment | snipd-ingest, investment-intelligence | Original (finance exception) | market-intelligence.md |
| The Startup Ideas Podcast | AI Analysis | snipd-ingest, ai-analysis | Original (keep source language) | ai-feature-registry.json |
| Founders | Book/Longform | snipd-ingest | Swedish (translate, quotes in original) | feed-registry.json |
| <Audiobooks> | Book/Longform | snipd-ingest | Swedish (translate, quotes in original) | feed-registry.json |

## Language Rules Summary

| Source Type | Rule |
|-------------|------|
| Finance/investment Snipd episodes | **Original language.** Do NOT translate snips or bullet points. Summary/insights in source language. |
| Books, personal development, general Snipd podcasts | **Swedish.** Translate all content. Quotes stay in original. |
| AI conversations, articles, web clippings (non-Snipd) | **Preserve source language.** Never translate. |
| Quotes (`> ...`) | **Always original language.** Never translate. |

## Extraction Methods Summary

| Method | When to Use | Key Rules |
|--------|------------|-----------|
| Mode 1 (snipd-ingest) | All Snipd podcast episodes | ALL bullet points verbatim. Quotes in original. Summary + insights. |
| Mode 2 (snipd-ingest) | Books, audiobooks, Founders | 2-3 strongest examples per themed section. 3-5 sentences each. Swedish. |
| Investment Intelligence | Finance episodes (after Mode 1) | Structured extraction → market-intelligence.md + host-credibility.json + company-registry.json |
| AI Feature Analysis | AI episodes (after Mode 1) | Extract features → QMD cross-reference → Curiosity Gate → Implementation plans → Telegram |
| 7-Dimension Framework | AI conversations, articles, project files | Problem → Solution → What Worked/Didn't → Key Insight → Applicability |
