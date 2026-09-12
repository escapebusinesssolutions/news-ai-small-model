# TechSignal Video Generator — Port Architecture

**Purpose of this document:** directive for GPT (executor) describing how to port a copy of the Large Model's video-generation capability into the Small Model (TechSignal) repo, as a new independent module — not a shared/live dependency.

**Governing principle:** this is a **copy, not a link**. The Large Model's own video generator instance stays untouched, in place, and continues serving the Large Model only. TechSignal gets its own independent fork of the relevant components, free to diverge.

---

## 1. Scope decision — what gets copied vs. left behind

The Large Model's video pipeline (M4/M4.5) solves two separate problems bundled together:

1. **Generic video production mechanics** — TTS narration, compositing/assembly, QC gating pattern, publishing to YouTube/WordPress. **This is reusable.**
2. **News-story semantic matching** — figuring out what an arbitrary, never-seen-before news story is "about" and finding/validating relevant visual assets for it (the reusable-media-library tagging system, the exoskeleton-reuse bug and its fix). **This does NOT transfer.** TechSignal doesn't have this problem — it already knows the exact product, and already has product images/specs in hand. Do not port this subsystem. Porting it would import unneeded complexity and the exact failure modes already fought through on the Large Model side.

**Rule for GPT:** if a piece of code exists specifically to answer "what is this story about and what visual matches it," it is out of scope. If a piece of code exists to answer "turn this known script + known assets into a finished video," it is in scope.

---

## 2. Components to port (in scope)

| Component | Source (Large Model) | Action |
|---|---|---|
| TTS narration generation | M4.5 audio step | Copy as-is into `small-model/video/tts.py` (or equivalent). Minimal changes expected. |
| Video compositing/assembly (FFmpeg-based timeline, text/graphic overlay, segment stitching) | M4.5 compositor | Copy core assembly functions. Strip any logic that selects assets from the reusable-media-library — TechSignal will supply assets directly (product images already in the product catalogue). |
| QC gate pattern (structural idea: automated pass/fail checks before publish) | M4.5 visual QC | Copy the *pattern*, not the specific checks. New checks defined in Section 4. |
| YouTube upload plumbing | M5 | Copy as-is. Swap credentials/destination channel (see Section 5). |
| WordPress video-embed publishing | M6/M7 publisher | Copy as-is. Swap destination site ID to TechSignal's (`257062637`, `techsignal.wasmer.app`) — never the Large Model's `51900195`. |

---

## 3. New components needed (not a port — build fresh, but small)

### 3.1 Input adapter: product brief → video script
TechSignal's existing article-generation pipeline already produces enriched product data (`detailed_specs`, `differentiators`, `known_limitations`, `who_its_for`, `who_should_skip`) and article copy. Build a new, small transformer that takes this existing data and produces a short video script with a simple arc:
- Hook (what is this / why care in one line)
- Key differentiator (pulled from `differentiators`)
- Who it's for / who should skip (pulled from existing fields)
- Verdict (reuse the article's verdict — do not regenerate separately, to keep article and video consistent)

This does **not** need the Large Model's news-narrative arc logic (hook/context/what-happened/why-it-matters/what's-next) — that structure is built for breaking news, not product review. Use the simpler arc above instead.

### 3.2 Asset supply
Since TechSignal already has product images as part of its product catalogue, no "asset discovery/matching" step is needed. The video assembler should simply be given: (a) the product image(s) already on file, (b) the generated script, (c) spec/price data. This directly replaces the Large Model's reusable-media-library lookup — TechSignal's product catalogue *is* its asset library, already tagged by definition (each image belongs to a known product).

### 3.3 New QC gate (TechSignal-specific)
Do not reuse the Large Model's checks (distinct visual sources, no cross-story asset reuse — irrelevant here). Define new, simpler checks:
- Does the video actually display the correct product image(s) for this product?
- Does the audio track exist and match expected duration (no silent/failed TTS)?
- Does on-screen text match the actual current price/spec data (avoid publishing stale pricing)?
- Reject and flag for regeneration — do not silently publish — on any failure, consistent with the Large Model's "stop rather than fabricate success" principle.

---

## 4. Destinations and credentials (must be fully separate from Large Model)

- **YouTube:** new/dedicated TechSignal channel (or the Evolution channel, if the operator confirms the handoff — pending decision, do not assume). Must NOT reuse the Large Model's YouTube credentials/channel.
- **WordPress:** `techsignal.wasmer.app`, site ID `257062637`. Must NOT publish to `escapebusinesssolutions.com` (`51900195`).
- **Social distribution:** feeds into TechSignal's existing dedicated X/Facebook accounts (separate from EBS's own accounts), consistent with the current distribution-automation plan.

---

## 5. Governance — deliberately lighter than the Large Model's

The Large Model's process (one-writer-at-a-time, protected branches, phased commit/CI/independent-confirmation loop, human-reviewed PRs for anything touching the live repo) exists because that system is large, production-critical, and slow-moving by design. TechSignal's video module should **not** inherit this overhead:

- Standard repo practices apply (don't break `main`, don't lose work), but the heavy phased-gate ceremony is not required for this module.
- Fast iteration is the priority — this is a small, disposable-if-it-doesn't-work module, not core infrastructure.
- Zero-cost constraint still applies: no paid APIs, no paid GitHub-hosted runners, free-tier/local resources only, same as both existing projects.

---

## 6. Suggested build sequence

1. Copy TTS + compositing + publishing code into `small-model/video/` as a new module, disconnected from the Large Model's live code path.
2. Strip out reusable-media-library / semantic-matching logic entirely — confirm it's gone, not just unused.
3. Build the input adapter (Section 3.1) using 2-3 existing TechSignal product briefs as test cases.
4. Wire in product images directly (Section 3.2) — no asset-matching step.
5. Implement the new QC gate (Section 3.3).
6. Point publishing at TechSignal's own YouTube/WordPress destinations (Section 4) — confirm credentials are separate from the Large Model's before any test upload.
7. Run end-to-end on 2-3 existing products; manually review output quality before considering any further automation of the review step itself.
8. Report back with: what ported cleanly, what needed rework, actual time spent, and sample output for review — evidence-based, not a status claim.

---

## 7. Explicit non-goals for this port

- Do not port or replicate the Large Model's story-relevance/semantic-asset-matching system.
- Do not use the Large Model's "business-leader-watchable" corporate quality bar — TechSignal's bar is fast, consumer-facing, product-showcase content, not corporate credibility content.
- Do not touch, modify, or share credentials/state with the Large Model's live video pipeline.
- Do not adopt the Large Model's full governance ceremony for this module.
