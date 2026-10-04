"""Tests for protected_branch_guard.py.

Uses throwaway git repos under C:/Projects/.tmp/apex-guard-* to verify
that the guard resolves branch from the TARGET (file or git -C path),
not from the session's cwd.
"""

import json
import os
import shutil
import stat
import subprocess
import sys

import pytest


def _force_rmtree(path):
    """rmtree that handles Windows read-only git objects."""
    if not os.path.exists(path):
        return

    def _on_error(_func, _path, _exc_info):
        os.chmod(_path, stat.S_IWRITE)
        _func(_path)

    shutil.rmtree(path, onerror=_on_error)


SCRIPT = os.path.normpath(
    os.path.join(
        os.path.dirname(__file__), "..", "scripts", "protected_branch_guard.py"
    )
)
TMP_ROOT = "C:/Projects/.tmp"


def _tmp_dir(name):
    path = os.path.join(TMP_ROOT, name)
    os.makedirs(path, exist_ok=True)
    return path


def _init_repo(path, branch="master"):
    """Create a git repo at `path` on the given branch."""
    if os.path.exists(path):
        _force_rmtree(path)
    os.makedirs(path, exist_ok=True)
    subprocess.run(["git", "init", "-b", branch, path], capture_output=True, check=True)
    # Need at least one commit for branch to exist
    dummy = os.path.join(path, "README.md")
    with open(dummy, "w") as f:
        f.write("init")
    subprocess.run(["git", "-C", path, "add", "."], capture_output=True, check=True)
    subprocess.run(
        ["git", "-C", path, "commit", "-m", "init", "--no-gpg-sign"],
        capture_output=True,
        check=True,
        env={
            **os.environ,
            "GIT_AUTHOR_NAME": "test",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "test",
            "GIT_COMMITTER_EMAIL": "t@t",
        },
    )
    return path


def _checkout_branch(repo, branch):
    subprocess.run(
        ["git", "-C", repo, "checkout", "-b", branch],
        capture_output=True,
        check=True,
    )


def _run_guard(tool_name, tool_input, cwd=None):
    """Run the guard script, return (exit_code, stderr)."""
    payload = json.dumps({"tool_name": tool_name, "tool_input": tool_input})
    result = subprocess.run(
        [sys.executable, SCRIPT],
        input=payload,
        capture_output=True,
        text=True,
        cwd=cwd or os.getcwd(),
    )
    return result.returncode, result.stderr


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def repo_on_master():
    path = _init_repo(_tmp_dir("apex-guard-master"))
    # Create src/ and tests/ dirs
    os.makedirs(os.path.join(path, "src"), exist_ok=True)
    os.makedirs(os.path.join(path, "tests"), exist_ok=True)
    yield path
    _force_rmtree(path)


@pytest.fixture(scope="module")
def repo_on_feature():
    path = _init_repo(_tmp_dir("apex-guard-feature"), branch="master")
    _checkout_branch(path, "feature/test-branch")
    os.makedirs(os.path.join(path, "src"), exist_ok=True)
    yield path
    _force_rmtree(path)


@pytest.fixture(scope="module")
def no_repo_dir():
    path = _tmp_dir("apex-guard-norepo")
    # Ensure it's not inside a git repo — remove .git if present
    git_dir = os.path.join(path, ".git")
    if os.path.exists(git_dir):
        shutil.rmtree(git_dir)
    yield path
    _force_rmtree(path)


# ── Measured failures (4 Oct 2026) ────────────────────────────────────


class TestMeasuredFailure1:
    """Write to repo on feature branch → should be ALLOWED.

    Old bug: session cwd on master caused this to be blocked.
    """

    def test_edit_feature_branch_from_master_cwd(self, repo_on_master, repo_on_feature):
        target = os.path.join(repo_on_feature, "src", ".gitignore").replace("\\", "/")
        code, stderr = _run_guard("Write", {"file_path": target}, cwd=repo_on_master)
        assert code == 0, f"Should allow edit on feature branch, got: {stderr}"


