"""Hook: Context change tracker.

Detects edits to context artifacts (CLAUDE.md, blueprints, plans) and
appends entries to .claude/eval.md so they can be validated before commit.

Event: PostToolUse (Edit|Write)
"""

import json
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
    display_path = normalized.split(PROJECT_DIR)[-1] if PROJECT_DIR and PROJECT_DIR in normalized else normalized

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entry = f"- [ ] `{display_path}` changed ({today}) - run {matched_skill}\n"

    eval_path = Path(EVAL_FILE)

    # Read existing entries to avoid duplicates
    existing = ""
    if eval_path.exists():
        existing = eval_path.read_text(encoding="utf-8")

    # Don't add duplicate entries for the same file
    if display_path in existing:
        return

    # Create or append
    if not eval_path.exists() or not existing.strip():
        content = f"# Context Evaluation Checklist\n\n{entry}"
    else:
        content = existing.rstrip("\n") + "\n" + entry

    eval_path.write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
