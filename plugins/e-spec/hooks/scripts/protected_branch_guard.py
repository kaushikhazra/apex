"""Hook: Protected branch guard.

Blocks edits/commits/pushes on main, master, and develop branches.
Forces agents to create a feature/bugfix/hotfix/release branch first.
Both 'main' and 'master' are treated identically — push is blocked on both.

For Edit/Write tools: resolves the repo from the TARGET file path, not from
the session's cwd. A file not in any git repo is always allowed.

For Bash/PowerShell: resolves the repo from `git -C <path>` or
`--git-dir`/`--work-tree` if present in the command, else from session cwd.

Event: PreToolUse (Edit|Write|Bash|PowerShell)
"""

import json
import os
import re
import subprocess
import sys

PROTECTED_BRANCHES = ("main", "master", "develop")

# Tools whose input is a shell command rather than a file path. Both shells
# must be inspected — a guard that covers one of them leaves the other as a
# working route around it.
COMMAND_TOOLS = ("Bash", "PowerShell")


def get_branch_for_dir(directory):
    """Get the current branch for the repo containing `directory`.

    Returns (branch, repo_root) or (None, None) if not in a git repo.
    """
    result = subprocess.run(
        ["git", "-C", directory, "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None, None
    branch = result.stdout.strip()

    result2 = subprocess.run(
        ["git", "-C", directory, "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    repo_root = result2.stdout.strip() if result2.returncode == 0 else None
    return branch, repo_root


def nearest_existing_parent(path):
    """Walk up from `path` until we find a directory that exists."""
    path = os.path.normpath(path)
    while not os.path.isdir(path):
        parent = os.path.dirname(path)
        if parent == path:
            # Reached filesystem root
            return path
        path = parent
    return path


def get_branch_for_file(file_path):
    """Resolve repo from TARGET file, not session cwd.

    For new files whose directory doesn't exist yet, walks up to the
    nearest existing parent.

    Returns (branch, repo_root) or (None, None) if not in a git repo.
    """
    dirname = os.path.dirname(file_path)
    existing_dir = nearest_existing_parent(dirname)
    return get_branch_for_dir(existing_dir)


def is_protected_source_path(file_path, repo_root):
    """Check if file_path is under a protected source directory RELATIVE to repo root.

    Only checks if the path starts with src/ or tests/ relative to the repo,
    not whether those strings appear anywhere in the absolute path.
    """
    if not repo_root:
        return False

    # Normalise both to forward slashes for comparison
    norm_file = os.path.normpath(file_path).replace("\\", "/")
    norm_root = os.path.normpath(repo_root).replace("\\", "/")

    # Strip trailing slash from root
    if norm_root.endswith("/"):
        norm_root = norm_root[:-1]

    # Get path relative to repo root
    if not norm_file.startswith(norm_root + "/") and norm_file != norm_root:
        return False

    rel_path = norm_file[len(norm_root) + 1 :]
    protected_prefixes = ("src/", "tests/")
    return any(
        rel_path.startswith(prefix) or rel_path == prefix.rstrip("/")
        for prefix in protected_prefixes
    )


def extract_git_target_dir(command):
    """Extract the target directory from git -C <path> in a command.

    Also handles --git-dir and --work-tree for trivial cases.
    Returns the path if found, else None.
    """
    # git -C <path>
    match = re.search(r"git\s+-C\s+(\S+)", command)
    if match:
        return match.group(1).strip("'\"")

    # --work-tree=<path>
    match = re.search(r"--work-tree[=\s]+(\S+)", command)
    if match:
        return match.group(1).strip("'\"")

    # --git-dir=<path> — derive the working directory
    match = re.search(r"--git-dir[=\s]+(\S+)", command)
    if match:
        git_dir = match.group(1).strip("'\"")
        return os.path.dirname(git_dir) if git_dir.endswith(".git") else git_dir

    return None


def main():
    data = json.loads(sys.stdin.read())
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name in COMMAND_TOOLS:
        command = tool_input.get("command", "")

        # Only inspect git commit / git push commands.
        # Use \b word boundaries so `git -C <path> commit` is matched,
        # not just `git commit` (subcommand may not be adjacent).
        is_commit = bool(re.search(r"\bgit\b.*\bcommit\b", command))
        is_push = bool(re.search(r"\bgit\b.*\bpush\b", command))
        if not is_commit and not is_push:
            return

        # Resolve repo from command's target, fall back to session cwd
        target_dir = extract_git_target_dir(command)
        if target_dir:
            branch, _ = get_branch_for_dir(nearest_existing_parent(target_dir))
        else:
            branch, _ = get_branch_for_dir(os.getcwd())

        if branch is None or branch not in PROTECTED_BRANCHES:
            return

        if is_commit:
            print(
                f"BLOCKED: Cannot commit on '{branch}'. "
                "Create a branch first: feature/*, bugfix/*, hotfix/*, release/*",
                file=sys.stderr,
            )
            sys.exit(2)

        if is_push and branch in ("main", "master"):
            print(
                "BLOCKED: Cannot push to 'main'. Use a release/* or hotfix/* branch.",
                file=sys.stderr,
            )
            sys.exit(2)
        return

    # Edit or Write — resolve repo from TARGET file path
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return

    branch, repo_root = get_branch_for_file(file_path)

    # Not in a git repo → allow
    if branch is None:
        return

    # Not on a protected branch → allow
    if branch not in PROTECTED_BRANCHES:
        return

    # On a protected branch — only block changes to source/test files
    if is_protected_source_path(file_path, repo_root):
        print(
            f"BLOCKED: Cannot edit source/test files on '{branch}'. "
            "Create a branch first: feature/*, bugfix/*, hotfix/*, release/*",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
