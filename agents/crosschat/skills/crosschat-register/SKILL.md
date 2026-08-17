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
crosschat register <project_path> [nats_url] [--id <project_id>]
```

`crosschat` is a console script from the `crosschat` package (`pip install
crosschat`) — this skill documents invoking it, not a separate
implementation. Prints `CROSSCHAT_REGISTERED <project_id>` on success.

**The id is the address.** It is resolved here and nowhere else, in this
order:

1. `--id <project_id>` — explicit, wins over everything.
2. `CROSSCHAT_PROJECT_ID` in the environment.
3. The slugified project directory name (`C:\Projects\velhari` → `velhari`).

Prefer an explicit id for anything long-lived: the folder fallback ties a
project's identity to its location, so renaming the directory renames the
project and two projects cannot share a directory name. The environment
variable is how an unattended SessionStart hook registers a project under a
chosen id without the hook itself knowing it — set it in that project's own
`.claude/settings.json` `env` block.

Whatever the source, the id is normalized the same way (lowercased,
non-alphanumeric runs collapsed to hyphens) because it has to be a legal NATS
subject token. No other cross-chat skill re-derives it.

If `crosschat-init` hasn't been run yet against this NATS deployment, prints
`CROSSCHAT_INIT_REQUIRED <error>` and does **not** create the infra itself —
run `/crosschat-init` first, then retry.

## Registering also publishes your public key

From crosschat 0.3.0, `register` creates this project's Ed25519 keypair on
first use and writes the **public** half into its registry entry. That is how
other projects verify your messages: they read your key from the registry and
check the signature on what you sent, instead of trusting the
`source_project_id` field you filled in yourself.

The private key stays at `~/.crosschat/keys/<project_id>.key` (override with
`CROSSCHAT_KEY_DIR`). It is never published and never leaves the machine.

**If you are upgrading an existing project, re-run `register` once.** The key
is only written during registration, so a project that upgraded but did not
re-register keeps sending signed messages that nobody can check — every peer
sees `no-key` rather than `verified`. This is the one step that is easy to miss
and produces a symptom that looks like a bug in signing.

A project without PyNaCl registers with no key and sends unsigned. That is a
supported state, not a failure: signed and unsigned peers interoperate, which
is what lets a mesh upgrade one project at a time.

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
