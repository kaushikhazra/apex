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
    be the verb's **first non-flag argument** — its target, the way a shell
    would parse it. Both constraints were earned: a whole-command scan
    blocks any text that merely mentions a verb and .git together, which
    includes a `git commit` or a status message describing this very guard.
    That is sanctioned work, and a guard that blocks sanctioned work gets
    switched off, which is the failure mode this whole change exists to fix.

    Known gap: a .git in second-or-later target position is not caught here.
    Distinguishing that from prose is not possible on bare words. The
    PowerShell form (`Remove-Item build .git -Recurse`) is still caught by
    DANGEROUS_COMMANDS via the verb-plus-flag pattern; the bash form
    (`rm -rf build .git`) is caught by nothing, because the `rm -rf`
    patterns require the target immediately after the flag. Stated rather
    than papered over — a false coverage claim inside a guard is the same
    defect as a guard that does not fire.
    """
    for line in command.splitlines():
        # Every verb on the line, not just the first — otherwise an earlier
        # incidental match shadows the real command behind it.
        for verb in DESTRUCTIVE_VERB.finditer(line):
            target = _relative_git_argument(line[verb.end() :])
            if target:
                return target
    return None


def _relative_git_argument(tail):
    """Return the verb's first non-flag argument if it is a relative .git."""
    for raw in tail.split():
        token = raw.strip("\"'`(){},;|")
        if not token:
            continue
        # Flags are not the target; keep looking past them.
        if token.startswith("-") or token.startswith("/"):
            continue
        # First real argument. It is the target or nothing is.
        if GIT_REFERENCE.search(token) and not ANCHORED_PATH.match(token):
            return token
        break
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
