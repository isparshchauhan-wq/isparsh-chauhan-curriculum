# Create a lecture script with Codex

Use `$create-lecture-script` where skill mentions are supported, or ask in ordinary language. The Markdown command reference is not an automatically registered slash command.

Supply batch ID, source session ID, module name, session name, topics, exact LOs, Announcements Yes/No, and optional announcement text. Supply a curriculum CSV when delivery status or richer context is needed; otherwise use the index and do not claim completion without evidence.

```text
Use $create-lecture-script for batch IITREICT-AIML-EN-II-2608, session 11.1.
Module: The Data Handling Toolkit: NumPy and Pandas
Session: Cleaning Data I: Missing Values and Duplicates
Topics: Missing values; Dropping and filling; Duplicate rows
Learning objectives: <paste the authoritative objectives verbatim>
Announcements: No
```

Resolve the existing directory:

```bash
python3 -I preread/scripts/resolve_session.py --batch IITREICT-AIML-EN-II-2608 --session 11.1 --artifact lecture-script
```

Read context from the index:

```bash
python3 -I lecture/tools/curriculum_context.py --index curriculum-index.json --batch IITREICT-AIML-EN-II-2608 --session-id 11.1 --json
```

Or inspect an external CSV:

```bash
python3 -I lecture/tools/curriculum_context.py curriculum.csv "Exact Session Title" --json
python3 -I lecture/tools/curriculum_context.py curriculum.csv --columns
```

CSV target matching is exact after whitespace/case normalization. Duplicate titles or IDs require disambiguation; suggestions are not selected automatically. Exit 2 means input or mapping needs clarification.

After authoring, run `python3 -I lecture/tools/check_script.py <script_path> --los <semicolon-separated LOs> --announcements no --module <module_name> --session <session_name>`.
Pass inputs as process arguments; do not interpolate arbitrary user text into a shell command.
