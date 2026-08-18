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

### `local-model-calibration`

Find out what a local model can actually do before you give it work.

Run one model through all six SDLC phases against a feature you have already built, score each phase on a six-criterion rubric, then iterate the prompt until the score stops climbing. What comes out is a capability map: baseline, best and ceiling per phase, and which technique unlocked each one.

**Same shape as `auto-iterate`, applied to a model instead of a document.** Probe, score, find the weakness, change one thing, re-score, stop at the plateau. Four iterations per phase is the cap.

The reusable finding so far: **under about 10B parameters, models are consistently better critics than creators.** Review phases score 0.10–0.20 above generation phases, and that gap is structural rather than a prompting problem. Assign roles accordingly.

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
