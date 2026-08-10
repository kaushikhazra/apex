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


def resolve_command(project_dir: str) -> list[str] | None:
    """How to invoke crosschat here, or None if it is not installed.

    Local first: a project that provisioned crosschat into its own
    ``.claude/.venv`` is not on PATH, and checking PATH alone would report it
    missing while it sits right there. Falls back to a global install.

    Prefers ``python -m crosschat`` over the console script deliberately. The
    script is a shim with an interpreter path baked in at install time, so it
    breaks the moment the directory is renamed or moved; resolving the
    interpreter now and running the module through it stores no path at all.
    """
    for candidate in (
        os.path.join(project_dir, ".claude", ".venv", "Scripts", "python.exe"),
        os.path.join(project_dir, ".claude", ".venv", "bin", "python"),
    ):
        if os.path.exists(candidate):
            return [candidate, "-m", "crosschat"]

    for name in ("python", "python3"):
        found = shutil.which(name)
        if found and _has_crosschat(found):
            return [found, "-m", "crosschat"]

    # Last resort: a console script on PATH, for installs that predate this.
    if shutil.which("crosschat"):
        return ["crosschat"]
    return None


def _has_crosschat(python_exe: str) -> bool:
    try:
        return (
            subprocess.run(
                [python_exe, "-c", "import crosschat"],
                capture_output=True,
                timeout=TIMEOUT_SECONDS,
            ).returncode
            == 0
        )
    except Exception:
        return False


def main() -> None:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()

    command = resolve_command(project_dir)
    if command is None:
        emit(
            "Cross-chat is not available in this session: `crosschat` is not "
            "installed in this project's .claude/.venv, and not importable by any "
            "python on PATH. Run the crosschat-init skill to provision it if you "
            "want this project reachable by other sessions. No action needed "
            "otherwise."
        )
        return

    try:
        result = subprocess.run(
            [*command, "register", project_dir, NATS_URL],
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

    # Hand back the exact invocation that worked here. A bare `crosschat` would
    # be wrong for a project whose install lives in its own .claude/.venv, and
    # the session has no way to know that.
    monitor_command = " ".join(f'"{part}"' if " " in part else part for part in command)

    if project_id:
        emit(
            f"Cross-chat registered as project_id={project_id}. Launch "
            f"`{monitor_command} monitor {project_id} {NATS_URL}` as a background "
            "process and watch it with the Monitor tool for the rest of this "
            "session — each CROSSCHAT_MESSAGE line is one incoming message. Use "
            "that command verbatim; this project's crosschat may not be on PATH. "
            "Start it exactly once; it runs for the whole session and is never "
            "relaunched between messages. See the crosschat-monitor skill."
        )
    else:
        emit(
            f"Cross-chat registration did not complete: {output or 'no output'}. "
            f"If this says init is required, run `{monitor_command} init` once "
            "against this NATS deployment, then restart the session. Session "
            "continues without cross-chat."
        )


if __name__ == "__main__":
    main()
