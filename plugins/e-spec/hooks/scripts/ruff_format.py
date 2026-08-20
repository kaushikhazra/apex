"""Hook: Ruff auto-format after Python edits.

Runs ruff check --fix and ruff format on edited Python files.

Event: PostToolUse (Edit|Write)
"""

import json
import subprocess
import sys
from pathlib import Path

# CONFIGURE: Command prefix for running ruff. Common options:
#   ["uv", "run", "ruff"]  — if using uv as the project runner
#   ["ruff"]                — if ruff is installed globally or in active venv
#   ["poetry", "run", "ruff"] — if using poetry
RUFF_CMD = ["ruff"]


def main():
    data = json.loads(sys.stdin.read())
    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path.endswith(".py"):
        return

    if not Path(file_path).is_file():
        return

    subprocess.run(
        [*RUFF_CMD, "check", "--fix", "--quiet", file_path],
        capture_output=True,
    )
    subprocess.run(
        [*RUFF_CMD, "format", "--quiet", file_path],
        capture_output=True,
    )


if __name__ == "__main__":
    main()
