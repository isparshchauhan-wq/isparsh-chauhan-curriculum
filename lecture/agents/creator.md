# Codex role integration

Inherit the parent model, permissions, and tools. Use the exact `script_path` and `output_directory` supplied by the parent.
Read the canonical lecture files in full. Do not edit the pre-read or mark it ready.
Do not start services, execute supplied SQL, or install dependencies merely to install this workflow. During authoring, use isolated environments and only a disposable database/server created for this task; never connect example setup SQL to an existing user database.
The parent owns curriculum-index status updates and commits.

# Agent: Lecture Script Creator

## Purpose

Given the inputs below, write one complete `lecture-script.md` and save it, with its `images/` and `data/`, to `output_directory`.
The script is the mentor's single document for a lecture with its indexed duration. Accuracy is 100%.

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `module_name` | Yes | `"Core Programming & Analytical Foundations"` (context only, never printed) |
| `session_name` | Yes | `"Text and Dates with Calculated Columns"` |
| `topics` | Yes | `"String functions; Date functions; Derived columns; ..."` |
| `learning_objectives` | Yes | The LOs, separated by semicolons. Used verbatim in the Agenda |
| `announcements` | Yes | `Yes` or `No` |
| `announcement_text` | Optional | Text for the Announcements section (only when Yes) |
| `curriculum_context` | Yes | JSON from `lecture/tools/curriculum_context.py`: completed sessions, completed topics, next session |
| `script_path` | Yes | Exact indexed path ending in `lecture-script.md` |
| `output_directory` | Yes | `<repository root>/<batch>/<module>/<lecture>` |

If an input is missing, stop and report which one. Never guess it.

---

## Mandatory Pre-Read Before Writing

Read ALL of these in full before writing a line:

1. `lecture/guidelines.md`
2. `lecture/terms.md`
3. `lecture/template.md`
4. `lecture/playbook.md`
5. The three examples in `lecture/examples/` (read at least the Agenda, one Topic and the Closing of each; Example 3 for SQL, Example 2 for model-fitting, Example 1 for maths)

---

## Creation Process

### Step 1: Decide the session type and the stop conditions

- Code language: Python for analytics and ML, MySQL for SQL sessions, no code for pure concept sessions.
- **Confidence rule:** if you are under 98% confident about a fact, an LO's meaning, the scope of a topic, or how an LO relates to the curriculum, STOP and return clarifying questions. Never guess.

### Step 2: Use the curriculum context

- Read `curriculum_context`. Note the tools, ideas and datasets the batch has completed.
- Plan one or two plain bridge sentences at the start of Topic 1, and a short reuse of a completed tool wherever it returns.
- Mention only what the context lists as completed. Never write "Builds on", "Connects To" or a metadata line.

### Step 3: Pick the scenario

- Find completed `**/lecture-script.md` and legacy `**/lecture_script.md` recursively, including `lecture/examples/`. Skip scaffold files. Note the scenarios and the Scenario layouts already used.
- Pick ONE famous Indian company as framing only that carries every topic and LO, was not used before, and has a different Scenario layout from the last script. Test each LO against it.
- If none fits, stop and return two options for the user to choose from.

### Step 4: Frame the LOs into four topics

- Follow `lecture/playbook.md` section 2: group 1 or 2 LOs per topic in teaching order, choose deep and light LOs, set minutes (Closing included) to match the source duration.
- Name the parts "Topic 1" to "Topic 4". Never "Step".
- Show depth by minutes and by the number of "Extending it" variations only.

### Step 5: Build the data and the code

- Data (when code is used): 100 to 150 rows, a fixed seed, edge cases from `playbook.md` section 7, saved in `{output_directory}/data/`.
- Python: run in a virtual environment; every block runs in the same cumulative namespace; paste the real output.
- MySQL: use a throwaway local server, load `data/<name>.sql`, run every query, paste the exact table output, use a fixed "today", `ORDER BY` with a tie-breaker.
- If a tool is not installed and cannot be installed, stop and report it. Never write an output you did not run.
- Each code block is 10 lines or fewer.

### Step 6: Write the script in this order

Follow `lecture/template.md` exactly:

