"""Hook: Security guard.

Blocks access to sensitive files (.env, credentials) and destructive commands.

Event: PreToolUse (Edit|Write|Read|Bash)
"""

import json
import re
import sys

SENSITIVE_PATTERNS = (
    r"\.env$",
    r"\.env\.",
    r"credentials",
    r"secrets?\.",
    r"\.pem$",
    r"\.key$",
    r"id_rsa",
    r"id_ed25519",
)

# Files that match SENSITIVE_PATTERNS but are safe to access
SAFE_FILES = (
    r"\.env\.example$",
    r"\.env\.template$",
)

DANGEROUS_COMMANDS = (
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\.",
    r"rm\s+-rf\s+\*",
    r"rmdir\s+/s",
    r"del\s+/s\s+/q",
    r"format\s+[a-z]:",
)


def check_file_path(file_path):
    """Check if a file path points to a sensitive file."""
    normalized = file_path.replace("\\", "/").lower()
    # Allow explicitly safe files
    for safe in SAFE_FILES:
        if re.search(safe, normalized):
            return None
    for pattern in SENSITIVE_PATTERNS:
        if re.search(pattern, normalized):
            return pattern
    return None


def main():
    data = json.loads(sys.stdin.read())
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    if tool_name == "Bash":
        command = tool_input.get("command", "")
        for pattern in DANGEROUS_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                print(
                    f"BLOCKED: Destructive command detected. "
                    f"Pattern: {pattern}",
                    file=sys.stderr,
                )
                sys.exit(2)

        # Check if bash command accesses sensitive files
        # Skip if the command only references safe files
        has_safe = any(re.search(s, command, re.IGNORECASE) for s in SAFE_FILES)
        if not has_safe:
            for pattern in SENSITIVE_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    print(
                        f"BLOCKED: Command accesses sensitive file. "
                        f"Pattern: {pattern}",
                        file=sys.stderr,
                    )
                    sys.exit(2)
        return

    # Edit, Write, or Read — check file path
    file_path = tool_input.get("file_path", "")
    if file_path:
        match = check_file_path(file_path)
        if match:
            print(
                f"BLOCKED: Cannot access sensitive file '{file_path}'. "
                f"Matched pattern: {match}",
                file=sys.stderr,
            )
            sys.exit(2)


if __name__ == "__main__":
    main()
