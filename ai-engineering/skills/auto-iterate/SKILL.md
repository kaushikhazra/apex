---
name: auto-iterate
description: Run a goal to convergence by iterating on one document. Scaffolds a loop folder, then on a schedule generates the artifact, checks it against the goal, and rewrites its own instruction for the next pass. Stops when the goal is met or the fail-safe expires. Use for work that has an answerable end state — find out, build, verify, polish, or code. Fires on "iterate on this", "let's run a few cycles", "keep going until it's ready", "work on X until Y", "I want you to loop through...".
invocation: /auto-iterate to start · cron prompt to tick
output: an artifact folder, an immutable cycle log, and a scheduled cron
---

# Loop

An agent iterating on one document until it satisfies a goal. **The document is what is under test. `action.md` is only the instrument, and the loop rewrites it each pass.**

Two entry points. Nothing else.

---

## Start

**Ask these one at a time, with the examples shown beneath the question.** Wait for each answer before asking the next — a block of seven is a form, and people fill forms badly.

**If an answer is already known from the conversation, suggest it instead of asking cold.** They confirm or correct in a word. Asking someone to retype what they just told you is a tax, not diligence.

Do not proceed on guesses. A loop that runs on an assumed goal produces confident waste.

> **1 — What are you trying to get done?**
> *find out —* "Which city we should move to."
> *build —* "An onboarding guide for new hires."
> *verify —* "Whether our pricing page matches what we actually charge."
> *polish —* "My CV, until it's ready to send."
> *code —* "Make the flaky auth test pass fifty times in a row."
>
> **2 — How will you know you're done?**
> What has to be true for you to stop.
> *e.g. "Someone in my industry could read it without flagging anything."*
> *code —* "The suite passes and coverage hasn't dropped."
>
> **3 — What should I produce, and where?**
> *e.g. `cv.md` · `src/convert.py` · "changes in the auth module"*
> **If it already exists, say so** — that changes how the first cycle behaves.
>
> **4 — How often should I work on it?** *e.g. "Every 5 minutes."*
>
> **5 — When should I stop if it hasn't landed?** *e.g. "After an hour."*
>
> **6 — Anything I should take as given rather than work out?** *(optional)*
> *e.g. "Two pages, no photo." · "Use the existing test framework, no new dependencies."*
>
> **7 — Where should the loop live?**
> **Suggest a folder from what has already been said** — the repo they are working in, the project they have been discussing.

**The loop folder always needs a location, including when the artifact already exists.** An artifact that already exists **stays at its own path and is never moved**; the loop points at it. Only a *new* artifact is created inside the loop folder.

## Iterations

A loop folder holds one or more **iterations**, and an iteration is one goal run to its end.

**`goal.md` is immutable, so a new goal means a new `iteration-N/`** — never an edit to the previous one. **An iteration is self-contained: its own goal, its own logs, its own artifact.** A new iteration starts by copying the previous iteration's artifact into its own folder and works on that copy.

**Iterations are not cycles.** An iteration is a whole run; a cycle is one pass inside it. Cycles are logged in that iteration's own `logs/`.

Then:

1. Copy `template/` to the folder they chose. If the folder already exists from an earlier goal, add the next `iteration-N/` rather than copying the whole template again.
2. Write answers 1 and 2 into `goal.md` as one sentence carrying both.
3. Write the optional answer into `assumption.md`.
4. Fill the artifact path, interval and fail-safe deadline into `loop.md`, and stamp the start time.
5. Write the first `action.md` — the one thing to tackle first.
6. Create the cron. **The prompt is one line:**

   `Read <absolute-path>/loop.md and run one iteration.`

**Absolute path.** The tick may wake in a context that knows nothing else.

---

## Tick

Read `loop.md` and follow it. It names every path and owns the exit.

---

## Rules

**The user never edits these files. The agent writes all of them.** The five questions are a conversation; the files are the output.

**One document, one intent — for the five files that run the loop** (`goal.md`, `observe.md`, `assumption.md`, `action.md`, `loop.md`). Only cycle logs carry multiple sections, because they are reports.

**The artifact is exempt. Its shape belongs to the user.** Produce what they asked for, in the file they named, however many sections that ends up being. Split it only if they ask. Separation of concerns is a preference, and it is not necessarily theirs.

**`goal.md` and `observe.md` never change.** Everything else may, including assumptions — when an assumption changes, record it in that cycle's Observe.

**Cycle logs are immutable.** They report the state at that cycle. Never revise one; write the next.

**Never write iteration numbers into the artifact.** Which pass produced which part is loop bookkeeping and belongs in `logs/`. **The artifact reads as a finished document at every point** — and most goals rewrite rather than append, so the numbering is not even true.

**If the artifact already exists, the first cycle reads it and records where it stands against the goal — it does not write.** Acting before that is writing blind. And the loop **edits** the artifact from then on; it never regenerates it, or cycle 1 destroys what the user came in with.

**Derive, don't generate.** Each cycle's move should come from the previous cycle's constraint, not from a fresh idea. Fresh ideas are generative and generation does not converge — that is what runs a loop to 189 iterations.

**Stop when the answer stops moving.** A cycle that changes nothing is the signal to halt and report the flat result, not to try another variant.

---

## Why the structure is shipped rather than described

`template/` is copied, not explained. A copy cannot drift; a description can. And the running agent never needs to know the layout — `loop.md` names every path it uses.

```
<name>/
  iteration-1/
    goal.md            immutable — the goal, and nothing else
    observe.md         immutable — what to record, and the goal check
    assumption.md      standing inputs; may change
    action.md          rewritten every cycle by the loop
    loop.md            the loop, the schedule, the fail-safe
    logs/cycle-N.md    immutable state reports
    artifact/          what this iteration produced
  iteration-2/         a second goal, starting from iteration-1's artifact
    ...
```

**Everything an iteration touches lives inside its own folder, artifact included.** A later iteration starts by copying the previous one's artifact into its own — so each iteration keeps the version it produced, and nothing overwrites work that has already been reported on.

---

## Not yet proven

This generalises from **one** run — a business feasibility model that converged in six cycles. **Run it on a second, unrelated goal before trusting it.** An instance is not a pattern.
