"""SessionStart hook — register this project with crosschat.

Emits a SessionStart `additionalContext` block telling the live session what
its project_id is and how to start the listener. Starting the listener itself
needs Claude-side action (the Monitor tool), which a hook cannot perform — so
the hook does the part it can do deterministically and hands over the rest.

Deliberately a Python script rather than an inline shell one-liner:

* No `cd`. The project directory is passed straight to `crosschat register` as
  an argument. An inline `cd "$DIR"; <command>` continues to the next command
  when the `cd` fails, and any relative path then resolves against whatever the
  session's working directory happened to be. That class of bug is not worth
  re-opening for the sake of fitting on one line.
* Never fails the session. A missing `crosschat`, an unreachable NATS server or
  an unexpected crash all become an informational context block, never a
  non-zero exit that blocks startup. Cross-chat is optional infrastructure; a
  session must start fine without it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess

NATS_URL = os.environ.get("CROSSCHAT_NATS_URL", "nats://localhost:4222")
TIMEOUT_SECONDS = 15


def emit(message: str) -> None:
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "SessionStart",
                    "additionalContext": message,
                }
            }
        )
    )


def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    if shutil.which("crosschat") is None:
        emit(
            "Cross-chat is not available in this session: the `crosschat` command "
            "is not on PATH. Install it with `pip install crosschat` if you want "
            "this project reachable by other sessions. No action needed otherwise."
        )
        return

    try:
        result = subprocess.run(
            ["crosschat", "register", project_dir, NATS_URL],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
        output = (result.stdout or "").strip() or (result.stderr or "").strip()
    except subprocess.TimeoutExpired:
        emit(
            f"Cross-chat registration timed out after {TIMEOUT_SECONDS}s against "
            f"{NATS_URL}. The NATS server may be down. Session continues without "
            "cross-chat."
        )
        return
    except Exception as e:  # never break session startup over optional infra
        emit(f"Cross-chat registration could not run ({e}). Session continues.")
        return

    project_id = ""
    for line in output.splitlines():
        if line.startswith("CROSSCHAT_REGISTERED "):
            project_id = line[len("CROSSCHAT_REGISTERED ") :].strip()
            break

    if project_id:
        emit(
            f"Cross-chat registered as project_id={project_id}. Launch "
            f"`crosschat monitor {project_id} {NATS_URL}` as a background process "
            "and watch it with the Monitor tool for the rest of this session — "
            "each CROSSCHAT_MESSAGE line is one incoming message. Start it exactly "
            "once; it runs for the whole session and is never relaunched between "
            "messages. See the crosschat-monitor skill."
        )
    else:
        emit(
            f"Cross-chat registration did not complete: {output or 'no output'}. "
            "If this says init is required, run `crosschat init` once against this "
            "NATS deployment, then restart the session. Session continues without "
            "cross-chat."
        )


if __name__ == "__main__":
    main()
