# Sources and mapping decisions

## AIML — IITREICT-AIML-EN-II-2608

Source: `IITREICT-AIML-EN-II-2608 - Batch 2 - Institute Version - EICT_AIML_6-month_V3_-_Session_wise_detailed_syllabus.pdf`.

- All 57 taught/masterclass session rows and four capstone rows have lecture folders (61 total).
- Source session 11.1 is Cleaning Data I: Missing Values and Duplicates. The source has no 10.2 row; no replacement 10.2 session was invented.
- Session numbers are preserved, including the duplicate 27.1 in different source sections. Capstone folders are separated from Module 8.
- The syllabus does not give Capstone Project a module number; its folder is `module-capstone-project`.
- Evaluation/examination labels without dedicated lesson rows have not been represented as taught lectures.
- Punctuation and whitespace are normalized for folder names; session meaning is preserved.

## BITSoM — BITSoM-BA-EN-IV-2609

Sources:

- `Business Analytics_BATCH 4_Calendar_Sept2026.xlsx - Calendar.pdf`
- `BITSoM-BA-EN-IV-2609_LO_Tracker.xlsx - LO Tracker.pdf`

- The calendar supplies the full 55-session sequence, including capstone sessions 47–55. The LO tracker covers sessions 1–46.
- Calendar module ranges: 1A = 1–8; 1B = 9–14; 2 = 15–20; 3 = 21–26; 4A = 27–30; 4B = 31–32; 5 = 33–36; 6 = 37–40; 7 = 41–46; 8 = 47–55.
- Some LO tracker module labels disagree with the calendar: examples include sessions 9, 15, 21, 33, 37 and 41. Folder placement follows the calendar; those inconsistencies have not been silently copied into the structure.
- Sessions 37–46 use concise descriptive names derived from the long source descriptions. These are organizational labels, not a claim that the source supplied those exact short titles.
- Several early learning-objective rows appear mismatched to their session titles (e.g., the data distributions and hypothesis testing rows). The scaffold does not copy those objectives into teaching content; reconcile them before authoring.
- Additional user-specified learning objectives for session 13 (layout/design, interactivity, sample dashboard creation) can be used when authoring its material.

## DSAI — IITREICT-DSAI-EN-III-2609

Partial evidence: earlier batch-specific session instructions and available pre-reads, including:

- `From_NumPy_to_Pandas_Series_and_DataFrames_preread.md`
- `Aggregating_and_Combining_groupby_merge_and_reshape_DSAI_preread.md`
- `Cleaning_Data_II_Type_Conversions_and_Tidying_DSAI_preread.md`
- `Databases_and_the_SQL_Landscape_SELECT_Basics_DSAI_preread.md`
- `Filtering_WHERE_and_Operators_DSAI_preread.md`
- `Sorting_Limiting_Aliases_String_Date_Functions_DSAI_preread.md`

Only sessions 5.1–8.2 (NumPy/Pandas) and 9.1, 9.2, 10.1 (SQL) are scaffolded, totaling 11. Module 2's full official title is unverified; `NumPy and Pandas` is a descriptive folder label. Module 3 Part A is SQL. The complete DSAI source PDF was referenced previously but was not located among current accessible resources, so earlier and later curriculum has not been invented.

## Content status

This commit creates the folder layout, navigation, reusable templates, and an exact machine-readable path index. Existing pre-read files have not been migrated; all lesson files are explicitly marked as scaffolds. No completed lectures, learning objectives, or schedules are claimed.
