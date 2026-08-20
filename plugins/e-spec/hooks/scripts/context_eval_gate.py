"""Hook: Context evaluation gate.

Checks if .claude/eval.md has unchecked items when the agent stops.
Outputs a reminder to run the appropriate dryrun skills.

Event: Stop
"""

import json
import os
import sys
from pathlib import Path

EVAL_FILE = ".claude/eval.md"


def resolve_eval_path(data):
    """Anchor on the session's project, never on the process cwd.

    This must resolve identically to context_change_tracker.py, which
    writes the file. A writer anchored on the project and a reader anchored
    on the process cwd agree in the common case and diverge silently
    otherwise — the tracker logs a pending review the gate never sees, and
    the gate is dead again for a new reason.
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    return Path(project_dir) / EVAL_FILE


def main():
    # Stop hooks must read stdin (JSON with session info)
    hook_input = json.loads(sys.stdin.read())

    # Prevent infinite loops -- if we already triggered a continuation,
    # don't block again
    if hook_input.get("stop_hook_active"):
        return

    eval_path = resolve_eval_path(hook_input)

    if not eval_path.exists():
        return

    content = eval_path.read_text(encoding="utf-8")
    unchecked = [
        line.strip()
        for line in content.splitlines()
        if line.strip().startswith("- [ ]")
    ]

    if not unchecked:
        return

    # Exit code 2 blocks the stop and sends stderr to Claude
    # as a continuation instruction
    msg = (
        "[WARNING] Context artifacts were changed but not evaluated.\n"
        "Run the following before committing:\n\n"
    )
    for item in unchecked:
        msg += f"  {item}\n"

    msg += (
        "\nEvaluate with the appropriate /dryrun-* skill, "
        "then note 'context evaluated' in the commit message."
    )

    print(msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
