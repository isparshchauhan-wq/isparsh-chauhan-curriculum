# Daily curriculum generation

## Configured behavior

- GitHub Actions runs daily at **06:00 IST** (`30 0 * * *` UTC), plus a manual Run workflow button.
- Up to one session per batch: three pre-reads and three lecture scripts per day when eligible source rows exist.
- Select upcoming rows in source order, starting with dates on/after the run's India date. Earlier unprepared lessons are not automatically backfilled. Open automation PRs reserve their sessions so subsequent runs can move forward.
- Preserve source duration, 90 or 120 minutes. Keep four topics and four quizzes. The user approved this source-duration policy on 20 November 2026.
- Skip completed pairs, pending PR targets, title/objective conflicts, unspecified durations, and rows needing an explicit four-topic coverage plan (fewer than four or more than eight source objectives).
- Separate creator and verifier passes follow the repository rules. If independent agents are unavailable, disclose sequential parent review.
- Default Setup No and Announcements No. Change the implementation alongside the configuration before supporting other values; a config edit alone must not bypass required setup inputs.
- Use one draft PR per run date. Never automatically merge. Structural checks do not prove factual accuracy; review evidence and unverified items in the PR body.

## Activate once

1. Create an OpenAI API project/key with API billing enabled. ChatGPT subscription billing and API usage are separate. Set an API project budget/usage alert appropriate to three daily lesson pairs; this workflow has no guaranteed dollar ceiling.
2. In this repository, open **Settings → Secrets and variables → Actions → New repository secret**. Name it `OPENAI_API_KEY` and paste the key there. Do not put it in a file, issue, PR, or chat.
3. Open **Settings → Actions → General**. Permit the workflow's referenced actions and enable **Allow GitHub Actions to create and approve pull requests**. The workflow creates draft PRs; it never approves them.
4. Open **Actions → Daily curriculum drafts → Run workflow**. Inspect the first run and its draft PR before relying on the daily schedule.

Until the secret exists, scheduled runs report Waiting for repository secret and make no model calls. This integration does not activate API billing or create keys for you. Repository administration/secrets cannot be changed through the current connected tools.

## What runs

1. `automation/pipeline.py plan` reads the index/config and pending PR reservations, creates an exact plan, and reports skipped conflicts.
2. The Codex GitHub Action authors the selected lesson files and assets. It has no repository write token. Installed Python packages, Mermaid CLI and a disposable MySQL 8 service support verification.
3. `collect` rejects changes outside selected session files/assets, runs structural checks, and packages a patch, plan, and verification report as a 14-day workflow artifact.
4. A separate publish job applies the patch to its exact generation base, validates scope/structure, updates only the relevant readiness metadata, regenerates batch exports, and opens a draft PR. Other student content is preserved.
5. The curriculum team reviews and merges the PR. Ready means artifact checks were reported complete; delivery status remains independent and unchanged.

A report's evidence is the agent's account of commands and observations, supplemented by structural checks. It is not an independent execution attestation. Always review code, outputs and instructional quality.

## Operating and recovery

- Inspect `automation/config.json` for enabled state and batch list. Keep `sessions_per_batch` at the configured one unless intentionally increasing workload. The workflow cron controls time; schedule_ist documents it.
- Pause in Actions with Disable workflow, or set enabled false. Pausing before the key is added prevents model usage entirely.
- A repeat run on the same date does not create another open PR. The planner checks remote daily branches before any model call, including closed/merged PR branches and a push followed by failed PR creation. A pre-existing daily branch is not overwritten; inspect it and remove it only if intentionally retrying that date.
- A failed generation/publish run appears as a failed Actions run, with logs. No automatic retries or merges are configured.
- If all targets are blocked or already ready/pending, the plan lists reasons and no agent call occurs. Some runs can produce fewer than three pairs.
- To revise earlier sessions, request a targeted authoring run; daily selection does not recreate the historical backlog.
- GitHub can delay scheduled runs. Public-repository schedules can be disabled after prolonged repository inactivity; inspect Actions if expected runs stop.
- If generated PRs become stale while teammates update main, resolve/rebase their conflicts through review. No force pushes are performed.
- Dependencies are installed on disposable hosted runners. Actual model generation and full hosted verification require the activation key and a successful first Actions run; offline tests cannot prove this deployment path.

## Sources

- [Official Codex GitHub Action](https://github.com/openai/codex-action)
- [ChatGPT/API billing](https://help.openai.com/en/articles/9039756-managing-billing-for-chatgpt-and-the-api-platform)
- [GitHub Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
- [Scheduled workflow behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
