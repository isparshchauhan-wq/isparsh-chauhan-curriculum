# Manual weekly curriculum workflow

Run this in a Git clone of the repository in the selected connected runtime on macOS or Linux. It uses local Codex with your ChatGPT sign-in. GitHub CLI submission uses your GitHub sign-in. The two accounts can use different email addresses. Model access and remaining Codex usage depend on your active ChatGPT account. GitHub Actions runs deterministic checks on PRs and can run the same checks on demand.

## Choose the execution environment first

Run `python3 tools/curriculum_environment.py` in each available runtime before deciding where to generate. The current assessment on 28 November 2026 has a connected Mac and no accessible cloud execution workspace. The default Mac Python lacks NumPy, pandas, Matplotlib and Seaborn. Node, Mermaid CLI, MySQL and GitHub CLI are also absent from PATH. VS Code is installed with Python and Jupyter support, while a Mermaid preview extension was absent from the extension inventory. Prior stage logs used another prepared Python runtime, so select and activate that runtime explicitly.

A cloud speed comparison remains pending. Confirm actual model execution with the repository policy and required dependencies before benchmarking. Use one complete representative batch, matching inputs, creator/verifier routes and validation. Include local VS Code handoff and checks in total time. Measure cloud and local separately without regenerating an already approved batch. Select cloud if the complete measured workflow is faster. The under-30-minute per-batch objective is a target until a live run demonstrates it. Shared account limits and model latency affect concurrent runs.

## Parallel batches and automatic correction

Use one invocation for all requested batches within a teaching week. Four jobs are a shared concurrency limit across those batches.

```bash
python3 tools/weekly_curriculum.py generate --week-start YYYY-MM-DD \
  --target BATCH_A/MODULE_A/SESSION_A --target BATCH_B/MODULE_B/SESSION_B \
  --jobs 4 --local-only
```

For different teaching weeks, prepare separate invocations. Each retains its own manifest. The coordinator can overlap weeks using separate checkouts to isolate Git administration and checkpoints. Model calls still share the signed-in account's limits.

Use local VS Code to preview every Mermaid diagram and to inspect code results and images. Execute each example with its required environment in the integrated Terminal or notebook. Record the runtime and output, and verify relative links from the session folder. A preview or syntax check alone leaves code execution unverified.

The verifier repairs findings and rechecks the artifact. If deterministic or reported checks still fail, the runner makes one additional repair pass with the failing evidence and retains the first report. It records `failure_history` and `prevention_pending` for the coordinator. Remaining failures trigger diagnosis and a separate draft workflow PR updating the applicable canonical creator and reviewer files, plus a checker regression check when the checker caused the failure. Missing dependencies need environment repair before re-verification. Source conflicts, model access and usage limits remain explicit blockers. Every correction is rechecked before marking an artifact ready.

## Before the first run

