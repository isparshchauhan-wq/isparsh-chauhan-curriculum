# Terms: use and do not use

## Use

| Say | Where |
|:--|:--|
| **Topic 1** to **Topic 4** | The four parts of the lecture: Agenda, headings, Mermaid flow, cross-references |
| **Mentor** | Whoever delivers the lecture. Write "Give learners 30 seconds to respond in chat." |
| **learners** | The audience |
| **Example**, **Extending it** | Headings for the worked example and its variations |
| **Predict before running: What will happen?** | Before the first run of each code block |
| **Code Explanation** / **Logic Explanation** | Under every code block / for reasoning with no code |
| **Result**, **Therefore,** | Green sentence after an output / the final answer |
| **Instructor Note** | Red note with the 🎯 heading, 1 to 2 lines |
| **Closing: Outcome & Summary** | The final teaching section |
| **Launch the Feedback Poll** | Big red H1 at the very end |
| "an Ola-style cab app", "a Flipkart-style shopping app" | Framing a real company. Add the Instructor Note that the data is invented |
| "invented for teaching" | The only way to describe the data's origin |
| Bridge in plain prose: "Last session you used GROUP BY" | Only for completed sessions listed in the curriculum CSV |

## Do not use

| Do not write | Use instead |
|:--|:--|
| synthetic | invented for teaching |
| Step 1 to Step 4 (as the name of a lecture part), Block, Part | Topic 1 to 4 |
| facilitator, trainer, instructor (as the person) | mentor |
| I Do, We Do, You Do (as stage labels) | Example, Extending it |
| Recap | none; the Closing answers the Problem Statement |
| Break, Time plan, Session Spine, Exit Ticket, Appendix | none |
| Connects To, Builds on, Format: (metadata lines) | a plain bridge sentence in prose |
| [Script:] or any scripted-line label | concept-style text |
| The Module Name | never printed |
| Any emoji except 🎯 | none |
| Per-topic "Why", "What", "How" headings | one Why, one What, one How per lecture |
| "deep", "light", "breadth", "depth" labels | show it by minutes and variations |
| Forward references ("more on that in Topic 4") | say it where it is taught |
| A real company's name with a claim that it uses these numbers | the Instructor Note disclaimer |
| Unfilled `{{ }}` placeholders | none |

Ordinary English such as "step by step" or "the standardising step" is allowed. It must never name a lecture part.

## Repository integration

Resolve the destination from `curriculum-index.json`, using the exact batch, module, and source session number.
Save `lecture-script.md` in that existing lecture directory, with `images/` and `data/` beside it. Never create a dated root folder.
Use `lecture/tools/curriculum_context.py` with the repository index or a supplied CSV. Only explicit delivery/coverage status can establish completed material; `ready` describes an artifact and does not mean taught.
When status is missing, report earlier sessions as scheduled/unconfirmed and do not claim learners completed them.
This pack's pacing is 120 minutes. If an authoritative session duration differs, resolve the pacing decision with the user before authoring.
The source specifies four topics and normally one or two LOs per topic. For fewer than four LOs, or conflicting grouping rules, resolve an explicit coverage plan rather than inventing or duplicating verbatim Agenda LOs.
