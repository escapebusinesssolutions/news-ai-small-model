# Small Model Roadmap

## Objective
Build the smallest useful autonomous affiliate-content machine and test whether it can produce revenue.

## Build sequence
- [x] STEP 0 — Scope frozen
- [x] STEP 1 — Extract proven components
- [x] STEP 2 — Build repository structure
- [x] STEP 3 — Build topic queue
- [x] STEP 4 — Build GENERATE
- [x] STEP 5 — Build affiliate link insertion
- [x] STEP 6 — Build WordPress publishing
- [x] STEP 7 — Build lightweight cross-linking
- [x] STEP 8 — End-to-end pipeline: Generate → affiliate links → cross-link → validation → WordPress publisher
- [x] STEP 9 — Automated test suite and WordPress integration path
- [x] STEP 10 — GitHub Actions automation
- [ ] STEP 11 — Unattended production test: blocked only by external account/site credentials and first-batch human approval

## Release targets
- v0.1.0 — First working machine: code complete
- v0.2.0 — Automated GitHub Actions execution: ready
- v0.3.0 — Cross-linking included: complete
- v1.0.0 — Validation release: after first commercial batch and four-week measurement

## Operating rule
Build only what is required to prove the commercial loop. Do not recreate the large news system.

## Current gate
Do not switch `WORDPRESS_DEFAULT_STATUS` from `draft` to `publish` until the first 10–15 articles have been generated, published as drafts, and human spot-checked.