class TestMeasuredFailure2:
    """Write to a folder NOT in any git repo → should be ALLOWED.

    Old bug: 'tests/' substring in absolute path caused blocking.
    """

    def test_edit_non_repo_with_tests_in_path(self, repo_on_master, no_repo_dir):
        # Path contains 'tests/' as a substring but is not in a repo
        target_dir = os.path.join(no_repo_dir, "factory", "tests")
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, "x.test.ts").replace("\\", "/")
        code, stderr = _run_guard("Write", {"file_path": target}, cwd=repo_on_master)
        assert code == 0, f"Should allow edit outside any repo, got: {stderr}"


class TestMeasuredFailure3:
    """Session cwd on feature branch, git commit targeting repo on master → BLOCKED.

    Old bug: session cwd on feature allowed committing to a master repo.
    """

    def test_commit_to_master_repo_from_feature_cwd(
        self, repo_on_master, repo_on_feature
    ):
        command = f"git -C {repo_on_master} commit -m 'oops'"
        code, stderr = _run_guard("Bash", {"command": command}, cwd=repo_on_feature)
        assert code == 2, "Should block commit on master repo"
        assert "BLOCKED" in stderr


# ── Additional coverage ───────────────────────────────────────────────


class TestEditWrite:
    """Edit/Write tool — repo resolution from target file."""

    def test_block_src_on_master(self, repo_on_master):
        target = os.path.join(repo_on_master, "src", "app.py").replace("\\", "/")
        code, stderr = _run_guard("Edit", {"file_path": target}, cwd=repo_on_master)
        assert code == 2, "Should block src/ edits on master"
        assert "BLOCKED" in stderr

    def test_allow_non_src_on_master(self, repo_on_master):
        target = os.path.join(repo_on_master, "docs", "readme.md").replace("\\", "/")
        code, stderr = _run_guard("Edit", {"file_path": target}, cwd=repo_on_master)
        assert code == 0, f"Should allow non-src edits on master, got: {stderr}"

    def test_block_tests_on_master(self, repo_on_master):
        target = os.path.join(repo_on_master, "tests", "test_foo.py").replace("\\", "/")
        code, stderr = _run_guard("Write", {"file_path": target}, cwd=repo_on_master)
        assert code == 2, "Should block tests/ edits on master"
        assert "BLOCKED" in stderr


class TestBashCommands:
    """Bash/PowerShell — git -C resolution."""

    def test_push_to_master_repo_from_feature_cwd(
        self, repo_on_master, repo_on_feature
    ):
        command = f"git -C {repo_on_master} push origin master"
        code, stderr = _run_guard("Bash", {"command": command}, cwd=repo_on_feature)
        assert code == 2, "Should block push to master repo"
        assert "BLOCKED" in stderr

    def test_commit_to_feature_repo_from_master_cwd(
        self, repo_on_master, repo_on_feature
    ):
        command = f"git -C {repo_on_feature} commit -m 'ok'"
        code, stderr = _run_guard("Bash", {"command": command}, cwd=repo_on_master)
        assert code == 0, f"Should allow commit on feature branch, got: {stderr}"

    def test_powershell_commit_blocked(self, repo_on_master):
        command = f"git -C {repo_on_master} commit -m 'oops'"
        code, stderr = _run_guard(
            "PowerShell", {"command": command}, cwd=repo_on_master
        )
        assert code == 2, "PowerShell should block commit on master too"
        assert "BLOCKED" in stderr

    def test_powershell_push_blocked(self, repo_on_master):
        command = f"git -C {repo_on_master} push origin master"
        code, stderr = _run_guard(
            "PowerShell", {"command": command}, cwd=repo_on_master
        )
        assert code == 2, "PowerShell should block push on master"
        assert "BLOCKED" in stderr

    def test_non_git_command_allowed(self, repo_on_master):
        code, stderr = _run_guard("Bash", {"command": "ls -la"}, cwd=repo_on_master)
        assert code == 0, f"Non-git commands should be allowed, got: {stderr}"
