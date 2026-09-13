# TechSignal Consumer Video Asset Strategy

**Status:** ACTIVE  
**Date:** 2026-09-13

## Objective

Give TechSignal a repeatable library of real, product-specific visual assets so consumer videos are visually about the products being evaluated rather than mostly animated information cards.

## Asset hierarchy

### Tier 1 — exact product media
Preferred for most of the runtime:
- exact product photography;
- exact product close-ups/details;
- exact product-in-use footage;
- multiple angles of the exact model;
- ports, controls, connectors and physical features that correspond to the narration.

### Tier 2 — buyer-context media
Use where it genuinely illustrates the purchase decision:
- product installed in the intended workspace;
- microphone on a desk during recording;
- webcam positioned for a call;
- SSD connected to a laptop;
- controller used in the relevant workflow.

The visual must not imply that TechSignal performed the depicted activity unless that is actually true.

### Tier 3 — decision-support graphics
Use for information that a photograph cannot communicate well:
- concise specification callouts;
- comparison matrices;
- trade-off indicators;
- compatibility/fit diagrams when factually supported;
- buyer decision frameworks;
- final verdict/CTA.

### Tier 4 — generic context
Use sparingly. Generic technology imagery must never substitute for exact-product coverage.

## Rights-first acquisition

The default low-cost acquisition source is Wikimedia Commons where an exact product asset exists under a commercially usable licence. Each asset must be individually checked; category membership alone is not a rights clearance.

The manifest must record:
- product identifier;
- asset identifier;
- local path;
- source URL;
- exact licence;
- rights-check status;
- commercial-reuse check;
- attribution requirements;
- creator/author;
- whether the asset depicts the exact product model;
- optional notes about visible branding or third-party people/property.

Do not automatically use manufacturer images merely because they are publicly accessible. Public availability is not equivalent to commercial reuse permission.

## Initial researched candidates

The following candidates were identified during the 2026-09-13 offline-quality pass:

- **Logitech C920:** `Webcam 01.jpg` on Wikimedia Commons. The page identifies it as a Logitech C920 and states CC0 1.0. This is already the repository's exact C920 asset. citeturn1view2
- **Røde NT-USB Mini:** `Rode NT-USB Mini microphone 001.jpg`, plus two additional images in the same Commons category. The specific image is an exact Røde NT-USB Mini and is licensed CC BY-SA 4.0. citeturn1view1turn0search1
- **Shure MV7:** `Shure MV7 microphone.jpg`, an exact Shure MV7 photograph licensed CC BY 2.0. citeturn2search0
- **Samsung T7 family:** Commons contains T7 Shield imagery, including multiple product views, but these are not automatically interchangeable with the catalogue's Samsung T7 Portable SSD 2TB. Exact-model matching remains mandatory. A T7 Shield image must not be silently substituted for the T7 2TB. citeturn1view0turn0search10

These are **research candidates, not yet integrated assets**. The local asset files, metadata and exact-product checks must be added and tested before they can satisfy the production gate.

## Library construction rule

For every product selected for video, target at least:

- 1 hero image;
- 1 alternate angle/detail image;
- 1 use/context image or short product clip where legally available;
- 1 optional specification/detail visual;
- 1 optional comparison visual for multi-product content.

A single image may be cropped/reframed for different editorial purposes, but repeated use does not increase the distinct-asset count and cannot be used to satisfy the quality gate.

## Cost rule

Use free/licensed sources and existing infrastructure first. Do not introduce a paid stock-media subscription, new video SaaS, or recurring asset service solely to solve the library problem unless later commercial evidence demonstrates that the asset bottleneck justifies the cost.

## Production consequence

The asset library is now a production dependency for unattended consumer video. If the required product-specific media is unavailable, the correct result is to hold/reject the video rather than fill the runtime with generic animated cards.

## Next implementation step

When the Windows execution machine is available:

1. acquire and locally store the cleared candidate assets;
2. extend `product_assets.json` to support multiple assets per product;
3. make V15 select product media according to scene purpose and avoid unapproved repeats;
4. make V16 render product media as the dominant visual layer;
5. retain original graphics for genuine decision-support scenes;
6. run the new V11 product-visual coverage gate;
7. perform manual visual review of the resulting MP4s;
8. only then consider the TechSignal video layer production-ready.
