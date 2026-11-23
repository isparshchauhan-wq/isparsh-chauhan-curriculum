#!/usr/bin/env python3
"""Merge an explicitly approved weekly PR and export its committed resources."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import urlencode
import zipfile

from weekly_curriculum import ROOT, StopRun, git, lesson_file, make_plan, read_json, run, week_start


SHA = r"[0-9a-f]{40}"


def scheduled_tasks(batch, start, config):
    plan = make_plan(read_json(ROOT / "curriculum-index.json"), config,
                     read_json(ROOT / "automation/model-policy.json"), start)
    tasks = [task for task in plan["tasks"] if task["batch"] == batch]
    if not tasks:
        raise StopRun(f"No sessions for {batch} in the week of {start}")
    return tasks


def api(endpoint, *args):
    return json.loads(run("gh", "api", endpoint, *args).stdout)


def review(event, config):
    repository = event["repository"]["full_name"]
    number = event["issue"]["number"]
    endpoint = f"repos/{repository}"
    if event["action"] != "created" or not event["issue"].get("pull_request"):
        raise StopRun("Review done must be posted on a curriculum PR")
    comment = api(f"{endpoint}/issues/comments/{event['comment']['id']}")
    owner = event["repository"]["owner"]["login"]
    approval = re.fullmatch(rf"Review done ({SHA})", comment["body"].strip())
    if (comment["user"]["login"] != owner or comment["body"] != event["comment"]["body"]
            or not approval):
        raise StopRun("Use the Review done command from the PR as the repository owner")
    pull = api(f"{endpoint}/pulls/{number}")
    head, base = pull["head"], pull["base"]
    if head["sha"] != approval[1]:
        raise StopRun("The PR changed since review. Review its current commit before approving again.")
    if (head["repo"] or {}).get("full_name") != repository or base["ref"] != config["base_branch"]:
        raise StopRun("Only same-repository curriculum PRs targeting the configured base can be approved")
    branch = re.fullmatch(r"curriculum/(correction/)?(\d{4}-\d{2}-\d{2})/([a-z0-9-]+)", head["ref"])
    if not branch:
        raise StopRun("This PR is outside the weekly curriculum branches")
    name = re.sub(r"-\d{8}-\d{6}$", "", branch[3]) if branch[1] else branch[3]
    batch = next((value for value in config["batches"] if value.lower() == name), None)
    if batch is None or (pull["state"] != "open" and not pull["merged"]):
        raise StopRun("The batch is unknown or its PR was closed without merging")
    start = week_start(branch[2], dt.date.today())
    return endpoint, pull, batch, start


def check_pr(endpoint, pull, batch, start, tasks):
    head = pull["head"]
    query = urlencode({"head_sha": head["sha"], "branch": head["ref"], "event": "pull_request"})
    runs = api(f"{endpoint}/actions/workflows/curriculum-validation.yml/runs?{query}")["workflow_runs"]
    validation = next((item for item in runs if item["head_sha"] == head["sha"]), None)
    if not validation or validation["conclusion"] != "success":
        raise StopRun("Wait for Validate curriculum to pass on this commit, then repost Review done")
    metadata = {"curriculum-index.json", f"curriculum-reviews/{start}/{batch}.json",
                *(f"{batch}/{name}" for name in ("README.md", "curriculum.md", "curriculum.json", "curriculum.csv")),
                *(str(PurePosixPath(task["path"]).parent / "README.md") for task in tasks)}
    lessons = {lesson_file(task) for task in tasks}
    assets = tuple(f"{task['path']}/{folder}/" for task in tasks if task["artifact"] == "lecture-script"
                   for folder in ("images", "data"))
    pages = api(f"{endpoint}/pulls/{pull['number']}/files?per_page=100", "--paginate", "--slurp")
    files = [item for page in pages for item in page]
    if len(files) != pull["changed_files"]:
        raise StopRun("The full list of PR changes is unavailable")
    for item in files:
        for path in filter(None, (item["filename"], item.get("previous_filename"))):
            if path not in metadata and path not in lessons and not path.startswith(assets):
                raise StopRun(f"The PR includes a file outside this batch and week: {path}")


def archive_members(checkout, batch, tasks):
    # Read Git blobs so a dirty checkout, a symlink or an untracked file cannot alter the ZIP.
    entries = git(checkout, "ls-tree", "--full-tree", "-rz", "HEAD", "--", batch).split("\0")
    tracked = {}
    for entry in filter(None, entries):
        info, path = entry.split("\t", 1)
        mode, _, blob = info.split()
        tracked[path] = (mode, blob)
    members = {}
    folders = {}
    for task in tasks:
        folder = task["path"]
        name = PurePosixPath(folder).name
        if folders.setdefault(name, folder) != folder:
            raise StopRun(f"Two sessions would use the ZIP folder {name}")
        artifact = lesson_file(task)
        mode, blob = tracked.get(artifact, (None, None))
        if mode not in {"100644", "100755"}:
            raise StopRun(f"Required committed resource is missing: {artifact}")
        contents = subprocess.check_output(["git", "cat-file", "blob", blob], cwd=checkout)
        if not contents.strip() or b"Status: scaffold" in contents:
            raise StopRun(f"Required resource is still a scaffold: {artifact}")
        members[f"{name}/{PurePosixPath(artifact).name}"] = blob
        if task["artifact"] == "lecture-script":
            for path, (asset_mode, asset_blob) in tracked.items():
                if path.startswith((f"{folder}/images/", f"{folder}/data/")):
                    if asset_mode not in {"100644", "100755"}:
                        raise StopRun(f"Invalid lesson asset: {path}")
                    members[f"{name}/{path[len(folder) + 1:]}"] = asset_blob
    return members


def write_archive(checkout, members, output):
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, delete=False) as temporary:
        path = Path(temporary.name)
    try:
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, blob in sorted(members.items()):
                entry = zipfile.ZipInfo(name)
                archive.writestr(entry, subprocess.check_output(["git", "cat-file", "blob", blob], cwd=checkout),
                                 compress_type=zipfile.ZIP_DEFLATED)
        os.replace(path, output)
    finally:
        path.unlink(missing_ok=True)


def set_outputs(**values):
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        for key, value in values.items():
            print(f"{key}={value}", file=output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("prepare", "merge", "package"))
    parser.add_argument("--checkout", type=Path)
    parser.add_argument("--week-start")
    parser.add_argument("--batch")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    config = read_json(ROOT / "automation/config.json")
    if args.command == "package":
        if not all((args.checkout, args.week_start, args.batch)):
            parser.error("package requires --checkout, --week-start, and --batch")
        start = week_start(args.week_start, dt.date.today())
        tasks = scheduled_tasks(args.batch, start, config)
        members = archive_members(args.checkout, args.batch, tasks)
        if args.output:
            write_archive(args.checkout, members, args.output)
        print(f"Checked {len(members)} committed resources for {args.batch} · {start}")
        return

    endpoint, pull, batch, start = review(read_json(Path(os.environ["GITHUB_EVENT_PATH"])), config)
    tasks = scheduled_tasks(batch, start, config)
    if not pull["merged"]:
        check_pr(endpoint, pull, batch, start, tasks)
    commit = pull["merge_commit_sha"] if pull["merged"] else pull["head"]["sha"]
    if args.command == "merge" and not pull["merged"]:
        if not args.checkout or git(args.checkout, "rev-parse", "HEAD") != commit:
            raise StopRun("The checked resources do not match the approved commit")
        archive_members(args.checkout, batch, tasks)
        if pull["draft"]:
            run("gh", "pr", "ready", str(pull["number"]), "--repo", endpoint.removeprefix("repos/"))
        result = api(f"{endpoint}/pulls/{pull['number']}/merge", "--method", "PUT",
                     "-f", f"sha={commit}", "-f", "merge_method=merge")
        if not result["merged"]:
            raise StopRun(f"GitHub declined the merge: {result['message']}")
        commit = result["sha"]
    if not re.fullmatch(SHA, commit or ""):
        raise StopRun("GitHub did not return a valid commit for the handoff")
    set_outputs(commit=commit, batch=batch, week=start, archive=f"{batch}-{start}-weekly-resources")


if __name__ == "__main__":
    try:
        main()
    except (StopRun, ValueError) as error:
        raise SystemExit(str(error)) from error
