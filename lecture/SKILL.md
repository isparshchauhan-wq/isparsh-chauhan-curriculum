---
name: create-lecture-script
description: Create and verify a source-duration lecture script with four topics and four quizzes, using exact learning objectives, tested outputs, charts and confirmed curriculum context. Use for lecture-script authoring and updates, not for pre-reads or repository setup.
---

# Create and verify a lecture script

Read `lecture/guidelines.md`, `lecture/terms.md`, `lecture/template.md`, `lecture/playbook.md`, and `lecture/commands/create-lecture-script.md` before authoring.

1. Collect batch ID, source session ID, module name, session name, topics, verbatim LOs, Announcements Yes/No, and optional announcement text. Use supplied authoritative context before asking for missing inputs. A curriculum CSV is optional when the repository index identifies the session; it is needed for additional delivery/topic details not in the index.
2. Resolve the destination with `python3 -I preread/scripts/resolve_session.py --batch <batch> --session <id> --artifact lecture-script`. Supply `--module` for ambiguous source IDs. Verify module and title. Fill an untouched scaffold, or update completed content when the user authorized that update.
3. Read context with `python3 -I lecture/tools/curriculum_context.py --index curriculum-index.json --batch <batch> --session-id <id> --module <module> --json`, or use an authoritative CSV via the documented interface. Do not infer taught material from scheduling, file readiness, or dates. Resolve uncertain bridges before using them; an empty confirmed list means no claim of completed material.
4. Confirm pacing against the source. Use the indexed source duration (90 or 120 minutes). Resolve missing durations and objective-grouping conflicts before drafting. Preserve all source LOs.
5. Pass all inputs, context, exact `script_path`, and its parent `output_directory` to `agent_lecture_creator`. Wait for it to finish. Then pass the same inputs and assets to `agent_lecture_verifier`, including announcement text. Use `lecture/agents/creator.md` and `reviewer.md` as the canonical role specs. If named roles are unavailable, use general-purpose subagents with those specs. If delegation is unavailable, perform sequential passes and disclose that independent review did not run.
6. Keep the single Why/What/How format, four Topic sections, four quizzes, verbatim Agenda LOs and indexed source-duration total. Save `lecture-script.md`, `images/`, and `data/` in the indexed lecture directory. Inspect the three reference examples in `lecture/examples/`; do not treat their recorded outputs as newly verified.
7. Run `lecture/tools/check_script.py` with exact LOs, announcement flag, module, and session inputs. It checks deterministic structure and assets, not factual accuracy or actual code execution. Re-run all code in an isolated appropriate environment, compare real outputs, recompute quiz answers, inspect charts, and validate Mermaid. Never fabricate outputs or run imported SQL against an existing user database. If dependencies are unavailable, report Needs verification.
8. Report Accepted only after all applicable checks pass; Rejected for unresolved defects; Needs verification for unavailable checks or missing evidence. Do not claim numerical confidence guarantees. State the path, scenario, topic minutes, confirmed bridges, fixes, and limitations.
9. After acceptance, set `lecture_script_status` to `ready` in `curriculum-index.json`. Set overall `status` to `partial` unless `pre_read_status` is also `ready`; only then set the overall session `ready`. Never mark an untouched pre-read ready. Commit intended script, assets, and metadata together and verify any authorized remote update.

Keep rules and templates canonical in `lecture/`. Role registration files point to the master Markdown specs; do not maintain duplicate copies.
