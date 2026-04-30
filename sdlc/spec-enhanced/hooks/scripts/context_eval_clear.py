"""Hook: Clear eval artifacts after a commit with 'context evaluated'.

Detects git commit commands that include 'context evaluated' in the
message and cleans up transient eval files: eval.md and dryrun reports.

Event: PostToolUse (Bash)
"""

import glob
import json
import re
import sys
from pathlib import Path

EVAL_FILE = ".claude/eval.md"
DRYRUN_PATTERN = ".claude/dryrun-*.md"


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

    # Clear eval checklist
    eval_path = Path(EVAL_FILE)
    if eval_path.exists():
        eval_path.unlink()

    # Clear dryrun reports
    for f in glob.glob(DRYRUN_PATTERN):
        Path(f).unlink()


if __name__ == "__main__":
    main()
