# Current Status

**Project:** NEWS AI SMALL MODEL  
**Date:** 2026-08-31  
**Current phase:** Phase 01 — Build / Validation

## Dashboard
| Step | Status |
|---|---|
| Scope frozen | DONE |
| Extract proven components | DONE |
| Repository structure | DONE |
| Topic queue | DONE — aligned to curated catalogue |
| Generate | DONE — catalogue-informed product brief and decision-support prompt |
| Affiliate links | DONE — catalogue is authoritative; exact links validated |
| WordPress publish | CODE DONE — live site test pending external credentials/site |
| Cross-linking | DONE — lightweight topic/category matching |
| End-to-end pipeline | DONE — Generate → affiliate links → cross-link → validation → WordPress |
| Testing | DONE — full GitHub Actions suite green |
| GitHub Actions | DONE — daily scheduled workflow plus manual dispatch |
| Unattended run | READY — intentionally held at draft until first 10–15 articles are spot-checked |
| Commercial measurement | READY — Search Console, Amazon Associates and Pinterest measurement plan documented |

## Current release
**Pre-v0.1.0** — code complete for the validation loop; external account/site setup remains.

## Source of truth
GitHub is the implementation source of truth. Notion holds the strategy and architecture.

## Completed build loop
`pipeline.py` now runs:

`topic → Generate → catalogue affiliate links → cross-link → pre-publish validation → WordPress`

The validation report records the exact products, IDs, affiliate URLs, tracking tag, link type, and validation result. Publication is blocked when affiliate validation fails.

## Catalogue authority
Stage 1 receives a product brief derived from `products.json`. Stage 2 may resolve only products present in that catalogue and may insert only the catalogue-approved Amazon URL with the configured tracking tag. Search-based affiliate links are not used.

## Automation
GitHub-hosted runners are used. The daily workflow selects one of the 15 catalogue-supported topics at 06:17 UTC. `WORDPRESS_DEFAULT_STATUS` controls the rollout: keep it `draft` for the first 10–15 articles, then change it to `publish` after human spot-check acceptance.

## External blockers
The remaining actions require accounts or credentials that cannot safely be created by repository automation:

- separate domain and brand
- separate hosting/WordPress installation
- Amazon Associates account/application
- OpenRouter API credential
- WordPress API credential
- Google Search Console setup
- Pinterest business account
- email provider account
- final keyword-volume/competition checks using an appropriate free keyword tool

These are business/setup prerequisites, not unresolved code defects.

## Next action
Configure the external accounts and credentials, then run the first 10–15 articles as drafts, inspect them, and only then switch unattended WordPress status to `publish`.
