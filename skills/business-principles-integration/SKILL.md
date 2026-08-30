---
name: business-principles-integration
description: "Fires on ANY question with a business-judgment component — strategy, pricing, growth, execution, hiring, product, competition, operations, decisions, mindset — in Swedish or English, even when the user names no framework or knowledge base. Trigger examples: 'ska jag höja priset', 'hur får jag fler kunder', 'borde jag anställa nu', 'vi tappar tillväxt', 'konkurrenten gör X', 'jag vet inte vad jag ska prioritera', 'is this a good hire', 'how should I price this', 'we are losing momentum', 'should I build this feature', 'how do I compete with', 'what should our strategy be'. Does NOT fire for purely technical or data-only questions with no business-judgment component. Enriches every business answer with 1-3 applied principles from the business-principles knowledge base, framework first, never force-fit."
---

# Business Principles Integration

## Load order: foreman first

This layer fills in **on top of** a foreman framework — it never replaces it.
Before applying anything below, load the closest-matching `Skill(foreman:<name>)`
and reason with that framework first. It is the analytical base, not an
afterthought.

In Claude Code a hook states this on every fire. In chat and Cowork there is no
hook, so it is stated here instead — the requirement is identical on every
surface, and this file is the only thing carrying it where hooks do not run.

If no foreman skill is available (the `foreman` marketplace is not installed on
this account), say so once and continue with the principles alone — never drop
the framework step silently.

## Purpose

Bidirectional synergy between framework-first strategic reasoning and a growing business-principles knowledge base:

1. **KB → ALL strategic analysis.** The business-principles KB is not a coaching-only resource. Every business answer may draw on it.
2. **Coaching → full framework.** `business-coaching-protocols` draws on diagnostics, playbooks, and this KB layer — the KB is one input, never the only one.

## Källåtkomst

Check for local filesystem access first, then fall back to GitHub:

