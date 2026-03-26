"""Hook: Protected branch guard.

Blocks edits/commits/pushes on main and develop branches.
Forces agents to create a feature/bugfix/hotfix/release branch first.

Event: PreToolUse (Edit|Write|Bash)
"""

import json
import re
import subprocess
import sys

PROTECTED_BRANCHES = ("main", "develop")


def get_current_branch():
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def main():
    branch = get_current_branch()
    if branch not in PROTECTED_BRANCHES:
        return

    data = json.loads(sys.stdin.read())
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        # Block direct commits on protected branches
        if re.search(r"git\s+commit", command):
            print(
                f"BLOCKED: Cannot commit on '{branch}'. "
                "Create a branch first: feature/*, bugfix/*, hotfix/*, release/*",
                file=sys.stderr,
            )
            sys.exit(2)
        # Block push to main (merges to develop need to be pushed)
        if re.search(r"git\s+push", command) and branch == "main":
            print(
                "BLOCKED: Cannot push to 'main'. "
                "Use a release/* or hotfix/* branch.",
                file=sys.stderr,
            )
            sys.exit(2)
        return

    # Edit or Write — block changes to source and test files
    # CONFIGURE: Path segments that identify protected source directories.
    # Any file containing these segments will be blocked on protected branches.
    protected_paths = ("src/", "tests/")
    file_path = tool_input.get("file_path", "").replace("\\", "/")
    if any(segment in file_path for segment in protected_paths):
        print(
            f"BLOCKED: Cannot edit source/test files on '{branch}'. "
            "Create a branch first: feature/*, bugfix/*, hotfix/*, release/*",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
