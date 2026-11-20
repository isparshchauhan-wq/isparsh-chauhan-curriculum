# Sources and mapping decisions

Curriculum refreshed on 20 November 2026 from the three supplied PDFs. `curriculum-index.json` is the authoritative editable index. Batch JSON, CSV, Markdown references and navigation are generated from it with `python3 tools/sync_curriculum.py`.

## AIML — IITREICT-AIML-EN-II-2608

Source: `IITREICT-AIML-EN-II-2608 - Batch 2 - Institute Version - EICT_AIML_6-month_V3_-_Session_wise_detailed_syllabus(1).pdf` (4 pages).

- All 57 instructional/masterclass rows and four capstone slots have folders (61 total).
- Objectives, separately listed topics, scheduled dates, durations and source page references are indexed. Most sessions are 120 minutes; five masterclasses are 90 minutes. Capstone durations and objectives are unspecified.
- Cleaning Data I is session 11.1. The source has no 10.2 row.
- Both source sessions numbered 27.1 are retained: Module 08 (Agentic AI) and the unnumbered capstone section. Select a module when resolving this ID.
- Capstone has no source module number, so it uses `module-capstone-project`.
- Source row order and dates are retained even where dates are nonmonotonic. Evaluation labels without a dedicated lesson row do not create lecture folders.

## DSAI — IITREICT-DSAI-EN-III-2609

Source: `IITREICT-DSAI-EN-III-2609 - Batch 3 - Institute Version - DSAI V2 syllabus.pdf` (4 pages).

- Full coverage is now available: 52 instructional rows plus four capstone slots (56 total), replacing the earlier partial 11-session scaffold.
- Module groups: 01 Programming & Data Foundations; 02 Data Analysis with NumPy & Pandas; 03A SQL; 03B Visualization & Data Storytelling; 04 Maths & Statistics for Data Science; 05 Machine Learning; 06 GenAI for Data Science; unnumbered Capstone Project.
- Module 02's former descriptive folder `module-02-numpy-and-pandas` is replaced by `module-02-data-analysis-with-numpy-and-pandas`. Its existing eight session folders are moved with their contents. Module 03A retains its existing path and gains the remaining SQL sessions.
- All 52 instructional rows specify 120 minutes. Capstone dates, durations, topics and objectives are unspecified and remain null/empty.
- Batch-specific source IDs are preserved: DSAI Cleaning Data I is 7.2, while AIML Cleaning Data I is 11.1.

## BITSoM — BITSoM-BA-EN-IV-2609

Primary source: `BITSoM-BA-EN-IV-2609_LO_Tracker.xlsx - LO Tracker(1).pdf` (5 pages), covering sessions 1–46 and 159 printed LO IDs.

Retained source: `Business Analytics_BATCH 4_Calendar_Sept2026.xlsx - Calendar.pdf` (3 pages), supplying the full 55-session sequence, module placement, 90-minute durations, and capstone slots 47–55.

- Calendar module ranges: 1A = 1–8; 1B = 9–14; 2 = 15–20; 3 = 21–26; 4A = 27–30; 4B = 31–32; 5 = 33–36; 6 = 37–40; 7 = 41–46; 8 = 47–55.
- Some tracker module labels differ from the calendar (including 9, 15, 21, 33, 37 and 41). Placement follows the full calendar; the discrepancy is recorded in the affected sessions' notes.
- Sessions 37–46 retain concise organizational titles derived from long source descriptions. These are not exact short titles supplied by the source.
- Early tracker titles and LO blocks appear misaligned. For example, session 2 is titled Understanding Data Distributions but LO 2.1–2.4 describe KPIs; session 3 is titled Hypothesis Testing Fundamentals but LO 3.1–3.4 describe Excel. Sessions 2–12 are flagged `curriculum_review_required` conservatively. Printed LOs remain under their printed IDs, with a warning in each affected scaffold. Reconcile the intended mapping before authoring; no remapping is assumed.
- Session 13 has one printed LO. The previously supplied user objectives (Layout and Design; Interactivity using filters etc.; Sample Dashboard creation) are preserved separately as supplemental objectives, not attributed to the PDF.
- The tracker uses FALSE in its LOs Covered column. `source_learning_objectives[].covered` records that checkbox value only. It does not imply a confirmed delivery state.
- Capstone slots retain calendar attribution and do not acquire invented objectives from the new tracker.

## Interpretation and authoring limits

PDF line-wrap whitespace is normalized; source wording and numbered LO identifiers are preserved. Folder punctuation is normalized. Empty topic/objective lists and null durations/dates mean unspecified. No private account identifiers or download URLs are recorded here; original PDFs are not copied into the repository.

Scheduled dates are source-plan dates and may change. All delivery states remain unknown unless supported by separate delivery evidence. Material readiness is independent: scaffolds are not completed pre-reads or lecture scripts.

The lecture workflow uses a standard 120-minute template. BITSoM sessions and AIML masterclasses require an explicit pacing decision before authoring. Some rows have fewer objectives than the template's four-topic format; define coverage without inventing or duplicating source objectives.
