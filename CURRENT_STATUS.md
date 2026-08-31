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
| Generate | DONE — implementation complete; live provider test pending credentials |
| Affiliate links | DONE — catalogue adapter ready |
| WordPress publish | DONE — publisher wired; live site test pending workflow execution |
| Cross-linking | DONE — lightweight topic/category matching |
| End-to-end pipeline | NEXT |
| Testing | TODO |
| GitHub Actions | SCAFFOLD READY |
| Unattended run | TODO |

## Current release
**Pre-v0.1.0** — build in progress.

## Source of truth
GitHub is the implementation source of truth. Notion holds the strategy and architecture.

## Current step
STEP 7 — Lightweight cross-linking complete.

## Cross-linking
`cross_link.py` ranks existing article records using simple title/topic word overlap plus category matching. It adds up to three unique internal links, skips the current article, and does nothing when there is no suitable match. It uses no additional AI call or database.

## Next action
Build the end-to-end pipeline connecting topic selection → generation → affiliate links → cross-linking → WordPress publication.
