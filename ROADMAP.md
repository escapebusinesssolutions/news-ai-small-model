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

See `OPTIMIZATION.md` for the Stage 6 operating plan.

## Release targets
- v0.1.0 — First working machine: code complete
- v0.2.0 — Automated GitHub Actions execution: ready
- v0.3.0 — Cross-linking included: complete
- v1.0.0 — Validation release: after commercial measurement period

## Operating rule
Build only what is required to prove the commercial loop. Do not recreate the large news system.

## Current gate
Stage 3 remains the immediate operating gate: establish real discovery and traffic. Stage 4 measurement is prepared. Stage 5 scaling is designed but must not be activated merely because the pipeline can publish more pages. Stage 6 is now defined but cannot be meaningfully activated until sufficient external performance data exists.
