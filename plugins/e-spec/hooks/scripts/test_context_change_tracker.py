"""Unit tests for context_change_tracker.py.

Every test runs inside its own TemporaryDirectory with CLAUDE_PROJECT_DIR
pointed at it, so no real eval.md is ever read or written.

Run from C:/Projects/APEX:
    python -m unittest plugins/e-spec/hooks/scripts/test_context_change_tracker.py -v
"""

import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = str(Path(__file__).with_name("context_change_tracker.py"))


def _load():
    spec = importlib.util.spec_from_file_location("context_change_tracker", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_main(payload: dict, env: dict) -> None:
    mod = _load()
    with (
        patch("sys.stdin", io.StringIO(json.dumps(payload))),
        patch.dict(os.environ, env, clear=False),
    ):
        mod.main()


def _edit(file_path: str) -> dict:
    return {"tool_name": "Edit", "tool_input": {"file_path": file_path}}


class TrackerTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name)
        self.eval_path = self.project / ".claude" / "eval.md"
        self.addCleanup(self._tmp.cleanup)

    def run_hook(self, file_path, cwd=None, use_env=True):
        payload = _edit(file_path)
        env = {}
        if use_env:
            env["CLAUDE_PROJECT_DIR"] = str(self.project)
        if cwd is not None:
            payload["cwd"] = cwd
        _run_main(payload, env)

    def write_eval(self, body):
        self.eval_path.parent.mkdir(parents=True, exist_ok=True)
        self.eval_path.write_text(body, encoding="utf-8")

    def eval_text(self):
        return (
            self.eval_path.read_text(encoding="utf-8")
            if self.eval_path.exists()
            else ""
        )

    def pending_count(self, path):
        return self.eval_text().count(f"- [ ] `{path}`")


class TestEntryCreation(TrackerTestCase):
    def test_first_edit_creates_entry(self):
        self.run_hook("C:/proj/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/proj/CLAUDE.md"), 1)
        self.assertIn("/dryrun-context", self.eval_text())

    def test_blueprint_edit_maps_to_dryrun_blueprint(self):
        self.run_hook("C:/proj/.claude/blueprints/api/readme.md")
        self.assertIn("/dryrun-blueprint", self.eval_text())

    def test_plan_edit_maps_to_dryrun_plan(self):
        self.run_hook("C:/proj/.claude/plans/001-thing.md")
        self.assertIn("/dryrun-plan", self.eval_text())

    def test_non_context_file_creates_nothing(self):
        self.run_hook("C:/proj/src/main.py")
        self.assertFalse(self.eval_path.exists())

    def test_missing_file_path_is_a_noop(self):
        _run_main(
            {"tool_name": "Edit", "tool_input": {}},
            {"CLAUDE_PROJECT_DIR": str(self.project)},
        )
        self.assertFalse(self.eval_path.exists())


class TestDedup(TrackerTestCase):
    """The invariant is 'is a review already pending', not 'ever seen'."""

    def test_pending_entry_is_not_duplicated(self):
        self.run_hook("C:/proj/CLAUDE.md")
        self.run_hook("C:/proj/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/proj/CLAUDE.md"), 1)

    def test_second_edit_after_review_creates_fresh_entry(self):
        # This is the defect: once checked off, the next edit must re-arm.
        self.write_eval(
            "# Context Evaluation Checklist\n\n"
            "- [x] `C:/proj/CLAUDE.md` changed (2026-08-04) - run /dryrun-context\n"
        )
        self.run_hook("C:/proj/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/proj/CLAUDE.md"), 1)

    def test_many_completed_entries_still_re_arm(self):
        lines = "".join(
            f"- [x] `C:/proj/CLAUDE.md` changed (2026-08-0{n}) - run /dryrun-context\n"
            for n in range(1, 5)
        )
        self.write_eval(f"# Context Evaluation Checklist\n\n{lines}")
        self.run_hook("C:/proj/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/proj/CLAUDE.md"), 1)

    def test_same_day_second_edit_after_review_still_re_arms(self):
        # Date-based keying would swallow this one.
        self.run_hook("C:/proj/CLAUDE.md")
        self.write_eval(self.eval_text().replace("- [ ]", "- [x]"))
        self.run_hook("C:/proj/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/proj/CLAUDE.md"), 1)
        self.assertEqual(self.eval_text().count("- [x]"), 1)

    def test_different_paths_do_not_collide_on_substring(self):
        self.run_hook("C:/proj/CLAUDE.md")
        self.run_hook("C:/proj/plugins/e-spec/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/proj/CLAUDE.md"), 1)
        self.assertEqual(self.pending_count("C:/proj/plugins/e-spec/CLAUDE.md"), 1)

    def test_backslash_path_is_normalized(self):
        self.run_hook(r"C:\proj\CLAUDE.md")
        self.run_hook("C:/proj/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/proj/CLAUDE.md"), 1)


class TestPathAnchoring(TrackerTestCase):
    def test_env_var_anchors_eval_file(self):
        self.run_hook("C:/proj/CLAUDE.md")
        self.assertTrue(self.eval_path.exists())

    def test_payload_cwd_used_when_env_absent(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            self.run_hook("C:/proj/CLAUDE.md", cwd=str(self.project), use_env=False)
        self.assertTrue(self.eval_path.exists())

    def test_user_global_claude_md_lands_in_session_project(self):
        # Anchoring on the edited file would send this to
        # C:/Users/hazra/.claude/.claude/eval.md instead.
        self.run_hook("C:/Users/hazra/.claude/CLAUDE.md")
        self.assertEqual(self.pending_count("C:/Users/hazra/.claude/CLAUDE.md"), 1)


if __name__ == "__main__":
    unittest.main()
