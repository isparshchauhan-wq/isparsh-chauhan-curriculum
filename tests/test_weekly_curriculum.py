import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
from threading import Barrier
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("weekly", ROOT / "tools/weekly_curriculum.py")
weekly = importlib.util.module_from_spec(spec)
spec.loader.exec_module(weekly)
CONFIG = weekly.read_json(ROOT / "automation/config.json")
POLICY = weekly.read_json(ROOT / "automation/model-policy.json")


class WeeklyPlanTests(unittest.TestCase):
    def test_next_saturday_and_inclusive_friday(self):
        start = weekly.week_start(None, dt.date(2026, 11, 20))
        self.assertEqual(str(start), "2026-11-21")
        plan = weekly.make_plan(weekly.read_json(ROOT / "curriculum-index.json"), CONFIG, POLICY, start)
        self.assertEqual(plan["week_end"], "2026-11-27")
        self.assertEqual({task["batch"] for task in plan["tasks"]}, set(CONFIG["batches"]))
        self.assertTrue(all(plan["week_start"] <= task["date"] <= plan["week_end"] for task in plan["tasks"]))
        self.assertTrue(any(task["minutes"] == 90 and task["artifact"] == "lecture-script" for task in plan["tasks"]))
        self.assertTrue(any(task["minutes"] == 120 and task["artifact"] == "lecture-script" for task in plan["tasks"]))
        self.assertEqual(str(weekly.week_start(None, start)), "2026-11-28")
        with self.assertRaises(ValueError):
            weekly.week_start("2026-11-22", start)

    def test_model_policy_and_usage_limit_fail_closed(self):
        for artifact in weekly.ARTIFACTS:
            for stage in ("create", "verify"):
                self.assertEqual(weekly.model_route(POLICY, artifact, stage),
                                 {"model": "gpt-6.1-terra", "effort": "high"})
        self.assertEqual(weekly.model_route(POLICY, "pre-read", "create", True)["model"], "gpt-6.2-astra")
        with self.assertRaises(ValueError):
            weekly.model_route({**POLICY, "automatic_escalation": True}, "pre-read", "create")
        self.assertEqual(weekly.task_error("You've hit your usage limit"), "usage_limit")
        self.assertEqual(weekly.task_error("This model is not supported"), "model_unavailable")
        with patch.dict(weekly.os.environ, {"OPENAI_API_KEY": "test", "CODEX_API_KEY": "test"}):
            self.assertNotIn("OPENAI_API_KEY", weekly.codex_environment())
            self.assertNotIn("CODEX_API_KEY", weekly.codex_environment())

    def test_self_report_without_check_evidence_stays_unverified(self):
        state, checks = weekly.verify_report({"status": "passed", "checks": []}, "pre-read",
                                            {"name": "structural_checker", "state": "passed", "evidence": "PASS"})
        self.assertEqual(state, "unverified")
        self.assertTrue(any(item["state"] == "unverified" for item in checks))

    def test_targets_select_exact_sessions_across_batches(self):
        args = weekly.parser().parse_args(["generate", "--week-start", "2026-11-21",
            "--target", "batch-one/01/1.1", "--target", "batch-two/02/2.1"])
        self.assertEqual(args.jobs, 4)
        self.assertTrue(weekly.selected(dict(batch="batch-one", module_id="01", session="1.1", artifact="pre-read"), args))
        self.assertTrue(weekly.selected(dict(batch="batch-two", module_id="02", session="2.1", artifact="lecture-script"), args))
        self.assertFalse(weekly.selected(dict(batch="batch-one", module_id="01", session="1.2", artifact="pre-read"), args))

    def test_artifact_scope_rejects_sibling_changes(self):
        task = {"path": "batch/lecture", "artifact": "pre-read"}
        weekly.scoped(task, ["batch/lecture/pre-read.md"])
        for name in ("batch/lecture/lecture-script.md", "batch/lecture/images/chart.png", "../outside"):
            with self.assertRaises(weekly.StopRun):
                weekly.scoped(task, [name])


