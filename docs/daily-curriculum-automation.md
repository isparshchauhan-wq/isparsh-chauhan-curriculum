# Manual weekly curriculum workflow

Run this in a Git clone of the repository on macOS or Linux. It uses local Codex with your ChatGPT sign-in and GitHub CLI with your GitHub sign-in. The two accounts can use different email addresses. Model access and remaining Codex usage depend on your active ChatGPT account. GitHub Actions runs deterministic checks on PRs and can run the same checks on demand.

## Before the first run

1. Install Git, Python 3.9 or later, [Codex CLI](https://learn.chatgpt.com/docs/cli) and [GitHub CLI](https://cli.github.com/). The runner can find the CLI bundled with ChatGPT on macOS if codex is absent from your PATH.
2. Run `codex login` and select **Sign in with ChatGPT**, then confirm with `codex login status`. Keep API-key authentication out of this workflow. The runner requires a ChatGPT login, removes API-key overrides, and uses the built-in OpenAI provider.
3. Run `gh auth login --hostname github.com` and `gh auth setup-git` to connect the GitHub account that can push to this repository. Configure Git commit authorship as described in the [Git and GitHub guide](git-github-curriculum-guide.md).
4. For your first live pilot, start from a clean checkout of the setup branch. Use `--local-only` so pilot content stays in local branches until the setup branch is reviewed and merged. For regular runs, start from an up-to-date main that contains the reviewed setup. Install the dependencies required by the sessions you choose, including a Mermaid renderer and a disposable SQL database for SQL examples. Unavailable checks are recorded as unverified.

## Each teaching week

```bash
python3 tools/weekly_curriculum.py plan
python3 tools/weekly_curriculum.py generate
python3 tools/weekly_curriculum.py status
```

In a Codex session opened in this clone, you can also ask **“Generate next week’s curriculum materials.”** AGENTS.md directs Codex to the same runner. The default is the next Saturday in Asia/Kolkata, strictly after today, through the following Friday. To select a specific week, pass `--week-start YYYY-MM-DD` with its Saturday. The plan shows the batch, source session, class date, title, duration, required artifacts, model and effort for each pass, and existing state. The plan and status use local files and do not make model calls.

To pilot one session that has both artifacts eligible:

```bash
python3 tools/weekly_curriculum.py generate --week-start 2026-11-21 \
  --batch IITREICT-AIML-EN-II-2608 --session 11.3 --limit 1 --local-only
python3 tools/weekly_curriculum.py status --week-start 2026-11-21
```

Use a different indexed Saturday/session if you are piloting another week. Processing runs one artifact at a time. Creator and verifier are separate CLI executions, each with a selected model/effort, and the verifier examines the saved draft. The runner applies the structural checker itself. It preserves indexed objectives and 90/120-minute pacing. Missing source facts or unresolved learning-objective grouping are listed as blocked. Already-ready artifacts are preserved.

## Models, usage and checkpoints

`automation/model-policy.json` selects GPT-6.2 Sol for daily work. Pre-read stages use medium effort and lecture stages use high. These are configured requests. Availability, reasoning support, and actual model execution must be confirmed against your signed-in CLI. A failed model or usage-limit response pauses processing. Automatic escalation is off. To request Astra, use `--astra` with exactly one batch, session and artifact (and module ID for an ambiguous session). An unavailable configured model requires your explicit choice before the policy changes.

Progress is saved under `.weekly-curriculum/<Saturday>/manifest.json`, with per-stage logs in its tasks directory. Keep this folder and the Git worktrees until review is complete. Each creator and verifier pass checkpoints its changes. This leaves enough version history to resume at the next unfinished stage and retain the exact checklist results. Separate worktrees keep in-progress or blocked drafts out of the branch the team reviews.

```bash
python3 tools/weekly_curriculum.py resume --week-start 2026-11-21
python3 tools/weekly_curriculum.py status --week-start 2026-11-21
```

After checking a transient failure or allowing a usage limit to reset, add `--retry-blocked` to resume. The default permits one explicit retry of a failed stage for the same model/effort and revision. A model change must be authorized by you. Failed and blocked content findings require input or a revision. If an interruption left uncommitted changes in a batch worktree, inspect its `git status` and preserve the files before continuing. Logs report which command and stage stopped.

## Review, approve and publish

After generation the runner pushes one curriculum branch per batch/week and opens or updates its draft PR. If you used `--local-only`, run `python3 tools/weekly_curriculum.py submit --week-start YYYY-MM-DD` when GitHub is ready. This step uses no model calls. If the setup branch is still unmerged, its changes may appear in the pilot PR diff. Keep the pilot local while reviewing setup if you want a lesson-only diff.

A PR shows the material links, changed files, model and effort requests, verification states and LMS/instructor handoff notes. Completed unverified drafts can be reviewed with their gaps visible. Failed or blocked drafts remain in local checkpoints. The manifest distinguishes `passed`, `failed`, `blocked` and `unverified`. Model reports describe their evidence, while structural checks run directly. Review the evidence before approving.

1. Open **Files changed** on the batch PR and check the rendered materials, verification evidence, images and data. Check every scheduled session for the batch that week.
2. To request a correction, use `revise --week-start YYYY-MM-DD --batch BATCH --session ID --artifact pre-read --note "Your correction"`. Add `--module-id ID` when necessary. The runner edits that artifact and re-verifies it. It updates the open PR or creates a correction branch for previously merged material.
3. Once **Validate curriculum** is green and you have reviewed the content, copy the `Review done <commit SHA>` line from **Owner review** and post it as a new PR comment from the repository owner's account. The SHA identifies the version you reviewed. Copy a fresh line after reviewing any updates. The workflow checks the approval, the PR scope and the presence of both resources for every scheduled session, then marks the PR ready and merges it into `main`.
4. Open the **Merge and package weekly resources** run in Actions and download the batch artifact. It contains one ZIP made from the merged commit, with a folder for each session that contains `pre-read.md`, `lecture-script.md`, and any committed `images/` and `data/`. Codex can retrieve the ZIP from that run for the conversation. If Actions stops after merging, rerun that action to package the same merged commit.
5. Preview the student pre-read in the LMS and publish it manually at **3 PM IST, one calendar day before class**. After publication, use `record --event published-to-lms --note "LMS URL or publication timestamp"` with the same selectors if you want a local publication record. Share the batch ZIP with the instructor manually.

The comment-triggered workflow becomes available after the setup PR is on the default branch. Review and merge that setup PR through GitHub. To recreate an expired batch artifact, check out the merge commit and run `python3 tools/weekly_handoff.py package --checkout . --batch BATCH --week-start YYYY-MM-DD --output BATCH-weekly-resources.zip`.

The repository is public. A draft branch on GitHub is readable before LMS publication. If your class requires an embargo, keep drafts local or use a private review repository.

## Troubleshooting

- **Codex starts but refuses the model or effort.** Check the model selector or the exact error in the stage log. Resume the original model after access returns, or explicitly approve a model policy change. The runner never falls back to API billing.
- **Nested Codex is unavailable in the current app.** Run the same command in Terminal from your clone, with a ChatGPT-authenticated Codex CLI. Preserve the existing manifest when resuming.
- **GitHub push or PR creation fails.** Confirm the authorized GitHub account and write access. Run `submit` again after correcting authentication. It uses the checkpointed branch and checks for an existing PR.
- **A session is absent or blocked.** Confirm the indexed date, module, source objectives and duration. For a corrected schedule or source conflict, update through a curriculum PR. A previously started manifest represents its original plan. Inspect it against the updated index before resuming.
- **Actions is red.** Open the failed step. Run `python3 tools/sync_curriculum.py --check` and `python3 tools/weekly_curriculum.py validate` locally. Deterministic checks do not replace code execution, diagram rendering or human review.

Official references: [Codex authentication](https://learn.chatgpt.com/docs/auth), [model selection](https://learn.chatgpt.com/docs/models), and [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).
