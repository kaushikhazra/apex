# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Document under test: {ARTIFACT_PATH}

Every {INTERVAL}, ONE iteration:
  - Action:  work on {ARTIFACT_PATH}, as action.md asks
  - Observe: check it against the goal, using observe.md
  - If goal met:     stop the loop and delete the cron
  - If goal not met: write the next action.md, then exit this run

Fail-safe: at {DEADLINE}, stop and delete the cron, converged or not.
```

`goal.md` and `observe.md` do not change. Everything else may, including the assumptions — if an assumption changes, record it in that cycle's Observe.

Each cycle is written to `logs/cycle-N.md`. **These are immutable — they report the state at that cycle and are never edited afterwards.**

If the artifact already existed at the start, **cycle 1 reads it and records where it stands. It does not write.** After that the loop edits the artifact; it never regenerates it.

**First run: {START}. Fail-safe deadline: {DEADLINE}.**