1. Install Git, Python 3.9 or later, [Codex CLI](https://learn.chatgpt.com/docs/cli) and [GitHub CLI](https://cli.github.com/). The runner can find the CLI bundled with ChatGPT on macOS if codex is absent from your PATH.
2. Run `codex login` and select **Sign in with ChatGPT**, then confirm with `codex login status`. Keep API-key authentication out of this workflow. The runner requires a ChatGPT login, removes API-key overrides, and uses the built-in OpenAI provider.
3. For submission through GitHub CLI, run `gh auth login --hostname github.com` and `gh auth setup-git` to connect the GitHub account that can push to this repository. Configure Git commit authorship as described in the [Git and GitHub guide](git-github-curriculum-guide.md).
4. Start from a clean, up-to-date checkout of `main`. Use `--local-only` for generation so the runner keeps the checkpointed work local while Codex tracks it. Prepare the dependencies once before running: activate a reusable Python environment with the session imports (such as pandas, Matplotlib and Seaborn for visualisation), put a working Mermaid renderer such as `mmdc` on PATH, and provision a disposable SQL database for SQL sessions. Test the imports and a sample Mermaid render in the same Terminal. The creator and verifier reuse this environment and report unavailable checks as unverified.

## Start from a topic

1. Tell Codex the starting topic or source session ID. Add the batch or module if the topic or session ID occurs more than once. Codex looks up the scheduled date in `curriculum-index.json` and finds the Saturday–Friday teaching week in Asia/Kolkata that contains it.
2. Codex lists the starting session and each later session in that batch and week, sorted by scheduled date and then by index order within a date. It checks the existing state and prepares one Terminal block with the exact selectors. Each selected session can produce a pre-read and a lecture script. The runner preserves ready materials and previously saved checkpoints.
3. Paste the prepared block into Terminal and launch it once. Use one command per batch and week. With `--jobs 4`, up to four artifacts run concurrently. Drafting still precedes independent verification for each artifact. If commands for separate batches are chained, `&&` stops the chain when a command exits with an error. Codex monitors the local manifest and task logs, diagnoses stops, checks the saved materials and assets, and reports verification gaps. If another Terminal launch is required, Codex prepares a scoped resume command and the remaining session commands.
4. Codex opens or updates the batch draft PR after the selected work finishes and sends you its link for review. The full-week ZIP also uses resources for earlier sessions that are already in the repository. If an earlier session is missing a pre-read or lecture script, Codex flags it in the handoff because the merge workflow requires both resources for every scheduled session that week.

The two-session example below uses placeholders. Codex supplies the checkout path, indexed Saturday, batch, module and session IDs. It repeats `--include-session MODULE/SESSION` for each selected session. A two-session batch has four artifact pipelines. Four jobs allow them to overlap. Use `--jobs 1` if your account needs a sequential run.

```bash
cd "/path/to/curriculum-checkout" &&
python3 tools/weekly_curriculum.py generate --week-start YYYY-MM-DD \
  --batch BATCH --include-session MODULE_A/SESSION_A --include-session MODULE_B/SESSION_B \
  --jobs 4 --local-only
```

The runner launches separate creator and verifier executions for each artifact that needs work. The verifier examines the saved draft, and the runner applies the structural checker. Missing source facts or unresolved learning-objective grouping are recorded as blocked. The `plan` and `status` commands show the selected sessions, dates, required artifacts, model requests and current state without making model calls.

## Models, usage and checkpoints

`automation/model-policy.json` selects GPT-6.2 Sol for daily work. Pre-read stages use medium effort and lecture stages use high. These are configured requests. Availability, reasoning support, and actual model execution must be confirmed against your signed-in CLI. A failed model or usage-limit response pauses processing. Automatic escalation is off. To request Astra, use `--astra` with exactly one batch, session and artifact (and module ID for an ambiguous session). An unavailable configured model requires your explicit choice before the policy changes.

Progress is saved under `.weekly-curriculum/<Saturday>/manifest.json`, with live per-stage logs in its tasks directory. Terminal shows stage starts, ends and elapsed times. On a model execution error, running calls can finish and save their checkpoints. The runner stops scheduling new stages after the error and preserves other completed checkpoints. Keep this folder and the Git worktrees until review is complete. Each creator and verifier pass checkpoints its changes. This leaves enough version history to resume at the next unfinished stage and retain the exact checklist results. Separate worktrees keep in-progress or blocked drafts out of the branch the team reviews.

```bash
python3 tools/weekly_curriculum.py resume --week-start YYYY-MM-DD \
  --batch BATCH --module-id MODULE --session SESSION --local-only
python3 tools/weekly_curriculum.py status --week-start YYYY-MM-DD \
  --batch BATCH --module-id MODULE --session SESSION
```

Use the same session selectors and job count when resuming a parallel run. After checking a transient failure or allowing a usage limit to reset, add `--retry-blocked` to resume. The default permits one explicit retry of a failed stage for the same model/effort and revision. A model change must be authorized by you. Failed and blocked content findings require input or a revision. If an interruption left uncommitted changes in a batch worktree, inspect its `git status` and preserve the files before continuing. Logs report which command and stage stopped.

## Review, approve and publish

After generation, Codex checks the selected session outputs, referenced assets and verification records. When the local batch branch is ready, Codex prepares or updates its draft PR through `submit --week-start YYYY-MM-DD` when GitHub CLI is available, or through the authorized GitHub connection. Submission uses no model calls. Codex provides the PR link and check results for your review.

A PR shows the material links, changed files, model and effort requests, verification states and LMS/instructor handoff notes. Completed unverified drafts can be reviewed with their gaps visible. Failed or blocked drafts remain in local checkpoints. The manifest distinguishes `passed`, `failed`, `blocked` and `unverified`. Model reports describe their evidence, while structural checks run directly. Review the evidence before approving.

1. Open **Files changed** on the batch PR and check the rendered materials, verification evidence, images and data. Check every scheduled session for the batch that week.
2. To request a correction, use `revise --week-start YYYY-MM-DD --batch BATCH --session ID --artifact pre-read --note "Your correction"`. Add `--module-id ID` when necessary. The runner edits that artifact and re-verifies it. It updates the open PR or creates a correction branch for previously merged material.
3. Once **Validate curriculum** is green and you have reviewed the content, copy the `Review done <commit SHA>` line from **Owner review** and post it as a new PR comment from the repository owner's account. The SHA identifies the version you reviewed. Copy a fresh line after reviewing any updates. The workflow checks the approval, the PR scope and the presence of both resources for every scheduled session, then marks the PR ready and merges it into `main`.
4. Open the **Merge and package weekly resources** run in Actions and download the batch artifact. It contains one ZIP made from the merged commit, with a folder for each session that contains `pre-read.md`, `lecture-script.md`, and any committed `images/` and `data/`. Codex can retrieve the ZIP from that run for the conversation. If Actions stops after merging, rerun that action to package the same merged commit.
5. Preview the student pre-read in the LMS and publish it manually at **3 PM IST, one calendar day before class**. After publication, use `record --event published-to-lms --note "LMS URL or publication timestamp"` with the same selectors if you want a local publication record. Share the batch ZIP with the instructor manually.

To recreate an expired batch artifact, check out the merge commit and run `python3 tools/weekly_handoff.py package --checkout . --batch BATCH --week-start YYYY-MM-DD --output BATCH-weekly-resources.zip`.

The repository is public. A draft branch on GitHub is readable before LMS publication. If your class requires an embargo, keep drafts local or use a private review repository.

## Troubleshooting

- **Codex starts but refuses the model or effort.** Check the model selector or the exact error in the stage log. Resume the original model after access returns, or explicitly approve a model policy change. The runner never falls back to API billing.
- **Nested Codex is unavailable in the current app.** Launch the block from Terminal with a ChatGPT-authenticated Codex CLI. Codex tracks the saved progress and prepares any needed resume commands with the original session selectors.
- **GitHub push or PR creation fails.** Confirm the authorized GitHub account and write access. Run `submit` again after correcting authentication. It uses the checkpointed branch and checks for an existing PR.
- **A session is absent or blocked.** Confirm the indexed date, module, source objectives and duration. For a corrected schedule or source conflict, update through a curriculum PR. A previously started manifest represents its original plan. Inspect it against the updated index before resuming.
- **Actions is red.** Open the failed step. Run `python3 tools/sync_curriculum.py --check` and `python3 tools/weekly_curriculum.py validate` locally. Deterministic checks do not replace code execution, diagram rendering or human review.

Official references: [Codex authentication](https://learn.chatgpt.com/docs/auth), [model selection](https://learn.chatgpt.com/docs/models), and [non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode).
