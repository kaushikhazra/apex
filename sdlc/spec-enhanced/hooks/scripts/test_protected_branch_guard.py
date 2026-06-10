"""Unit tests for protected_branch_guard.py.

Mocks subprocess.run so no real git repo is required.
Run from C:/Projects/APEX:
    python -m unittest sdlc/spec-enhanced/hooks/scripts/test_protected_branch_guard.py -v
"""

import importlib
import io
import json
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Helper — load the module under test each time so module-level state is fresh
# ---------------------------------------------------------------------------
SCRIPT_PATH = "sdlc/spec-enhanced/hooks/scripts/protected_branch_guard"


def _run_main(branch: str, stdin_data: dict) -> int:
    """Load (reload) the guard module, inject branch + stdin, call main()."""
    spec = importlib.util.spec_from_file_location(
        "protected_branch_guard",
        "sdlc/spec-enhanced/hooks/scripts/protected_branch_guard.py",
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    fake_proc = MagicMock()
    fake_proc.returncode = 0
    fake_proc.stdout = branch + "\n"

    with (
        patch.object(mod, "subprocess") as mock_subproc,
        patch("sys.stdin", io.StringIO(json.dumps(stdin_data))),
        patch("sys.stderr", io.StringIO()),
    ):
        mock_subproc.run.return_value = fake_proc
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


if __name__ == "__main__":
    unittest.main()
