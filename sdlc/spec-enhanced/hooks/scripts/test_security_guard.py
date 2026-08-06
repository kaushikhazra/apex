"""Unit tests for security_guard.py.

No filesystem or shell is touched — main() is fed a payload on stdin and its
exit code inspected.

Run from C:/Projects/APEX:
    python -m unittest sdlc/spec-enhanced/hooks/scripts/test_security_guard.py -v
"""

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = str(Path(__file__).with_name("security_guard.py"))

# The command that destroyed a repository's git history on 2026-08-04.
# Set-Location failed (non-terminating), the ; chain continued, and ".git"
# resolved against the session's real cwd.
INCIDENT_COMMAND = (
    'Set-Location "C:/Projects/claude-sandbox/sb"; '
    'if (Test-Path ".git") { Remove-Item ".git" -Recurse -Force }'
)


def _load():
    spec = importlib.util.spec_from_file_location("security_guard", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _run_main(stdin_data: dict) -> int:
    """Call main() with the given hook payload; return its exit code."""
    mod = _load()
    with (
        patch("sys.stdin", io.StringIO(json.dumps(stdin_data))),
        patch("sys.stderr", io.StringIO()),
    ):
        try:
            mod.main()
            return 0
        except SystemExit as exc:
            return int(exc.code)


def _command(tool_name: str, command: str) -> dict:
    return {"tool_name": tool_name, "tool_input": {"command": command}}


class TestIncidentRegression(unittest.TestCase):
    """The literal incident command must be blocked in both shells."""

    def test_incident_command_powershell_blocked(self):
        self.assertEqual(_run_main(_command("PowerShell", INCIDENT_COMMAND)), 2)

    def test_incident_command_bash_blocked(self):
        self.assertEqual(_run_main(_command("Bash", INCIDENT_COMMAND)), 2)

    def test_incident_first_half_force_only_blocked(self):
        # The same cleanup's earlier statement: -Force with no -Recurse.
        self.assertEqual(
            _run_main(
                _command(
                    "PowerShell",
                    'Remove-Item ".claude/.self-aware" -Force',
                )
            ),
            2,
        )


class TestDestructivePowerShell(unittest.TestCase):
    """Remove-Item with -Recurse/-Force is blocked regardless of target."""

    def test_absolute_throwaway_path_blocked(self):
        # Velasari's live-fire (a): absolute, non-.git, still destructive.
        self.assertEqual(
            _run_main(
                _command(
                    "PowerShell",
                    "Remove-Item C:/Projects/.tmp/probe -Recurse -Force",
                )
            ),
            2,
        )

    def test_flags_before_target_blocked(self):
        self.assertEqual(
            _run_main(_command("PowerShell", "Remove-Item -Recurse -Force C:/tmp/x")),
            2,
        )

    def test_alias_blocked(self):
        self.assertEqual(
            _run_main(_command("PowerShell", "rd C:/tmp/x -Recurse -Force")), 2
        )

    def test_path_parameter_blocked(self):
        self.assertEqual(
            _run_main(_command("PowerShell", 'Remove-Item -Path "C:/tmp/x" -Recurse')),
            2,
        )

    def test_benign_powershell_allowed(self):
        self.assertEqual(
            _run_main(_command("PowerShell", "Get-ChildItem C:/Projects")), 0
        )

    def test_non_destructive_remove_item_allowed(self):
        # No -Recurse/-Force and no .git — outside both guards by design.
        self.assertEqual(
            _run_main(_command("PowerShell", "Remove-Item C:/tmp/scratch.txt")),
            0,
        )


class TestRelativeGitGuard(unittest.TestCase):
    """Narrowly scoped: a destructive verb plus an unanchored .git target."""

    def test_bare_relative_git_blocked(self):
        self.assertEqual(_run_main(_command("PowerShell", 'del ".git"')), 2)

    def test_dot_slash_relative_git_blocked(self):
        self.assertEqual(_run_main(_command("Bash", "rm -r ./.git")), 2)

    def test_relative_git_subpath_blocked(self):
        self.assertEqual(
            _run_main(_command("PowerShell", "Remove-Item .git/objects")), 2
        )

    def test_absolute_git_without_flags_allowed(self):
        # Anchored path — not the accidental-cwd failure this guard exists for.
        self.assertEqual(
            _run_main(_command("PowerShell", "Remove-Item C:/Projects/sandbox/.git")),
            0,
        )

    def test_git_reference_without_destructive_verb_allowed(self):
        self.assertEqual(_run_main(_command("PowerShell", 'Test-Path ".git"')), 0)

    def test_gitignore_is_not_a_git_reference(self):
        self.assertEqual(
            _run_main(_command("Bash", "git commit -m 'update .gitignore'")), 0
        )

    def test_github_dir_is_not_a_git_reference(self):
        self.assertEqual(_run_main(_command("Bash", "ls .github/workflows")), 0)

    def test_commit_message_discussing_the_guard_is_allowed(self):
        """Caught live: this guard blocked the commit that introduced it.

        The message names Remove-Item on one line and .git on another. A
        verb and its target meet on one line; prose does not.
        """
        message = (
            "fix(e-spec): harden three hooks\n\n"
            "Adds Remove-Item/-Recurse/-Force patterns, and a guard for a\n"
            "destructive command whose target is a relative path\n"
            "resolving to .git. Scoped to .git deliberately.\n"
        )
        self.assertEqual(_run_main(_command("Bash", f"git commit -m '{message}'")), 0)

    def test_single_line_prose_naming_verb_and_target_is_allowed(self):
        """Caught live: this guard blocked a status message describing it.

        The whole message is one line, so line-scoping alone does not save
        it — .git must be the verb's first non-flag argument, not the
        fifth word of a sentence.
        """
        prose = (
            "my own guard blocked my first commit: the message named "
            "Remove-Item on one line and .git on another, so I rescoped it"
        )
        self.assertEqual(
            _run_main(_command("Bash", f"send-message apex velasari '{prose}'")),
            0,
        )

    def test_second_target_position_is_a_documented_gap(self):
        # Not caught by this guard, and not by the pattern list either —
        # the rm -rf patterns need the target right after the flag.
        self.assertEqual(_run_main(_command("PowerShell", "Remove-Item build .git")), 0)
        self.assertEqual(_run_main(_command("Bash", "rm -rf build .git")), 0)

    def test_second_target_position_with_flags_is_caught_in_powershell(self):
        self.assertEqual(
            _run_main(_command("PowerShell", "Remove-Item build .git -Recurse")), 2
        )

    def test_verb_after_the_git_reference_on_one_line_is_allowed(self):
        self.assertEqual(
            _run_main(_command("Bash", "echo '.git is protected, never rm it'")),
            0,
        )


class TestSensitiveFiles(unittest.TestCase):
    """PowerShell commands are screened for sensitive files like bash ones."""

    def test_powershell_env_access_blocked(self):
        self.assertEqual(
            _run_main(_command("PowerShell", "Test-Path C:/Projects/APEX/.env")),
            2,
        )

    def test_powershell_env_example_allowed(self):
        self.assertEqual(
            _run_main(_command("PowerShell", "Get-Content .env.example")), 0
        )

    def test_read_sensitive_file_blocked(self):
        self.assertEqual(
            _run_main({"tool_name": "Read", "tool_input": {"file_path": "/x/.env"}}),
            2,
        )

    def test_edit_ordinary_file_allowed(self):
        self.assertEqual(
            _run_main({"tool_name": "Edit", "tool_input": {"file_path": "/x/main.py"}}),
            0,
        )


class TestBashRegression(unittest.TestCase):
    """Pre-existing bash coverage is unchanged."""

    def test_rm_rf_root_blocked(self):
        self.assertEqual(_run_main(_command("Bash", "rm -rf /")), 2)

    def test_rm_rf_star_blocked(self):
        self.assertEqual(_run_main(_command("Bash", "rm -rf *")), 2)

    def test_ordinary_bash_allowed(self):
        self.assertEqual(_run_main(_command("Bash", "git status --short")), 0)


if __name__ == "__main__":
    unittest.main()
