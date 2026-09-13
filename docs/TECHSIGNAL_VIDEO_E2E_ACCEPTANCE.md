# TechSignal Video E2E Acceptance Test

**Status:** ACTIVE  
**Date:** 2026-09-13

## Purpose

Prevent a technically successful render from being mistaken for production-quality consumer video.

## Required E2E run

The proof batch must cover three different buyer-intent articles/products. For each case:

1. Generate the article using the normal Small Model path.
2. Derive `techsignal-video-brief-v2` from the finished article and selected product data.
3. Resolve product-specific assets through the TechSignal asset manifest.
4. Render the 12-scene consumer sequence.
5. Run V11 technical and consumer QC.
6. Inspect the final MP4 manually.
7. Store the article, brief, selector manifest, MP4 and QC record as proof artifacts.
8. Do not publish to WordPress or YouTube during acceptance.

## Mandatory automated gates

Every case must pass:

- video exists and is playable;
- expected duration is non-zero;
- at least 10 meaningful visual changes;
- no black-frame interval;
- no prohibited long static hold;
- audio preflight passes;
- rights metadata passes;
- no unapproved asset repetition;
- consumer narrative arc passes;
- exact product identity passes;
- **product-specific visual coverage >= 60%**;
- **at least 3 distinct product-specific visual assets**;
- every selected product is represented by identifiable product media in multi-product content;
- source/asset density passes.

## Manual acceptance

A human reviewer must answer YES to all of the following:

1. Within the first few seconds, is it obvious which exact product is being discussed?
2. Does the video show the actual product rather than merely naming it?
3. Do the visuals change when the buyer question changes?
4. Do feature/spec scenes show the relevant physical feature or otherwise provide meaningful product-specific evidence?
5. Are product-in-use visuals credible and not presented as TechSignal's own testing when they are not?
6. Are trade-offs visually understandable?
7. In a comparison, can the viewer distinguish the products visually?
8. Is the video predominantly substantive product media rather than dark/abstract slides?
9. Does any graphic exist because it communicates information that imagery alone cannot?
10. Does the final verdict visually return to the actual product?
11. Would this video be useful to a consumer deciding whether to buy?
12. Does it look like a consumer technology video rather than an article pasted into a slideshow?

Any NO is a production-quality rejection until corrected.

## Failure policy

A failed video must not be distributed merely because the article itself is valid. Video failure is isolated from article publication.

If insufficient licensed product media exists, the run should fail honestly and report the missing asset requirement. It must not compensate by generating additional abstract slides.

## Acceptance result

The batch is accepted only when all three cases:

- pass automated QC;
- pass manual visual review;
- contain sufficient product-specific visual coverage;
- contain no unsupported product experience/testing claims;
- preserve the article's product selection and verdict;
- remain unpublished during proof.

Only after this batch is green may the dedicated TechSignal YouTube distribution path be considered for a controlled private/unlisted publication test.
