# Cycle 2 — 2026-08-18 17:41 IST — phase 2, resolve the open questions from evidence

**Phase:** 2 of 4. **Action:** survey real plugin repositories and resolve the six questions the specification leaves open. **Nothing in APEX was touched.**

## Rule count

| | Cycle 1 | Cycle 2 |
|---|---|---|
| Total rules | 23 | **31** |
| — spec-derived | 23 | 23 |
| — convention-derived | 0 | **8** |
| Pass | 0 | 0 |
| Fail | 0 | 0 |
| Unchecked | 23 | 31 |
| Open questions | 6 | **0** |

**All six open questions resolved.** O1→D1, O2→D2, O3→D2, O4→D4/D5, O5→D3, O6→D8.

## Evidence base

| Repository | Plugins | Placement |
|---|---|---|
| `anthropics/claude-code` | 10+ | every one at `./plugins/<name>` |
| `anthropics/claude-plugins-official` | many | Anthropic's own at `./plugins/<name>`; third parties by `git-subdir` |
| `42Crunch-AI/claude-plugins` | multi | `plugins/api-security-testing` |
| `adobe/skills` | multi | `plugins/creative-cloud/adobe-for-creativity` |

Two sampled and discarded as uninformative: `databricks-solutions/ai-dev-kit` lists no plugins; `apache/hamilton` has one, so it says nothing about arranging several.

**Four multi-plugin repositories, two of them Anthropic's own. All use a single `plugins/` parent. No counter-example found.**

## Rules added — D1 to D8

Placement under `plugins/`; grouping permitted below it; `$schema` declared; `description`/`version`/`author` populated; `category` populated; `sha` pinned alongside `ref`; relative sources for same-repo plugins; `metadata.pluginRoot` unused.

## ⭐ Two findings the survey produced that the documentation did not

**`category` is used on every Anthropic entry and does not appear in the documented schema table.** Recorded as convention-only (D5), not as a specification requirement. Worth knowing that the published table is not exhaustive of what Anthropic themselves write.

**Anthropic does not use `git-subdir` for plugins in their own repository.** Same-repo entries are relative paths — `"./plugins/<name>"` — and `git-subdir` is reserved for plugins living in *other* repositories. That is D7, and it is the rule most likely to matter to APEX, which uses `git-subdir` pointed at itself.

## ⚠ D7 conflicts with a deliberate decision, and that is recorded rather than resolved

APEX commit `6d045ec`, *"marketplace: resolve every plugin from GitHub, not from the local clone"*, chose `git-subdir` over relative paths on purpose. **Phase 3 will record this as a convention breach with a stated reason and mark it a candidate for `exception`, not `fail`.** The loop surfaces a deliberate decision; it does not overturn one.

## The trap in this phase, and what was done about it

Cycle 1 flagged that the answer to O1 was already suspected — the walkthrough uses `plugins/<name>/` and `metadata.pluginRoot` exists to support that shape — which makes it easy to survey until the expected answer appears and stop.

**Two sampled repositories were discarded for being uninformative rather than quietly dropped, and the discard is recorded above.** The count is four supporting, zero contradicting, two uninformative. Had the community repositories been split, D1 would have stayed open.

**And D8 cuts against the hint.** `metadata.pluginRoot` exists precisely for this case and neither Anthropic marketplace uses it — so the evidence closed one question in the direction the hint pointed and another against it. That is what a survey looks like when it is not confirming itself.

## Goal check — **NOT MET**

31 rules, all unchecked.

## Next

**Phase 3.** Audit APEX against all 31 rules. Pass or fail, per rule, per plugin. **Change nothing** — the audit is a measurement, and measuring after fixing destroys the reading.
