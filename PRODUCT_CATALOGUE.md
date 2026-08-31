# Product Catalogue

## Purpose

This catalogue is the Small Model's curated product layer. It follows the governing architecture: tech/workspace gear, buyer-intent decision support, preference for products in the £30–£300 band, and original content based on structured product facts rather than competitor-article rewriting.

## What is stored

Each product record contains:

- `name` — canonical product name used for matching generated recommendations.
- `asin_or_id` — Amazon identifier when known.
- `url` — Amazon UK destination.
- `category` — content category.
- `price_range` — planning band, not a live Amazon price.
- `use_cases` — buyer-intent contexts.
- `key_points` — factual product points that can inform the article prompt.

The catalogue deliberately does **not** store live Amazon prices, availability, ratings, review text, or copied Amazon marketing copy. Amazon's current Associates rules restrict displaying price/availability unless served through Amazon's tools or obtained through the permitted API, and product content must be linked to the relevant Amazon page. See the Amazon UK Associates linking requirements before adding such data.

## Current catalogue

The initial catalogue covers:

- Audio: Samson Q2U, RØDE NT-USB Mini, Beyerdynamic DT 770 PRO, Shure MV7
- Webcams: Logitech C920 HD Pro Webcam
- Storage: Samsung T7 Portable SSD 2TB
- Workspace/control: Elgato Stream Deck MK.2
- Power/mobile work: Anker 737 Power Bank

## Selection rule

Do not add a product merely because it is a high-volume Amazon seller. Add it when it gives the site a useful decision-support angle: budget choice, upgrade choice, use-case fit, comparison against another catalogue product, or a clear long-tail search intent.

## Adding a product

1. Confirm the exact Amazon UK product page and ASIN.
2. Confirm the product is relevant to the site's tech/workspace niche.
3. Add factual specifications and use cases from public manufacturer/product documentation.
4. Do not copy competitor review language.
5. Do not add a live price unless the publishing system obtains it through an approved Amazon mechanism.
6. Keep the URL on `amazon.co.uk`.
7. Commit the catalogue change and test affiliate-link insertion.

## Affiliate handling

The catalogue is intentionally separate from the affiliate implementation. `insert_links.py` adds the `techsignal-20` tracking tag. This keeps the Amazon-specific layer replaceable when Creators API is introduced.

The current implementation can fall back to a tagged Amazon UK search link when a generated recommendation has no exact catalogue match. Exact catalogue matches are preferred.
