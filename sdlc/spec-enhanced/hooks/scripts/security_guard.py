"""Hook: Security guard.

Blocks access to sensitive files (.env, credentials) and destructive commands.

Event: PreToolUse (Edit|Write|Read|Bash|PowerShell)

Both shells are inspected. A guard that covers only one of them is not a
guard — on 2026-08-04 the bash form of a destructive command was correctly
blocked here and the PowerShell form of the same command walked past and
destroyed a repository's git history.
"""

import json
import re
import sys

# Tools whose input is a shell command rather than a file path.
COMMAND_TOOLS = ("Bash", "PowerShell")

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

# PowerShell's Remove-Item and its aliases. PowerShell accepts any
# unambiguous parameter prefix, so -Recurse/-Force are matched by prefix too.
REMOVE_VERB = (
    r"(?:Remove-Item|Remove-ItemProperty|\bri\b|\brd\b|\brmdir\b|\bdel\b|\berase\b)"
)
RECURSE_OR_FORCE = r"-(?:recurse|recurs|recur|recu|rec|r|force|forc|for|fo|f)\b"

DANGEROUS_COMMANDS = (
    r"rm\s+-rf\s+/",
    r"rm\s+-rf\s+\.",
    r"rm\s+-rf\s+\*",
    r"rmdir\s+/s",
    r"del\s+/s\s+/q",
    r"format\s+[a-z]:",
    # Remove-Item with -Recurse and/or -Force, target-independent, whether
    # the flags come before or after the target — a PowerShell flag always
    # follows its verb, so one forward pattern covers both orders.
    # [^\r\n]* keeps a match inside a single line.
    REMOVE_VERB + r"[^\r\n]*?\s" + RECURSE_OR_FORCE,
    r"\brd\s+/s",
    r"\bdel\s+/s",
)

# Verbs that destroy content, for the narrowly scoped relative-path guard
# below. No flag is required here — `del .git` is as fatal as
# `Remove-Item .git -Recurse -Force`.
DESTRUCTIVE_VERB = re.compile(
    r"(?:Remove-Item|Remove-ItemProperty|Clear-Content|\bri\b|\brd\b|\brmdir\b"
    r"|\bdel\b|\berase\b|\brm\b)",
    re.IGNORECASE,
)

# A high-value target whose destruction is unrecoverable. Deliberately just
# `.git` — a blanket "block all relative-path destructive commands" rule
# fires on sanctioned routine work and gets switched off, and a guard that
# gets disabled protects nothing.
GIT_REFERENCE = re.compile(r"\.git\b", re.IGNORECASE)

# A path is anchored if it starts with a drive letter, a separator, or ~.
# Anything else resolves against the process's current directory — which is
# the failure the 2026-08-04 incident went through.
ANCHORED_PATH = re.compile(r"(?:[A-Za-z]:|[/\\]|~)")

# Characters that end a shell token.
TOKEN_BOUNDARY = " \t\"'`;|,()={}"


def find_relative_git_target(command):
    """Return a relative path token referring to .git, or None.

    Two facets are detected independently and blocked on their conjunction:
    a destructive verb, and a .git reference that is not anchored. Matching
    the two as one order-coupled regex is how a guard ends up looking armed
    without being armed — real commands put the flags before the target as
    often as after it.

    The conjunction is scoped to a single line, and the .git reference must
    follow the verb. A statement lives on one line, so that is where a verb
    and its target actually meet; scanning the whole command instead makes
    the guard fire on any text that merely mentions both — a `git commit`
    whose message discusses Remove-Item and .git, for one, which is
    sanctioned work, and a guard that blocks sanctioned work gets disabled.
    """
    for line in command.splitlines():
        verb = DESTRUCTIVE_VERB.search(line)
        if not verb:
            continue

        for match in GIT_REFERENCE.finditer(line, verb.end()):
            start = match.start()
            while start > 0 and line[start - 1] not in TOKEN_BOUNDARY:
                start -= 1
            token = line[start : match.end()]
            if ANCHORED_PATH.match(token):
                continue
            return token
    return None


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

    # Both shells carry the command on the same `command` field.
    if tool_name in COMMAND_TOOLS:
        command = tool_input.get("command", "")
        for pattern in DANGEROUS_COMMANDS:
            if re.search(pattern, command, re.IGNORECASE):
                print(
                    f"BLOCKED: Destructive command detected. Pattern: {pattern}",
                    file=sys.stderr,
                )
                sys.exit(2)

        relative_git = find_relative_git_target(command)
        if relative_git:
            print(
                f"BLOCKED: Destructive command targets '{relative_git}' by "
                f"relative path. It resolves against this process's current "
                f"directory, not the directory you think you are in. Use an "
                f"absolute path if this is really what you meant.",
                file=sys.stderr,
            )
            sys.exit(2)

        # Check if the command accesses sensitive files
        # Skip if the command only references safe files
        has_safe = any(re.search(s, command, re.IGNORECASE) for s in SAFE_FILES)
        if not has_safe:
            for pattern in SENSITIVE_PATTERNS:
                if re.search(pattern, command, re.IGNORECASE):
                    print(
                        f"BLOCKED: Command accesses sensitive file. Pattern: {pattern}",
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
