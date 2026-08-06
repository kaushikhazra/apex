"""Unit tests for branch_name_validator.py.

No git repo required — main() is fed a payload on stdin and its exit code
inspected.

Run from C:/Projects/APEX:
    python -m unittest sdlc/spec-enhanced/hooks/scripts/test_branch_name_validator.py -v
"""

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = str(Path(__file__).with_name("branch_name_validator.py"))


def _run_main(tool_name: str, command: str) -> int:
    spec = importlib.util.spec_from_file_location("branch_name_validator", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    payload = {"tool_name": tool_name, "tool_input": {"command": command}}
    with (
        patch("sys.stdin", io.StringIO(json.dumps(payload))),
        patch("sys.stderr", io.StringIO()),
    ):
        try:
            mod.main()
            return 0
        except SystemExit as exc:
            return int(exc.code)


class TestBashBehaviour(unittest.TestCase):
    def test_nonconforming_checkout_blocked(self):
        self.assertEqual(_run_main("Bash", "git checkout -b fix/hook-hardening"), 2)

    def test_nonconforming_switch_blocked(self):
        self.assertEqual(_run_main("Bash", "git switch -c wip"), 2)

    def test_conforming_prefixes_allowed(self):
        for prefix in ("feature", "bugfix", "hotfix", "release", "milestone"):
            with self.subTest(prefix=prefix):
                self.assertEqual(
                    _run_main("Bash", f"git checkout -b {prefix}/thing"), 0
                )

    def test_switching_to_protected_branch_allowed(self):
        self.assertEqual(_run_main("Bash", "git checkout -b master"), 0)

    def test_non_branch_command_ignored(self):
        self.assertEqual(_run_main("Bash", "git status --short"), 0)

    def test_branch_name_inside_commit_message_ignored(self):
        self.assertEqual(
            _run_main("Bash", "git commit -m 'git checkout -b wip mentioned'"), 0
        )


class TestPowerShellParity(unittest.TestCase):
    """Before the matcher covered PowerShell, none of these reached the hook."""

    def test_nonconforming_checkout_blocked(self):
        self.assertEqual(
            _run_main("PowerShell", "git checkout -b fix/hook-hardening"), 2
        )

    def test_nonconforming_switch_blocked(self):
        self.assertEqual(_run_main("PowerShell", "git switch -c wip"), 2)

    def test_conforming_checkout_allowed(self):
        self.assertEqual(
            _run_main("PowerShell", "git checkout -b bugfix/hook-hardening"), 0
        )

    def test_non_branch_command_ignored(self):
        self.assertEqual(_run_main("PowerShell", "Get-ChildItem C:/Projects"), 0)


if __name__ == "__main__":
    unittest.main()
