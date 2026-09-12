# TechSignal Video Transplant â€” Implementation Record

Date: 2026-09-12

## Scope

The Large Model video capability was copied into TechSignal as an independent implementation. The Large Model source was not modified or made a runtime dependency.

## Completed steps

1. **Isolated engine area:** `video_engine/large_model_m46_copy/` contains the copied Large Model production machinery; `video_engine/techsignal/` contains the TechSignal adapter.
2. **Copied production machinery:** V15 selector, rights-aware acquisition, V16 compositor, V11 QC and V17 runner were copied. TechSignal does not invoke the Large Model repository at runtime.
3. **TechSignal input contract:** `video_adapter.py` builds `techsignal-video-brief-v1` from existing article/product data.
4. **Consumer asset layer:** `product_assets.json` records product identity, local visual, source URL, rights status, rights check and commercial-reuse check.
5. **Consumer scene layer:** 12 consumer-oriented slots are generated from product facts and buyer guidance.
6. **Narration:** `voice_generator.py` uses Edge TTS locally through the existing free runtime dependency.
7. **Runtime:** FFmpeg/ffprobe are available on the HP execution machine; `edge-tts` is declared in `requirements.txt`.
8. **Real production proof:** Logitech C920 test video rendered successfully to MP4 and passed the complete TechSignal QC runner.
9. **Article independence:** video is an optional `--video` stage and video exceptions are captured without preventing article publication.
10. **Distribution:** automatic YouTube upload is intentionally not enabled. A separate TechSignal YouTube identity/channel and OAuth credentials have not been established in this repo, so no credential or channel assumption is made.

## Real render evidence

- Output: `video_runs/c920-techsignal-v2.mp4`
- Duration: 43.2 seconds
- Video: H.264, 1080x1920, 25 fps
- Audio: AAC, 24 kHz, mono
- Visual slots: 12
- Distinct visual count: 12
- Rights-metadata gate: PASS
- Repeat gate: PASS
- Black-frame gate: PASS
- Narrative gate: PASS
- Segment relevance: PASS
- Voice preflight: PASS
- Freeze/static-hold gate: PASS
- Overall QC: PASS
- Run record: `video_runs/c920-run-3/run-record.json`

## Recovery / rollback

- Large Model remains untouched; rollback of TechSignal video requires deleting/reverting only the new `video_engine/` paths and optional pipeline wiring.
- Existing article/WordPress path remains available without `--video`.
- No automatic WordPress video publication or YouTube upload was performed.
- Generated render artifacts are kept under `video_runs/` and are not treated as source-of-truth code.

## Remaining gate

Before automatic distribution, establish a dedicated TechSignal YouTube destination and credentials, then add and test the upload adapter without reusing Large Model credentials. This is intentionally separated from the successful renderer proof.

## Phase 1 quality-foundation completion â€” 2026-09-12

The first post-proof quality pass is complete. The TechSignal V17 runner now resolves brief, voice, output, and run-directory paths to absolute paths before invoking the four production stages. This removes the relative-path failure observed when the runner was launched from `video_engine/techsignal`.

Verification performed:
- Python compilation: PASS
- Existing TechSignal transplant tests: PASS (2/2)
- Real runner launched from its own module directory using relative input paths: PASS
- All four stages completed with exit code 0: V15 selector, V08 acquisition, V16 compositor, V11 consumer QC
- Resulting run record: PASS
- Existing C920 production artifact remains technically valid: H.264 1080x1920, AAC 24 kHz mono, 43.2 seconds

This phase fixes a real portability defect. It does not yet claim that the consumer video is sufficiently engaging for unattended publishing; that remains a separate content-quality phase requiring richer product-specific visual treatment and broader multi-product evidence.

## Phase 2 distribution preparation — 2026-09-12

Distribution preparation is complete up to the external-credential boundary.

Implemented:
- Added `video_engine/techsignal/youtube_publisher.py` as a TechSignal-only distribution adapter.
- The adapter builds upload metadata from the validated TechSignal video brief and finished MP4.
- Default privacy is `private`; the adapter identifies the destination as `TECHSIGNAL_ONLY`.
- Dry-run verification completed successfully against the real C920 MP4 and video brief.
- The adapter explicitly refuses live upload until dedicated TechSignal YouTube OAuth/channel credentials are configured.

Safety boundary:
- No Large Model YouTube token, client secret, channel ID, or credential file was copied or reused.
- No external upload was attempted.
- A live YouTube upload is therefore not yet claimed as complete.

Phase 2 status: PREPARED / BLOCKED ONLY BY DEDICATED TECHSIGNAL YOUTUBE IDENTITY AND OAUTH CREDENTIALS.

## Phase 3 — product-specific engagement and multi-product E2E proof — 2026-09-12

The TechSignal video layer was upgraded from a generic fact-card sequence to a product-decision sequence. The objective is not to imitate the Large Model's news storytelling; it is to make each consumer video visibly about the exact product/article being evaluated and useful to a buyer.

### Changes implemented

- `video_adapter.py` now emits `techsignal-video-brief-v2` with the article topic, selected products, buyer-use cases, differentiators, specifications, limitations, best-for/skip-if guidance and the article verdict.
- The scene contract is now: `Hook -> Product -> Key feature -> Real-world use -> Spec check -> Trade-off -> Best for -> Skip if -> Verdict`, with buyer-check and CTA frames added to complete the short-form sequence.
- V15 now produces 12 deliberate consumer slots rather than cycling generic news graphics. Each slot carries the product ID and an exact product/article fact.
- V16 maps those consumer scene types to distinct visual layouts and retains the copied FFmpeg compositor as the rendering foundation.
- V11 now validates the consumer arc and product identity in addition to the existing technical, rights, relevance, audio and motion gates.
- A manual GitHub Actions workflow `TechSignal Video E2E Proof` was added. It uses the existing Small Model OpenRouter secret, generates three article-to-video runs without publishing, validates the finished MP4/QC evidence, and uploads proof artifacts for seven days.

### Distribution boundary

The E2E proof workflow does **not** publish WordPress or YouTube content. The article-to-video path is intentionally proven before distribution is enabled.

### Current acceptance target

Three different buyer-intent topics must each produce:

1. a generated article;
2. a validated video brief derived from that article;
3. a rendered MP4;
4. a PASS consumer QC record;
5. product-identity and narrative-arc evidence;
6. no WordPress or YouTube distribution.

Only after this proof is green should dedicated TechSignal distribution be considered for activation.
