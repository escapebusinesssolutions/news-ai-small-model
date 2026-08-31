# Current Status

**Project:** NEWS AI SMALL MODEL  
**Date:** 2026-08-31  
**Current phase:** Phase 01 — Build

## Dashboard
| Step | Status |
|---|---|
| Scope frozen | DONE |
| Extract proven components | DONE |
| Repository structure | DONE |
| Topic queue | DONE |
| Generate | DONE — live provider test pending credentials |
| Affiliate links | DONE — catalogue adapter ready |
| WordPress publish | DONE — publisher wired; live site connection pending credentials/site |
| Cross-linking | NEXT |
| End-to-end pipeline | TODO |
| Testing | TODO |
| GitHub Actions | SCAFFOLD READY |
| Unattended run | TODO |

## Current release
**Pre-v0.1.0** — build in progress.

## Source of truth
GitHub is the implementation source of truth. Notion holds the strategy and architecture.

## Current step
STEP 6 — WordPress publishing implementation complete.

## WordPress publishing
`publish.py` now converts the generated article into WordPress-ready HTML and calls the proven `reused/wordpress_publisher.py` module. The publisher defaults to safe draft mode and only publishes when `WORDPRESS_PUBLISH_ENABLED=true` and a valid access token is supplied.

Required runtime settings:
- `WORDPRESS_SITE_ID`
- `WORDPRESS_ACCESS_TOKEN`
- `WORDPRESS_PUBLISH_ENABLED`
- optional `WORDPRESS_DEFAULT_STATUS`

No WordPress credentials are stored in the repository.

## Live connection status
The code is ready for a real WordPress.com site, but a live publish test has not been performed because the new WordPress site/address and access token have not yet been supplied. The first live test should remain a draft until verified.

## Next action
Build lightweight cross-linking.
