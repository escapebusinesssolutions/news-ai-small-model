# Step 1 — Extract What Already Works

Status: COMPLETE
Date: 2026-08-31

## Reused from `news-ai-automation`

1. `intelligence/wordpress_publisher.py`
   - Copied to `reused/wordpress_publisher.py`.
   - Provides WordPress.com site health check, authorization check, safe draft mode, publishing, and stable slugs.
   - Existing production evidence: a WordPress post was successfully published with post ID 6407 on 2026-08-29.

2. `ai_provider.py`
   - Copied to `reused/ai_provider.py`.
   - Provides the existing AI connection with Hugging Face and bounded OpenRouter fallback.
   - This is the useful reusable part of the existing content-generation system; the news-specific prompts and pipeline are NOT copied.

## Reusable scheduling pattern

The existing GitHub Actions pattern uses `ubuntu-latest`, checkout, Python setup, dependency installation, and scheduled/manual execution. The Small Model will use this pattern later, but will NOT copy the large project's workflow or its self-hosted HP runner requirements.

## Deliberately NOT reused

- M1–M7 discovery/news machinery
- Machine 2 news-writing contract
- video generation/publishing
- self-hosted Windows runner
- OpenCode workflow
- large-project CI/governance structure
- large project's news-specific schemas and run directories

## Step 1 conclusion

The proven building blocks are available locally in the Small Model repository. The next build step is to create the Small Model's own simple content-generation stage around these reusable pieces, without importing the large pipeline.