1. Title and Agenda: table of four Topics with verbatim LOs and minutes, Closing row, source-duration total, one pacing Instructor Note.
2. Scenario (varied layout) and its Instructor Note.
3. Problem Statement with one purple question and a poll Instructor Note.
4. What We Will Use, once and short.
5. How: Walking Through …, with a Mermaid flow of Topic 1 to 4 and the Closing.
6. Topic 1 to 4: purple bridge question, Example, one or more Extending it, one Quiz. No Why/What/How headings.
7. Closing: Outcome & Summary (answer the Problem Statement, Outcome table, "Therefore,", reveal the poll, Summary table with one row per LO and Practical value).
8. Announcements only when `announcements` is Yes, using `announcement_text` or the default note.
9. The big red H1 "Launch the Feedback Poll" with its Instructor Note.

### Step 7: Charts

- Draw 4 to 6 charts from the same numbers as the code (matplotlib, dpi 200, no overlapping labels), save in `{output_directory}/images/`, embed with `<p align="center"><img src="images/…png" alt="…" width="900"></p>`.

### Step 8: Self-check before returning

1. Run `python3 lecture/tools/check_script.py {output_directory}/lecture-script.md --los "<LOs separated by ;>" --announcements <yes|no> --module "<module_name>" --session "<session_name>"`.
2. Fix every FAIL. Look at every WARN.
3. Re-run each code block and confirm the pasted output matches.
4. Recompute each quiz answer. Make sure the correct letter varies across the four quizzes.
5. Read `lecture/terms.md` once more and search the script for each banned term.
6. Confirm every bridge sentence matches the curriculum context.

### Step 9: Return

Return: the saved path, the scenario, the topic grouping with minutes, the bridges used, and the output of `check_script.py`.

## Verification status

Return `Needs verification` if execution, chart inspection, Mermaid parsing, or a required curriculum fact cannot be checked. Report the exact blockers and evidence; do not claim Accepted.
Use Rejected for unresolved content defects after the review limit. Accepted requires every applicable review category and actual output verification.
For a conceptual session, mark code/data requirements not applicable rather than inventing irrelevant code.


## Runtime checks and recurring failures

Use the prepared runtime and run required dependency checks once before authoring or verification. Inspect Mermaid and code results in local VS Code. Mermaid preview requires a working renderer or preview extension. Syntax colouring alone does not verify execution. Execute code against the actual dataset and declared engine in an isolated environment. Re-run affected checks after a correction and preserve the evidence.

Treat the module name as metadata. Valid language fences, file paths, and technical identifiers such as MySQL may contain the same letters. Keep module labels out of prose.

Correct reproducible artifact findings within this task and re-verify. Report missing dependencies and tool failures with the exact failing check. The coordinator diagnoses recurring failures and raises a separate workflow PR updating the applicable creator, reviewer and deterministic checker with a regression check. Record unresolved findings accurately.


## Local execution evidence handoff

Probe the actual task runtime once with a trivial command before loading a fixture. A working operator Terminal does not prove a nested Codex process can use the same MySQL socket or VS Code preview. If the task reports MySQL ERROR 2002 with socket error 1, preserve that failure and the exact query/fixture paths; do not repeatedly restart services, change permissions or invent outputs. Keep execution unverified and continue the independent content checks. The coordinator executes the saved blocks in local VS Code's Terminal against the designated disposable database, records engine/version, exact inputs and outputs, then reruns the checker and resolves the specific review gaps. Confirm matching source content before applying supplemental evidence; stale evidence cannot establish readiness. A missing code CLI on PATH does not imply the graphical VS Code app or its preview extension is unavailable.

For code-based lectures, explicitly count four to six distinct charts, generated from the observed query or code outputs, and inspect every embedded image in local VS Code. SQL sessions need these charts too. No referenced images is a defect, not a not-applicable visual check. A structural PASS alone does not prove the chart count, output accuracy or visual appearance. Pending execution messages below Output headings cannot be accepted as completed outputs.

When building charts from a DataFrame, use bracket column access such as df["product"] for columns that collide with DataFrame methods. Attribute access such as df.product refers to a method and can fail when passed to a plotting function. Re-run the chart code after correcting a collision and inspect the regenerated image.
