# Curriculum repository instructions

## Manual weekly generation

For a weekly run, ask the owner for the starting topic or source session ID if they have not provided one. Resolve its batch, module, session and date in `curriculum-index.json`. A unique topic is sufficient. Use the Saturday–Friday teaching week in Asia/Kolkata that contains that date. Select the starting session and later sessions in the same batch and week, in scheduled date order with ties in curriculum index order. Preserve ready artifacts and existing checkpoints.

Prepare a single copy-and-paste Terminal command block with exact batch, module and session selectors and `--local-only`, as shown in [the weekly guide](docs/daily-curriculum-automation.md). The owner launches the runner in Terminal. Codex tracks the manifest and task logs, verifies the saved materials and assets, and opens or updates the draft GitHub PR after the selected work finishes. Resume only within the selected scope. Report blockers with their checkpoint state. The runner selects models and effort from `automation/model-policy.json` before launching separate ChatGPT-authenticated Codex CLI tasks.

On a weekly PR, the owner's `Review done <commit SHA>` comment authorizes merging that exact revision after validation. The weekly ZIP includes existing resources from earlier sessions in the batch that week. If those earlier sessions have missing resources, report the gap before approval because the merge and full-week package require both resources for every scheduled session. Provide the merged ZIP in the requesting conversation. Student pre-reads are published manually in the LMS at 15:00 IST the calendar day before class. Instructors receive their weekly resources manually.

## Curriculum and artifact rules

- Resolve sessions through `curriculum-index.json` using batch, module and source session ID. Preserve paths, source numbering, exact objectives and dates. AIML 27.1 needs module disambiguation.
- Use indexed dates, objectives, topics and durations, and consult `SOURCES.md` for conflicts. Do not infer teaching delivery, resolve flagged source conflicts silently, or overwrite verified material without a requested revision.
- Pre-reads use `preread/SKILL.md` and `preread/template.md`. Lecture scripts use `lecture/SKILL.md` and `lecture/template.md`. The corresponding repository skills point to the canonical rules.
- For ad hoc authoring, run the applicable creator then verifier sequentially. Prefer the named agents in `.codex/agents/`, then separate agents with the canonical role specs. Disclose when independent verification could not run. For a runner task, act only as the supplied creator or verifier role.
- Use source durations of 90 or 120 minutes, four lecture topics and four quizzes. Confirm missing duration or an unresolved objective grouping. Keep batch/module identifiers out of the student document. Preserve supplied setup text without inventing URLs.
- Run the artifact checker and verify code outputs, diagrams, calculations, quizzes and assets as applicable. Report unavailable checks accurately. Keep artifact generation, verification, human approval, LMS publication and class delivery separate.
- After changing the index, run `python3 tools/sync_curriculum.py`. Preserve unrelated work and use a branch and draft PR for curriculum changes.
