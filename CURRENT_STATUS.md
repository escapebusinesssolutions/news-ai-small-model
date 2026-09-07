# Current Status

**Project:** NEWS AI SMALL MODEL  
**Date:** 2026-09-07  
**Current phase:** Stage 3 — Build Audience / Stage 4 — Monetization validation

## Dashboard
| Area | Status |
|---|---|
| Scope frozen | DONE |
| Repository structure | DONE |
| Topic queue | DONE — buyer-intent catalogue |
| Generate | DONE — catalogue-informed, source-bound content |
| Affiliate links | DONE — exact Amazon UK catalogue links |
| WordPress publish | DONE — controlled unattended production path verified |
| External image gate | DONE — compliant hero/context image path verified |
| Cross-linking | DONE |
| End-to-end pipeline | DONE |
| Tests | DONE — run #95: 34/34 passed |
| Unattended production test | DONE — run #103 succeeded and published post 55 |
| Audience health | DONE — 2026-09-07 scheduled health run passed all checks |
| TechSignal branding | DONE — controlled WordPress logo deployment verified live |
| Audience acquisition | IN PROGRESS — Search Console/Bing setup complete; external indexing/traffic evidence pending |
| Monetization instrumentation | READY — affiliate metadata and validation already recorded |
| Search performance intelligence | READY — page-level Search Console collection implemented; external credentials/data still pending |
| Monetization measurement plan | DONE — see `MONETIZATION.md` |
| Revenue proof | NOT YET PROVEN — requires real traffic and Amazon reporting data |
| Production target | HOLD — 5/day |

## Latest verified production evidence — 2026-09-07
The Small Model Publish workflow completed successfully at run `34136401446` on `main`. The repository's adaptive publishing state remains `recommended_target=5` and `current_target=5`; the scale gate explicitly holds at 5/day until quality, indexing, traffic, and affiliate evidence improves.

The 2026-09-07 Audience Health workflow also completed successfully. It verified HTTP 200 for the public site, `robots.txt`, the WordPress sitemap, and the feed; verified the latest published post is HTTP 200, has a canonical link, and is not `noindex`; and verified the public WordPress REST posts endpoint returns successfully. The latest verified post slug was `audio-gear-marathon-work-sessions`.

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
The verified production run published to `techsignal.wasmer.app`, because the GitHub Actions production credentials currently resolve to that WordPress endpoint. The previously planned AwardSpace host `techsignal.mypressonline.com` has **not** been verified by the current production run. Treat the AwardSpace migration as a separate deployment/configuration milestone; do not assume the current Actions secrets have been migrated to it.

GitHub Issue #9 — `STEP 10 — Unattended production test` — is closed as completed.

## Feature-freeze rule
The build remains frozen. Do not add features, expand scope, or tune editorial behavior without evidence. Future changes require one of:
1. a concrete production defect;
2. a reliability or safety failure;
3. a measurable commercial bottleneck; or
4. evidence-backed improvement that can be evaluated against the production baseline.

Operating sequence:

`BUILD → SHIP → MEASURE → LEARN → IMPROVE`

## Current business position
**BUILD → PROVE CONTENT → BUILD AUDIENCE → MONETIZE → SCALE**

Build is complete. Controlled unattended content production, affiliate validation, site health validation, and the 5/day operating target are operational. The business question is now whether TechSignal can attract real buyer-intent visitors and convert that attention into affiliate revenue.

## Affiliate controls
`products.json` is the commercial source of truth. The current Amazon UK tracking ID is `echsignalnews-21`. Affiliate insertion accepts only exact catalogue products and Amazon UK URLs, and publication validation records the marketplace, tracking ID, selected products, exact matches, and validation result.

Search-based affiliate links are disabled. Catalogue mismatches block publication.

## Stage 4 measurement
`MONETIZATION.md` defines the commercial measurement model:

`visitor → affiliate click → qualifying purchase → dispatched item → commission`

The key metrics are traffic, affiliate clicks, click-through rate, items ordered, items dispatched, conversion, dispatched-items revenue, earnings, revenue/article, and revenue/1,000 visitors.

No revenue, conversion or traffic result is considered valid until it comes from external reporting data.

## Search performance intelligence
`metrics_collector.py` now supports page-level Google Search Console Search Analytics collection. When valid GSC credentials are available, the scheduled measurement job records a durable `data/search_performance.json` snapshot containing the measurement period, aggregate clicks/impressions/CTR, and per-page clicks/impressions/CTR/average position ranked by clicks. This creates the evidence layer needed to distinguish traffic winners and weak pages without changing publishing behavior.

The implementation is instrumentation only: it does not infer traffic or revenue when GSC is unavailable and does not alter the production target based on unverified data.

## Current measured state
The latest persisted scaling state records:
- `current_target=5`
- `recommended_target=5`
- `published_posts=35`
- `gsc_available=false`
- `index_rate=0.0`
- `affiliate_click_rate=0.0`
- `traffic_7d_change=0.0`

These zeros are treated as **missing external evidence**, not as proof of zero commercial performance. The next measurement cycle must obtain authoritative Search Console/analytics and Amazon reporting data before commercial conclusions are made.

## Operating model
1. Keep the verified production system running at the 5/day target.
2. Collect external discovery/indexing and traffic evidence.
3. Collect Amazon Associates click/order/dispatched-item/earnings evidence.
4. Rank articles and topic clusters by commercial performance.
5. Improve only the largest measurable bottleneck.
6. Increase volume only after a winning commercial signal is proven.

## External discovery verification - 2026-09-07
A public discovery spot-check was executed against the live TechSignal site. The live robots.txt returns HTTP 200 and explicitly references the WordPress sitemap; the sitemap returns HTTP 200 and currently contains 36 post URLs, including the three September 7 posts. Public search queries for the live TechSignal domain returned no indexed results in the checked window. This is **not** treated as proof of deindexing or zero traffic; it is evidence that external indexing remains unproven and should remain the primary acquisition bottleneck until Search Console/Bing reporting confirms otherwise.

## External actions / evidence pending
- Google Search Console ownership verification and sitemap submission — COMPLETED (user-confirmed 2026-09-05)
- Bing Webmaster ownership verification and sitemap submission — COMPLETED (user-confirmed 2026-09-05)
- Search Console/indexing performance evidence — PENDING
- Analytics visitor data, if used — PENDING
- Amazon Associates reporting access/data for revenue proof — PENDING
- AwardSpace deployment/configuration verification if the migration remains the intended production target — PENDING
- Additional Amazon tracking IDs — NOT NEEDED for the first validation period

These are account-level evidence items, not code defects.

## Next business milestone
Prove the first measurable commercial chain:

`real visitor → affiliate click → qualifying purchase → dispatched item → commission`

Until that chain occurs, remain in monetization validation and keep the production target at 5/day.
