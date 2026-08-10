---
name: crosschat-init
description: One-time, idempotent setup of the shared cross-chat NATS infrastructure (CROSSCHAT JetStream stream + crosschat-registry KV bucket). Not tied to any project — run once, from any Claude Code session, before any project uses crosschat-register/-send/-monitor.
allowed-tools: Bash
---

# Cross-chat — Infra Setup

Ensures the shared NATS resources that session cross-chat depends on exist:
the `CROSSCHAT` JetStream stream (subjects `project.>`, 1-day retention) and
the `crosschat-registry` KV bucket (5-minute entry TTL). See
`.claude/specs/session-cross-chat/design.md` for the full architecture.

## When to run this

Once, ever, per NATS deployment — not per project, not per session. If the
infra already exists, running this again is a safe no-op. `crosschat-register`
depends on this having been run at least once; it will fail with a clear
error naming this skill if the infra is missing.

## Mechanism

```
crosschat init [nats_url]
```

`crosschat` is a console script from the `crosschat` package
(`src/crosschat/cli.py`, wrapping `src/crosschat/core.py`) — this
skill is documentation for invoking it, not a separate implementation.
Prints `CROSSCHAT_INIT_OK` on success, or `NATS_CONNECT_FAIL <error>` if NATS
is unreachable. Idempotent — creating a stream/bucket that already exists is
treated as success, not an error.

## Scope

This skill does not register any project and does not start any listener —
it only ensures the shared infra exists. See `crosschat-register` for
per-project registration.
