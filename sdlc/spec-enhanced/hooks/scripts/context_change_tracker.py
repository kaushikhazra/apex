"""Hook: Context change tracker.

Detects edits to context artifacts (CLAUDE.md, blueprints, plans) and
appends entries to .claude/eval.md so they can be validated before commit.

Event: PostToolUse (Edit|Write)
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Context artifacts and their corresponding eval skills
CONTEXT_ARTIFACTS = {
    r"CLAUDE\.md$": "/dryrun-context",
    r"\.claude/blueprints/": "/dryrun-blueprint",
    r"\.claude/plans/": "/dryrun-plan",
}

EVAL_FILE = ".claude/eval.md"


def resolve_eval_path(data):
    """Anchor eval.md on the session's project, never on the process cwd.

    The session owns the review, so the anchor is the project directory —
    not the edited file's own directory, which would send an edit of the
    user-global CLAUDE.md to ~/.claude/.claude/eval.md.
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    return Path(project_dir) / EVAL_FILE


def has_pending_review(existing, display_path):
    """True if an unchecked entry for exactly this path is already logged.

    The invariant is *is a review already pending for this file* — not *has
    this file ever been seen*, which silently swallows every edit after the
    first, and not *has it been seen today*, which swallows the second edit
    of any given day.
    """
    pattern = rf"^- \[ \] `{re.escape(display_path)}` "
    return any(re.match(pattern, line) for line in existing.splitlines())


def main():
    data = json.loads(sys.stdin.read())
    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path:
        return

    normalized = file_path.replace("\\", "/")

    # Check if the edited file is a context artifact
    matched_skill = None
    for pattern, skill in CONTEXT_ARTIFACTS.items():
        if re.search(pattern, normalized):
            matched_skill = skill
            break

    if matched_skill is None:
        return

    # CONFIGURE: Replace with your project's root directory name to strip
    # absolute path prefixes for cleaner display in eval.md entries.
    PROJECT_DIR = ""  # e.g., "my-project/"
    display_path = (
        normalized.split(PROJECT_DIR)[-1]
        if PROJECT_DIR and PROJECT_DIR in normalized
        else normalized
    )

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"- [ ] `{display_path}` changed ({today}) - run {matched_skill}\n"

    eval_path = resolve_eval_path(data)

    # Read existing entries to avoid duplicates
    existing = ""
    if eval_path.exists():
        existing = eval_path.read_text(encoding="utf-8")

    # Don't stack a second pending review on a file already awaiting one
    if has_pending_review(existing, display_path):
        return

    # Create or append
    if not existing.strip():
        content = f"# Context Evaluation Checklist\n\n{entry}"
    else:
        content = existing.rstrip("\n") + "\n" + entry

    eval_path.parent.mkdir(parents=True, exist_ok=True)
    eval_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
