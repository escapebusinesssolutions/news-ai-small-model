# Stage 4 — Monetization

## Objective
Prove that TechSignal can turn buyer-intent traffic into measurable Amazon affiliate revenue.

## Current commercial setup
- Marketplace: Amazon UK
- Tracking ID: `echsignalnews-21`
- Affiliate links: direct product links only
- Product source: `products.json`
- Link generation: `insert_links.py`
- Search affiliate links: disabled
- Catalogue mismatches: publication-blocking validation failure

The repository already records the affiliate marketplace, tracking ID, selected products, exact catalogue matches, link count, and validation result in the validation report.

## Metrics

### Traffic
- Visitors
- Search impressions
- Search clicks
- Referral source

### Commercial intent
- Amazon affiliate clicks
- Affiliate click-through rate
- Clicks per article
- Clicks per 1,000 visitors

### Revenue
- Items ordered
- Items dispatched
- Conversion rate
- Dispatched-items revenue
- Referral fees / earnings
- Revenue per article
- Revenue per 1,000 visitors

Amazon defines conversion as dispatched items divided by affiliate clicks. Its Associates reporting also provides tracking-ID-level clicks, orders, dispatched items, revenue and earnings.

## Operating model
1. Publish buyer-intent content.
2. Acquire real visitors.
3. Measure affiliate clicks.
4. Compare commercial intent by topic and article.
5. Import Amazon reporting data when available.
6. Rank topics by clicks, conversion and earnings.
7. Expand winning topics; stop weak topics.

## Stage 4 success gate
Stage 4 is not considered proven by traffic or clicks alone.

The minimum proof is:

`real visitor → affiliate click → qualifying purchase → dispatched item → commission`

Until that chain occurs, the project remains in monetization validation.

## What can be automated now
- Enforce catalogue-only affiliate links.
- Validate Amazon UK URLs and tracking tags before publication.
- Record affiliate metadata in validation artifacts.
- Keep product selection aligned with buyer-intent topics.
- Produce repeatable commercial metrics once traffic/report data exists.

## What requires external account data
- Amazon Associates reporting data
- Search Console performance data
- Analytics visitor data, if used
- Creation of additional Amazon tracking IDs

Do not fabricate revenue, conversion or traffic metrics when external reporting data is unavailable.

## Tracking-ID strategy
The current single tracking ID is sufficient for the first validation period. Amazon supports multiple tracking IDs for analysing different sites or merchandising strategies. Additional IDs should only be introduced when there is enough traffic to justify the segmentation and after they are created in Associates Central.

## Decision rules
- High traffic + low affiliate clicks: improve commercial relevance and calls to action.
- Low traffic + high click rate: improve distribution/search acquisition before changing the content model.
- High clicks + low conversion: investigate product choice and buyer fit.
- High conversion + low traffic: increase coverage around the same intent.
- Sustained earnings: move the winning topic cluster toward Stage 5 scaling.
