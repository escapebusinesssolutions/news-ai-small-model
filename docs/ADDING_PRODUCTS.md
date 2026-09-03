# Adding Amazon UK Products

The Small Model currently uses a manually maintained Amazon UK catalogue because programmatic product discovery is not yet available to this Associates account.

## 1. Create an Amazon affiliate link

Sign in to Amazon.co.uk with the Amazon account associated with Associates, open the specific product page, and use Associates SiteStripe → Get Link. SiteStripe can generate a link with the selected Associate ID/tracking ID already included.

## 2. Add the product

Edit `products.json` and add an entry:

```json
{
  "name": "Example Product",
  "category": "keyboards",
  "url": "https://www.amazon.co.uk/dp/EXAMPLE/ref=nosim?tag=echsignalnews-21",
  "asin": "EXAMPLE"
}
```

The catalogue root must remain:

```json
{
  "marketplace": "amazon.co.uk",
  "tracking_id": "echsignalnews-21",
  "products": []
}
```

## 3. Optional enrichment fields (recommended)

`generate.py` passes these through to the model when present, in addition to `key_points`. They give the writer concrete material for specific buyer reasoning instead of generic filler.

```json
{
  "detailed_specs": ["exact published specifications"],
  "differentiators": ["what separates the product from alternatives in the catalogue"],
  "known_limitations": ["genuine buyer trade-offs"],
  "who_its_for": ["specific buyer scenarios"],
  "who_should_skip": ["specific buyer scenarios to avoid"]
}
```

Only add facts verified from the manufacturer or another authoritative source. Do not guess, copy review text verbatim, or add unsupported specifications. If a fact cannot be verified, leave it out.

## 4. Rules

- Use Amazon.co.uk product URLs only.
- Use the configured tracking ID `echsignalnews-21`.
- Use links to the specific product detail page.
- Do not put Amazon API credentials in this file.
- Do not add prices, ratings, images, or other Amazon product data manually unless the applicable Associates rules permit the use.

Amazon documents the basic Amazon.co.uk product-link format as `/dp/ASIN/...?...tag=YOURASSOCIATEID` and recommends its Associates linking tools for correctly formatted links.

## 5. Why this is temporary

When Creators API/PA API access becomes available, this catalogue adapter can be replaced with an Amazon API adapter. Amazon's current policy requires an account identifier/key pair plus an Associates tag for API calls.

## 6. Verify a link

Amazon provides a Link Checker for links constructed or modified outside Associates Central. Links generated directly by Associates Central/SiteStripe are already coded by Amazon's tools.
