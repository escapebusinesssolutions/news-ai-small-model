# TechSignal Consumer Video Production Standard

**Status:** ACTIVE QUALITY GATE  
**Date:** 2026-09-13

## Purpose

Define the minimum visual-production standard for TechSignal consumer technology videos. A technically valid MP4 is not sufficient for acceptance. The video must visibly help a consumer evaluate the exact product(s) in the article.

## Non-negotiable production values

1. **Product-first visuals** — the exact product being discussed must be visible for a substantial part of the video. Generic technology imagery, abstract shapes, dark information cards, and category graphics are supporting material only.
2. **Real product evidence** — use real product photography, product footage, close-ups, ports/controls/details, packaging where useful, or credible product-in-use footage. The visual should correspond to the narrated point.
3. **Visual progression** — scenes must change because the buyer question changes: what it is → what matters → how it is used → strengths → trade-offs → who should buy → who should skip → verdict.
4. **Consumer relevance** — every major visual must answer or illustrate a buyer decision. Decorative motion does not count as substantive visual coverage.
5. **Product identity** — the exact model must be identifiable, not merely a generic product category.
6. **Evidence hierarchy** — licensed/verified real product media takes priority over original graphics. Original graphics are appropriate for specifications, comparisons, trade-offs, decision frameworks and calls to action, but must not dominate the video.
7. **No invented experience** — the video must never imply TechSignal physically tested, owned, measured, photographed or reviewed a product unless first-hand evidence actually exists.
8. **Rights discipline** — every externally sourced visual must have a recorded source, rights status, usage basis, attribution where required, and commercial-reuse check before production acceptance.
9. **Readable overlays** — text supports the visual; it does not replace it. Avoid long paragraphs and repeated title cards.
10. **Short-form pacing** — visual changes should follow the narration and maintain attention without artificial motion used solely to hide a lack of substantive imagery.

## Minimum visual mix

For an unattended TechSignal product video:

- At least **60% of visual duration** must contain real product/product-in-use media or a sequence of product-specific images/footage.
- At least **3 distinct product-specific visual assets** are required for a single-product video where the source library can reasonably provide them.
- For multi-product videos, each selected product must receive identifiable visual treatment; one product image cannot represent the entire comparison.
- Original graphics may fill the remaining duration where they provide genuine decision-support information.
- A video dominated by abstract graphics, empty/dark slides, generic category imagery, or repeated stills is **FAIL**, even if technical QC passes.

## Preferred asset hierarchy

1. Exact product video showing the product or product in use.
2. Exact product photography from a verified commercial-use source.
3. Multiple verified close-up/detail images of the exact product.
4. Product-specific diagrams or manufacturer documentation where permitted and genuinely useful.
5. Original comparison/specification graphics.
6. Generic technology/category imagery only as minor contextual support.

## Scene acceptance

| Scene | Minimum acceptable visual |
|---|---|
| Hook | Exact product or compelling product-in-use visual |
| Product | Exact product hero/detail |
| Key feature | Product close-up or feature-specific visual |
| Real-world use | Product in the relevant use context |
| Spec check | Product visual plus concise spec overlay, or strong product-specific graphic |
| Trade-off | Product visual plus concise trade-off explanation |
| Best for | Product/use-case visual |
| Skip if | Product/use-case visual or clear comparison visual |
| Comparison | Both products visibly represented where applicable |
| Verdict | Product visual, preferably with a decisive final shot |
| Buyer check | Product-specific decision cue |
| CTA | Product/guide visual; not a generic blank card |

## Automated QC requirements

Technical QC must be supplemented by content-visual QC that records at minimum:

- total duration;
- product-specific visual duration;
- product-specific visual percentage;
- distinct product asset count;
- distinct product count represented;
- generic/abstract visual duration;
- repeated-asset ratio;
- scene-to-product mapping;
- rights status for every external asset;
- consumer narrative arc result.

The production gate must fail when the minimum product-visual coverage is not met. A passing codec/audio/black-frame/motion check cannot override this gate.

## Current implementation implication

The current TechSignal selector/compositor was originally capable of rendering 12 consumer-oriented slots but still represents most slots as `original_graphic`. That is not sufficient by itself for this standard. The asset library must be enriched and the selector must prefer verified product media before falling back to explanatory graphics.

Until the asset library and visual-coverage gate satisfy this standard, TechSignal videos remain **production-quality development output**, not approved unattended consumer publishing output.

## Business rationale

TechSignal is a consumer buying-guide property. The video's job is to increase understanding and commercial intent around a real product decision, not merely to convert an article into moving slides. Video production therefore earns its place only when it provides additional visual decision support and can be produced consistently without weakening factual, rights or commercial controls.
