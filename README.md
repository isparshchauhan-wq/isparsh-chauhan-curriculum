# Isparsh Chauhan — Curriculum

Curriculum workspace for three Masai batches. Each lecture contains `pre-read.md` and `lecture-script.md`; shared authoring templates are in [templates](templates).

| Batch | Lecture folders | Coverage |
| --- | ---: | --- |
| [IITREICT-AIML-EN-II-2608](IITREICT-AIML-EN-II-2608/README.md) | 61 | Complete scaffold from available source |
| [IITREICT-DSAI-EN-III-2609](IITREICT-DSAI-EN-III-2609/README.md) | 56 | Full supplied syllabus, including capstone |
| [BITSoM-BA-EN-IV-2609](BITSoM-BA-EN-IV-2609/README.md) | 55 | Complete scaffold from available source |

## Folder convention

`<batch>/module-<number>-<topic>/lecture-<source-session>-<topic>/`

For example, [AIML session 11.1](IITREICT-AIML-EN-II-2608/module-03-the-data-handling-toolkit-numpy-and-pandas/lecture-11.1-cleaning-data-i-missing-values-and-duplicates/) contains the pre-read and lecture script for Cleaning Data I.

- All lesson files remain scaffolds until authored and verified. Source objectives are included as authoring inputs.
- Source session IDs are preserved. `lecture-08.1-...` means source session 8.1; integer sessions use `lecture-01-...`.
- Module suffixes such as 1A/1B and 4A/4B are preserved as 01a/01b and 04a/04b.
- AIML capstone slots live in `module-capstone-project` because the syllabus does not assign them a module number. This also keeps the two source sessions numbered 27.1 distinct.
- Schedules in source documents can change; this setup organizes curriculum and does not assert current delivery dates.
- Full original source PDFs are not copied into the repository; source filenames and mapping decisions are recorded in SOURCES.md.

## Updating material

Use the batch README to locate the correct module and session. Replace the scaffold in the existing lesson file with the finished content, update its status, and commit the change. Use [the pre-read template](templates/pre-read-template.md) and [the lecture-script template](templates/lecture-script-template.md) for future material. Do not reuse a session number across batches without checking the batch-specific source.

See [source coverage and mapping decisions](SOURCES.md).

## Curriculum metadata

The supplied curricula are indexed across **172 sessions**. Each batch contains `curriculum.md`, `curriculum.json`, and `curriculum.csv` with source objectives, available topics, scheduled dates, durations, provenance, and authoring caveats. The DSAI syllabus now includes all modules. BITSoM title/objective inconsistencies are flagged for review.

Edit `curriculum-index.json` as the source of truth, then regenerate references:

```bash
python3 tools/sync_curriculum.py
python3 tools/sync_curriculum.py --check
python3 -I -m unittest discover -s tests -v
```

Source schedules and LO checkboxes do not establish whether a class was delivered. Resolve 90/120-minute pacing conflicts and flagged objective mappings before creating a lecture script.


## Codex pre-read workflow

The supplied pre-read pipeline is installed as a repository-scoped Codex workflow. Use `$create-pre-read` where supported, or ask Codex to create a pre-read for a batch and source session. It runs the creator then the verifier on that lecture's existing `pre-read.md`.

- [Setup and compatibility notes](docs/preread-pipeline-setup.md)
- [Inputs and example prompt](preread/commands/create-pre_read.md)
- [Canonical pre-read rules](preread/guidelines.md)
- [Student document template](preread/template.md)

Existing lesson files remain scaffolds until authored. This installation does not mark any session as completed.

Run the offline regression checks from the repository root:

```bash
python3 -I -m unittest discover -s preread/tests -v
```

## Codex lecture-script workflow

Use `$create-lecture-script` or ask for a lecture script with its batch, source session, topics and verbatim learning objectives. The creator and verifier run sequentially on that lecture's `lecture-script.md`, with sibling `images/` and `data/`.

- [Setup and validation limits](docs/lecture-script-pipeline-setup.md)
- [Inputs and examples](lecture/commands/create-lecture-script.md)
- [Fixed v2 template](lecture/template.md)

The pack uses 120 minutes, four topics and four quizzes. Earlier scheduled sessions are not labeled completed without explicit delivery evidence.
