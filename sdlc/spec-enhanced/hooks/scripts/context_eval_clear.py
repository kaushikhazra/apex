"""Hook: Clear eval artifacts after a commit with 'context evaluated'.

Detects git commit commands that include 'context evaluated' in the
message and cleans up transient eval files: eval.md and dryrun reports.

Event: PostToolUse (Bash|PowerShell)
"""

import json
import os
import re
import sys
from pathlib import Path

EVAL_NAME = "eval.md"
DRYRUN_GLOB = "dryrun-*.md"


def resolve_claude_dir(data):
    """Anchor on the session's project, never on the process cwd."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    return Path(project_dir) / ".claude"


def main():
    data = json.loads(sys.stdin.read())
    tool_input = data.get("tool_input", {})
    command = tool_input.get("command", "")

    # Only act on git commit commands
    if not re.search(r"git\s+commit", command):
        return

    # Check if the commit message contains "context evaluated"
    if "context evaluated" not in command.lower():
        return

    claude_dir = resolve_claude_dir(data)

    # Clear eval checklist
    eval_path = claude_dir / EVAL_NAME
    if eval_path.exists():
        eval_path.unlink()

    # Clear dryrun reports
    for f in claude_dir.glob(DRYRUN_GLOB):
        f.unlink()


if __name__ == "__main__":
    main()
