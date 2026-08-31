# Adding Amazon UK Products

The Small Model currently uses a manually maintained Amazon UK catalogue because programmatic product discovery is not yet available to this Associates account.

## 1. Create an Amazon affiliate link

Sign in to Amazon.co.uk with the Amazon account associated with Associates, open the specific product page, and use Associates SiteStripe → Get Link. Amazon says SiteStripe includes the Associate ID/tracking ID in generated links. citeturn0search0

## 2. Add the product

Edit `products.json` and add an entry:

```json
{
  "name": "Example Product",
  "category": "keyboards",
  "url": "https://www.amazon.co.uk/dp/EXAMPLE/ref=nosim?tag=techsignal-20",
  "asin": "EXAMPLE"
}
```

The catalogue root must remain:

```json
{
  "marketplace": "amazon.co.uk",
  "tracking_id": "techsignal-20",
  "products": []
}
```

## 3. Rules

- Use Amazon.co.uk product URLs only.
- Use the configured tracking ID `techsignal-20`.
- Use links to the specific product detail page.
- Do not put Amazon API credentials in this file.
- Do not add prices, ratings, images, or other Amazon product data manually unless the applicable Associates rules permit the use.

Amazon documents the basic Amazon.co.uk product-link format as `/dp/ASIN/... ?tag=YOURASSOCIATEID` and recommends its Associates linking tools for correctly formatted links. citeturn0search4turn0search3

## 4. Why this is temporary

When Creators API/PA API access becomes available, this catalogue adapter can be replaced with an Amazon API adapter. Amazon's current policy requires an account identifier/key pair plus an Associates tag for API calls. citeturn0search14

## 5. Verify a link

Amazon provides a Link Checker for links constructed or modified outside Associates Central. Amazon notes that links generated directly by Associates Central/SiteStripe are already coded and are not checked by that tool. citeturn0search6turn0search9