- **If `~/OneDrive/Dokument/Obsidian/Knowledge Base/` exists** (Cowork or local Claude Code on Anton's machine): read files directly from that vault. Canonical file: `wiki/entrepreneurship/business-principles.md`.
- **Else if a GitHub MCP connector is available**: read against the private repo `oloflun/anton-vault`, branch `vault-main`, using whatever GitHub file-read tool is available (e.g. get file contents). Business principles are mirrored **one file per §**: `wiki/entrepreneurship/bp-sections/NN-<slug>.md`. Always prefer these section mirrors over the full source file — read `wiki/entrepreneurship/bp-sections/INDEX.md` first if unsure which `NN` matches the routed domain, then fetch only that section file.
- **Else** (a Code session in a project repo, no vault cloned, no connector configured yet): neither of the above is reachable. Do NOT spend tool calls probing for KB paths that don't exist in this repo (Glob/Read against `wiki/` here will just fail). Fall back to the **named principles already listed in the Domain Routing table below** — they are real, citable KB entries (name + § + one-line gist), just without the fuller paragraph the source file would give. Say explicitly in the answer that this is the routing-table-level citation, not the full KB passage, so the gap is visible rather than silently patched over.
- **Never quote-dump.** Whichever path you read from, extract 1-3 principles — each as NAME + SOURCE + one-sentence APPLICATION — never the raw section text.

## Marknadskontext: svensk som default

Anton driver svenska bolag mot svenska/nordiska kunder. **Om inget annat anges är
marknaden Sverige** — konkurrenter, prisnivåer, kanaler, regelverk, kundbeteende
och exempel ska vara svenska eller nordiska.

- Använd svenska/nordiska jämförelsebolag, inte amerikanska, när du illustrerar
  ett läge. Amerikanska jättar (Manhattan Associates, SAP EWM, HubSpot...) är
  relevanta bara när de faktiskt konkurrerar om samma svenska kund, och då ska
  det sägas uttryckligen.
- Svenska realiteter som ändrar svaret: mindre TAM (bygger inte samma
  volymlogik), moms/F-skatt/enskild firma vs AB, GDPR-tolkning i praktiken,
  längre och mer relationsdrivna B2B-säljcykler, LAS/anställningskostnad vid
  hiring-frågor, offentlig upphandling som kanal.
- Frameworken själva (Porter, BCG, Four Ps, Cialdini) är marknadsneutrala —
  det är EXEMPLEN och kalibreringen som ska vara svenska.
- Anta aldrig amerikansk kontext tyst. Är marknaden oklar och det ändrar svaret:
  fråga, eller säg vilket antagande du gjort.

## Domain Routing (question type → KB domain)

| Question | Domain | Example principles (name / number) |
|---|---|---|
| Strategy, positioning, competition | §2 STRATEGI | First principles (2.1), vertical integration (2.2), cost obsession / Idiot Index (2.3), megatrends (2.4), distribution (2.5), niche-first (2.6), timing windows (2.7), validate cheap (2.9), date the product marry the niche (2.14), taste as moat (2.16) |
| Pricing, costs | §2 STRATEGI | Idiot Index (2.3), cost obsession (2.3), distribution bottleneck (2.5) |
| Market entry | §2 STRATEGI | Distribution (2.5), niche-first (2.6), timing windows (2.7), validate cheap (2.9) |
| Execution, operations, process | §4 EXEKVERING | Musk's Algorithm (femstegs), Walk to the Red (100 beslut/dag), hastighet som designkrav, besatt research, frontline feedback (två frågorna), organisation före design, djupgående lärlingskap |
| Growth, retention, scaling | §5 TILLVÄXT | Långsiktighet slår allt (5.1), de deals du undviker (5.2), relationer driver världen (5.3), varumärke via operationell excellens (5.4), metrikdriven retention (5.6), AI-kostnadsstyrning (5.7) |
| Product, innovation, building | §6 SKAPANDE | Följ nyfikenheten (6.1), kopiera mellan fält (6.2), skapa som gåva (6.3), enkelhet (6.4), gotcha-funktionen (6.5), kurering (6.6), bygg-distribuera-loopen (6.7), solo-first iteration (6.8B), underhåll som produkt (6.9), Codex-native SaaS (6.10) |
| Hiring, team, leadership | §3 TALANG | En tom stol bättre än fel person (3.1), omöjligt att överbetalda för talang (3.2), små team (3.3), dialektiska tänkare (3.4), karisma förvränger feedback (3.5) |
| Mindset, motivation, decisions | §1 MINDSET | Mental klarhet (1.1), självtro före förmåga (1.2), negativa tankar som data (1.3), skydda entusiasmen (1.4) |
| AI-era business models | §8 LOKAL AI | Äg en del av stacken (8.2), manuellt först (8.4), AI-anställda (8.5), skala AI inte headcount (8.9), FDE-metoden (8.12), gratis-audit (8.13), bygg för de 1 000 misslyckandena (8.14) |
| Implementation, tools, action | §7 IMPLEMENTERING | Quit-test, två frågor, frontline loop, first principles drill, nyfikenhetsinventering, veckokoll, börja med en agent |
| No match | — | Scan the KB headings; if nothing fits, state "no matching principle in KB" explicitly — never force-fit |

Note: numbering inside §4 EXEKVERING is inconsistent in the source (duplicate numbers) — cite §4 principles BY NAME rather than number. The KB grows continuously; if the routing table above has no match, scan the section headings for a new domain rather than forcing an existing one.

## Protocol

1. **Framework first.** Apply the standard analytical layer first: the matching diagnostic, playbook, or framework for the question type.
2. **Query the KB.** Route the question to a domain (table above), then read the relevant section via the Källåtkomst path.
3. **Synthesize.** Framework result + 1-3 principles, each cited BY NAME and SOURCE in one sentence, then APPLIED to the specific situation.
4. **Coaching check.** If the situation matches `business-coaching-protocols` triggers (stuck, big decision, team, mindset) — also load it. Coaching is tone + protocols on top of this layer, not a replacement for it.
5. **No-match honesty.** If no principle fits, say so explicitly.

## Citation Rules

- **Name + source + application, one sentence.** "Brad Jacobs: 'En tom stol är bättre än fel person' — du tolererar B-spelare för att du fruktar vakansen, inte för att de är bra." is good.
- **Never dump the library.** One principle, one application, one action — not a tour of the KB.
- **Never let principles replace analysis.** The KB amplifies the numbers and frameworks; it does not substitute for them.

## Anti-Patterns

1. **Force-fitting.** A principle added because "we always add KB" — if nothing fits, say so.
2. **Quote tour.** Three citations in a row with no application = noise, not insight.
3. **Skipping the framework.** The KB is not a replacement for structured analysis (Porter, diagnostics, playbooks).
4. **Stale routing.** The KB grows; if the domain table is outdated, scan the headings and note the gap.

## Relationship to business-coach

`business-coach` is a separate persona skill, loaded only on explicit request; this skill is the always-on KB layer underneath any business-judgment answer, persona or not.
