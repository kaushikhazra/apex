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

## Coordination protocol — peer sessions, not sub-agents

Crosstalk connects independent Claude Code sessions, each with its own
attention and pacing — not a dispatcher/worker relationship where a
completion report is guaranteed. The receiving side may not even have a
live session running (no listener), in which case `send` itself fails loud
(`CROSSCHAT_SEND_FAIL`) rather than the message going unanswered silently —
but a *registered* destination that simply hasn't looked at its messages
yet looks identical to one that's ignoring you. Work like a teammate, not
a function call:

- **Acknowledge before working.** On receiving an actionable request, send
  a quick "on it" before diving into multi-step work — the sender has no
  other signal the message landed and something started.
- **Ping progress, don't go dark — on a concrete cadence.** Whoever is
  actively working self-reports **at least every ~10 minutes, or at each
  natural milestone, whichever comes first** — proactively, without being
  asked. This is on the WORKER's side, not the orchestrator's: the listening
  side should never need to poll or check in to find out if something is
  still alive — that's a burden on the wrong party. A "milestone" is
  judgment-dependent (a completed block, a resolved sub-problem, a passed
  verification) — when in doubt, report anyway; an extra update costs
  nothing, a silent 30-minute gap costs the other side's confidence that
  anything is still in flight.
- **Check the registry before assuming silence = ignoring.** `crosschat
  list` shows who's currently registered. If the other side isn't listed,
  there's no live listener right now — don't wait indefinitely on a dead
  channel, and don't read that as a snub.
- **Announce long quiet stretches up front.** Before a heavy build/render
  that will keep you from replying for a while, say so — it turns an
  unexplained silence into an expected one.

## Default posture: drive an agreed backlog, don't wait for per-item go-aheads

The most common failure mode isn't a dropped message — it's both sides going
quiet because each is waiting on the other. If a backlog of remaining work
has already been scoped and agreed (a list of blocks, primitives, fixes —
whatever was actually discussed and settled), the side executing it should
default to **continuing autonomously through that backlog**, self-verifying
each item the same way it verified the first one, and proactively pinging
progress — not stopping after each item to ask "what's next?" when the next
item was already agreed.

Reserve an actual stop-and-ask for genuinely new decisions: something needing
a category of fix/component that was never agreed on, a real ambiguity in
how to proceed, or anything destructive/irreversible. Don't reserve it for
"the next item on a list we already fixed together" — that's not a decision,
that's just execution, and treating it as one is what stalls the
conversation with neither side in flight.

The sender's job is symmetric: hand over the *whole* known backlog with
explicit standing authorization to drive it, not approve items one at a time
reactively — a one-at-a-time approval pattern is what forces the receiver
into a stop-after-every-item posture even when it would rather keep going.
