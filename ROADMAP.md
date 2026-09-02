# Small Model Roadmap

## Objective
Build the smallest useful autonomous affiliate-content machine and test whether it can produce revenue.

## Business sequence
- [x] STAGE 1 — BUILD
- [x] STAGE 2 — PROVE THE CONTENT
- [ ] STAGE 3 — BUILD AN AUDIENCE
- [ ] STAGE 4 — MONETIZE
- [ ] STAGE 5 — SCALE

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
- [ ] STEP 11 — Unattended production test / controlled production operation

## Stage 5 scale gates
- Audience signal exists.
- Affiliate-click signal exists.
- Revenue signal exists before aggressive scaling.
- Winning topic cluster identified from external performance data.
- Production quality remains stable as volume increases.

## Stage 5 operating rule
Scale winning intent, not article count. Increase output in bounded increments and only expand into new clusters when existing evidence justifies it.

## Release targets
- v0.1.0 — First working machine: code complete
- v0.2.0 — Automated GitHub Actions execution: ready
- v0.3.0 — Cross-linking included: complete
- v1.0.0 — Validation release: after commercial measurement period

## Operating rule
Build only what is required to prove the commercial loop. Do not recreate the large news system.

## Current gate
Stage 3 remains the immediate operating gate: establish real discovery and traffic. Stage 4 measurement is prepared. Stage 5 scaling is designed but must not be activated merely because the pipeline can publish more pages.
