# Current Status

**Project:** NEWS AI SMALL MODEL  
**Date:** 2026-08-31  
**Current phase:** Phase 01 â€” Build

## Dashboard
| Step | Status |
|---|---|
| Scope frozen | DONE |
| Extract proven components | DONE |
| Repository structure | DONE |
| Topic queue | DONE |
| Generate | DONE â€” implementation complete; live provider test pending credentials |
| Affiliate links | DONE â€” catalogue adapter ready |
| WordPress publish | DONE â€” publisher wired; live site test pending workflow execution |
| Cross-linking | DONE â€” lightweight topic/category matching |
| End-to-end pipeline | NEXT |
| Testing | TODO |
| GitHub Actions | SCAFFOLD READY |
| Unattended run | TODO |

## Current release
**Pre-v0.1.0** â€” build in progress.

## Source of truth
GitHub is the implementation source of truth. Notion holds the strategy and architecture.

## Current step
STEP 7 â€” Lightweight cross-linking complete.

## Cross-linking
`cross_link.py` ranks existing article records using simple title/topic word overlap plus category matching. It adds up to three unique internal links, skips the current article, and does nothing when there is no suitable match. It uses no additional AI call or database.

## Next action
Build the end-to-end pipeline connecting topic selection â†’ generation â†’ affiliate links â†’ cross-linking â†’ WordPress publication.

