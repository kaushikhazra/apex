"""Unit tests for security_guard.py.

No filesystem or shell is touched — main() is fed a payload on stdin and its
exit code inspected.

Run from C:/Projects/APEX:
    python -m unittest plugins/e-spec/hooks/scripts/test_security_guard.py -v
"""

import importlib.util
import io
import json
import re
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


def _run(stdin_data: dict):
    """Call main() with the given hook payload; return (exit code, stdout)."""
    mod = _load()
    out = io.StringIO()
    with (
        patch("sys.stdin", io.StringIO(json.dumps(stdin_data))),
        patch("sys.stdout", out),
        patch("sys.stderr", io.StringIO()),
    ):
        try:
            mod.main()
            code = 0
        except SystemExit as exc:
            code = int(exc.code)
    return code, out.getvalue()


def _run_main(stdin_data: dict) -> int:
    """2 when the call is held (file-tool exit 2, or a shell-command deny), else 0."""
    code, out = _run(stdin_data)
    if code:
        return code
    return 2 if out.strip() else 0


def _command(tool_name: str, command: str) -> dict:
    return {"tool_name": tool_name, "tool_input": {"command": command}}


def _deny(tool_name: str, command: str):
    """The parsed deny decision for a command, or None when it passes silently."""
    code, out = _run(_command(tool_name, command))
    assert code == 0, "shell commands deny through stdout, never exit 2"
    return json.loads(out)["hookSpecificOutput"] if out.strip() else None


def _ack_of(decision) -> str:
    return re.search(
        r"guard-ack:([0-9a-f]+)", decision["permissionDecisionReason"]
    ).group(1)


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


class TestDenyThenAck(unittest.TestCase):
    """Issue #26: a held command is denied once, then passes with its own ack."""

    # The command that stalled a Raspberry Pi cleanup on 2026-10-28: a delete of
    # one absolute path, matched by `rm\s+-rf\s+/`.
    PI_COMMAND = "ssh pi@raspberrypi 'rm -rf /home/pi/old-build'"

    def test_first_try_is_denied_with_reason_and_code(self):
        d = _deny("Bash", self.PI_COMMAND)
        self.assertEqual(d["permissionDecision"], "deny")
        self.assertEqual(d["hookEventName"], "PreToolUse")
        self.assertIn("rm", d["permissionDecisionReason"])
        self.assertRegex(d["permissionDecisionReason"], r"guard-ack:[0-9a-f]{6}")

    def test_correct_ack_lets_it_through_silently(self):
        code = _ack_of(_deny("Bash", self.PI_COMMAND))
        self.assertIsNone(_deny("Bash", f"{self.PI_COMMAND} # guard-ack:{code}"))

    def test_ack_on_a_new_last_line_works(self):
        code = _ack_of(_deny("Bash", self.PI_COMMAND))
        self.assertIsNone(_deny("Bash", f"{self.PI_COMMAND}\n# guard-ack:{code}"))

    def test_ack_copied_onto_another_command_is_denied_again(self):
        code = _ack_of(_deny("Bash", self.PI_COMMAND))
        other = "rm -rf /home/pi/other-dir"
        d = _deny("Bash", f"{other} # guard-ack:{code}")
        self.assertIsNotNone(d)
        self.assertNotEqual(_ack_of(d), code)

    def test_wrong_ack_is_denied_again(self):
        self.assertIsNotNone(_deny("Bash", f"{self.PI_COMMAND} # guard-ack:000000"))

    def test_ack_must_be_the_trailing_comment(self):
        code = _ack_of(_deny("Bash", self.PI_COMMAND))
        self.assertIsNotNone(_deny("Bash", f"# guard-ack:{code}\n{self.PI_COMMAND}"))

    def test_safe_command_stays_silent(self):
        self.assertIsNone(_deny("Bash", "git status --short"))
        self.assertIsNone(_deny("PowerShell", "Get-ChildItem C:/Projects"))

    def test_safe_command_with_a_stray_ack_stays_silent(self):
        self.assertIsNone(_deny("Bash", "git status # guard-ack:abcdef"))

    def test_powershell_follows_the_same_flow(self):
        cmd = "Remove-Item C:/tmp/x -Recurse -Force"
        d = _deny("PowerShell", cmd)
        self.assertIsNotNone(d)
        self.assertIsNone(_deny("PowerShell", f"{cmd} # guard-ack:{_ack_of(d)}"))

    def test_incident_command_needs_an_ack_in_both_shells(self):
        for tool in ("Bash", "PowerShell"):
            d = _deny(tool, INCIDENT_COMMAND)
            self.assertIsNotNone(d, tool)
            self.assertIsNone(
                _deny(tool, f"{INCIDENT_COMMAND}\n# guard-ack:{_ack_of(d)}")
            )

    def test_sensitive_file_command_is_acked_too(self):
        cmd = "cat /home/pi/.env"
        d = _deny("Bash", cmd)
        self.assertIsNotNone(d)
        self.assertIsNone(_deny("Bash", f"{cmd} # guard-ack:{_ack_of(d)}"))

    def test_every_finding_is_named_in_one_denial(self):
        d = _deny("PowerShell", 'Remove-Item ".git" -Recurse -Force; cat .env')
        reason = d["permissionDecisionReason"]
        self.assertIn("Destructive command detected", reason)
        self.assertIn("relative path", reason)
        self.assertIn("sensitive file", reason)

    def test_code_is_stable_and_command_specific(self):
        a1 = _ack_of(_deny("Bash", "rm -rf /a"))
        a2 = _ack_of(_deny("Bash", "rm -rf /a"))
        b = _ack_of(_deny("Bash", "rm -rf /b"))
        self.assertEqual(a1, a2)
        self.assertNotEqual(a1, b)

    def test_file_tool_sensitive_path_stays_a_hard_block(self):
        # No command to append a comment to, so no ack path.
        code, out = _run({"tool_name": "Read", "tool_input": {"file_path": "/x/.env"}})
        self.assertEqual(code, 2)
        self.assertEqual(out.strip(), "")


if __name__ == "__main__":
    unittest.main()
