# Small Model Operations

## Current objective
Prove the commercial loop with the smallest useful system:

`topic -> generate -> catalogue affiliate links -> cross-link -> WordPress -> measure`

## GitHub Actions
The repository uses GitHub-hosted runners only.

### Required repository secrets

- `OPENROUTER_API_KEY` — AI generation provider credential.
- `WORDPRESS_SITE_ID` — numeric ID of the separate Small Model WordPress site.
- `WORDPRESS_ACCESS_TOKEN` — preferred WordPress API credential.
- Or the WordPress OAuth exchange set: `WORDPRESS_USERNAME`, `WORDPRESS_APP_PASSWORD`, `WORDPRESS_CLIENT_ID`, `WORDPRESS_CLIENT_SECRET`.
- `WORDPRESS_DEFAULT_STATUS` — start with `draft` for the first 10–15 articles; change to `publish` only after human spot-check acceptance.

No credentials belong in source files.

## Publishing workflow
`.github/workflows/publish.yml` runs once per day at 06:17 UTC and selects one of the 15 curated topics. It produces `validation-report.json` as a workflow artifact.

The scheduled path is intentionally gated by `WORDPRESS_DEFAULT_STATUS`. With `draft`, the system can exercise the full publishing path without making articles public. Set the secret to `publish` only after the first batch is accepted.

## First-batch procedure

1. Configure the separate WordPress site and required credentials.
2. Configure `OPENROUTER_API_KEY`.
3. Run the publish workflow manually with `publish=false` and inspect the validation artifact.
4. Run with `publish=true` while `WORDPRESS_DEFAULT_STATUS=draft` and verify the resulting WordPress draft.
5. Repeat for 10–15 articles.
6. Human spot-check the articles, product facts, affiliate links, formatting, and disclosures.
7. Set `WORDPRESS_DEFAULT_STATUS=publish` only after acceptance.
8. Allow the daily schedule to run unattended.

## Commercial measurement
Track four sources:

- Google Search Console: impressions, clicks, queries, ranking movement.
- Amazon Associates: affiliate clicks, ordered items, conversion and commission data.
- Pinterest: impressions and outbound traffic once enabled.
- WordPress: published article count and publication failures.

The first business decision is made approximately four weeks after the first public batch. Keep topics that show commercial/search signals; replace or drop topics with no signal.

## External prerequisites
The following cannot be completed safely from repository automation alone:

- Registering and paying for the new domain.
- Creating the separate hosting/WordPress account.
- Completing the Amazon Associates application and qualifying-sales requirement.
- Creating the Pinterest business account.
- Creating the email provider account.
- Supplying the corresponding credentials as GitHub Actions secrets.
- Final keyword-volume/competition checks where a third-party tool requires an account or interactive access.

These are account/business actions, not code blockers. The repository is designed to remain usable without them until the commercial loop is ready.

## Operations dashboard and auto-repair
A separate `TechSignal Operations` workflow runs every 15 minutes and can also be started manually.

The workflow:

- reads recent `Small Model Publish` runs from GitHub Actions;
- classifies failed jobs from their logs;
- automatically retries only bounded transient failures (rate limits, timeouts, network errors, and temporary 5xx failures);
- never auto-retries validation, duplicate, affiliate, authentication, permission, or unknown failures;
- records every repair decision in `data/repair_history.json`;
- generates an operational dashboard with recent runs, success rate, failures, repairs, scale state, and persistent metrics;
- updates `TechSignal Operations Dashboard` as a WordPress **draft** when WordPress credentials are configured;
- uploads the dashboard as a GitHub Actions artifact on every operations run.

Repair is limited to two attempts per failed run with a 20-minute cooldown. Unresolved failures are recorded as escalations rather than retried indefinitely.
