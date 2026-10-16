# Cycle 4 — 2026-08-18 18:00 IST — phase 4, fix X5

**Phase:** 4 of 4, first fix. **Rule:** X5, install documentation must name the ref the manifest pins. **First cycle to change APEX.**

## Rule count

| | Cycle 3 | Cycle 4 |
|---|---|---|
| Total rules | 31 | 31 |
| Pass | 23 | **24** |
| Fail | 7 | **6** |
| Exception | 1 | 1 |
| Unchecked | 0 | 0 |
| — spec-derived | 22 pass, 1 fail | **23 pass, 0 fail** |

## ⭐ The specification side is now clean

**All 23 spec-derived rules pass.** Everything left in the table is convention.

## What changed

`README.md`, two occurrences:

```
- /plugin marketplace add kaushikhazra/apex#develop
+ /plugin marketplace add kaushikhazra/apex
```

Nothing else in the file, and nothing else in the repository.

## The ref was dropped rather than corrected

`#master` would also have passed X5. Omitting the ref entirely takes the repository's default branch, so the instruction survives a future branch rename; a hardcoded `#master` would have to be found and corrected a second time.

**The default branch was verified rather than assumed** — `gh repo view --json defaultBranchRef` returns `master`. Had it returned anything else, dropping the ref would have silently pointed users at a branch the manifest does not publish from, which is the same failure in a new costume.

## Re-check

Searched `README.md` for `#develop`: **zero matches.** Both install lines now read `/plugin marketplace add kaushikhazra/apex`, and `marketplace.json` continues to pin `"ref": "master"` — the default branch — so documentation and manifest agree.

## Held back deliberately

Two other `README.md` problems were left untouched, both noted in earlier cycles:

- The structure block omits `ai-engineering/` and `agents/`, where two of the three plugins live.
- The file states *"Private repository. Internal use only."* while the repository is public.

**Neither is governed by a rule in the table.** The second is worth Kaushik's attention and sits in *Candidates dropped* for that reason. Fixing them here would be the loop widening its own scope mid-run, which is how a bounded goal stops being bounded.

## Goal check — **NOT MET**

Six convention failures remain: D1, D2, D3, D4, D5, D6.

## Next

**D3** — add `$schema` to `marketplace.json`. Additive, no consumer impact. The safe changes are taken first so the risky one, moving the plugin directories, lands last against a repository that is otherwise already correct.
