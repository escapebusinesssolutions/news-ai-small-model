# Small Model Validation Report

**Date:** 2026-08-31
**Test:** Catalogue-backed USB microphone article
**Repository:** `escapebusinesssolutions/news-ai-small-model`
**Topic index:** 13
**WordPress:** `https://techsignalnews.wordpress.com/`
**WordPress post:** #9
**Expected status:** Draft

## Executive result

**PASS — end-to-end catalogue-backed article generation and WordPress draft creation are proven.**

The GitHub Actions test completed successfully. The generated article was submitted to WordPress and WordPress returned post ID 9 with draft status.

## Checks

| Check | Result | Evidence / note |
|---|---|---|
| Topic selected | PASS | `Best USB Microphones Under $100` |
| AI generation | PASS | Article generation step completed successfully |
| Product catalogue loaded | PASS | `products.json` contains curated Amazon UK products |
| Relevant microphone products available | PASS | Samson Q2U and RØDE NT-USB Mini are in catalogue |
| Affiliate configuration | PASS | Marketplace `amazon.co.uk`; tracking ID `techsignal-20` |
| Affiliate processing | PASS | Article passed through affiliate insertion stage |
| WordPress authentication | PASS | Existing username + application-password route worked |
| WordPress draft creation | PASS | Post ID `9`, status `draft` |
| Cross-linking capability | PASS | Cross-linking stage exists; useful links depend on existing public articles |
| Public publishing | NOT TESTED | Correctly kept as draft |
| Exact final affiliate URLs | NOT PROVEN IN THIS RUN | Workflow did not preserve generated article as an artifact, so final HTML could not be independently inspected |

## WordPress result

Title: **Best USB Microphones Under $100: A Practical Buyer’s Guide**

Post ID: **9**

Status: **Draft**

Slug: `best-usb-microphones-under-100`

## Product catalogue

Current catalogue contains 8 products covering audio, webcams, storage, workspace/control and portable power. The catalogue stores Amazon UK destinations, product identifiers, use cases and factual key points.

## Important limitation

This report does not claim that the final WordPress HTML was independently inspected for every inserted affiliate URL. The pipeline and WordPress creation passed, but the test workflow produced no downloadable artifact containing the final article body.

## Next hardening action

The authoritative publisher workflow should emit a machine-readable validation record containing:

- products selected;
- exact outbound URLs inserted;
- confirmation that each Amazon URL contains `techsignal-20`;
- internal links inserted;
- WordPress post ID and status.

This should become a required quality gate before public publishing is enabled.
