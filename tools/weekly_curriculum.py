#!/usr/bin/env python3
"""Plan, generate, verify and submit a week of curriculum using local Codex."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import contextlib
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = {"pre-read": "pre_read_status", "lecture-script": "lecture_script_status"}
STATES = ["passed", "failed", "blocked", "unverified"]
GATE_CHECKS = {
    "pre-read": ["source_objectives", "student_suitability", "code_examples", "mermaid", "dependencies"],
    "lecture-script": ["source_objectives", "pedagogy", "math", "code_examples", "quizzes",
                       "mermaid", "dependencies", "instructor_suitability"],
}
SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": STATES},
        "checks": {"type": "array", "items": {
            "type": "object",
            "properties": {"name": {"type": "string"}, "state": {"type": "string", "enum": STATES},
                           "evidence": {"type": "string"}},
            "required": ["name", "state", "evidence"], "additionalProperties": False}},
        "handoff": {"type": "array", "items": {"type": "string"}},
        "notes": {"type": "string"},
    },
    "required": ["status", "checks", "handoff", "notes"],
    "additionalProperties": False,
}
BUNDLED_CODEX = Path("/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex")


class StopRun(RuntimeError):
    """Stop without losing completed checkpoints."""


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write("\n")
    os.replace(output.name, path)


def run(*arguments, cwd=ROOT, check=True, **kwargs):
    result = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True, **kwargs)
    if check and result.returncode:
        raise StopRun(f"{arguments[0]} {arguments[1]} failed: {result.stderr.strip()[-1000:]}")
    return result


def git(cwd, *arguments, check=True):
    return run("git", *arguments, cwd=cwd, check=check).stdout.strip()


def week_start(value, today):
    start = dt.date.fromisoformat(value) if value else today + dt.timedelta(days=(5 - today.weekday()) % 7 or 7)
    if start.weekday() != 5:
        raise ValueError("--week-start must be a Saturday")
    return start


def model_route(policy, artifact, stage, astra=False):
    if policy["automatic_escalation"]:
        raise ValueError("Automatic model escalation requires a workflow change and explicit approval")
    route = policy["exception"] if astra else {**policy["default"], **policy["tasks"].get(f"{artifact}.{stage}", {})}
    if "astra" in route["model"].lower() and not astra:
        raise ValueError("Astra requires an explicit --astra task run")
    if not re.fullmatch(r"[A-Za-z0-9._-]+", route["model"]) or route["effort"] not in {
        "low", "medium", "high", "xhigh", "max", "ultra"
    }:
        raise ValueError("Invalid model identifier or reasoning effort")
    return dict(route)


def make_plan(index, config, policy, start):
    end = start + dt.timedelta(days=6)
    tasks = []
    for batch in index["batches"]:
        if batch["batch"] not in config["batches"]:
            continue
        for module in batch["modules"]:
            for session in module["sessions"]:
                date = session.get("scheduled_date")
                if not date or not str(start) <= date <= str(end):
                    continue
                objectives = session.get("learning_objectives", [])
                for artifact, status_key in ARTIFACTS.items():
                    ready = session.get(status_key) == "ready"
                    reason = None
                    if session.get("curriculum_review_required"):
                        reason = "Source title and objectives need reconciliation"
                    elif not objectives:
                        reason = "Source objectives are missing"
                    elif artifact == "lecture-script" and session.get("duration_minutes") not in {90, 120}:
                        reason = "Source duration is unspecified or unsupported"
                    elif artifact == "lecture-script" and not 4 <= len(objectives) <= 8:
                        reason = "Four-topic objective grouping needs an explicit plan"
                    key = f"{batch['batch']}/{module['module_id']}/{session['source_session']}/{artifact}"
                    tasks.append({
                        "id": key, "batch": batch["batch"], "module": module["title"],
                        "module_id": module["module_id"], "session": session["source_session"],
                        "title": session["title"], "date": date, "minutes": session.get("duration_minutes"),
                        "path": session["path"], "objectives": objectives, "topics": session.get("topics", []),
                        "authoring_notes": session.get("authoring_notes", []), "artifact": artifact,
                        "existing_status": session.get(status_key, "scaffold"),
                        "create_model": model_route(policy, artifact, "create"),
                        "verify_model": model_route(policy, artifact, "verify"),
                        "generation": "existing" if ready else "pending",
                        "verification": "unverified" if ready or not reason else "blocked",
                        "checks": [], "handoff": [], "attempts": [],
                        "blocked_reason": reason if not ready else None,
                        "checkpoint": None, "branch": None, "pr": None,
                        "approved": None, "published_to_lms": None, "revision": 0,
                    })
    tasks.sort(key=lambda task: (task["batch"], task["date"], task["module_id"], task["session"],
                                 task["artifact"] != "pre-read"))
    return {"week_start": str(start), "week_end": str(end), "tasks": tasks, "batches": {}, "paused_at": None}


def lesson_file(task):
    return f"{task['path']}/{task['artifact']}.md"


def scoped(task, paths):
    prefix = task["path"] + "/"
    for name in paths:
        path = Path(name)
        allowed_asset = task["artifact"] == "lecture-script" and (
            name.startswith(prefix + "images/") or name.startswith(prefix + "data/")
        )
        if path.is_absolute() or ".." in path.parts or (name != lesson_file(task) and not allowed_asset):
            raise StopRun(f"Changes outside the assigned artifact: {name}")


def changed(worktree):
    tracked = run("git", "diff", "--no-renames", "--name-only", "-z", "HEAD", cwd=worktree).stdout
    untracked = run("git", "ls-files", "--others", "--exclude-standard", "-z", cwd=worktree).stdout
    return sorted(set(filter(None, (tracked + untracked).split("\0"))))


def check_artifact(worktree, task):
    path = worktree / lesson_file(task)
    if path.is_symlink() or not path.resolve().is_relative_to(worktree.resolve()):
        return {"name": "structural_checker", "state": "failed", "evidence": "Invalid artifact path"}
    if not path.is_file() or "Status: scaffold" in path.read_text(encoding="utf-8"):
        return {"name": "structural_checker", "state": "failed", "evidence": "Artifact is missing or still a scaffold"}
    if task["artifact"] == "pre-read":
        args = ["preread/scripts/check_preread.py", "--file", lesson_file(task), "--setup", "No", "--root", "."]
    else:
        args = ["lecture/tools/check_script.py", lesson_file(task), "--los-json", json.dumps(task["objectives"]),
                "--module", task["module"], "--session", task["title"], "--announcements", "no",
                "--duration", str(task["minutes"])]
    result = run(sys.executable, "-I", *args, cwd=worktree, check=False)
    return {"name": "structural_checker", "state": "failed" if result.returncode else "passed",
            "evidence": (result.stdout + result.stderr).strip()[-3000:]}


def codex_environment():
    env = {key: value for key, value in os.environ.items() if key not in {
        "OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE", "AZURE_OPENAI_API_KEY",
        "CODEX_ACCESS_TOKEN", "CODEX_WORKLOAD_IDENTITY_TOKEN",
    } and not key.startswith(("CODEX_WORKLOAD_", "OPENAI_WORKLOAD_"))}
    return env


def codex_preflight():
    cli = shutil.which("codex") or (str(BUNDLED_CODEX) if BUNDLED_CODEX.is_file() else None)
    if not cli:
        raise StopRun("Install the Codex CLI and sign in with ChatGPT")
    env = codex_environment()
    auth = run(cli, "login", "status", env=env, check=False)
    if auth.returncode or "Logged in using ChatGPT" not in auth.stdout + auth.stderr:
        raise StopRun("ChatGPT authentication is required. Run codex login and select ChatGPT")
    help_text = run(cli, "exec", "--help", env=env).stdout
    for option in ("--ignore-user-config", "--output-schema", "--ephemeral", "--json"):
        if option not in help_text:
            raise StopRun(f"Update Codex CLI. This version is missing {option}")
    return cli, env


def task_error(output):
    if re.search(r"usage limit|rate.limit|quota exceeded|too many requests|\b429\b", output, re.I):
        return "usage_limit"
    if re.search(r"model.{0,120}(?:not supported|not available|not found|does not exist)|unsupported model|invalid reasoning", output, re.I):
        return "model_unavailable"
    return "execution_error"


def model_task(cli, env, worktree, directory, task, stage, route):
    schema = directory / "schema.json"
    output = directory / f"{stage}-result.json"
    output.unlink(missing_ok=True)
    write_json(schema, SCHEMA)
    pack = "preread" if task["artifact"] == "pre-read" else "lecture"
    role = "creator" if stage == "create" else "reviewer"
    prompt = (worktree / "automation/prompt.md").read_text()
    prompt += f"\nRole: {stage}. Read {pack}/agents/{role}.md. Artifact: {lesson_file(task)}.\n"
    if stage == "verify":
        prompt += "Supply one result with evidence for each check named here: " + ", ".join(GATE_CHECKS[task["artifact"]]) + ".\n"
    if task.get("revision_note"):
        prompt += "Requested correction: " + task["revision_note"] + "\n"
    prompt += json.dumps({key: task[key] for key in (
        "batch", "module", "module_id", "session", "title", "date", "minutes",
        "topics", "objectives", "path", "authoring_notes",
    )}, ensure_ascii=False)
    log = directory / f"{stage}-cli.log"
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(
            [cli, "exec", "--ignore-user-config", "--ephemeral", "--json",
             "-c", 'force_login_method="chatgpt"', "-c", 'model_provider="openai"',
             "-c", f'model_reasoning_effort="{route["effort"]}"', "-m", route["model"],
             "-s", "workspace-write", "--output-schema", str(schema), "-o", str(output), "-"],
            input=prompt, text=True, stdout=stream, stderr=subprocess.STDOUT, cwd=worktree, env=env,
        )
    combined = log.read_text(encoding="utf-8", errors="replace")
    if result.returncode or not output.is_file():
        return None, task_error(combined)
    events = []
    for line in combined.splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    if not any(event.get("type") == "turn.completed" for event in events if isinstance(event, dict)):
        return None, task_error(combined)
    report = read_json(output)
    if report.get("status") not in STATES or not isinstance(report.get("checks"), list):
        raise StopRun("Codex returned an invalid stage report")
    return report, None


def verify_report(report, artifact, structural):
    evidence_by_name = {item["name"]: item for item in report["checks"]}
    checks = []
    for name in GATE_CHECKS[artifact]:
        item = evidence_by_name.get(name)
        if not item or item.get("state") not in STATES or not item.get("evidence", "").strip():
            item = {"name": name, "state": "unverified", "evidence": "No verifier evidence supplied"}
        checks.append(item)
    checks.append(structural)
    states = {item["state"] for item in checks} | {report["status"]}
    return next(state for state in ("failed", "blocked", "unverified", "passed") if state in states), checks


@contextlib.contextmanager
def manifest_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / "run.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise StopRun("A runner already owns this week's manifest") from exc
        yield


def commit(worktree, paths, message):
    if paths:
        git(worktree, "add", "--", *paths)
    if run("git", "diff", "--cached", "--quiet", cwd=worktree, check=False).returncode == 1:
        git(worktree, "commit", "-m", message)
    return git(worktree, "rev-parse", "HEAD")


def batch_tree(state, folder, manifest, task):
    batch = task["batch"]
    record = state["batches"].get(batch)
    if record:
        return Path(record["worktree"]), record
    branch = f"curriculum/{state['week_start']}/{batch.lower()}"
    worktree = folder / "batches" / batch
    worktree.parent.mkdir(parents=True, exist_ok=True)
    if not worktree.exists():
        git(ROOT, "worktree", "add", "-b", branch, str(worktree), state["base_commit"])
    if git(worktree, "branch", "--show-current") != branch:
        raise StopRun(f"Unexpected branch for {worktree}")
    record = {"worktree": str(worktree), "branch": branch, "pr": None, "pushed": None}
    state["batches"][batch] = record
    write_json(manifest, state)
    return worktree, record


def validate_delta(worktree, task, paths, baseline="HEAD"):
    scoped(task, paths)
    for name in paths:
        candidate = worktree / name
        if candidate.is_symlink() or not candidate.resolve().is_relative_to(worktree.resolve()):
            raise StopRun(f"Unsafe generated asset: {name}")
        tracked = run("git", "cat-file", "-e", baseline + ":" + name, cwd=worktree, check=False)
        if not candidate.exists() and tracked.returncode == 0:
            raise StopRun(f"Unexpected deletion: {name}")


def checkpoint_task(state, task, manifest, folder, cli, env, args,
                    model_slot=contextlib.nullcontext, halted=lambda: False):
    batch, record = batch_tree(state, folder, manifest, task)
    label = "Weekly artifact " + task["id"] + " revision " + str(task["revision"])
    key = task["id"].replace("/", "--") + f"--r{task['revision']}"
    directory = folder / "tasks" / key
    worktree = directory / "worktree"
    if not worktree.exists():
        directory.mkdir(parents=True, exist_ok=True)
        task.setdefault("base", git(batch, "rev-parse", "HEAD"))
        write_json(manifest, state)
        git(batch, "worktree", "add", "--detach", str(worktree), task["base"])
    before = task["base"]
    task["branch"] = record["branch"]
    if not task.get("finished"):
        for stage in ("create", "verify"):
            if task.get(f"{stage}_checkpoint"):
                continue
            if halted():
                return
            route = model_route(args.policy, task["artifact"], stage, args.astra)
            active = [entry for entry in task["attempts"] if entry["stage"] == stage
                      and entry["route"] == route and entry["revision"] == task["revision"]]
            if active and active[-1]["state"] == "running":
                active[-1]["state"] = "interrupted"
            limit = 1 + args.policy["maximum_retries"]
            if active and (not args.retry_blocked or len(active) >= limit):
                raise StopRun(f"{task['id']} {stage} has a prior interruption. Check status and retry explicitly within the configured limit")
            validate_delta(worktree, task, changed(worktree))
            attempt = {"stage": stage, "route": route, "revision": task["revision"],
                       "start": dt.datetime.now(dt.timezone.utc).isoformat(), "state": "running"}
            task["attempts"].append(attempt)
            write_json(manifest, state)
            print(f"Started {stage} for {task['id']}", flush=True)
            started = time.monotonic()
            try:
                with model_slot():
                    report, error = model_task(cli, env, worktree, directory, task, stage, route)
            finally:
                attempt["seconds"] = round(time.monotonic() - started, 1)
                print(f"Ended {stage} for {task['id']} after {attempt['seconds']:.1f}s", flush=True)
            if error:
                attempt["state"] = error
                task["blocked_reason"] = error
                task["verification"] = "blocked"
                raise StopRun(f"{task['id']} {stage} stopped with {error}. See its local task log")
            paths = changed(worktree)
            validate_delta(worktree, task, paths)
            if report["status"] == "blocked" or not (worktree / lesson_file(task)).is_file():
                attempt["state"] = "blocked"
                task["blocked_reason"] = report.get("notes") or "Artifact was not produced"
                task["verification"] = "blocked"
                task["finished"] = True
                return
            if stage == "create" and (not paths or report["status"] == "failed"):
                attempt["state"] = "failed"
                task["verification"] = "failed"
                task["finished"] = True
                task["blocked_reason"] = "Creation did not produce a usable draft"
                return
            attempt["state"] = "completed"
            task[f"{stage}_checkpoint"] = commit(worktree, paths, f"{label}: {stage}")
            task["checkpoint"] = task[f"{stage}_checkpoint"]
            if stage == "create":
                task["generation"] = "generated"
            else:
                task["verification"], task["checks"] = verify_report(
                    report, task["artifact"], check_artifact(worktree, task)
                )
                task["handoff"] = report["handoff"]
                task["verification_notes"] = report["notes"]
                task["finished"] = True
            task["blocked_reason"] = None
            write_json(manifest, state)
    if task["verification"] not in {"passed", "unverified"}:
        return
    if changed(batch):
        raise StopRun(f"Inspect an interrupted checkpoint in {batch} before resuming")
    if git(batch, "log", "-1", "--format=%s") == label:
        task["checkpoint"] = git(batch, "rev-parse", "HEAD")
        task["included"] = True
        return
    paths = git(worktree, "diff", "--no-renames", "--name-only", before, "HEAD").splitlines()
    validate_delta(worktree, task, paths, before)
    if not paths:
        raise StopRun(f"No artifact changes to submit for {task['id']}")
    patch = run("git", "diff", "--binary", "--full-index", before, "HEAD", cwd=worktree).stdout
    run("git", "apply", "--index", "-", cwd=batch, input=patch)
    index_path = batch / "curriculum-index.json"
    index = read_json(index_path)
    lesson = next(session for batch_row in index["batches"] if batch_row["batch"] == task["batch"]
                  for module in batch_row["modules"] if module["module_id"] == task["module_id"]
                  for session in module["sessions"] if session["source_session"] == task["session"])
    field = ARTIFACTS[task["artifact"]]
    lesson[field] = "ready" if task["verification"] == "passed" else "needs_verification"
    lesson["status"] = "ready" if all(lesson.get(key) == "ready" for key in ARTIFACTS.values()) else "partial"
    write_json(index_path, index)
    run(sys.executable, "tools/sync_curriculum.py", cwd=batch)
    task["checkpoint"] = commit(batch, changed(batch), label)
    task["included"] = True


def run_pending(state, pending, manifest, folder, cli, env, args):
    # Git integration and the shared manifest have one writer at a time.
    # Only Codex invocations in detached worktrees overlap.
    lock = threading.Lock()
    stop = threading.Event()
    state["paused_at"] = None

    @contextlib.contextmanager
    def model_slot():
        lock.release()
        try:
            yield
        finally:
            lock.acquire()

    def process(task):
        with lock:
            if stop.is_set() or (task.get("finished") and task["verification"] in {"failed", "blocked"}):
                return
            try:
                checkpoint_task(state, task, manifest, folder, cli, env, args, model_slot, stop.is_set)
            except (StopRun, OSError, ValueError, KeyboardInterrupt) as exc:
                if not stop.is_set():
                    state["paused_at"] = {"task": task["id"], "reason": str(exc) or "Interrupted by the operator"}
                    stop.set()
            finally:
                write_json(manifest, state)

    if args.jobs == 1:
        for task in pending:
            process(task)
    else:
        with ThreadPoolExecutor(max_workers=args.jobs) as workers:
            try:
                for _ in workers.map(process, pending):
                    pass
            except KeyboardInterrupt:
                stop.set()
                raise
    return state["paused_at"]


def submit_batches(state, manifest, config):
    for batch, record in state["batches"].items():
        tasks = [task for task in state["tasks"] if task["batch"] == batch and task.get("included")
                 and task["branch"] == record["branch"]]
        if not tasks:
            continue
        worktree = Path(record["worktree"])
        branch = record["branch"]
        if changed(worktree):
            raise StopRun(f"Review uncommitted files in {worktree} before pushing")
        audit = worktree / "curriculum-reviews" / state["week_start"] / f"{batch}.json"
        snapshot = {"week_start": state["week_start"], "week_end": state["week_end"], "batch": batch,
                    "branch": branch, "tasks": [
                        {key: value for key, value in task.items() if key not in {"pr", "approved", "published_to_lms"}}
                        for task in tasks
                    ]}
        entries = read_prs(worktree, branch)
        if entries and entries[0]["state"].upper() != "OPEN":
            if record["pushed"] == git(worktree, "rev-parse", "HEAD"):
                continue
            raise StopRun(f"The PR for {branch} is closed. Start a correction branch for further changes")
        write_json(audit, snapshot)
        commit(worktree, [str(audit.relative_to(worktree))], f"Record curriculum review for {batch}")
        head = git(worktree, "rev-parse", "HEAD")
        if record["pushed"] != head:
            git(worktree, "push", "-u", "origin", branch)
            record["pushed"] = head
            write_json(manifest, state)
        changed_files = git(worktree, "diff", "--name-only", f"{record.get('base_commit', state['base_commit'])}...HEAD").splitlines()
        lines = [f"Teaching week {state['week_start']} through {state['week_end']}.", "",
                 "## Materials and verification", ""]
        for task in tasks:
            path = lesson_file(task)
            lines.append(f"- Session {task['session']} [{task['artifact']}]({path}) · {task['verification']}")
            for attempt in task["attempts"]:
                route = attempt["route"]
                lines.append(f"  - {attempt['stage']}: {route['model']} / {route['effort']} ({attempt['state']})")
            lines.extend(f"  - {check['state']}: {check['name']} — {check['evidence']}"
                         for check in task["checks"] if check["state"] != "passed")
            lines.extend("  - Handoff: " + item for item in task["handoff"])
        omitted = [task for task in state["tasks"] if task["batch"] == batch and not task.get("included")
                   and task["generation"] != "existing"]
        if omitted:
            lines += ["", "## Pending or withheld artifacts", ""]
            lines.extend(f"- {task['session']} {task['artifact']}: {task.get('blocked_reason') or task['verification']}"
                         for task in omitted)
        lines += ["", f"[Review manifest]({audit.relative_to(worktree)})", "", "## Changed files", ""]
        lines += [f"- `{name}`" for name in changed_files]
        lines += ["", "## Owner review", "", "- [ ] Check curriculum, timing, exercises and handoff assets.",
                  "- [ ] Resolve failed or unverified checks before approving the affected artifact.",
                  "- [ ] Wait for **Validate curriculum** to pass, then post this as a new PR comment:",
                  "", f"```text\nReview done {head}\n```", "",
                  "The owner comment approves this exact commit and starts the merge and batch ZIP export.",
                  "Publish student pre-reads in the LMS manually."]
        with tempfile.NamedTemporaryFile("w", encoding="utf-8") as body:
            body.write("\n".join(lines))
            body.flush()
            if entries:
                url = entries[0]["url"]
                run("gh", "pr", "edit", url, "--body-file", body.name, cwd=worktree)
            else:
                url = run("gh", "pr", "create", "--draft", "--base", config["base_branch"], "--head", branch,
                          "--title", f"{batch} curriculum · {state['week_start']}", "--body-file", body.name,
                          cwd=worktree).stdout.strip()
        record["pr"] = url
        for task in tasks:
            task["pr"] = url
        write_json(manifest, state)


def read_prs(worktree, branch):
    result = run("gh", "pr", "list", "--state", "all", "--head", branch, "--limit", "1",
                 "--json", "url,state", cwd=worktree)
    return json.loads(result.stdout)


def print_plan(state):
    print(f"Teaching week {state['week_start']} through {state['week_end']} (IST)")
    for task in state["tasks"]:
        create = task["create_model"]
        verify = task["verify_model"]
        status = task["blocked_reason"] or f"{task['generation']} / {task['verification']}"
        print(f"{task['batch']} {task['session']} | {task['title']} | {task['date']} | "
              f"{task['minutes'] or 'unspecified'} min | {task['artifact']} | "
              f"create {create['model']}:{create['effort']} | verify {verify['model']}:{verify['effort']} | "
              f"index {task['existing_status']} | {status}")
        if task["attempts"] and task["attempts"][-1]["state"] == "running":
            print("  Last recorded stage: " + task["attempts"][-1]["stage"])
        if task["pr"]:
            print("  PR " + task["pr"])
        if task["approved"] or task["published_to_lms"]:
            print(f"  Approval recorded: {bool(task['approved'])} | LMS publication recorded: {bool(task['published_to_lms'])}")
    if not state["tasks"]:
        print("No scheduled sessions in this week")
    if state["paused_at"]:
        print("Stopped at " + json.dumps(state["paused_at"]))


def selected(task, args):
    sessions = args.include_session
    return all(not getattr(args, field) or getattr(args, field) == task[field]
               for field in ("batch", "module_id", "session", "artifact")) and (
                   not sessions or f"{task['module_id']}/{task['session']}" in sessions)


def revise_task(state, task, folder, manifest, args, config):
    record = state["batches"].get(task["batch"])
    existing = read_prs(Path(record["worktree"]), record["branch"]) if record and record["pr"] else []
    if record is None or (record["pr"] and (not existing or existing[0]["state"].upper() != "OPEN")):
        git(ROOT, "fetch", "origin", config["base_branch"])
        base = git(ROOT, "rev-parse", "FETCH_HEAD")
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
        branch = f"curriculum/correction/{state['week_start']}/{task['batch'].lower()}-{stamp}"
        worktree = folder / "batches" / (task["batch"] + "-" + stamp)
        worktree.parent.mkdir(parents=True, exist_ok=True)
        git(ROOT, "worktree", "add", "-b", branch, str(worktree), base)
        record = {"worktree": str(worktree), "branch": branch, "pr": None, "pushed": None, "base_commit": base}
        state["batches"][task["batch"]] = record
    source = Path(record["worktree"]) / lesson_file(task)
    if not source.is_file() or "Status: scaffold" in source.read_text(encoding="utf-8"):
        raise StopRun("The correction requires an existing draft or published artifact")
    history = task.setdefault("revision_history", [])
    recorded_fields = ("revision", "checkpoint", "checks", "pr", "approved", "published_to_lms",
                       "verification", "branch", "verification_notes", "handoff", "revision_note")
    history.append({field: task.get(field) for field in recorded_fields})
    for field in ("base", "create_checkpoint", "verify_checkpoint", "finished", "included"):
        task.pop(field, None)
    task.update(revision=task["revision"] + 1, revision_note=args.note,
                generation="pending", verification="unverified", checks=[], handoff=[],
                blocked_reason=None, checkpoint=None, branch=record["branch"], pr=record["pr"],
                approved=None, published_to_lms=None)
    write_json(manifest, state)


def record_status(state, manifest, task, args):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    if args.event == "approve":
        if task["verification"] != "passed" or not task["pr"]:
            raise StopRun("Record approval after the artifact passes verification and has a review PR")
        task["approved"] = {"at": now, "note": args.note, "pr": task["pr"], "checkpoint": task["checkpoint"]}
    else:
        if task["artifact"] != "pre-read" or not task["approved"]:
            raise StopRun("Record LMS publication for a pre-read with explicit approval")
        task["published_to_lms"] = {"recorded_at": now, "note": args.note}
    write_json(manifest, state)


def validate_repository(index):
    errors = []
    for batch in index["batches"]:
        for module in batch["modules"]:
            for session in module["sessions"]:
                for artifact, field in ARTIFACTS.items():
                    if session.get(field) != "ready":
                        continue
                    task = dict(path=session["path"], artifact=artifact, module=module["title"],
                                objectives=session["learning_objectives"], title=session["title"],
                                minutes=session.get("duration_minutes"))
                    result = check_artifact(ROOT, task)
                    if result["state"] != "passed":
                        errors.append(lesson_file(task) + ": " + result["evidence"])
    if errors:
        raise StopRun("\n".join(errors))
    print("Structural checks passed for all ready artifacts")


def parser():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("command", choices=["plan", "generate", "resume", "status", "submit", "revise", "record", "validate"])
    argp.add_argument("--week-start", help="Saturday in YYYY-MM-DD form (default: next Saturday in IST)")
    argp.add_argument("--batch")
    argp.add_argument("--module-id")
    argp.add_argument("--session")
    argp.add_argument("--include-session", action="append", metavar="MODULE/SESSION",
                      help="Exact session to include in a batch. Repeat to select multiple sessions")
    argp.add_argument("--jobs", type=int, choices=range(1, 5), default=1,
                      help="Maximum concurrent artifacts for one batch (default: 1)")
    argp.add_argument("--artifact", choices=ARTIFACTS)
    argp.add_argument("--limit", type=int, help="Maximum number of distinct sessions in this invocation")
    argp.add_argument("--retry-blocked", action="store_true", help="Explicitly retry interrupted work within policy")
    argp.add_argument("--astra", action="store_true", help="Authorize Astra for exactly one selected artifact")
    argp.add_argument("--local-only", action="store_true", help="Save local checkpoints without opening or updating PRs")
    argp.add_argument("--note")
    argp.add_argument("--event", choices=["approve", "published-to-lms"])
    return argp


def main():
    argp = parser()
    args = argp.parse_args()
    if args.include_session and (not args.batch or args.module_id or args.session
                                 or args.command not in {"plan", "status", "generate", "resume"}):
        argp.error("--include-session requires --batch and replaces --module-id and --session")
    if args.jobs > 1 and (not args.batch or args.command not in {"generate", "resume"}):
        argp.error("--jobs above 1 requires generate or resume with --batch")
    config = read_json(ROOT / "automation/config.json")
    args.policy = read_json(ROOT / "automation/model-policy.json")
    index = read_json(ROOT / "curriculum-index.json")
    if args.command == "validate":
        validate_repository(index)
        return
    today = dt.datetime.now(ZoneInfo(config["timezone"])).date()
    start = week_start(args.week_start, today)
    folder = ROOT / ".weekly-curriculum" / str(start)
    manifest = folder / "manifest.json"
    initial = make_plan(index, config, args.policy, start)
    if args.include_session:
        available = {f"{task['module_id']}/{task['session']}" for task in initial["tasks"]
                     if task["batch"] == args.batch}
        unknown = set(args.include_session) - available
        if unknown:
            argp.error("Sessions outside the selected batch and week: " + ", ".join(sorted(unknown)))
    if args.command in {"plan", "status"}:
        state = read_json(manifest) if manifest.exists() else initial
        print_plan({**state, "tasks": [task for task in state["tasks"] if selected(task, args)]})
        if args.command == "status":
            print("Progress manifest " + str(manifest) if manifest.exists() else "No run has started for this week")
        return
    if args.limit is not None and args.limit < 1:
        raise ValueError("--limit must be positive")
    if args.policy["maximum_retries"] < 0:
        raise ValueError("maximum_retries must be nonnegative")
    with manifest_lock(folder):
        state = read_json(manifest) if manifest.exists() else initial
        tasks = [task for task in state["tasks"] if selected(task, args)]
        if args.astra and len(tasks) != 1:
            raise StopRun("Select exactly one artifact using batch, session, artifact and module if needed for --astra")
        if args.command in {"revise", "record"} and (len(tasks) != 1 or not args.note):
            raise StopRun("Select exactly one artifact and supply --note")
        if args.command == "record":
            if not args.event:
                raise StopRun("Supply --event approve or --event published-to-lms")
            record_status(state, manifest, tasks[0], args)
            return
        if args.command in {"resume", "submit"} and not manifest.exists():
            raise StopRun("No week manifest exists. Use generate first with the same --week-start")
        if not args.local_only or args.command == "submit":
            if not shutil.which("gh"):
                raise StopRun("GitHub CLI is required for draft PRs. Use --local-only to generate without it")
            run("gh", "auth", "status", "--hostname", "github.com")
        if args.command == "submit":
            submit_batches(state, manifest, config)
            return
        if run("git", "rev-parse", "--show-toplevel", check=False).returncode:
            raise StopRun("Open a real Git clone of the repository before generating")
        if not state.get("base_commit"):
            if changed(ROOT):
                raise StopRun("Commit or set aside working changes before starting a weekly run")
            state["base_commit"] = git(ROOT, "rev-parse", "HEAD")
            write_json(manifest, state)
        if args.command == "revise":
            revise_task(state, tasks[0], folder, manifest, args, config)
        if args.limit:
            session_ids = list(dict.fromkeys(tuple(task["id"].split("/")[:-1]) for task in tasks
                                            if not task.get("included") and task["generation"] != "existing"))
            keep = set(session_ids[:args.limit])
            tasks = [task for task in tasks if tuple(task["id"].split("/")[:-1]) in keep]
        for task in tasks:
            if not task.get("included") and task["generation"] != "existing":
                task["create_model"] = model_route(args.policy, task["artifact"], "create", args.astra)
                task["verify_model"] = model_route(args.policy, task["artifact"], "verify", args.astra)
        write_json(manifest, state)
        print_plan({**state, "tasks": tasks})
        pending = [task for task in tasks if task["generation"] != "existing" and not task.get("included")
                   and (not task["blocked_reason"] or task["attempts"] or task.get("base"))]
        if not pending:
            print("No selected artifacts need generation")
            if not args.local_only:
                submit_batches(state, manifest, config)
            return
        cli, env = codex_preflight()
        stopped = run_pending(state, pending, manifest, folder, cli, env, args)
        if not args.local_only:
            submit_batches(state, manifest, config)
        if stopped:
            raise StopRun(f"{stopped['reason']}\nResume using the same selectors and the resume command")
        print(f"Saved manifest at {manifest}")


if __name__ == "__main__":
    try:
        main()
    except (StopRun, OSError, ValueError, KeyError) as exc:
        sys.exit(str(exc))
