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
import shlex
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


def _extract_git_subcommand(command):
    """Find the git subcommand, skipping global options.

    Global options that take a value: -C <path>, -c <key=val>,
    --git-dir=.., --work-tree=.., --namespace=.., --exec-path=..
    Global flags (no value): --no-pager, --bare, --no-replace-objects, etc.

    Returns the first non-option token after 'git', or None if the
    command doesn't start with git (after pipe splitting).
    """
    # Only look at the segment before any pipe — later segments are
    # separate commands (e.g. `git log | grep commit`).
    segment = command.split("|")[0]
    tokens = _shlex_split(segment)

    # Find the 'git' token
    try:
        git_idx = tokens.index("git")
    except ValueError:
        return None

    # Walk tokens after 'git', skipping global options
    # Options that consume the NEXT token as their value:
    options_with_value = {
        "-C",
        "-c",
        "--git-dir",
        "--work-tree",
        "--namespace",
        "--exec-path",
        "--super-prefix",
    }
    i = git_idx + 1
    while i < len(tokens):
        tok = tokens[i]

        # Options that consume a following value token
        if tok in options_with_value:
            i += 2  # skip the option and its value
            continue

        # --key=value style global options (skip)
        if tok.startswith("--") and "=" in tok:
            i += 1
            continue

        # Any other flag (--no-pager, --bare, etc.)
        if tok.startswith("-"):
            i += 1
            continue

        # First non-option token → the subcommand
        return tok

    return None


def _shlex_split(command):
    """Split a shell command into tokens, handling quoted paths.

    Uses posix=True so quotes are removed and spaces inside quotes are
    preserved.  Windows backslashes inside double-quotes are kept as-is
    by pre-escaping them before shlex sees them.
    """
    # shlex posix mode treats backslash as escape; double them so
    # Windows paths like C:\Projects survive splitting.
    escaped = command.replace("\\", "\\\\")
    try:
        return shlex.split(escaped, posix=True)
    except ValueError:
        # Unbalanced quotes — fall back to naive whitespace split
        return command.split()


def extract_git_target_dir(command):
    """Extract the target directory from git -C <path> in a command.

    Also handles --git-dir and --work-tree for trivial cases.
    Returns the path if found, else None.
    """
    tokens = _shlex_split(command)

    i = 0
    while i < len(tokens):
        tok = tokens[i]

        # git -C <path>
        if tok == "-C" and i + 1 < len(tokens):
            return tokens[i + 1]

        # --work-tree=<path> or --work-tree <path>
        if tok.startswith("--work-tree="):
            return tok.split("=", 1)[1]
        if tok == "--work-tree" and i + 1 < len(tokens):
            return tokens[i + 1]

        # --git-dir=<path> or --git-dir <path>
        if tok.startswith("--git-dir="):
            git_dir = tok.split("=", 1)[1]
            return os.path.dirname(git_dir) if git_dir.endswith(".git") else git_dir
        if tok == "--git-dir" and i + 1 < len(tokens):
            git_dir = tokens[i + 1]
            return os.path.dirname(git_dir) if git_dir.endswith(".git") else git_dir

        i += 1

    return None


def main():
    data = json.loads(sys.stdin.read())
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name in COMMAND_TOOLS:
        command = tool_input.get("command", "")

        # Only inspect git commit / git push commands.
        # Parse the actual subcommand (first non-option word after 'git')
        # so that `git log --grep commit` is not mistaken for a commit.
        subcommand = _extract_git_subcommand(command)
        is_commit = subcommand == "commit"
        is_push = subcommand == "push"
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
