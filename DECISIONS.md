# Decisions

## 2026-08-31 — Standalone repository
The Small Model is a separate GitHub repository, not a branch of news-ai-automation.

## 2026-08-31 — Reuse proven components
Reuse the proven WordPress publisher and AI provider from the large model. Do not copy the wider news pipeline.

## 2026-08-31 — GitHub as build control
GitHub is the technical source of truth: code, issues, releases, Actions, roadmap, status, and change history.

## 2026-08-31 — Keep project management light
Use GitHub Issues for work and problems. Jira/Linear are not required unless the project grows enough to justify them.

## 2026-08-31 — GitHub-hosted automation
Prefer GitHub-hosted Actions. The HP/self-hosted runner is not part of the Small Model.

## 2026-08-31 — Commercial validation first
The objective is to prove an unattended content-to-monetisation loop, not to build a large platform.

## 2026-09-05 — Controlled production verification complete
The unattended production path is verified for a real controlled run: tests passed 34/34; production run #103 published WordPress post 55; the public URL check returned HTTP 200; pre-publish affiliate validation passed with two exact Amazon UK catalogue matches; the external image gate passed with one compliant hero and one context image; and the run metrics/published history were persisted. GitHub Issue #9 is closed as completed.

## 2026-09-05 — Small Model feature freeze
The Small Model build is frozen at the verified production baseline. No further feature expansion or editorial-engineering tuning should be performed merely because additional improvements are possible. Future changes require evidence from audience, affiliate-click, conversion, revenue, reliability, or a concrete production defect. The operating sequence is now BUILD → SHIP → MEASURE → LEARN → IMPROVE.

## 2026-09-05 — External image safety gate retained
Publication must continue to require one compliant hero plus at least one compliant context image. Images remain remotely hosted with licence and attribution metadata; the WordPress Media Library is not used by this pipeline. Deterministic licensed fallbacks may be used when live Commons search is empty or unreliable.

## 2026-09-05 — Audience and revenue are the next proof
Pipeline completion is not treated as business success. The next decision gate is external evidence: search discovery, traffic, affiliate clicks, Amazon reporting, conversion, and revenue. No scaling decision is justified before those signals exist.
