"""Hook: Security guard.

Holds access to sensitive files (.env, credentials) and destructive commands.

Event: PreToolUse (Edit|Write|Read|Bash|PowerShell)

Shell commands are deny-then-ack (second-brain's command guard design): the
first try is denied with the reason and an ack code, the same command re-run
with `# guard-ack:<code>` appended goes through. File tools (Read/Edit/Write)
have no command to append a comment to, so a sensitive path stays a hard block.

Both shells are inspected. A guard that covers only one of them is not a
guard — on 2026-08-04 the bash form of a destructive command was correctly
blocked here and the PowerShell form of the same command walked past and
destroyed a repository's git history.
"""

import hashlib
import json
import re
import sys

# Tools whose input is a shell command rather than a file path.
COMMAND_TOOLS = ("Bash", "PowerShell")

# Deny-then-ack: a held shell command is denied once with a code that is the
# hash of its exact text; re-running it with `# guard-ack:<code>` appended lets
# it through to the owner's own permission rules. `#` starts a comment in both
# shells, so the ack changes nothing that runs. A fixed word would get
# pre-written onto every command and the guard would vanish.
ACK = re.compile(r"\s*#\s*guard-ack:(?P<code>[0-9a-fA-F]+)\s*\Z")
ACK_LEN = 6

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


def split_ack(command):
    """(command without its trailing ack comment, the code the ack carried or None)."""
    m = ACK.search(command)
    if not m:
        return command.strip(), None
    return command[: m.start()].strip(), m.group("code").lower()


def ack_code(command):
    """Short hash of the exact command text: an ack cannot be written before the
    command is known, and one command's ack means nothing on another."""
    return hashlib.sha256(command.encode("utf-8", "replace")).hexdigest()[:ACK_LEN]


def command_findings(command):
    """Why a shell command is held, one sentence per reason; empty when it is clean."""
    findings = []
    for pattern in DANGEROUS_COMMANDS:
        if re.search(pattern, command, re.IGNORECASE):
            findings.append(f"Destructive command detected (pattern: {pattern}).")
            break

    relative_git = find_relative_git_target(command)
    if relative_git:
        findings.append(
            f"Destructive command targets '{relative_git}' by relative path. It "
            f"resolves against this process's current directory, not the "
            f"directory you think you are in. Use an absolute path if this is "
            f"really what you meant."
        )

    # Skip the sensitive-file check if the command only references safe files
    has_safe = any(re.search(s, command, re.IGNORECASE) for s in SAFE_FILES)
    if not has_safe:
        for pattern in SENSITIVE_PATTERNS:
            if re.search(pattern, command, re.IGNORECASE):
                findings.append(
                    f"Command accesses a sensitive file (pattern: {pattern})."
                )
                break
    return findings


def deny(reason):
    """Deny, never allow: allow would skip the owner's own permission rules."""
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )


def main():
    data = json.loads(sys.stdin.read())
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})

    # Both shells carry the command on the same `command` field.
    if tool_name in COMMAND_TOOLS:
        command, acked = split_ack(tool_input.get("command", ""))
        findings = command_findings(command)
        if not findings:
            return  # nothing suspected: no output, the normal permission flow decides
        code = ack_code(command)
        if acked == code:
            return  # checked and re-run with the matching ack: the owner's rules decide
        deny(
            "BLOCKED: "
            + " ".join(findings)
            + f" If you checked and still want it, re-run the same command with"
            f" ` # guard-ack:{code}` appended (on a new last line if it ends in a heredoc)."
        )
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