class CheckpointIntegrationTests(unittest.TestCase):
    def test_git_checkpoint_resume_and_draft_pr_request(self):
        with tempfile.TemporaryDirectory() as sandbox:
            root = Path(sandbox) / "repo"
            root.mkdir()
            session_dir = root / "example/module/lecture"
            session_dir.mkdir(parents=True)
            (session_dir / "pre-read.md").write_text("Status: scaffold\n")
            (root / ".gitignore").write_text(".weekly-curriculum/\n")
            (root / "tools").mkdir()
            (root / "tools/sync_curriculum.py").write_text("pass\n")
            index = {"batches": [{"batch": "example", "modules": [{"module_id": "01", "title": "Example",
                      "sessions": [{"source_session": "1", "title": "Class", "scheduled_date": "2026-11-21",
                                    "duration_minutes": 120, "learning_objectives": ["One", "Two", "Three", "Four"],
                                    "path": "example/module/lecture"}]}]}]}
            weekly.write_json(root / "curriculum-index.json", index)
            weekly.git(root, "init", "-b", "main")
            weekly.git(root, "config", "user.name", "Test")
            weekly.git(root, "config", "user.email", "test@example.com")
            weekly.git(root, "add", ".")
            weekly.git(root, "commit", "-m", "Seed fixture")
            remote = Path(sandbox) / "remote.git"
            weekly.git(root, "init", "--bare", str(remote))
            weekly.git(root, "remote", "add", "origin", str(remote))
            weekly.git(root, "push", "origin", "main")
            config = {**CONFIG, "batches": ["example"]}
            state = weekly.make_plan(index, config, POLICY, dt.date(2026, 11, 21))
            state["base_commit"] = weekly.git(root, "rev-parse", "HEAD")
            task = state["tasks"][0]
            folder = root / ".weekly-curriculum/2026-11-21"
            manifest = folder / "manifest.json"
            arguments = SimpleNamespace(policy=POLICY, astra=False, retry_blocked=False)
            model_stages = []
            gh_calls = []
            actual_run = weekly.run

            def fake_model(_cli, _env, checkout, _directory, unit, stage, _route):
                model_stages.append(stage)
                if stage == "create":
                    (checkout / weekly.lesson_file(unit)).write_text("# Draft\n")
                elif model_stages.count("verify") == 1:
                    return None, "usage_limit"
                elif model_stages.count("verify") == 2:
                    return {"status": "failed", "checks": [
                        {"name": "code_examples", "state": "failed", "evidence": "Fix the expected result"}
                    ], "handoff": [], "notes": ""}, None
                return {"status": "unverified", "checks": [], "handoff": [], "notes": ""}, None

            def fake_gh(*command, **kwargs):
                if command[0] != "gh":
                    return actual_run(*command, **kwargs)
                gh_calls.append(command)
                return SimpleNamespace(stdout=("[]" if command[2] == "list" else "https://example.test/pull/1"))

            with patch.object(weekly, "ROOT", root), patch.object(weekly, "model_task", side_effect=fake_model), \
                 patch.object(weekly, "run", side_effect=fake_gh), patch.object(
                     weekly, "check_artifact", return_value={"name": "structural_checker", "state": "passed", "evidence": "test"}
                 ):
                with self.assertRaisesRegex(weekly.StopRun, "usage_limit"):
                    weekly.checkpoint_task(state, task, manifest, folder, "codex", {}, arguments)
                self.assertEqual(weekly.read_json(manifest)["tasks"][0]["generation"], "generated")
                arguments.retry_blocked = True
                weekly.checkpoint_task(state, task, manifest, folder, "codex", {}, arguments)
                self.assertEqual(model_stages, ["create", "verify", "verify", "verify"])
                self.assertTrue(task["prevention_pending"])
                self.assertEqual(task["repair_attempts"], 1)
                self.assertTrue(task["failure_history"])
                self.assertTrue(task["included"])
                self.assertEqual(task["verification"], "unverified")
                weekly.submit_batches(state, manifest, config)
            self.assertTrue(any("--draft" in command for command in gh_calls))
            self.assertFalse(any("merge" in command for command in gh_calls))
            self.assertTrue(task["pr"].endswith("/1"))
            self.assertIsNone(task["approved"])
            self.assertIsNone(task["published_to_lms"])
            self.assertEqual(weekly.git(root, "rev-parse", "main"), state["base_commit"])

    def test_four_artifacts_overlap_and_share_a_consistent_batch_checkpoint(self):
        self.check_parallel_batches(False)

    def test_two_batches_overlap_with_separate_consistent_branches(self):
        self.check_parallel_batches(True)

    def check_parallel_batches(self, split_batches):
        with tempfile.TemporaryDirectory() as sandbox:
            root = Path(sandbox) / "repo"
            root.mkdir()
            for path in ("example/module/one", "example/module/two"):
                (root / path).mkdir(parents=True)
                for artifact in weekly.ARTIFACTS:
                    (root / path / f"{artifact}.md").write_text("Status: scaffold\n")
            (root / ".gitignore").write_text(".weekly-curriculum/\n")
            (root / "tools").mkdir()
            (root / "tools/sync_curriculum.py").write_text("pass\n")
            sessions = [
                {"source_session": label, "title": label, "scheduled_date": "2026-11-21",
                 "duration_minutes": 120, "learning_objectives": ["One", "Two", "Three", "Four"],
                 "path": f"example/module/{label}"}
                for label in ("one", "two")
            ]
            index = {"batches": [{"batch": "example", "modules": [
                {"module_id": "01", "title": "Example", "sessions": sessions}
            ]}]}
            if split_batches:
                index["batches"] = [
                    {"batch": name, "modules": [
                        {"module_id": "01", "title": "Example", "sessions": [session]}
                    ]}
                    for name, session in zip(("example", "other"), sessions)
                ]
            weekly.write_json(root / "curriculum-index.json", index)
            weekly.git(root, "init", "-b", "main")
            weekly.git(root, "config", "user.name", "Test")
            weekly.git(root, "config", "user.email", "test@example.com")
            weekly.git(root, "add", ".")
            weekly.git(root, "commit", "-m", "Seed fixture")
            config = {**CONFIG, "batches": [row["batch"] for row in index["batches"]]}
            state = weekly.make_plan(index, config, POLICY, dt.date(2026, 11, 21))
            state["base_commit"] = weekly.git(root, "rev-parse", "HEAD")
            folder = root / ".weekly-curriculum/2026-11-21"
            manifest = folder / "manifest.json"
            arguments = SimpleNamespace(policy=POLICY, astra=False, retry_blocked=False, jobs=4)
            creators = Barrier(4)
            verifiers = Barrier(4)

            def fake_model(_cli, _env, checkout, _directory, task, stage, _route):
                artifact = checkout / weekly.lesson_file(task)
                if stage == "create":
                    creators.wait(timeout=10)
                    artifact.write_text(f"# Draft for {task['id']}\n")
                else:
                    self.assertIn(task["id"], artifact.read_text())
                    verifiers.wait(timeout=10)
                checks = [{"name": name, "state": "passed", "evidence": "test"}
                          for name in weekly.GATE_CHECKS[task["artifact"]]]
                return {"status": "passed", "checks": checks, "handoff": [], "notes": ""}, None

            with patch.object(weekly, "ROOT", root), patch.object(weekly, "model_task", side_effect=fake_model), \
                 patch.object(weekly, "check_artifact", return_value={
                     "name": "structural_checker", "state": "passed", "evidence": "test"
                 }):
                self.assertIsNone(weekly.run_pending(
                    state, state["tasks"], manifest, folder, "codex", {}, arguments
                ))
            saved = weekly.read_json(manifest)
            for task in saved["tasks"]:
                batch = Path(saved["batches"][task["batch"]]["worktree"])
                self.assertTrue(task["included"])
                self.assertEqual(task["verification"], "passed")
                self.assertEqual([entry["stage"] for entry in task["attempts"]], ["create", "verify"])
                self.assertIn(task["id"], (batch / weekly.lesson_file(task)).read_text())
            self.assertFalse(weekly.changed(batch))
            self.assertEqual(weekly.git(root, "rev-parse", "main"), state["base_commit"])


if __name__ == "__main__":
    unittest.main()
