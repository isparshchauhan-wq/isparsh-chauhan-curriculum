# Curriculum automation and release schedule

## Three separate workflows

| Workflow | Schedule/trigger | Purpose |
| --- | --- | --- |
| Prepare scheduled curriculum | Daily 06:00 IST; lecture mode only Friday in auto mode | Pre-read drafts two days before class; lecture drafts for the following Monday–Sunday |
| Release pre-reads at 3 PM IST | Starts 14:40 IST and waits until 15:00 IST | Formal downloadable release for the following day's classes, only from approved ready content merged into main |
| Share approved weekly instructor packs | Relevant changes merged into main, or manual run | ZIP per batch for the following teaching week, once every calendar-listed script for that batch/week is ready |

**Generation, review, merge, and release are different events.** A generated draft is not approved or formally released. The pre-read and lecture-script schedules and readiness states are independent.

The 3 PM target uses Asia/Kolkata. GitHub schedules and API requests can be delayed; this workflow prevents early publication, starts early, refreshes main after waiting, and records the actual release attempt time. It cannot guarantee an exact 15:00:00 release. If an exact-time service commitment is mandatory, use an external reliable scheduler/distribution service and monitor its acknowledgements. A public repository also exposes draft branches and approved files before the formal release; GitHub release timing is not an access embargo.

## Pre-reads

For a Sunday class, generation runs Friday 06:00 IST. Review and merge before Saturday 15:00 IST; formal release targets Saturday 15:00 IST. This uses one preceding calendar day, not a fixed 24-hour interval from class start.

All actual sessions on the target class date are selected across configured batches. There is no artificial one-session-per-batch cap. Conflicted titles/objectives and missing objectives are reported; no later class is substituted. Pre-reads with fewer than four source LOs are allowed when all source objectives can be covered within the student template; the lecture's four-topic grouping constraint does not block the pre-read.

The release job requires `pre_read_status: ready` in main, a non-scaffold file, and passing structural checks. Team review/merge is the human approval gate. Unready/missing material fails visibly in Actions rather than publishing a scaffold. Other ready pre-reads can still release; inspect the failure log for omitted sessions.

Formal releases are per batch/module/session/class date, with a Markdown download and source commit/hash. Re-running does not overwrite an already published release. There is no LMS upload, email, or WhatsApp sending configured.

## Weekly lecture scripts

Friday 06:00 IST prepares all calendar-listed sessions dated the following Monday through Sunday. A batch may have one, two, or more sessions; the actual dates determine the count. Missing dates, source durations, unresolved objective alignment, and four-topic coverage conflicts must be corrected explicitly. Do not change curriculum merely to force two sessions into a week.

Review and merge the weekly lecture PR before Monday. On merge, each complete approved batch/week becomes a GitHub instructor-pack release containing the scripts, sibling images/data, and a sessions manifest. Incomplete batch packs are reported rather than silently sent as a partial week. A batch with no scheduled class needs no pack. The release link is what the team can share with instructors; no external recipient messaging is configured.

The default pack covers the following week. For late approval during the teaching week, use the manual pack action with that week's explicit Monday date. Published packs are snapshots; corrections after publication need a deliberately versioned replacement release.

## Activation

1. Add `OPENAI_API_KEY` under Settings → Secrets and variables → Actions. API usage is billed separately from ChatGPT. Never commit the key.
2. Under Settings → Actions → General, enable the referenced actions and Allow GitHub Actions to create and approve pull requests. These workflows only create draft PRs, not approvals.
3. Open Actions → Prepare scheduled curriculum → Run workflow. Choose pre-read or lecture-script for a targeted test. Auto follows the weekday schedule. An optional class date supports a missed/manual pre-read run.
4. Review the generated PR and merge accepted material into main. Resolve any Needs verification items first.
5. Run release/pack actions with dry_run enabled for the first verification. Scheduled/publication runs do not require an API key, only correctly approved ready files and GitHub's workflow token.

The integration cannot add the API key or change repository administration settings through the current connected tools. If no key exists, generation reports Waiting for secret and makes no model calls. Release jobs can still distribute previously approved content.

## Review and readiness

The creator and verifier follow canonical repository instructions. Missing execution or rendering evidence remains Needs verification. Structural checks supplement review; they do not prove factual accuracy. The publisher updates only the generated artifact's readiness and regenerates exports. Overall session ready still requires both artifacts, independently of delivery status.

Each generation run uses a separate artifact/date branch. Open PR reservations include the artifact, so a pre-read PR does not block that session's weekly lecture draft. Existing branches are checked before model calls to avoid paid regeneration on retries. The publisher never force-pushes or merges. Temporary plans/reports/patches remain Actions artifacts for 14 days; student content stays in its indexed folder.

## Operations and failure recovery

- All deadlines depend on `scheduled_date` in `curriculum-index.json`. Update class reschedules there and run `python3 tools/sync_curriculum.py`.
- Correct objectives or explicitly supply a coverage plan for blocked lessons. A red workflow run is a signal to inspect logs, not proof that every batch failed.
- Review timing is operational: unmerged or unverified content will miss release. Check the pre-read queue before 3 PM and weekly packs before Monday.
- For a pushed branch whose PR creation failed, inspect/create the PR manually; do not blindly regenerate or delete work.
- For stale/conflicting PRs, resolve/rebase through review; no force pushes are automated.
- To pause generation and publication, disable each workflow in Actions, or set config.enabled false. A pause never retracts already published releases.
- GitHub can delay/drop scheduled events or disable public-repository schedules after prolonged inactivity. Exact-time release remains a service limitation, even with the early-start wait.
- Hosted generation, API credentials, temporary permissions, code/SQL/diagram execution, and release uploads need a successful live test. Offline tests cannot establish deployment success.

## Sources

- https://github.com/openai/codex-action
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://cli.github.com/manual/gh_release_create
- https://cli.github.com/manual/gh_release_edit
