# Current Status

**Project:** NEWS AI SMALL MODEL  
**Date:** 2026-09-05  
**Current phase:** Stage 3 — Build Audience / Stage 4 — Monetization preparation

## Dashboard
| Area | Status |
|---|---|
| Scope frozen | DONE |
| Repository structure | DONE |
| Topic queue | DONE — 15 buyer-intent topics |
| Generate | DONE — catalogue-informed, source-bound content |
| Affiliate links | DONE — exact Amazon UK catalogue links |
| WordPress publish | DONE — controlled unattended production path verified |
| External image gate | DONE — 1 compliant hero + 1 compliant context image verified in production |
| Cross-linking | DONE |
| End-to-end pipeline | DONE |
| Tests | DONE — run #95: 34/34 passed |
| Unattended production test | DONE — run #103 succeeded and published post 55 |
| Audience health | DONE — automated site/REST health check passing |
| TechSignal branding | DONE — controlled WordPress logo deployment verified live |
| Audience acquisition | IN PROGRESS — search-engine ownership steps remain external |
| Monetization instrumentation | READY — affiliate metadata and validation already recorded |
| Monetization measurement plan | DONE — see `MONETIZATION.md` |
| Revenue proof | NOT YET PROVEN — requires real traffic and Amazon reporting data |

## Verified production baseline — 2026-09-05
Production run #103 completed successfully on the verified code baseline. The run generated and published:
- Topic: `best USB microphones under $100`
- WordPress post ID: `55`
- Status: `publish`
- Public URL check: HTTP 200
- Affiliate products: 2 exact Amazon UK catalogue matches
- External images: 1 hero + 1 context, both licence-checked with attribution metadata
- WordPress Media Library storage: false
- Pre-publish validation: passed
- Run metrics/history: persisted

The preceding image-gate defect was resolved by preserving the authoritative topic category through the pipeline so category-aware licensed image acquisition could operate correctly. Deterministic licensed Commons fallbacks remain available if live search is empty or unreliable.

### Deployment note
The verified run #103 published to `techsignal.wasmer.app`, because the GitHub Actions production credentials currently resolve to that WordPress endpoint. The previously planned AwardSpace host `techsignal.mypressonline.com` has **not** been verified by this production run. Treat the AwardSpace migration as a separate deployment/configuration milestone; do not assume the current Actions secrets have been migrated to it.

GitHub Issue #9 — `STEP 10 — Unattended production test` — is closed as completed.

## Feature-freeze rule
The build is now frozen. Do not add features, expand scope, or tune editorial behavior without evidence. Future changes require one of:
1. a concrete production defect;
2. a reliability or safety failure;
3. a measurable commercial bottleneck; or
4. evidence-backed improvement that can be evaluated against the production baseline.

Operating sequence:

`BUILD → SHIP → MEASURE → LEARN → IMPROVE`

## Current business position
**BUILD → PROVE CONTENT → BUILD AUDIENCE → MONETIZE → SCALE**

Build is complete. Controlled unattended content production and affiliate validation are operational. The business question is now whether TechSignal can attract real buyer-intent visitors and convert that attention into affiliate revenue.

## Affiliate controls
`products.json` is the commercial source of truth. The current Amazon UK tracking ID is `echsignalnews-21`. Affiliate insertion accepts only exact catalogue products and Amazon UK URLs, and publication validation records the marketplace, tracking ID, selected products, exact matches, and validation result.

Search-based affiliate links are disabled. Catalogue mismatches block publication.

## Stage 4 measurement
`MONETIZATION.md` defines the commercial measurement model:

`visitor → affiliate click → qualifying purchase → dispatched item → commission`

The key metrics are traffic, affiliate clicks, click-through rate, items ordered, items dispatched, conversion, dispatched-items revenue, earnings, revenue/article, and revenue/1,000 visitors.

No revenue, conversion or traffic result is considered valid until it comes from external reporting data.

## External actions still required
- Google Search Console ownership verification and sitemap submission
- Bing Webmaster ownership verification and sitemap submission
- Analytics account/property setup if selected
- Amazon Associates reporting access/data for revenue proof
- AwardSpace deployment/configuration verification if the site migration remains the intended production target
- Additional Amazon tracking IDs only if later segmentation is justified

These are account-level actions, not code defects.

## Next business milestone
Get search discovery operating, publish the controlled content set, collect real visitor and affiliate-click data, then use Amazon reporting to determine whether any topic cluster produces measurable revenue.
