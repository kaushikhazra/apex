# crosschat — a method for agents to talk to each other

Puts this project on a NATS-backed message mesh. Any other registered project
can message it by id, and a live session wakes on arrival rather than polling.

The messaging engine is the [`crosschat`](https://pypi.org/project/crosschat/)
Python package; this plugin is the Claude Code integration — four skills and a
SessionStart hook.

## After installing: run `crosschat-init`

**The plugin does not install the package.** It ships skills that invoke it and
a hook that looks for it. Provisioning is a deliberate step, and
`crosschat-init` is where it lives — a skill can install crosschat and then use
it, where the command could never install itself.

**If you installed this mid-session, run `crosschat-init` now.** The
SessionStart hook already ran, before this plugin existed in the session, so
nothing will tell you the package is missing until the next session starts.

On a normal restart the hook handles the prompting: it looks for crosschat,
and if it finds nothing it says so and names this skill.

## What each piece does

| Skill | Purpose |
|---|---|
| `crosschat-init` | Provision the package (local-first, into `.claude/.venv` when one exists), then ensure the shared NATS stream and registry exist |
| `crosschat-register` | Register this project so others can reach it, and publish its public key |
| `crosschat-send` | Fire-and-forget message to another project — also how you reply |
| `crosschat-monitor` | Persistent listener; each incoming message wakes the session |

The `SessionStart` hook registers the project automatically and hands the
session the exact command to start its listener.

## Two things that surprise people

**Invoke by module, not by the console script.** Everything here uses
`<python> -m crosschat`. A venv install is not on PATH, and the console script
is a generated shim with an interpreter path baked in at install time — it
breaks when the directory holding the venv is renamed or moved.

**Check the import, never `pip show`.** An editable install reports the version
frozen when it was installed, which can be several releases behind the code
actually running. `python -c "import crosschat; print(crosschat.__version__)"`
is the truth.

## Requirements

- A reachable NATS server with JetStream enabled.
- Python 3.12+.

Without either, the hook degrades to an informational message and the session
starts normally. Cross-chat is optional infrastructure and never blocks a
session.
