import datetime as dt
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


TOOLS = Path(__file__).resolve().parents[1] / "tools"
spec = importlib.util.spec_from_file_location("handoff", TOOLS / "weekly_handoff.py")
handoff = importlib.util.module_from_spec(spec)
with patch.object(sys, "path", [str(TOOLS), *sys.path]):
    spec.loader.exec_module(handoff)


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.repository = "owner/curriculum"
        self.sha = "1" * 40
        self.config = {"batches": ["AIML"], "base_branch": "main"}
        self.comment = {"id": 17, "body": f"Review done {self.sha}", "user": {"login": "owner"}}
        self.event = {"action": "created", "comment": dict(self.comment),
                      "issue": {"number": 2, "pull_request": {"url": "pulls/2"}},
                      "repository": {"full_name": self.repository, "owner": {"login": "owner"}}}
        self.pull = {"number": 2, "state": "open", "draft": True, "merged": False, "changed_files": 1,
                     "head": {"sha": self.sha, "ref": "curriculum/2026-11-28/aiml",
                              "repo": {"full_name": self.repository}}, "base": {"ref": "main"}}

    def test_review_requires_owner_and_current_commit(self):
        with patch.object(handoff, "api", side_effect=[self.comment, self.pull]):
            _, _, batch, start = handoff.review(self.event, self.config)
        self.assertEqual((batch, start), ("AIML", dt.date(2026, 11, 28)))
        with patch.object(handoff, "api", return_value={**self.comment, "user": {"login": "someone-else"}}):
            with self.assertRaisesRegex(handoff.StopRun, "repository owner"):
                handoff.review(self.event, self.config)
        self.pull["head"]["sha"] = "2" * 40
        with patch.object(handoff, "api", side_effect=[self.comment, self.pull]):
            with self.assertRaisesRegex(handoff.StopRun, "changed since review"):
                handoff.review(self.event, self.config)

    def test_review_checks_validation_and_change_scope(self):
        path = "AIML/module/lecture-12.2"
        tasks = [{"path": path, "artifact": "lecture-script"}]
        check = {"workflow_runs": [{"head_sha": self.sha, "conclusion": "success"}]}
        arguments = (f"repos/{self.repository}", self.pull, "AIML", dt.date(2026, 11, 28), tasks)
        with patch.object(handoff, "api", side_effect=[check, [[{"filename": f"{path}/images/chart.png"}]]]):
            handoff.check_pr(*arguments)
        with patch.object(handoff, "api", return_value={"workflow_runs": []}):
            with self.assertRaisesRegex(handoff.StopRun, "Wait for Validate curriculum"):
                handoff.check_pr(*arguments)
        with patch.object(handoff, "api", side_effect=[check, [[{"filename": "tools/weekly_handoff.py"}]]]):
            with self.assertRaisesRegex(handoff.StopRun, "outside this batch and week"):
                handoff.check_pr(*arguments)

    def test_merge_uses_approved_sha_and_retry_uses_merged_sha(self):
        endpoint = f"repos/{self.repository}"
        start = dt.date(2026, 11, 28)
        merged_sha = "3" * 40
        with patch.object(sys, "argv", ["weekly_handoff.py", "merge", "--checkout", "reviewed"]), \
                patch.dict(handoff.os.environ, {"GITHUB_EVENT_PATH": "event.json"}), \
                patch.object(handoff, "read_json", return_value={}), \
                patch.object(handoff, "review", return_value=(endpoint, self.pull, "AIML", start)), \
                patch.object(handoff, "scheduled_tasks", return_value=[]), \
                patch.object(handoff, "check_pr") as check, patch.object(handoff, "archive_members") as archive, \
                patch.object(handoff, "git", return_value=self.sha), patch.object(handoff, "run") as run, \
                patch.object(handoff, "api", return_value={"merged": True, "sha": merged_sha}) as api, \
                patch.object(handoff, "set_outputs") as outputs:
            handoff.main()
            check.assert_called_once()
            archive.assert_called_once()
            run.assert_called_once_with("gh", "pr", "ready", "2", "--repo", self.repository)
            api.assert_called_once_with(f"{endpoint}/pulls/2/merge", "--method", "PUT",
                                        "-f", f"sha={self.sha}", "-f", "merge_method=merge")
            self.assertEqual(outputs.call_args.kwargs["commit"], merged_sha)
            self.pull.update(merged=True, merge_commit_sha=merged_sha)
            handoff.main()
            api.assert_called_once()
            self.assertEqual(outputs.call_args.kwargs["commit"], merged_sha)


class ArchiveTests(unittest.TestCase):
    def test_two_sessions_use_committed_resources_and_keep_relative_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            handoff.git(root, "init", "-b", "main")
            handoff.git(root, "config", "user.name", "Test")
            handoff.git(root, "config", "user.email", "test@example.com")
            tasks = []
            for number in ("12.2", "13.1"):
                path = f"AIML/module/lecture-{number}"
                session = root / path
                (session / "images").mkdir(parents=True)
                (session / "data").mkdir()
                (session / "images/chart.png").write_bytes(b"\x89PNG\x00\xff")
                (session / "data/demo.csv").write_bytes(b"value\n1\n")
                for artifact in ("pre-read", "lecture-script"):
                    (session / f"{artifact}.md").write_text(f"# {number} {artifact}\n", encoding="utf-8")
                    tasks.append({"path": path, "artifact": artifact})
            handoff.git(root, "add", ".")
            handoff.git(root, "commit", "-m", "Approved resources")
            (root / "AIML/module/lecture-12.2/pre-read.md").write_bytes(b"uncommitted edit")
            (root / "AIML/module/lecture-12.2/data/private.csv").write_bytes(b"untracked")
            members = handoff.archive_members(root, "AIML", tasks)
            output = root / "weekly.zip"
            handoff.write_archive(root, members, output)
            with zipfile.ZipFile(output) as archive:
                self.assertEqual({name.split("/")[0] for name in archive.namelist()}, {"lecture-12.2", "lecture-13.1"})
                self.assertEqual(len(archive.namelist()), 8)
                self.assertEqual(archive.read("lecture-12.2/pre-read.md"), b"# 12.2 pre-read\n")
                self.assertEqual(archive.read("lecture-13.1/images/chart.png"), b"\x89PNG\x00\xff")
                self.assertIsNone(archive.testzip())
            handoff.git(root, "rm", "AIML/module/lecture-13.1/lecture-script.md")
            handoff.git(root, "commit", "-m", "Remove script")
            with self.assertRaisesRegex(handoff.StopRun, "Required committed resource is missing"):
                handoff.archive_members(root, "AIML", tasks)
