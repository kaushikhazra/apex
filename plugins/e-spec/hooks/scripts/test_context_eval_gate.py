"""Unit tests for context_eval_gate.py.

Every test runs inside its own TemporaryDirectory with CLAUDE_PROJECT_DIR
pointed at it, so no real eval.md is ever read.

Run from C:/Projects/APEX:
    python -m unittest plugins/e-spec/hooks/scripts/test_context_eval_gate.py -v
"""

import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

GATE = str(Path(__file__).with_name("context_eval_gate.py"))
TRACKER = str(Path(__file__).with_name("context_change_tracker.py"))


def _load(script, name):
    spec = importlib.util.spec_from_file_location(name, script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run(script, name, payload, env):
    mod = _load(script, name)
    with (
        patch("sys.stdin", io.StringIO(json.dumps(payload))),
        patch("sys.stderr", io.StringIO()),
        patch.dict(os.environ, env, clear=False),
    ):
        try:
            mod.main()
            return 0
        except SystemExit as exc:
            return int(exc.code)


class GateTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name)
        self.eval_path = self.project / ".claude" / "eval.md"
        self.addCleanup(self._tmp.cleanup)

    def write_eval(self, body):
        self.eval_path.parent.mkdir(parents=True, exist_ok=True)
        self.eval_path.write_text(body, encoding="utf-8")

    def run_gate(self, payload=None):
        return _run(
            GATE,
            "context_eval_gate",
            payload if payload is not None else {},
            {"CLAUDE_PROJECT_DIR": str(self.project)},
        )


class TestGating(GateTestCase):
    def test_unchecked_entry_blocks_stop(self):
        self.write_eval(
            "- [ ] `CLAUDE.md` changed (2026-08-06) - run /dryrun-context\n"
        )
        self.assertEqual(self.run_gate(), 2)

    def test_all_checked_allows_stop(self):
        self.write_eval(
            "- [x] `CLAUDE.md` changed (2026-08-06) - run /dryrun-context\n"
        )
        self.assertEqual(self.run_gate(), 0)

    def test_missing_eval_file_allows_stop(self):
        self.assertEqual(self.run_gate(), 0)

    def test_stop_hook_active_short_circuits(self):
        self.write_eval(
            "- [ ] `CLAUDE.md` changed (2026-08-06) - run /dryrun-context\n"
        )
        self.assertEqual(self.run_gate({"stop_hook_active": True}), 0)


class TestPathAnchoring(GateTestCase):
    def test_process_cwd_is_not_the_anchor(self):
        """A bystander .claude/eval.md under the process cwd is not read."""
        self.write_eval(
            "- [x] `CLAUDE.md` changed (2026-08-06) - run /dryrun-context\n"
        )
        with tempfile.TemporaryDirectory() as other:
            bystander = Path(other) / ".claude"
            bystander.mkdir(parents=True)
            (bystander / "eval.md").write_text("- [ ] `x` changed\n", encoding="utf-8")
            original_cwd = os.getcwd()
            os.chdir(other)
            try:
                # Reading the bystander would block; reading ours must not.
                self.assertEqual(self.run_gate(), 0)
            finally:
                os.chdir(original_cwd)

    def test_payload_cwd_used_when_env_absent(self):
        self.write_eval(
            "- [ ] `CLAUDE.md` changed (2026-08-06) - run /dryrun-context\n"
        )
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            code = _run(GATE, "context_eval_gate", {"cwd": str(self.project)}, {})
        self.assertEqual(code, 2)


class TestWriterReaderAgreement(GateTestCase):
    """The tracker writes eval.md and the gate reads it. If they disagree on
    where it lives, the gate never arms and D2 is dead for a new reason."""

    def test_tracked_edit_arms_the_gate(self):
        env = {"CLAUDE_PROJECT_DIR": str(self.project)}
        _run(
            TRACKER,
            "context_change_tracker",
            {"tool_name": "Edit", "tool_input": {"file_path": "C:/proj/CLAUDE.md"}},
            env,
        )
        self.assertTrue(self.eval_path.exists())
        self.assertEqual(self.run_gate(), 2)

    def test_gate_and_tracker_resolve_the_same_path(self):
        payload = {"cwd": str(self.project)}
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            gate = _load(GATE, "context_eval_gate")
            tracker = _load(TRACKER, "context_change_tracker")
            self.assertEqual(
                gate.resolve_eval_path(payload), tracker.resolve_eval_path(payload)
            )


if __name__ == "__main__":
    unittest.main()
