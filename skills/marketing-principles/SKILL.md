---
name: marketing-principles
description: "Fires on marketing and go-to-market judgment questions — distribution, copy, ICP, ads, CRO, brand, positioning, channels, growth engines — in Swedish or English, even when the user names no framework or KB. Trigger examples: 'hur ska jag positionera det här', 'vilken kanal ska jag satsa på', 'hur skriver jag en bättre annons', 'vad ska rubriken vara', 'hur får jag fler leads', 'hur höjer jag konverteringen', 'vem är min målgrupp', 'how do I position this', 'which growth channel should I use', 'write better ad copy', 'improve conversion rate', 'who is my ICP', 'landing page copy', 'brand trust', 'GTM strategy', 'pricing the offer for the market'. Does NOT fire for general business-building questions without a GTM angle — see business-principles-integration for those."
---

# Marketing Principles

Thin routing skill onto the marketing-principles knowledge base — go-to-market judgment only (distribution, copy, ICP, ads, CRO, brand, positioning, growth engines, marketing ops).

## Källåtkomst

Check for local filesystem access first, then fall back to GitHub:

- **If `~/OneDrive/Dokument/Obsidian/Knowledge Base/` exists** (Cowork or local Claude Code on Anton's machine): read files directly from that vault.
- **Else if a GitHub MCP connector is available**: read against the private repo `oloflun/anton-vault`, branch `vault-main`.
- **Else** (a Code session in a project repo, no vault cloned, no connector yet): don't probe for these paths, they won't exist here. Cite by name + group from the table below instead, and say plainly that the fuller KB passage wasn't reachable.

Files (same relative path on both surfaces):
- `wiki/domains/marketing/CONTEXT.md` — domain purpose and retrieval rules, read this first
- `wiki/domains/marketing/marketing-principles.md` — canonical KB, 32 principles across 8 numbered groups, with a Cite index table near the top

## Marknadskontext: svensk som default

**Om inget annat anges är marknaden Sverige.** Kanaler, kostnadsnivåer,
konkurrenter, tonalitet och exempel ska vara svenska/nordiska.

- Kanalverkligheten skiljer sig: LinkedIn och branschmedia väger tyngre i
  svensk B2B än i amerikansk; Meta/Google-CPM ligger på andra nivåer; svensk
  e-post-kultur tål mindre volym; kallmail regleras av GDPR:s berättigade
  intresse, inte CAN-SPAM.
- Principerna (Ogilvy, Hopkins, Lasker) är tidlösa och marknadsneutrala —
  men tillämpningen och jämförelseexemplen ska vara svenska.
- Skriv svensk copy som svensk copy: inte översatt amerikansk säljretorik.
  Superlativ och hype-ton fungerar sämre mot svenska köpare.
- Anta aldrig amerikansk marknad tyst. Ändrar marknadsvalet svaret: säg det.

## Protocol

1. **C1 — orient.** Read `wiki/domains/marketing/CONTEXT.md`, then the Cite index table at the top of `marketing-principles.md` (source keys + best sections). This is enough to route the question.
2. **C2 — fetch only the matched group(s).** Read ONLY the `## N. GROUP` section(s) that match the question (e.g. `## 3. BUDSKAP OCH COPY` for copy questions) — never the whole file, on either surface. Groups:

| Group | Covers |
|---|---|
| 1. POSITIONERING | salesmanship framing, emotional transformation + mechanism, desired benefit vs. narrow prevention, product-as-hero |
| 2. DISTRIBUTION | service-first / low-friction first action, individual not mass, content-led proof, obsoleting the intermediary, channel pivots, distribution-before-product |
| 3. BUDSKAP OCH COPY | research before create, specific claims, headline weight, one idea per campaign, full story to intelligent buyers, human not corporate voice, ad variant generation, landing pages |
| 4. TILLVÄXTMOTORER | small tests before scale, samples + reciprocity, moving-parade audiences, engine-of-growth pivots |
| 5. AI-MARKETING OPS | API-first growth stack, warehouse + cron over dashboard-watching, fresh task agents, orchestrator + lead-magnet gap, domain vocabulary, competitor capture tooling |
| 6. VARUMÄRKE OCH FÖRTROENDE | unchanging human nature, craft + close (killer + poet), keeping promises, speaking to the average reader |
| 7. MÄTNING | direct response as truth serum, ad-to-ad variance, winner identification as the scarce skill, structural cost/tech edges |
| 8. PLAYBOOKS | research-before-create sequence, infinite-ads-finite-winners sequence, headline+specificity drill, skills-OS sequence |

3. **Cite every borrowed fact.** Format: `[[source]] › §heading` — copy the citation straight from the principle's **Källor** list; never invent a citation. If the question needs a claim beyond the cited sections, open that source `§heading` directly rather than guessing.
4. **Synthesize, don't dump.** 1-3 principles, each as NAME (or short label) + citation + one-sentence APPLICATION to the specific question. Never quote the raw principle body wholesale.
5. **No-match honesty.** If no group fits, say so explicitly rather than force-fitting.

## One-home rule

- **GTM questions never route to business-principles.** Distribution, copy, ICP, ads, CRO, brand, positioning, and growth-channel questions live here, not in `wiki/entrepreneurship/business-principles.md`.
- **Business-building questions never route here.** Strategy, pricing-as-cost-structure, hiring, execution, product, and mindset questions belong to the sibling skill `business-principles-integration` — cross-reference it instead of pulling marketing citations into a non-GTM answer.
- A question can legitimately need both (e.g. "should we raise prices" touches §2 STRATEGI cost obsession AND marketing positioning) — in that case load both skills and keep each citation in its own home.

## Anti-Patterns

1. **Reading the whole KB file.** Load the Cite index + matched group(s) only.
2. **Citation-free claims.** Every borrowed fact carries `[[source]] › §heading`.
3. **Section-level over-fetching.** Retrieve at group level (e.g. `§3 BUDSKAP OCH COPY`), not a single subsection — the group gives enough context to pick the right principle without repeated round trips.
4. **Force-fitting a GTM principle onto a non-GTM question**, or vice versa — respect the one-home rule above.
