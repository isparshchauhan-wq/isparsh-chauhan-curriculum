# Pre-read pipeline for this curriculum repository

This repository includes the required files from the provided pre-read pack (version 1.0, 2026-11-17), adapted for Codex.
The student-facing structure, single-scenario rules, Bloom outcome verbs, three hinted questions, and ten-category review remain in place.

## What was installed

| Location | Purpose |
| --- | --- |
| `AGENTS.md` | Repository routing and authoring instructions |
| `.agents/skills/create-pre-read/SKILL.md` | Discoverable Codex workflow entry point |
| `.codex/agents/agent_preread_creator.toml` | Creator role definition |
| `.codex/agents/agent_preread_verifier.toml` | Reviewer role definition |
| `.codex/commands/create-pre_read.md` | Invocation reference, not an automatically registered slash command |
| `preread/SKILL.md` | Canonical sequential creator/reviewer workflow |
| `preread/guidelines.md` and `template.md` | Student-facing rules and fixed skeleton |
| `preread/agents/creator.md` and `reviewer.md` | Canonical role instructions |
| `preread/commands/create-pre_read.md` | Inputs and a ready-to-use example |
| `preread/scripts/resolve_session.py` | Read-only resolver for existing curriculum paths |
| `preread/scripts/check_preread.py` | Deterministic checks with JSON output and a failing exit code |

The original examples are optional reference documents and are not installed as course material.
The original Downloads folder is preserved. No personal/global Codex settings or credentials are copied.

## Use it

Open a local checkout of this repository as a Codex project. A GitHub account connection alone does not activate local project instructions in another directory.
Use a current Codex client that supports project skills and custom TOML agents.
Ask to create a pre-read, supplying the batch and source session number, topics, objectives, module/session names, and Setup value.
You can invoke `$create-pre-read` explicitly in clients supporting skill mentions.
See [the command reference](../preread/commands/create-pre_read.md) for a complete example.

The parent resolves the lecture in `curriculum-index.json`, then runs the creator and reviewer in order on the same `pre-read.md`.
AIML session 27.1 is ambiguous without a module: one entry is in Module 8 and another is a capstone slot.
An untouched scaffold can be filled; completed content requires an authorized update.
The workflow preserves the batch/module/lecture structure and does not create dated root folders.

## Validation

Python 3.9 or later runs the two scripts with the standard library.
The checker never executes Markdown snippets. The agent must separately run previews with their setup data, or report them as parsed but not executed.
Mermaid rendering needs an available renderer such as Mermaid CLI and its browser dependencies; Node.js alone is not a completed render check.
If rendering or execution is unavailable, the result remains Needs verification and must not be presented as fully Accepted.
Originality, curriculum alignment, reading level, and unanswered-question quality still need the reviewer.
The checker reports possible scenario reuse; exact wording comparison cannot detect every reused story.

The deterministic checker can reject the supplied examples if they violate the pack's documented rules. Examples are not evidence of passing validation.
Before changing a rule to make a document pass, check for a real rule conflict and report it.

## Changes from the supplied pack

- Native Codex TOML agent files replace Claude-specific Markdown registration and the pinned Claude model. Agents inherit the active Codex model.
- A repository workflow entry point replaces the Claude slash-command assumption. The legacy command file is documentation only.
- Output uses the indexed lecture's `pre-read.md`, replacing dated root folders and the legacy `preread.md` name.
- Scenario discovery scans completed pre-reads recursively across all three batches and recognizes both filenames.
- Required setup text may be pasted instructions, a URL, or both; the workflow never invents a link.
- Deterministic findings now reject the check; execution and rendering are explicitly separate checks.
- Supplied session titles, Topics labels, core-term names, and exact pasted setup input are separated from authored prose for vocabulary checks.
- A finished pre-read changes only its own artifact readiness; a scaffold lecture script keeps the overall session partial.
- Agent registration points to the canonical role instructions, avoiding two copies that can drift.
- The generic pre-read authoring template now points to the fixed pack template. Lecture script templates are unchanged.

## Current limits

The full Codex client was not available as a command-line executable in the setup environment. Configuration, paths, and scripts can be checked here; native role discovery and a full authored pre-read still need a run inside a checkout opened in a supported Codex client.
DSAI coverage remains partial as documented in [SOURCES.md](../SOURCES.md).

## Platform references

- [Codex custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
- [Repository skills](https://learn.chatgpt.com/docs/build-skills)
