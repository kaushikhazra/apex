"""Unit tests for protected_branch_guard.py.

Mocks subprocess.run so no real git repo is required.
Run from C:/Projects/APEX:
    python -m unittest plugins/e-spec/hooks/scripts/test_protected_branch_guard.py -v
"""

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helper — load the module under test each time so module-level state is fresh
# ---------------------------------------------------------------------------
SCRIPT = str(Path(__file__).with_name("protected_branch_guard.py"))


def _run_main(
    branch: str,
    stdin_data: dict,
    guard_config: str | None = None,
    tags: tuple = ("v1.0", "v1.3.0"),
    heads: tuple = (),
) -> int:
    """Load (reload) the guard module, inject branch + stdin, call main().

    `guard_config` is the value of `git config apex.branchGuard` (None = unset).
    `tags` / `heads` are the tag and extra branch names the fake repo holds.
    """
    spec = importlib.util.spec_from_file_location("protected_branch_guard", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    def fake_run(cmd, **_kwargs):
        proc = MagicMock()
        if "config" in cmd:
            proc.returncode = 0 if guard_config is not None else 1
            proc.stdout = (guard_config or "") + "\n"
        elif "show-ref" in cmd:
            ref = cmd[-1]
            known = {f"refs/tags/{t}" for t in tags} | {
                f"refs/heads/{h}" for h in (branch, *heads)
            }
            proc.returncode = 0 if ref in known else 1
            proc.stdout = ""
        elif "--show-toplevel" in cmd:
            proc.returncode = 0
            proc.stdout = "/project\n"
        else:
            proc.returncode = 0
            proc.stdout = branch + "\n"
        return proc

    with (
        patch.object(mod, "subprocess") as mock_subproc,
        patch("sys.stdin", io.StringIO(json.dumps(stdin_data))),
        patch("sys.stderr", io.StringIO()),
    ):
        mock_subproc.run.side_effect = fake_run
        try:
            mod.main()
            return 0
        except SystemExit as exc:
            return int(exc.code)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestProtectedBranchGuard(unittest.TestCase):
    # 1. branch=master, Bash git commit → BLOCKED (exit 2)
    def test_master_bash_commit_blocked(self):
        code = _run_main(
            "master",
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'oops'"}},
        )
        self.assertEqual(code, 2)

    # 2. branch=master, Bash git push → BLOCKED (exit 2)
    def test_master_bash_push_blocked(self):
        code = _run_main(
            "master",
            {"tool_name": "Bash", "tool_input": {"command": "git push origin master"}},
        )
        self.assertEqual(code, 2)

    # 3. branch=main, Bash git commit → BLOCKED (exit 2)
    def test_main_bash_commit_blocked(self):
        code = _run_main(
            "main",
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'bad'"}},
        )
        self.assertEqual(code, 2)

    # 4. branch=develop, Bash git commit → BLOCKED (exit 2)
    def test_develop_bash_commit_blocked(self):
        code = _run_main(
            "develop",
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'nope'"}},
        )
        self.assertEqual(code, 2)

    # 5. branch=feature/foo, Bash git commit → ALLOWED (exit 0)
    def test_feature_bash_commit_allowed(self):
        code = _run_main(
            "feature/foo",
            {"tool_name": "Bash", "tool_input": {"command": "git commit -m 'ok'"}},
        )
        self.assertEqual(code, 0)

    # 6. branch=master, Write to src/foo.py → BLOCKED (exit 2)
    def test_master_write_src_blocked(self):
        code = _run_main(
            "master",
            {"tool_name": "Write", "tool_input": {"file_path": "/project/src/foo.py"}},
        )
        self.assertEqual(code, 2)

    # 7. branch=feature/foo, Write to src/foo.py → ALLOWED (exit 0)
    def test_feature_write_src_allowed(self):
        code = _run_main(
            "feature/foo",
            {"tool_name": "Write", "tool_input": {"file_path": "/project/src/foo.py"}},
        )
        self.assertEqual(code, 0)


class TestPowerShellParity(unittest.TestCase):
    """Until the matcher and the tool-name test covered PowerShell, every
    case below was an unguarded route onto a protected branch."""

    # branch=master, PowerShell git commit → BLOCKED (exit 2)
    def test_master_powershell_commit_blocked(self):
        code = _run_main(
            "master",
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": "git commit -m 'oops'"},
            },
        )
        self.assertEqual(code, 2)

    # branch=master, PowerShell git push → BLOCKED (exit 2)
    def test_master_powershell_push_blocked(self):
        code = _run_main(
            "master",
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": "git push origin master"},
            },
        )
        self.assertEqual(code, 2)

    # branch=main, PowerShell git push → BLOCKED (exit 2)
    def test_main_powershell_push_blocked(self):
        code = _run_main(
            "main",
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": "git push origin main"},
            },
        )
        self.assertEqual(code, 2)

    # branch=develop, PowerShell git commit → BLOCKED (exit 2)
    def test_develop_powershell_commit_blocked(self):
        code = _run_main(
            "develop",
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": "git commit -m 'nope'"},
            },
        )
        self.assertEqual(code, 2)

    # PowerShell here-string commit message → still BLOCKED (exit 2)
    def test_master_powershell_here_string_commit_blocked(self):
        code = _run_main(
            "master",
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": "git commit -m @'\nchore: sweep\n'@"},
            },
        )
        self.assertEqual(code, 2)

    # branch=bugfix/foo, PowerShell git commit → ALLOWED (exit 0)
    def test_bugfix_powershell_commit_allowed(self):
        code = _run_main(
            "bugfix/foo",
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": "git commit -m 'ok'"},
            },
        )
        self.assertEqual(code, 0)

    # branch=master, PowerShell non-git command → ALLOWED (exit 0)
    def test_master_powershell_read_only_allowed(self):
        code = _run_main(
            "master",
            {
                "tool_name": "PowerShell",
                "tool_input": {"command": "git status --short"},
            },
        )
        self.assertEqual(code, 0)


