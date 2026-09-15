# TechSignal Distribution Architecture

## Current production decision — 2026-09-15

WordPress at `https://techsignal.wasmer.app` remains the TechSignal publishing destination and content source. The Small Model's existing GitHub Actions schedule is the current unattended publication scheduler; it targets five publication slots per day through the adaptive scale gate.

Social distribution is a separate synchronized layer. It must consume successful TechSignal publication records and must never invent or recycle content merely to fill a social quota.

## Distribution model

1. TechSignal produces the article and, when available, the compliant product video.
2. WordPress publishes the article on the existing scheduled production cadence.
3. A distribution queue records the WordPress URL and the corresponding social destinations.
4. Each social destination uses channel-specific copy and explicit account authorization.
5. Publication status and resulting URLs are recorded per channel.
6. Failures are retried and remain visible; a missing social credential must not block WordPress publication.

## Initial channels

- YouTube — Evolution is the designated TechSignal channel.
- TikTok — new TechSignal channel to be created/authorized by the owner.
- Facebook — TechSignal Page.
- Instagram — TechSignal account if connected and suitable for the content format.
- LinkedIn — optional secondary distribution channel after the first channels are stable.

## Scheduler decision

Do not make Buffer, HubSpot Marketing Hub, or Adobe Express Scheduler a mandatory dependency. The preferred architecture is direct platform publishing orchestrated by the existing automation infrastructure. Adobe Express remains an optional design tool.

## Current implementation boundary

`social_distribution.py` and `.github/workflows/distribution-queue.yml` now create a live synchronized distribution queue from published WordPress content. Direct social publication is intentionally blocked until the corresponding platform OAuth/API credentials are explicitly configured in GitHub Actions secrets. This prevents silent or unauthorized posting.

Required future secret families:

- TikTok: approved Content Posting API application and authorized account/token.
- Meta: authorized Facebook Page/Instagram publishing credentials.
- YouTube: existing TechSignal/Evolution OAuth credentials.
- LinkedIn: only if/when LinkedIn distribution is enabled.

## Non-negotiable content rule

Distribution does not weaken TechSignal production standards. Only videos that have passed the current hard product-media standard may enter the video distribution queue: at least 10 distinct exact-product photographs/video clips, no dark/blank slides, no graphics-only assets, no recycled media, rights provenance, American English narration, and automated visual/audio acceptance.
