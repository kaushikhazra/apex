---
name: crosschat-register
description: Register this project in the cross-chat registry and start its persistent listener. Fire from the project's session-start hook whenever cross-chat should be available for this session. Requires crosschat-init to have been run at least once against this NATS deployment.
allowed-tools: Bash
---

# Cross-chat — Project Registration

Registers this project so other sessions can discover and message it, then
starts its listener (`crosschat-monitor`) for the rest of the session. See
`.claude/specs/session-cross-chat/design.md`.

## Mechanism

```
crosschat register <project_path> [nats_url]
```

`crosschat` is a console script from the `crosschat` package
(`src/crosschat/cli.py`) — this skill documents invoking it, not a
separate implementation. `project_id` is derived from `project_path`
(slugified directory name) — the single derivation point; no other
cross-chat skill re-derives it. Prints `CROSSCHAT_REGISTERED <project_id>`
on success.

If `crosschat-init` hasn't been run yet against this NATS deployment, prints
`CROSSCHAT_INIT_REQUIRED <error>` and does **not** create the infra itself —
run `/crosschat-init` first, then retry.

## The cycle

1. **Register** — run the command above once, at session start.
2. **Start the listener** — launch `crosschat monitor <project_id>
   [nats_url]` as a **background** process, watched via the Monitor tool
   (each stdout line becomes a notification). Start it exactly once per
   session — it runs for the session's full duration, never relaunched
   between messages. See `crosschat-monitor`'s SKILL.md.
3. **Send / reply** — use `crosschat-send` for both an initial message and a
   reply (same call, only the destination `project_id` differs).

## Listener lifecycle

A session's cross-chat listener is on for its entire session duration —
started here, kept alive by `crosschat-monitor`'s own loop, and stopped only
when the session ends. Its registry entry then falls out of
`crosschat-registry` within 5 minutes (bucket TTL) with no manual cleanup
step.
