"""Hook: Cross-module import guard.

Blocks direct imports between isolated modules.
All cross-module communication must go through the project's IPC mechanism.
The shared package is the only one all modules may import.

Event: PreToolUse (Edit|Write)
"""

import json
import re
import sys

# CONFIGURE: List the isolated module directory names in your project.
# These modules must not import from each other directly.
MODULES = ("agent", "memory", "gateway", "event")

# CONFIGURE: The source root path segment that contains the modules above.
# Example: "src/sb/" means modules live at src/sb/agent/, src/sb/memory/, etc.
SRC_ROOT = "src/sb/"

# CONFIGURE: The top-level import package that maps to SRC_ROOT.
# Used to detect import statements like "from <PKG>.agent import ..."
IMPORT_PKG = "sb"

# CONFIGURE: Describe the expected IPC mechanism in the block message.
IPC_MECHANISM = "the project's IPC layer (e.g., message bus, events)"


def main():
    data = json.loads(sys.stdin.read())
    file_path = data.get("tool_input", {}).get("file_path", "")

    if not file_path.endswith(".py"):
        return

    # Normalize path separators
    file_path = file_path.replace("\\", "/")

    if SRC_ROOT not in file_path:
        return

    # Determine which module this file belongs to
    current_module = None
    for mod in MODULES:
        if f"{SRC_ROOT}{mod}/" in file_path:
            current_module = mod
            break

    if current_module is None:
        return

    # Get the content being written/edited
    tool_input = data.get("tool_input", {})
    content = tool_input.get("new_string", "") or tool_input.get("content", "")

    if not content:
        return

    # Check for direct imports from other modules
    for mod in MODULES:
        if mod == current_module:
            continue
        pattern = rf"(from\s+{re.escape(IMPORT_PKG)}\.{mod}|import\s+{re.escape(IMPORT_PKG)}\.{mod}|from\s+\.\.{mod})"
        if re.search(pattern, content):
            print(
                f"BLOCKED: {current_module}/ cannot import from {mod}/. "
                f"Use {IPC_MECHANISM} for cross-module communication. "
                "Only shared/ may be imported across modules.",
                file=sys.stderr,
            )
            sys.exit(2)


if __name__ == "__main__":
    main()
