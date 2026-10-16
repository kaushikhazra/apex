# Loop

```
Goal:                goal.md          (immutable)
Observe rules:       observe.md       (immutable)
Assumptions:         assumption.md
Action:              action.md
Document under test: artifact/conformance.md

Every 6 minutes, ONE iteration:
  - Action:  work on artifact/conformance.md, as action.md asks
  - Observe: check it against the goal, using observe.md
  - If goal met:     stop the loop and delete the cron
  - If stalled:      stop the loop and delete the cron, and say what it was trying to do
  - Otherwise:       write the next action.md, then exit this run
```

Absolute folder: `C:/Projects/APEX/.claude/loops/plugin-conformance/iteration-1/`

Repository under audit: `C:/Projects/APEX/`, on branch `feature/plugin-spec-conformance`.

`goal.md` and `observe.md` do not change. Everything else may, including the assumptions — if an assumption changes, record it in that cycle's Observe.

Each cycle is written to `logs/cycle-N.md`. **These are immutable — they report the state at that cycle and are never edited afterwards.** The rule counts live only there; the artifact carries no history.

The artifact does **not** exist at the start. Cycle 1 creates it. Every cycle after that **edits it in place** — it is never regenerated, and it never mentions cycles or iterations. It reads as a finished document at every point.

**One phase per cycle, and one move within it.** Take the constraint the last cycle left, not a fresh idea.

**Nothing in APEX changes before phase 3 is complete.** Phases 1 to 3 write only the artifact.

**Fail-safe: 19:30 IST, 18 August 2026.** Stop and delete the cron, converged or not, and state where it had reached. This is a runaway guard rather than the intended exit — the goal is expected to hold the exit.

**First run: 2026-08-18 17:26 IST.**
