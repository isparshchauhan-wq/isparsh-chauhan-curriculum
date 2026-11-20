# Curriculum repository instructions

## Manual weekly generation

For “Generate next week’s curriculum materials”, run `python3 tools/weekly_curriculum.py generate` from a Git checkout. Use `plan`, `resume` and `status` as documented in [the weekly guide](docs/daily-curriculum-automation.md). The runner selects models and effort from `automation/model-policy.json` before launching separate ChatGPT-authenticated Codex CLI tasks. If it cannot run, report the blocker. Preserve its manifest, validation and draft PR workflow. Merge only with explicit owner authorization. Student pre-reads are published manually in the LMS at 15:00 IST the calendar day before class. Instructors receive scripts manually for their teaching week.

## Curriculum and artifact rules

- Resolve sessions through `curriculum-index.json` using batch, module and source session ID. Preserve paths, source numbering, exact objectives and dates. AIML 27.1 needs module disambiguation.
- Use indexed dates, objectives, topics and durations, and consult `SOURCES.md` for conflicts. Do not infer teaching delivery, resolve flagged source conflicts silently, or overwrite verified material without a requested revision.
- Pre-reads use `preread/SKILL.md` and `preread/template.md`. Lecture scripts use `lecture/SKILL.md` and `lecture/template.md`. The corresponding repository skills point to the canonical rules.
- For ad hoc authoring, run the applicable creator then verifier sequentially. Prefer the named agents in `.codex/agents/`, then separate agents with the canonical role specs. Disclose when independent verification could not run. For a runner task, act only as the supplied creator or verifier role.
- Use source durations of 90 or 120 minutes, four lecture topics and four quizzes. Confirm missing duration or an unresolved objective grouping. Keep batch/module identifiers out of the student document. Preserve supplied setup text without inventing URLs.
- Run the artifact checker and verify code outputs, diagrams, calculations, quizzes and assets as applicable. Report unavailable checks accurately. Keep artifact generation, verification, human approval, LMS publication and class delivery separate.
- After changing the index, run `python3 tools/sync_curriculum.py`. Preserve unrelated work and use a branch and draft PR for curriculum changes.
