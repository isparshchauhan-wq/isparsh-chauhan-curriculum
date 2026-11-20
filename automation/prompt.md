Create ONLY the artifact named in each exact run-plan target: pre-read OR lecture-script. The schedules are independent; never create the sibling merely because a session folder contains both scaffolds.

Read AGENTS.md and the applicable canonical preread/ or lecture/ instructions, template and role specs in full. Execute the applicable creator → verifier sequentially. Delegate to the documented roles when available; otherwise use sequential parent passes and disclose that independent review did not run.

For pre-reads, prepare the student curiosity-first document for the scheduled class. It will be released at 15:00 IST the preceding calendar day only after approval and merge. Generation is earlier to allow review. A pre-read request must not modify lecture scripts or images/data.

For lecture scripts, the plan contains all eligible sessions for the following Monday–Sunday, grouped implicitly by batch. This may be one, two, or another count supported by the actual calendar; do not invent or cap the number. Preserve each source duration (90 or 120 minutes), four topics and four quizzes. Pass --duration to the checker. Keep exact source objectives in the Agenda. Where separate topic labels are absent, derive labels within the objectives and disclose that derivation. Setup No; Announcements No. Dates and artifact readiness do not establish which earlier classes were taught.

Edit ONLY the target artifact Markdown and, for lecture scripts only, its images/ and data/. Do not edit siblings, curriculum-index.json, exports, rules, code or workflows. Do not commit, push, create PRs/releases, access credentials, or change settings; publication is handled separately.

Execute applicable demonstrations and record actual outputs, recompute quiz answers, inspect charts, and render Mermaid using installed mmdc (PUPPETEER_CONFIG names its browser configuration). Installed Python packages are available. SQL uses the disposable classroom MySQL service only (localhost:3306, root, password classroom). If sandbox/network limits prevent SQL execution, report Needs verification. Do not invent execution evidence, install packages, or make external API calls. Tableau/UI work that cannot be verified remains Needs verification.

Run the applicable structural checker and fix within documented review limits. Leave usable drafts with needs_verification when a required check is unavailable. Preserve existing content if blocked.

Write JSON to the absolute environment path DAILY_REVIEW_PATH. Keys are exact target directory paths. Each value contains status (accepted|needs_verification|blocked), evidence (actual commands and observed outcomes), unverified_checks (list), independent_review (true only if a separate reviewer agent ran), and notes. Include every planned target, including blocked ones. This temporary report is the only permitted write outside the selected artifact paths. It becomes PR review evidence, never student content.
