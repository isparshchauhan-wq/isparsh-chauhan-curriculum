# Learning Git and GitHub through this curriculum project

## 1. What we are managing

Your repository is https://github.com/isparshchauhan-wq/isparsh-chauhan-curriculum . It contains the three batch curricula, session pre-reads and scripts, templates, agent instructions, validation scripts, and automation workflows.

Git records changes as versioned snapshots. GitHub hosts the repository online and adds collaboration, pull requests, Actions and Releases. A ChatGPT account, a GitHub account, and an OpenAI API project are separate identities/services; their email addresses do not have to match. Git commit identity records authorship; it is not the password or API key used to sign in.

We are using version control because a lesson changes over time. You need to know which objectives changed, who changed them, why, and which approved version instructors received. Sending files named final-v2-final-new.md does not provide that history reliably.

## 2. Vocabulary using your project

| Term | Meaning | Curriculum example |
| --- | --- | --- |
| Repository/repo | Files together with their Git history | The entire curriculum project |
| main | The branch we treat as the approved working edition | Reviewed content from which releases are built |
| Branch | A separate line of changes | Pre-read drafts can be reviewed before entering main |
| Commit | A saved snapshot with a description and identifier | Fix the date conversion example in AIML 11.3 |
| Diff | The exact additions/deletions between versions | Compare the previous and revised puzzle |
| Pull request/PR | A proposal to merge branch changes | An agent asks the team to review a new pre-read |
| Review | Comments and decisions on a proposal | Instructor checks explanations and expected outputs |
| Merge | Bring accepted branch changes into main | The approved pre-read becomes available for manual LMS publication |
| Actions | Workflow runs executed on GitHub runners | Run deterministic checks on curriculum pull requests |
| Release | A named published snapshot with downloads | A tagged download if the team creates one separately |
| Clone | Create a local Git working copy | Work from your computer rather than only the browser |
| Push | Send local commits to GitHub | Share your edited branch with the team |
| Pull | Fetch and integrate remote changes locally | Update your local main after the team merges a PR |

A commit saves history; it does not automatically publish a student release. A push uploads commits; it does not automatically approve them. A merged PR changes main; you publish student material manually in the LMS.

## 3. Learn the website first

Open the repository while signed into the intended GitHub account.

- **Code:** browse batches, modules, lectures and documentation. Open README.md for navigation.
- **Pull requests:** review proposed content. Each PR shows a discussion, commits, checks and Files changed.
- **Actions:** inspect automated jobs. Green indicates job success, not proof that content was created: the Actions checks are deterministic. Read your weekly runner manifest for generation progress.
- **Releases:** browse any historical GitHub releases. Your weekly workflow distributes content manually through the LMS or instructor handoff.
- **Settings:** configure collaborators, repository access and Actions settings. Reading a public repository does not grant editing rights; invite curriculum teammates as collaborators when they need write access. People without write permission can propose contributions through forks/PRs.

## 4. Your routine for reviewing a generated pre-read

1. Open Pull requests and choose a pre-read proposal. Read its class date, batch, verification report and unverified items. Confirm it targets the correct session.
2. Open Files changed. Green lines were added; red lines were removed. Read the whole rendered lesson as well as the diff. Check the scenario, objectives, exercises, setup and diagram.
3. Review the readiness change in curriculum-index.json. A pre-read PR should not mark an untouched script ready. If verification is missing, request the correction rather than treating a green job as acceptance.
4. Add a specific comment on the relevant line or in the conversation, for example: “This date is ambiguous: use an explicit dd/mm/yyyy example and show the expected conversion.”
5. Ask Codex to revise that same PR/branch, or edit the branch yourself. More commits update the same PR; another proposal is unnecessary.
6. Once the review and actual checks are complete, mark the draft Ready for review if needed, then use the available Merge/Squash and merge button and confirm. Squashing combines a set of draft-fix commits into one main-branch commit; normal merge preserves the branch commits. Either can fit this project; pick a team convention.
7. Confirm the PR is merged. Use the approved version and record approval for its checkpoint.
8. Use the LMS preview to check formatting, manually publish at 3 PM IST the day before class, then record the LMS publication.

For weekly scripts, review the Saturday–Friday plan and share the approved Markdown and its sibling images/data manually with the instructor. Use the PR manifest to check which sessions are included.

## 5. A safe first practice exercise in the browser

Use a documentation change so you can learn without editing teaching content.

