"""Unit tests for context_eval_clear.py.

This hook deletes files. Every test therefore runs against its own
TemporaryDirectory with CLAUDE_PROJECT_DIR pointed at it — the real
.claude/ is never in scope.

What the hook deletes is a settled decision and is not under test here;
these cover the plumbing: where it looks, and which shells reach it.

Run from C:/Projects/APEX:
    python -m unittest sdlc/spec-enhanced/hooks/scripts/test_context_eval_clear.py -v
"""

import importlib.util
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Resolved against this file, not the process cwd — one test chdirs.
SCRIPT = str(Path(__file__).with_name("context_eval_clear.py"))

COMMIT_CMD = "git commit -m 'chore: context evaluated'"


def _load():
    spec = importlib.util.spec_from_file_location("context_eval_clear", SCRIPT)
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


class ClearTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name)
        self.claude = self.project / ".claude"
        self.addCleanup(self._tmp.cleanup)
        self.seed(self.claude)

    @staticmethod
    def seed(claude_dir):
        claude_dir.mkdir(parents=True, exist_ok=True)
        (claude_dir / "eval.md").write_text("- [ ] `x` changed\n", encoding="utf-8")
        (claude_dir / "dryrun-code-1.md").write_text("report\n", encoding="utf-8")
        (claude_dir / "dryrun-design-2.md").write_text("report\n", encoding="utf-8")
        (claude_dir / "keep.md").write_text("keep\n", encoding="utf-8")

    def run_hook(self, command, tool_name="Bash"):
        _run_main(
            {"tool_name": tool_name, "tool_input": {"command": command}},
            {"CLAUDE_PROJECT_DIR": str(self.project)},
        )

    def assert_cleared(self, claude_dir=None):
        claude_dir = claude_dir or self.claude
        self.assertFalse((claude_dir / "eval.md").exists())
        self.assertFalse((claude_dir / "dryrun-code-1.md").exists())
        self.assertFalse((claude_dir / "dryrun-design-2.md").exists())
        self.assertTrue((claude_dir / "keep.md").exists())

    def assert_intact(self, claude_dir=None):
        claude_dir = claude_dir or self.claude
        self.assertTrue((claude_dir / "eval.md").exists())
        self.assertTrue((claude_dir / "dryrun-code-1.md").exists())
        self.assertTrue((claude_dir / "dryrun-design-2.md").exists())


class TestTriggering(ClearTestCase):
    def test_bash_commit_with_phrase_clears(self):
        self.run_hook(COMMIT_CMD)
        self.assert_cleared()

    def test_commit_without_phrase_leaves_everything(self):
        self.run_hook("git commit -m 'feat: add thing'")
        self.assert_intact()

    def test_non_commit_command_leaves_everything(self):
        self.run_hook("git status --short")
        self.assert_intact()

    def test_phrase_is_case_insensitive(self):
        self.run_hook("git commit -m 'chore: Context Evaluated'")
        self.assert_cleared()


class TestPowerShellParity(ClearTestCase):
    def test_powershell_commit_with_phrase_clears(self):
        self.run_hook(COMMIT_CMD, tool_name="PowerShell")
        self.assert_cleared()

    def test_powershell_here_string_commit_clears(self):
        command = "git commit -m @'\nchore: sweep\n\ncontext evaluated\n'@"
        self.run_hook(command, tool_name="PowerShell")
        self.assert_cleared()

    def test_powershell_non_commit_leaves_everything(self):
        self.run_hook("Get-ChildItem .claude", tool_name="PowerShell")
        self.assert_intact()


class TestPathAnchoring(ClearTestCase):
    def test_process_cwd_is_not_the_anchor(self):
        """A different .claude/ under the process cwd must survive."""
        with tempfile.TemporaryDirectory() as other:
            bystander = Path(other) / ".claude"
            self.seed(bystander)
            original_cwd = os.getcwd()
            os.chdir(other)
            try:
                self.run_hook(COMMIT_CMD)
            finally:
                os.chdir(original_cwd)
            self.assert_cleared()
            self.assert_intact(bystander)

    def test_payload_cwd_used_when_env_absent(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            _run_main(
                {
                    "tool_name": "Bash",
                    "tool_input": {"command": COMMIT_CMD},
                    "cwd": str(self.project),
                },
                {},
            )
        self.assert_cleared()

    def test_missing_claude_dir_is_a_noop(self):
        with tempfile.TemporaryDirectory() as empty:
            _run_main(
                {"tool_name": "Bash", "tool_input": {"command": COMMIT_CMD}},
                {"CLAUDE_PROJECT_DIR": empty},
            )
        self.assert_intact()


if __name__ == "__main__":
    unittest.main()
