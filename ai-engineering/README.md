# ai-engineering

Methods for engineering agent **behaviour**, not agent code.

## Skills

### `auto-iterate`

Run a goal to convergence by iterating on one document.

The agent generates the artifact, checks it against an immutable goal, rewrites its own instruction for the next pass, and stops — either when the goal is met, or when a fail-safe expires.

**The document is what is under test. `action.md` is only the instrument, and the loop rewrites it each cycle.**

```
<name>/
  iteration-1/
    goal.md          immutable — the goal, and nothing else
    observe.md       immutable — what to record, and the goal check
    assumption.md    standing inputs; may change
    action.md        rewritten every cycle by the loop
    loop.md          the loop, the schedule, the fail-safe
    logs/cycle-N.md  immutable state reports
    artifact/        what this iteration produced
  iteration-2/       a second goal, seeded from iteration-1's artifact
```

**Iterations are not cycles.** An iteration is one goal run to its end; a cycle is one pass inside it.

## Why it exists

A previous unbounded analysis ran to 189 passes and produced a document nobody read. Given the same subject with a stated goal and a fail-safe, this converged in four cycles, six, and five across three separate runs.

**The loop does not find things. The goal finds things. The loop stops.** That is its entire contribution, and it is the thing the unbounded version lacked.

## Track record

| Run | Cycles | Outcome |
|---|---|---|
| Business feasibility model | 4 | Converged; reduced the question to a single threshold |
| Validation pass over that model | 6 | Killed its central premise; found two internal contradictions |
| Astronomical date check | 5 | Corrected four dates against an independent ephemeris |

**Generalised from three runs in two domains.** Treat it as working rather than proven.
