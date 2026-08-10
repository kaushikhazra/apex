---
name: crosschat-send
description: Send a fire-and-forget message to another project's cross-chat channel — no blocking wait, no timeout. Use for both an initial message and a reply (pass the received source_project_id back as the destination).
allowed-tools: Bash
---

# Cross-chat — Send

Publishes a message to another project's channel and returns immediately.
There is no request/reply mechanism here and no client-side timeout anywhere
— see `.claude/specs/session-cross-chat/design.md` ("Messaging model —
fire-and-forget, symmetric") for why.

## Mechanism

```
crosschat send <source_project_id> <dest_project_id> <text> [nats_url]
```

`crosschat` is a console script from the `crosschat` package
(`src/crosschat/cli.py`) — this skill documents invoking it, not a
separate implementation. Prints `CROSSCHAT_SENT <dest_project_id>` on
success. If the destination project has no live `crosschat-registry` entry
(not registered, or its session ended and the entry expired), prints
`CROSSCHAT_SEND_FAIL <error>` and does not publish into a channel nobody is
listening on.

## Replying

There is no separate reply mechanism. A session that received a message with
`source_project_id` X replies by calling this same command with
`dest_project_id` = X:

```
crosschat send <my_project_id> <X> "<reply text>" [nats_url]
```

A reply composed minutes after the original message was received is not
lost — there is no timeout window during which a late reply could be
silently dropped (this closes what would otherwise be the most common
failure mode for human-paced, asynchronous session-to-session exchanges).
