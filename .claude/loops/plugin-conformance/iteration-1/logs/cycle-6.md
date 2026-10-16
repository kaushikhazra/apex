# Cycle 6 — 2026-08-18 18:16 IST — D6 settled, not satisfied

**Phase:** 4, third fix. **Rule:** D6. **Outcome: the rule was investigated rather than obeyed, and it moved to `exception`.** Nothing was edited in APEX.

## Rule count

| | Cycle 5 | Cycle 6 |
|---|---|---|
| Total rules | 31 | 31 |
| Pass | 27 | 27 |
| Fail | 3 | **2** |
| Exception | 1 | **2** |
| — spec-derived | 23 pass, 0 fail | 23 pass, 0 fail |
| — convention-derived | 4 pass, 3 fail, 1 exception | **4 pass, 2 fail, 2 exceptions** |

## Why this cycle did not just add a `sha`

Cycle 5 flagged a circularity: the `sha` D6 wants is the commit that *contains* the fix, which does not exist while the fix is being written. Pinning the current master HEAD would pin every consumer to a commit predating everything this run has done.

That was enough to justify re-testing the rule rather than working around it.

## The full re-read — 286 entries

| | Count | Pins `sha` |
|---|---:|---|
| Same-repo (relative string source) | 53 | 0 — a string source has no field to pin |
| External (object source) | 233 | **233 — every one** |
| — of which `git-subdir` | 83 | **83 — every one** |
| `git-subdir` pointed at the marketplace's own repository | **0** | — |

One correction to an intermediate count: a first pass reported one same-repo entry carrying `sha`. That was `csharp-lsp`, whose *path* contains the letters — `./plugins/csharp-lsp`. **A substring test, not a field.** The real count is zero, and structurally so.

## ⭐ The finding

**D6 was not mis-scoped. It was under-explained.**

Every `git-subdir` entry pins `sha`, without exception — but `git-subdir` is used exclusively for repositories the marketplace does not control. A branch ref in someone else's repository moves under you; a commit pin is what stops it. The rule is real and its reason is foreign ownership.

**Zero of 83 `git-subdir` entries point at their own marketplace's repository.** APEX sits in a configuration that occurs nowhere in a 286-entry catalogue.

**So D6 is a consequence of D7, not an independent failure.** Take the D7 exception and you inherit a rule written for foreign repositories. Resolve D7 — relative sources for same-repo plugins — and D6 disappears, because a relative source cannot pin a `sha` and has nothing to protect against.

The circularity cycle 5 noticed was not an obstacle to fixing D6. **It was a symptom of the thing D6 is downstream of.**

## What was resisted

The easy paths were both available and both wrong.

- **Pin `85487d3` and mark it done.** Passes the check, points consumers at code without the fixes.
- **Write `"sha": ""` and call it deferred.** Passes nothing, adds a field that means nothing.

**Neither closes the rule; both close the row.** The row is not the point.

## What is left for Kaushik rather than for the loop

D6 and D7 are one decision, and it is his. Commit `6d045ec` chose `git-subdir` deliberately. The options, recorded in the artifact:

- **Keep it.** D6 and D7 stay as exceptions with a stated reason. If D6 is to be closed anyway it takes two commits — merge, then a follow-up on `master` writing the merge `sha` — and every release thereafter has to bump the pin or consumers freeze on it.
- **Revisit it.** Relative sources for same-repo plugins, and both exceptions vanish.

**The loop does not pick.** It has established that the two are one question and that the question is his.

## Goal check — **NOT MET**

Two failures remain, D1 and D2, and they are the same move.

## Next

**D1 and D2 — move the three plugin directories under `plugins/`.** The only remaining change, the only one that can break a live install, and deliberately last.
