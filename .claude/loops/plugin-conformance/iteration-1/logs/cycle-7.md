# Cycle 7 — 2026-08-18 18:28 IST — the move — **GOAL MET, LOOP STOPPED**

**Phase:** 4, final fix. **Rules:** D1 and D2.

## Rule count

| | Cycle 6 | Cycle 7 |
|---|---|---|
| Total rules | 31 | 31 |
| **Pass** | 27 | **29** |
| **Fail** | 2 | **0** |
| Exception | 2 | 2 |
| Unchecked | 0 | 0 |

## What moved

```
sdlc/spec-enhanced   ->  plugins/e-spec          1.2.1 -> 1.2.2
agents/crosschat     ->  plugins/crosschat       0.5.1 -> 0.5.2
ai-engineering       ->  plugins/ai-engineering  0.2.0 -> 0.2.1
```

`git mv` throughout — every file shows as `R` in status, so history follows. `marketplace.json` paths and all six version fields moved in the same working tree, never as a separate step.

**Each directory is named for the plugin it publishes.** `sdlc/spec-enhanced` published a plugin called `e-spec`; the directory, the manifest `name` and the marketplace entry disagreed. They now read the same word.

## Live references fixed, dated records left alone

The grep found 60+ hits. They split cleanly, and the split was the judgment of this cycle:

**Fixed — live references that the move broke:**

- `.claude-plugin/marketplace.json` — three paths
- `README.md` — install example, manifest sentence, internals pointer, **and the structure block**, which still drew the old tree
- `plugins/e-spec/README.md` — two install lines
- `blueprints/local-agent/readme.md` — the calibration-skill pointer, corrected an hour earlier and now corrected again
- Six `test_*.py` docstrings carrying `python -m unittest sdlc/spec-enhanced/...`

**Left untouched — dated records:**

- `.claude/specs/**` — dryrun reports, designs, requirements
- `plugins/e-spec/specs/**` — same

**These describe what was true when they were written.** A dryrun report from June that says the plugin root was `sdlc/spec-enhanced` was correct in June. Rewriting it would make the record claim something that never happened, which is worse than a stale path in a document nobody resolves.

## Re-check, rule by rule

| Rule | e-spec | crosschat | ai-engineering |
|---|---|---|---|
| D1 under `plugins/` | pass | pass | pass |
| X1 path resolves | pass | pass | pass |
| X2 manifest present | pass | pass | pass |
| X3 entry name = plugin name | pass | pass | pass |
| M9 entry version = manifest version | pass | pass | pass |

`marketplace.json` parses. **D2 checked by sweep**: every directory beside `plugins/` searched for a stray `.claude-plugin/plugin.json` — none found.

The C-section rules were re-checked explicitly rather than assumed, because this was the one change that could break them.

## Two things deliberately not done

**No grouping subdirectory.** `adobe/skills` uses `plugins/creative-cloud/<name>` because it has enough plugins to need one. Three do not. Inventing a taxonomy to demonstrate that D2 was understood would be the same failure as inventing categories to fill a column — which cycle 5 already declined once.

**`sdlc/` was left holding only `scaled-agile`.** It is not a plugin, no rule reaches it, and `assumption.md` puts it out of scope. `agents/` is now empty and was likewise left alone.

## Goal check — ✅ **MET**

> Done when every rule has been checked against the actual files, item by item, and each one either passes or has been fixed.

**31 rules. 29 pass. 0 fail. 2 exceptions, both recorded with reasons.**

`observe.md` permits an exception only as *"a deliberate departure with a reason"*. D6 and D7 are one decision, taken deliberately in commit `6d045ec`, recorded rather than overridden.

**Loop stopped. Cron deleted.**

---

**Ran 17:32 → 18:28 IST, seven cycles, well inside the 19:30 fail-safe.**

## What the run produced beyond the fixes

**The separation of compliance from convention was the whole value.** APEX was conformant to the specification from the start — 22 of 23, with the twenty-third a README string. Everything that actually needed doing was convention. A single "make it compliant" pass would have reported healthy plugins as broken and then changed them for the wrong reason.

**And one rule was withdrawn rather than satisfied.** D6 survived phase 2, survived the audit, and fell in phase 4 when the circularity in fixing it turned out to be a symptom of D7 rather than an obstacle. A loop that can only close rows would have pinned a stale commit and called it done.
