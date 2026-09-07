# Current Plan — Large Model + Small Model

**Date:** 2026-09-07
**Decision status:** LOCKED FOR CURRENT PHASE

## Purpose

Define how the Large Model and Small Model coexist without prematurely coupling their repositories, orchestration, or commercial logic.

## Core decision

The Large Model and Small Model remain **separate peer systems**.

- **Large Model:** `news-ai-automation` — autonomous news/media production.
- **Small Model:** `news-ai-small-model` — autonomous buyer-intent/commercial content production.

The Small Model was created to reach a viable market-facing product while the Large Model was being built. The Large Model is now production-pipeline GREEN, but this does not justify merging the systems yet.

## What can be shared now

### 1. WordPress destination

Both systems may publish to the same TechSignal WordPress installation where operationally appropriate.

The WordPress site is a publishing destination, not a reason to merge codebases.

### 2. Separate WordPress publisher identities — DO NOW

Each engine should publish using its own WordPress identity/credentials.

Objectives:
- clean audit trail;
- immediate identification of which engine published a post;
- easier incident investigation;
- no credential coupling between projects.

This is the one shared-infrastructure change approved for immediate implementation.

## What is explicitly deferred

### Topic registry — DEFERRED

Do **not** build a new datastore, topic ID system, alias model, or claim semantics yet.

The NVIDIA-style collision scenario is illustrative, not an observed production problem.

At current volumes and with different editorial lanes, use the existing WordPress REST API as the cheap stopgap when topic overlap protection is needed:

`candidate topic → recent WordPress posts → title/category similarity check → skip or publish`

Upgrade to a dedicated registry only after evidence of real collisions or when publishing volume makes the REST check inadequate.

### Commercial-intent JSON contract — DEFERRED

Do not define or implement a cross-repository commercial-intent interface yet. Small Model continues to operate independently until it produces real commercial evidence.

### Shared orchestration — DEFERRED

Do not merge orchestration, repositories, workflows, or runtime architecture.

Any eventual integration must be evidence-driven.

## Editorial coexistence

The systems occupy different primary lanes:

| System | Primary content |
|---|---|
| Large Model | News, analysis, scripts, video and related media |
| Small Model | Buying guides, comparisons, reviews and affiliate-oriented content |

Both may use the same WordPress property, but they must not intentionally produce duplicate/cannibalizing content.

## Commercial gate

Small Model remains at **5 published articles/day** while the commercial loop is measured.

Primary progression:

`real visitor → affiliate click → qualifying purchase → dispatched item → commission`

Do not increase production volume or redesign the architecture based on zeros that are merely missing external evidence.

The first important signal is a real affiliate click. The decisive business proof is a first commission.

## Strategic future — not current implementation

If Small Model proves that its commercial loop works, its proven commercial capabilities may later become a specialized capability within the broader Large Model platform.

That is a future architectural decision, not a current merge task.

The intended evolution is:

`Large Model = media production system`

`Small Model = commercial-content system`

`Future possibility = integrated TechSignal platform with specialized commercial intelligence`

Integration should follow evidence, not precede it.

## Current execution order

1. Keep Large Model production baseline stable.
2. Keep Small Model operating at 5/day.
3. Separate WordPress publisher identities.
4. Use WordPress REST title/category checking if an overlap concern arises.
5. Collect external traffic, indexing and Amazon evidence.
6. Obtain the first measurable affiliate click.
7. Obtain first commission.
8. Only then evaluate whether shared interfaces or deeper integration create measurable value.

## Governance

- No speculative engineering.
- No new recurring infrastructure cost.
- Verify before changing production behavior.
- Keep repositories separate.
- One writer at a time for each repository.
- Architecture changes require evidence or a concrete production need.

## Current status

Large Model production pipeline: **GREEN / accepted for its defined M1–M7 production scope**, based on the latest accepted production evidence.

Small Model: **operational at 5/day; commercial validation in progress**.

The immediate business bottleneck is not architecture. It is proving that Small Model content can attract buyer-intent traffic and generate an affiliate click/commission.
