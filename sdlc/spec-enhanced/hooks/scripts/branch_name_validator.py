"""Hook: Branch name validator.

Validates that new branches follow git flow naming conventions.

Event: PreToolUse (Bash)
"""

import json
import re
import sys

VALID_PREFIXES = (
    "feature/",
    "bugfix/",
    "hotfix/",
    "release/",
)


def main():
    data = json.loads(sys.stdin.read())
    command = data.get("tool_input", {}).get("command", "")

    # Only check commands that start with git checkout -b or git switch -c
    # Use ^ or start after && / ; to avoid matching inside commit messages
    first_command = command.strip().split("&&")[0].strip()
    match = re.match(
        r"git\s+(checkout\s+-b|switch\s+-c)\s+(\S+)", first_command
    )
    if not match:
        return

    branch_name = match.group(2)

    # Allow protected branches (switching to, not creating — but -b
    # would fail anyway if they exist)
    if branch_name in ("main", "develop"):
        return

    if not any(branch_name.startswith(p) for p in VALID_PREFIXES):
        print(
            f"BLOCKED: Branch '{branch_name}' does not follow naming "
            f"convention. Use one of: "
            f"{', '.join(p + '*' for p in VALID_PREFIXES)}",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
