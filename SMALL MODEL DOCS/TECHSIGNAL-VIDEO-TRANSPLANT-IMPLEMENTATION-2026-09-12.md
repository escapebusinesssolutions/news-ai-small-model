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