class TestTagPush(unittest.TestCase):
    """A push that only moves tags changes no branch; anything that could
    move a protected branch stays blocked."""

    @staticmethod
    def _push(command, branch="main", tool="Bash", **kwargs):
        return _run_main(
            branch,
            {"tool_name": tool, "tool_input": {"command": command}},
            **kwargs,
        )

    def test_tag_push_allowed(self):
        for command in (
            "git push origin v1.0",
            "git push origin refs/tags/v1.0",
            "git push --tags",
            "git push origin --tags",
            "git push origin tag v1.0",
            "git push origin :v1.0",
            "git push -f origin v1.0",
        ):
            for branch in ("main", "master"):
                with self.subTest(command=command, branch=branch):
                    self.assertEqual(self._push(command, branch=branch), 0)

    def test_tag_push_allowed_in_powershell(self):
        self.assertEqual(self._push("git push origin v1.3.0", tool="PowerShell"), 0)

    def test_branch_push_blocked(self):
        for command in (
            "git push",
            "git push origin",
            "git push origin main",
            "git push origin master",
            "git push origin HEAD",
            "git push -u origin HEAD",
        ):
            for branch in ("main", "master"):
                with self.subTest(command=command, branch=branch):
                    self.assertEqual(self._push(command, branch=branch), 2)

    def test_tag_and_branch_blocked(self):
        self.assertEqual(self._push("git push origin v1.0 main"), 2)
        self.assertEqual(self._push("git push --tags origin main"), 2)

    def test_branch_updating_flags_blocked(self):
        for command in (
            "git push --all origin",
            "git push --mirror origin",
            "git push --follow-tags origin v1.0",
        ):
            with self.subTest(command=command):
                self.assertEqual(self._push(command), 2)

    def test_tag_source_to_branch_destination_blocked(self):
        self.assertEqual(self._push("git push origin v1.0:refs/heads/main"), 2)
        self.assertEqual(self._push("git push origin v1.0:main"), 2)

    def test_unknown_name_blocked(self):
        self.assertEqual(self._push("git push origin v9.9"), 2)

    def test_name_shared_by_tag_and_branch_blocked(self):
        self.assertEqual(self._push("git push origin v1.0", heads=("v1.0",)), 2)

    def test_develop_push_stays_allowed(self):
        self.assertEqual(self._push("git push origin develop", branch="develop"), 0)

    def test_guard_off_allows_branch_push(self):
        self.assertEqual(self._push("git push origin main", guard_config="off"), 0)


class TestBranchGuardOptOut(unittest.TestCase):
    """`git config apex.branchGuard off` allows the call; anything else, or
    unset, is today's behaviour."""

    COMMIT = {"tool_name": "Bash", "tool_input": {"command": "git commit -m x"}}
    WRITE = {"tool_name": "Write", "tool_input": {"file_path": "/project/src/foo.py"}}

    def test_off_allows_commit_on_master(self):
        self.assertEqual(_run_main("master", self.COMMIT, guard_config="off"), 0)

    def test_off_allows_src_write_on_master(self):
        self.assertEqual(_run_main("master", self.WRITE, guard_config="off"), 0)

    def test_other_value_still_blocks(self):
        self.assertEqual(_run_main("master", self.COMMIT, guard_config="on"), 2)

    def test_unset_still_blocks(self):
        self.assertEqual(_run_main("master", self.COMMIT, guard_config=None), 2)


if __name__ == "__main__":
    unittest.main()
