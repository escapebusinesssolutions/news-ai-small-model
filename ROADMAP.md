# Small Model Roadmap

## Objective
Build the smallest useful autonomous affiliate-content machine and test whether it can produce revenue.

## Business sequence
- [x] STAGE 1 — BUILD
- [x] STAGE 2 — PROVE THE CONTENT
- [ ] STAGE 3 — BUILD AN AUDIENCE
- [ ] STAGE 4 — MONETIZE
- [ ] STAGE 5 — SCALE
- [ ] STAGE 6 — OPTIMIZE
- [ ] STAGE 7 — EXPAND
- [ ] STAGE 8 — AUTOMATE
- [ ] STAGE 9 — DEFENSIBILITY
- [ ] STAGE 10 — BUSINESS SCALE

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

## Stage 6 optimization gates
- Enough traffic and affiliate data exists to distinguish signal from noise.
- At least one meaningful funnel bottleneck can be identified.
- Commercially relevant winners can be separated from traffic-only winners.
- Optimization changes can be measured against a defined baseline.
- Quality, factual grounding, and affiliate validation remain intact.

## Stage 6 operating rule
Optimize the commercial system before increasing complexity. Fix the largest measurable bottleneck first, make small attributable changes, and keep authoritative commercial reporting as the source of truth.

## Stage 6 work plan
1. Diagnose the funnel: demand → traffic → affiliate click → purchase → earnings.
2. Identify winning articles, products, topic clusters, and traffic sources.
3. Improve existing winners before producing large numbers of new pages.
4. Run bounded content, structure, internal-link, and commercial-placement experiments.
5. Measure economic impact, not vanity metrics alone.
6. Stop changes that reduce usefulness, factual quality, or commercial efficiency.
7. Feed proven winners back into Stage 5 scaling decisions.

## Stage 7 expansion gates
- A repeatable commercial winner exists.
- The expansion serves a related buyer decision or deliberately selected new market.
- Product/evidence and measurement are available.
- Initial volume is bounded and success/kill criteria are defined.

See `EXPANSION.md`.

## Stage 8 automation gates
- The decision is repeatable and evidence-backed.
- Explicit production limits exist.
- Existing validation controls cannot be bypassed.
- Human approval remains for new markets, revenue sources, major category changes, material spend, and brand/legal decisions.

See `AUTOMATION.md`.

## Stage 9 defensibility gates
- An economically valuable area is proven before moat investment.
- Historical performance data is retained.
- Editorial provenance and first-hand evidence remain honest.
- First-party audience relationships are pursued where useful.

See `DEFENSIBILITY.md`.

## Stage 10 business-scale gates
- Traffic and commercial conversion are repeatable.
- Unit economics are measurable.
- Quality remains stable as volume increases.
- Additional resources have a credible path to incremental profit.

See `BUSINESS_SCALE.md`.

## Release targets
- v0.1.0 — First working machine: code complete
- v0.2.0 — Automated GitHub Actions execution: ready
- v0.3.0 — Cross-linking included: complete
- v1.0.0 — Validation release: after commercial measurement period

## Operating rule
Build only what is required to prove the commercial loop. Do not recreate the large news system.

## Current gate
Stage 3 remains the immediate operating gate: establish real discovery and traffic. Stage 4 measurement is prepared. Stages 5-10 are defined as controlled business stages, but none should be activated merely because the pipeline can produce more pages. External performance evidence must determine when each stage becomes active.
