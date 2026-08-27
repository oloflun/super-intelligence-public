---
name: visual-catalog-matcher
description: "When the user wants to reliably extract and map products from unstructured photos to a structured CSV or database, avoiding OCR hallucinations by using a two-pass Vision LLM approach."
version: 1.0.0
metadata:
  tags: [vision, data-extraction, catalog-sync, ocr-fallback]
  category: data-processing
---

# Visual Catalog Matcher

## When to Use
Use this skill when you need to identify products in unstructured, messy images (e.g., raw supplier photos, social media scrapes, warehouse shelf photos) and map them precisely to a known database, CSV, or catalog, ensuring zero hallucinated SKUs.

## Procedure
Implement a "Two-Pass Vision Pipeline" using a high-context Vision model (like Gemini 1.5/2.5 Pro or Flash).

### Pass 1: Exhaustive Extraction
1. Feed the image to the Vision model.
2. Prompt it to return strict JSON containing the Article Number/SKU and physical description printed on the label.
3. CRITICAL: Instruct the model that if a label is unreadable or non-existent, it MUST output `UNREADABLE` or `NO_LABEL` rather than guessing.

### Pass 2: The CSV-Injected Verification Loop
1. Diff the extracted SKUs against the source-of-truth database.
2. If the SKU is not found in the database, OR if the Pass 1 result was `UNREADABLE`/`NO_LABEL`, trigger Pass 2.
3. Feed the image back to the Vision model, but **inject the entire text content of the product CSV/catalog** into the prompt context.
4. Prompt the model: "Compare the visual appearance of the items in the image to the physical descriptions provided in the attached CSV catalog. Return the exact matching SKU with 99% certainty."
5. If the model still cannot find a definitive visual match against the CSV, flag the image for manual human audit.

## Pitfalls
- **OCR Hallucinations:** Traditional OCR or simple vision prompts often hallucinate numbers (e.g., reading a blurry `RE1711` as `1801`). This is why Pass 2 (visual feature matching against a known list) is mandatory for accuracy.
- **Context Limits:** Injecting the entire CSV requires a high-context window model. Ensure the model supports at least 1M+ tokens (like Gemini 1.5 Pro/Flash) if the catalog is large.

## Verification
- Confirm that every extracted SKU directly matches a row in the source-of-truth database.
- Review the `MANUAL_AUDIT` list to ensure the model correctly deferred ambiguous images rather than guessing.

## Changelog
- 2026-06-08 v1.0.0 — Initial creation based on the successful project-a unstructured catalog sync workflow.
