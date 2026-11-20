---
name: create-pre-read
description: Create and review one curiosity-first curriculum pre-read using the supplied module, session, topics, objectives, and optional setup text. Use for pre-read requests in this curriculum repository; do not use for lecture scripts or generic curriculum scaffolding.
---

# Create and review a curriculum pre-read

Read `preread/guidelines.md`, `preread/template.md`, and `preread/commands/create-pre_read.md` before writing.
Use the repository root containing `curriculum-index.json` and `preread/`.

1. Collect `batch_id`, `session_id`, `module_name`, `session_name`, `topics`, `learning_objectives`, and `setup` (`Yes` or `No`). Require `setup_text` only for `Yes`. The user may provide text, a URL, or both. Use already supplied, authoritative curriculum information before asking; never invent missing inputs.
2. Resolve the existing lecture with `python3 -I preread/scripts/resolve_session.py --batch <batch_id> --session <session_id>`. Supply `--module <module_id>` if the source session number occurs twice, as for AIML 27.1. Check that the resolved title and module match the request. Report ambiguity rather than choosing silently.
3. Use the returned absolute `output_path`, ending in `pre-read.md`. Replace an untouched scaffold. Update an existing completed pre-read when the user's request authorizes that update; otherwise ask before replacing completed content. Preserve other files and directories.
4. Read `preread/agents/creator.md`. Spawn `agent_preread_creator` with the resolved path and all inputs. Wait for creation to finish before starting review.
5. Read `preread/agents/reviewer.md`. Spawn `agent_preread_verifier` with the same path and all inputs, including `setup_text`. Have it review all ten categories and fix the pre-read in place within the documented iteration limit. Do not run both writers concurrently on the same file.
6. If custom roles are unavailable but delegation exists, spawn general-purpose agents with each canonical role specification. If delegation is unavailable, perform creator then reviewer passes in the parent and clearly report that no independent agent review ran.
7. Run `python3 -I preread/scripts/check_preread.py --file <output_path> --setup Yes|No --root .`. When Setup = Yes, also pass the exact supplied setup text as `--setup-text` so literal input can be distinguished from authored prose. Test each code preview with its needed setup and confirm output. If a dependency is unavailable, parse and report `parsed-not-executed`. Render Mermaid when the required renderer is available; otherwise report render validation as unavailable.
8. Report Accepted only when all required content, deterministic, code, and diagram checks are satisfied. If any remain unverified, report Needs verification. If findings remain after the reviewer limit, report Rejected. Report the actual path, scenario, fixes, and unverified checks without writing review side files.
9. Once accepted, set that session's `pre_read_status` to `ready` in `curriculum-index.json` and keep the pre-read at the same indexed path. Set overall `status` to `partial` while the lecture script remains a scaffold; mark the overall session `ready` only after `pre_read_status` and `lecture_script_status` are both `ready`. Do not mark the untouched lecture script ready. This repository expects completed changes to be committed. If an authorized remote write is available, synchronize the intended changes and verify the result; otherwise report the local change and the remaining synchronization step.

Search for scenario reuse across completed `**/pre-read.md` and legacy `**/preread.md` files. Skip scaffolds and templates.
Keep canonical rules in `preread/guidelines.md` and `preread/template.md`. Keep role behavior in `preread/agents/creator.md` and `reviewer.md`.
The `.codex/agents/*.toml` files register roles and point to these canonical instructions; do not maintain duplicate role copies.
