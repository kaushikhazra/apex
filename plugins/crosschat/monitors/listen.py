"""Plugin monitor -- this session's crosschat listener, for the whole session.

Claude Code starts this once per session from `monitors/monitors.json` and keeps
it running until the session ends. Every stdout line becomes a notification, so
each `CROSSCHAT_MESSAGE <json>` wakes the session. This replaces the listener
the session used to start itself with the Monitor tool, which Claude Code caps
at 30 minutes and which then had to be re-armed on every expiry.

Self-sufficient on purpose: it registers before it listens, so it never depends
on the SessionStart hook having finished first. Registration is idempotent.

A monitor gets no CLAUDE_PROJECT_DIR in its environment; it runs in the
session's working directory, which is the project directory.

Never loops on failure. A missing `crosschat` or a failed registration prints
one line and exits, so the session hears about it once rather than never.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "hooks"))
from register import NATS_URL, TIMEOUT_SECONDS, resolve_command  # noqa: E402


def main() -> int:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    command = resolve_command(project_dir)
    if command is None:
        print(
            "CROSSCHAT_UNAVAILABLE crosschat is not installed for this project",
            flush=True,
        )
        return 0

    try:
        result = subprocess.run(
            [*command, "register", project_dir, NATS_URL],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except Exception as e:  # NATS down, crash: say so once and stop
        print(f"CROSSCHAT_UNAVAILABLE registration failed: {e}", flush=True)
        return 0

    output = (result.stdout or "") + (result.stderr or "")
    project_id = next(
        (
            l.split(" ", 1)[1].strip()
            for l in output.splitlines()
            if l.startswith("CROSSCHAT_REGISTERED ")
        ),
        "",
    )
    if not project_id:
        print(
            f"CROSSCHAT_UNAVAILABLE registration did not complete: {output.strip() or 'no output'}",
            flush=True,
        )
        return 0

    # Inherit stdout: every line `crosschat monitor` prints reaches the session as-is.
    return subprocess.run([*command, "monitor", project_id, NATS_URL]).returncode


if __name__ == "__main__":
    sys.exit(main())
