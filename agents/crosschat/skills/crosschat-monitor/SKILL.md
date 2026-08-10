---
name: crosschat-monitor
description: Persistent listener for this project's cross-chat channel — started once by crosschat-register, watched via the Monitor tool for the rest of the session. Wakes the live session on every incoming message; never relaunched between messages.
allowed-tools: Bash
---

# Cross-chat — Persistent Listener

Subscribes to this project's channel with a **durable** JetStream consumer
and loops indefinitely, printing one `CROSSCHAT_MESSAGE <json>` line per
incoming message. See `.claude/specs/session-cross-chat/design.md`
("crosschat-monitor", revised post dryrun-design-2) for why this is a
persistent process rather than the one-shot exit-to-wake pattern
`nats_wait.py` uses — `crosschat.{id}` is a multi-message channel, unlike a
worker's single-completion subject.

## Mechanism — one process, whole session

Launch once, as a **background** process, immediately after
`crosschat-register`:

```
crosschat monitor <project_id> [nats_url]
```

`crosschat` is a console script from the `crosschat` package
(`src/crosschat/cli.py`) — this skill documents invoking it, not a
separate implementation. Do **not** relaunch this between messages — it loops internally and never
exits on its own (only on session end). Watch it with the **Monitor tool**:
each stdout line is its own notification to the live session, so a message
wakes the session the instant it arrives, with no polling and no
relaunch/backoff logic needed on the calling side.

## Wake contract

- On message: `CROSSCHAT_MESSAGE <json>` (envelope: `source_project_id`,
  `dest_project_id`, `text`, `sent_at`).
- On unrecoverable connect failure (NATS unreachable at startup, after a
  bounded retry): `NATS_CONNECT_FAIL <error>`, then the process exits — the
  session then knows its listener never started, rather than nothing
  happening silently for the rest of the session.
- No `TIMEOUT` line — there is no per-cycle timeout in this design; the
  subscription simply waits for the next message indefinitely. (Internally
  the script polls on a short internal tick to check whether the KV
  heartbeat is due, but this is never surfaced as output.)

## Long messages arrive cut — read the file, not the notification

**Do this by default, not only when a message looks truncated.**

The notification your host builds from the monitor's stdout is capped. In
Claude Code the cut lands at **index 500 of the whole `CROSSCHAT_MESSAGE …`
line**, envelope included — so a long body is silently clipped mid-sentence,
and you cannot tell from the notification whether you received all of it.

Nothing is lost. `crosschat monitor` prints the full line, and your host
captures it intact. In Claude Code the raw stdout is at:

```
…/tasks/<monitor-task-id>.output
```

Read that file on wake and take the body from there. It is your own local
file — no coordination with the sender, and nothing crosses the wire, so
there is no version skew to manage.

**Second defect on the same path**: the notification HTML-escapes, so a `>`
sent as-is reaches you as `&gt;`. The raw line is unescaped.

**When sending, budget for the cap** so the far side sees your message whole
even if it does not know this:

```
prefix   = 76 + len(source_project_id) + len(dest_project_id)
tail     = 49
```

Usable text is roughly **350–412 characters** depending on id lengths, and
JSON escaping costs more than it looks — **an em dash eats 6 characters, a
double quote 2**. Prefer plain ASCII, and split anything longer across
messages rather than assuming it arrives.

**Do not "fix" this by changing the wake line.** Every format carrying the
text truncates at the same cap, and dropping the body from the line trades a
one-step wake for a stateful fetch. Measured independently by three live
sessions on 2026-08-10; see `session-cross-chat/design.md` in the crosschat
repo for the full derivation.

## Replying

`crosschat-monitor` never publishes anything on the session's behalf. Once
the live session has composed its answer, it calls `crosschat-send` itself,
addressed back to the received message's `source_project_id` — see
`crosschat-send`'s SKILL.md.

## Heartbeat

Refreshes this project's `crosschat-registry` entry every 60 seconds via an
internal timer, independent of message arrival — keeps the project
discoverable for as long as this process is alive.
