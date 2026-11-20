# Create a pre-read with Codex

Use natural language in the repository, or explicitly invoke `$create-pre-read` where the client supports skill mentions.
This repository does not install a native `/create-pre_read` slash command. `.codex/commands/` contains compatibility documentation only.

Supply:

| Input | Required |
| --- | --- |
| Batch ID | Yes; match `curriculum-index.json` |
| Source session ID | Yes |
| Module ID | When a source session is ambiguous |
| Module name | Yes; context only |
| Session name | Yes |
| Topics | Yes; semicolon-separated or a list |
| Learning objectives | Yes; semicolon-separated or a list |
| Setup | Yes or No |
| Setup text | Only for Yes; pasted instructions, URL, or both |

Example prompt:

```text
Use $create-pre-read for batch IITREICT-AIML-EN-II-2608, session 11.1.
Module: The Data Handling Toolkit: NumPy and Pandas
Session: Cleaning Data I: Missing Values and Duplicates
Topics: Missing values; Dropping and filling; Duplicate rows
Objectives: Identify missing entries; Choose a handling strategy; Remove duplicate rows; Explain why cleaning matters
Setup: No
```

Resolve the destination:

```bash
python3 -I preread/scripts/resolve_session.py --batch IITREICT-AIML-EN-II-2608 --session 11.1
```

The creator writes that session's existing `pre-read.md`. The reviewer then fixes the same file.
Run the checker with the resolved path and the Setup value. Report actual execution and rendering evidence.
No PNG, dated root folder, or review report file is produced.
