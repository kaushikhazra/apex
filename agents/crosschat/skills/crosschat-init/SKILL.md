---
name: crosschat-init
description: RUN THIS FIRST after the crosschat plugin is installed — including when it was installed mid-session, where no SessionStart hook has fired and nothing else will prompt you. Provisions the crosschat package for this project (local-first, into .claude/.venv when one exists), then sets up the shared NATS infrastructure. Also run it whenever cross-chat reports that crosschat is not installed or not importable. Safe to re-run: both halves are idempotent.
allowed-tools: Bash
---

# Cross-chat — Provision and Infra Setup

## When to run this — read first

**Immediately after this plugin is installed.** Nothing else will provision the
package: the plugin ships skills and a hook, and none of them install anything.

**Especially when the plugin was installed mid-session.** The SessionStart hook
that would otherwise tell you crosschat is missing has already run — it fired
before this plugin existed in the session, so it will not fire again until the
next session starts. Between now and then, nothing prompts you. **This skill is
the only thing standing in that gap, and the session has to reach for it
unprompted.** If the plugin appeared partway through this conversation, run
this now rather than waiting.

Also run it when anything reports that crosschat is not installed, not
importable, or not on PATH.

Both rounds are idempotent — re-running when everything is already in place
costs one import check and one no-op call.

---

Two rounds. **Round 0 installs the package** for this project; **Round 1**
ensures the shared NATS resources exist. Round 1 cannot run without Round 0,
because it is invoked *through* the package it is setting up.

That ordering is the whole reason provisioning lives in this skill rather than
inside the CLI: a skill is instructions the session executes, so it can install
crosschat and then use it. The command could never install itself.

---

## Round 0 — Provision crosschat

**Local first.** A project with its own `.claude/.venv` gets crosschat inside
it, isolated from every other project on the machine. Only a project without
one falls back to the global interpreter.

Let **`PROJECT_DIR`** be this project's root.

### 1. Pick the interpreter

Check in this order and stop at the first hit:

1. `PROJECT_DIR/.claude/.venv/Scripts/python.exe` (Windows)
2. `PROJECT_DIR/.claude/.venv/bin/python` (POSIX)
3. Whatever `python` resolves to on PATH — **global fallback**

If 1 or 2 exists, that is the interpreter. Do not create a venv here: this
skill provisions a package, it does not decide a project's environment layout.
If a project wants isolation and has no venv, create one first, then re-run.

### 2. Is it already there?

```
<python> -c "import crosschat, sys; print(crosschat.__version__)"
```

Exit 0 means installed — **skip to Round 1**. Report the version you saw.

**Check the import, never `pip show`.** For an editable install `pip show`
reports the version frozen at install time, which can be many releases behind
the code actually running. The import is the truth.

### 3. Install

```
<python> -m pip install crosschat
```

To upgrade an existing install, `-m pip install --upgrade crosschat`. Plain
`pip install` does nothing when any version is already present — it checks
presence, not currency.

**Do not upgrade an editable install.** If step 2 shows crosschat importing
from a source checkout rather than site-packages, it is deliberately linked to
that checkout and `--upgrade` would silently replace it with a PyPI copy. Say
so and stop; that is the user's call, not yours.

### 4. Invoke by module, never by the console script

Everywhere after this — here, `crosschat-register`, `crosschat-send`,
`crosschat-monitor` — use:

```
<python> -m crosschat <command> ...
```

**Not** the bare `crosschat` command. Two reasons, and the second is the one
that bites. A venv install is not on PATH at all, so the bare command finds
nothing or, worse, finds a *different* project's crosschat. And the console
script is a generated shim with the interpreter's absolute path baked in at
install time: rename or move the directory holding that venv and every shim
inside it points at a python that no longer exists. Resolving the interpreter
at the moment of use stores no path and survives the move.

Record the interpreter path you resolved and reuse it for the rest of the
session.

---

## Round 1 — Shared NATS infra

```
<python> -m crosschat init [nats_url]
```

Creates the `CROSSCHAT` JetStream stream (subjects `crosschat.>`, 1-day
retention) and the `crosschat-registry` KV bucket (5-minute entry TTL).

Prints `CROSSCHAT_INIT_OK` on success, or `NATS_CONNECT_FAIL <error>` if NATS
is unreachable. Idempotent — creating a stream or bucket that already exists is
treated as success.

**Round 1 is per NATS deployment, not per project.** The first project to run
it creates the shared resources; every later run is a no-op. Round 0, by
contrast, is per project — each one needs its own installed copy.

---

## Scope

This skill installs the package and ensures the shared infra exists. It does
**not** register this project and does **not** start a listener — see
`crosschat-register`, which the plugin's SessionStart hook invokes for you and
which resolves the same interpreter the same way.