1. In Code, use the branch selector showing main to create a branch named practice/github-basics. This gives your practice its own history.
2. On that branch, choose Add file → Create new file. Name it docs/my-github-practice.md.
3. Write two lines: a title and one sentence explaining a term you learned, such as “A pull request proposes changes for review.”
4. Choose Commit changes. Use the message “Add my GitHub practice note.” Keep the change on your practice branch.
5. Choose Compare & pull request or open Pull requests → New pull request. Set base to main and compare to practice/github-basics.
6. Give it a clear title and explain that this is a documentation practice change. Inspect Files changed before creating the PR.
7. Add a comment, edit the note once, and commit again on the same branch. See how the PR updates.
8. If you want the practice note retained, review and merge it. If you want no change to main, close the PR without merging. Delete the practice branch only when finished; this does not delete main.

This exercise teaches branch → edit → commit → PR → review → merge/close. It is a suggested exercise, not an operation already performed by this guide.

## 6. Then learn Git on your computer

A downloaded ZIP or a materialized folder is not necessarily a Git checkout. To create one, use GitHub Desktop's Clone repository option or run the commands below from the parent directory where you want your project. Do not clone over an existing folder containing uncommitted work.

```bash
git clone https://github.com/isparshchauhan-wq/isparsh-chauhan-curriculum.git
cd isparsh-chauhan-curriculum
git status
git remote -v
```

Clone downloads the files and history. Status tells you your current branch and local changes. Remote shows which GitHub repository the checkout is connected to; origin is its conventional name.

Configure authorship once for this checkout, replacing the example email with your verified GitHub address or the exact no-reply address shown in your GitHub email settings:

```bash
git config user.name "Isparsh Chauhan"
git config user.email "YOUR_VERIFIED_OR_GITHUB_NOREPLY_EMAIL"
```

Authenticate pushes through GitHub Desktop, GitHub CLI or a supported credential manager. Do not put a password or token in the repository URL or commit it into a file. Authorship configuration alone does not sign you into GitHub.

## 7. The normal local editing loop

Start with no unrelated local edits. If git status shows work you do not recognize, inspect it before switching branches or pulling.

```bash
git switch main
git pull --ff-only
git switch -c docs/explain-my-review-process
```

Switch selects a branch; pull --ff-only updates main without creating an unexpected merge commit and stops if the history has diverged. Switch -c starts a new branch. Edit a documentation file in your editor, then inspect and save only the intended change:

```bash
git status
git diff
git add docs/my-github-practice.md
git diff --staged
git commit -m "Explain my curriculum review process"
git push -u origin docs/explain-my-review-process
```

Here git add selects the exact version for the next commit. If you edit again after adding, add the file again to include the latest edit. The staged diff is what the commit will save. Push publishes this branch; -u records which remote branch later pushes/pulls use.

Open the resulting PR on GitHub and follow the review process above. After merging, switch back to main and pull --ff-only again. There is no need to memorize every Git command to use the project effectively.

## 8. Editing curriculum metadata

`curriculum-index.json` is the editable source of truth. The per-batch JSON/CSV/Markdown references are generated from it. If a class date changes, edit that session's scheduled_date on a branch, explain why, and regenerate exports:

```bash
python3 tools/sync_curriculum.py
python3 tools/sync_curriculum.py --check
python3 -I -m unittest discover -s tests -v
```

Inspect the diff, stage the intended index/export changes, commit, push and open a PR. This keeps navigation and authoring tools consistent. A reschedule changes the manual LMS deadline and which Saturday–Friday week contains the lecture.

## 9. Mistakes and recovery

- Added the wrong file to staging? `git restore --staged PATH` removes it from the next commit while preserving its working file.
- Need to find an older version? Open the file's History or use `git log --oneline`. Compare the relevant commits before changing anything.
- Merged a mistake? Use GitHub's Revert option on the merged PR where available, then review the corrective PR. Revert records a compensating change; it does not silently erase history or retract an already downloaded release.
- See a merge conflict? Both branches changed overlapping content. Resolve it by retaining the intended combined result, validate it, and commit. Do not choose an entire side blindly, especially in curriculum-index.json.
- Publication already happened? Fix main through review and deliberately publish a corrected release/version. Do not assume changing a file updates an existing downloaded ZIP.

Avoid destructive reset, force-push and file-discard commands while learning unless their effect on your actual changes is understood. Keep one topic per branch and write commit/PR descriptions explaining both what changed and why.

## 10. A practical learning progression

First, browse one lesson and its history. Next, complete the documentation practice PR. Then review one generated pre-read with me. After that, make one local documentation commit and push. Finally, perform a curriculum reschedule and inspect how it changes the weekly plan. Each exercise introduces one new responsibility while retaining review and recoverable history.

## Official references

- https://docs.github.com/en/get-started/using-github/hello-world
- https://docs.github.com/en/get-started/using-git/about-git
- https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository
- https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository
