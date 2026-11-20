# Lecture-script pipeline for Codex

Adapted from the supplied Lecture Script Pipeline v1.0 (2026-11-18, lecture format v2).

## Included files

| Location | Purpose |
| --- | --- |
| `.agents/skills/create-lecture-script/SKILL.md` | Repository workflow entry point |
| `.codex/agents/agent_lecture_creator.toml` | Creator registration |
| `.codex/agents/agent_lecture_verifier.toml` | Verifier registration |
| `lecture/SKILL.md` | Sequential authoring, review, and readiness workflow |
| `lecture/guidelines.md`, `terms.md`, `template.md`, `playbook.md` | Canonical format and teaching rules |
| `lecture/agents/creator.md`, `reviewer.md` | Canonical role specifications |
| `lecture/commands/create-lecture-script.md` | Input and invocation reference |
| `lecture/tools/curriculum_context.py` | Exact session matching and confirmed completion context |
| `lecture/tools/check_script.py` | Deterministic structural and asset checks |
| `lecture/examples/` | All three supplied reference scripts, PNG charts, datasets, and sample CSV |
| `lecture/tests/` | Offline regression checks |

The Downloads source is preserved. No `.claude` registration or pinned Claude model is installed. Both roles inherit the active Codex model and permissions.
The existing pre-read workflow remains separate. `templates/lecture-script-template.md` now points to the fixed lecture template.

## Use it

Open this repository as a Codex project. Use `$create-lecture-script` where supported, or ask in ordinary language.
Supply the batch, source session ID, topics, verbatim learning objectives, module/session names and Announcements Yes/No.
The [invocation reference](../lecture/commands/create-lecture-script.md) contains commands and an example prompt.
The `.codex/commands` Markdown file documents migration; it does not register a native slash command.

The shared resolver now accepts `--artifact lecture-script`. Its default remains `pre-read`, preserving existing behavior.
The output is the existing lecture's `lecture-script.md`, with sibling `images/` and `data/`. No dated root directory is created.
AIML source session 27.1 occurs twice; supply its module to disambiguate.

## Rules preserved

One Why, What and How; four Topic sections; four quizzes; verbatim Agenda LOs; 120 total minutes; one company-framed teaching scenario; code blocks of at most ten lines; actual outputs; chart/data consistency; optional Announcements; final Feedback Poll.
Creator and verifier run sequentially on the same script and assets. A script is not Accepted until every applicable check has evidence.
Reference examples retain their original `lecture_script.md` filename and are teaching references, not authored batch sessions.
Their recorded outputs are not evidence of a fresh code run.

## Corrections and integration decisions

- Source CSV matching used fuzzy matches without confirmation. The reader now requires an exact normalized title or explicit source ID and rejects ambiguous targets.
- Source CSV logic inferred completion from row order when status was missing. The reader now separates earlier scheduled material from explicitly completed material.
- Repository-index completion reads only `delivery_status`. Artifact `status: ready` does not mean taught. Missing topics/LOs remain unknown.
- CSVs may supply a `delivery status`, `coverage status`, or `status` field. Explicit done/completed/delivered values establish earlier completed sessions. Mixed-batch CSVs must identify the intended batch.
- `--columns` works even when required title/topics columns are not yet mapped. Ambiguous duplicate aliases produce a clarification request.
- Agenda pacing checks are scoped to Agenda rows. Unrelated numeric tables no longer change the minute total.
- Each quiz must have unique A–D options and explanations. Agenda LOs are compared as whole items rather than substring matches.
- A missing mandatory Output label is a failure. Feedback Poll ordering and local image-path containment are checked.
- Readiness is per artifact: `lecture_script_status` and `pre_read_status`. Overall `ready` requires both; one finished artifact leaves the session `partial`.

## Source conflicts to resolve before authoring

The index and context helper now include source objectives, source durations, schedules, and authoring caveats for all three batches. BITSoM tracker checkbox values are recorded separately and do not establish delivery.

The supplied format is fixed at 120 minutes. The BITSoM calendar includes 90-minute sessions and AIML contains shorter masterclasses. Do not silently stretch those sessions; agree on pacing before creating their scripts.
The source says four topics, normally one or two LOs per topic, and each verbatim Agenda LO once. Its fewer-than-four-LO advice is ambiguous. Obtain an explicit coverage plan in that case rather than inventing or duplicating objectives.
Treat the source's numerical confidence/accuracy language as a quality requirement, not a measurable guarantee from the checker.

## Checks and current limits

Run from the repository root:

```bash
python3 -I -m unittest discover -s lecture/tests -v
python3 -I -m unittest discover -s preread/tests -v
```

The helpers use Python 3.9+ and the standard library. Registration checks cover the deliberately restricted string-field schema; native Codex role discovery has not been exercised here.
The structural checker never executes lesson code or proves factual correctness. The verifier must rerun Python or MySQL code, recompute quiz answers, inspect each chart, and validate Mermaid.
Scientific Python packages, a supported MySQL server for SQL lessons, and a Mermaid renderer are required as applicable during authoring. Installation does not install or start them.
Use an isolated environment and a disposable database/server. Never run the supplied example SQL against an existing user database.
If required execution or rendering is unavailable, report Needs verification rather than Accepted.
No batch lecture script or lesson-completion status was changed by installing this pipeline.
