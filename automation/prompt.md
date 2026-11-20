Prepare the pre-read AND lecture script for each target in the exact run plan below.
Read AGENTS.md and the canonical preread/ and lecture/ instructions, templates, and role specs in full before authoring. Execute pre-read creator → verifier, then lecture creator → verifier, sequentially. Delegate to the documented roles where available; otherwise use sequential parent passes and disclose the lack of independent review.

The user authorized source-duration lectures: 90 or 120 minutes as specified in each target. Preserve four topics and four quizzes; change pacing and the Agenda total to the target duration. Run check_script.py with --duration. Do not stretch 90-minute classes to 120 minutes. Do not invent, duplicate, or silently replace objectives. Where topics are not separately enumerated, derive teaching topic labels within the exact supplied objectives and disclose that derivation. Setup: No; Announcements: No. Never infer that earlier scheduled material was taught.

Edit ONLY selected target pre-read.md, lecture-script.md, images/, and data/. Preserve an already-ready artifact; author only its missing sibling. Do not edit curriculum-index.json, exports, rules, scripts, workflows or other sessions. Do not commit, push, open PRs, access credentials or modify settings. The publisher handles status and GitHub changes.

Run each code block with actual outputs, recompute quiz answers, check charts, and render Mermaid with installed mmdc. Use Python's installed packages. For SQL, use the job's disposable MySQL service (localhost, port 3306, root, password classroom); never connect to any other database. Freeze dates/seeds and keep all teaching assets beside their script. Tableau/UI demonstrations that cannot be verified remain Needs verification. Do not claim execution based on source examples or a checker alone. Do not install dependencies or make network calls from the agent; report missing dependencies instead.

Run the structural checkers. Fix problems within the documented review limits. Never mark a scaffold accepted. If any required check is unavailable, keep usable drafts and report needs_verification. If blocked, preserve existing content and report the reason. Do not invent missing setup instructions, APIs, links, credentials or source facts.

Write a machine-readable JSON report to the absolute path in environment DAILY_REVIEW_PATH. Its keys must be the exact target path strings. Each value must contain:
- status: accepted, needs_verification, or blocked
- evidence: a list of actual commands/checks run and observed results
- unverified_checks: a list, empty only if all applicable checks passed
- independent_review: true only if a separate reviewer agent actually ran
- notes: concise findings, fixes and limitations
This temporary report is the ONLY permitted write outside the selected lesson paths. It will appear in the draft pull request, not in student documents. Keep all selected targets represented, including blocked ones.
