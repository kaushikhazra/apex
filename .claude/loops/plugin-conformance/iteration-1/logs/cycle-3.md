# Cycle 3 — 2026-08-18 17:52 IST — phase 3, the audit

**Phase:** 3 of 4. **Action:** check all 31 rules against APEX. **Nothing was edited.**

## Rule count

| | Cycle 2 | Cycle 3 |
|---|---|---|
| Total rules | 31 | 31 |
| Pass | 0 | **23** |
| Fail | 0 | **7** |
| Exception | 0 | **1** |
| Unchecked | 31 | **0** |

## ⭐ The headline

**APEX conforms to the published specification.** Twenty-two of twenty-three spec-derived rules pass. The twenty-third is a documentation inconsistency, not a manifest defect.

**Every substantive failure is convention, not compliance.** That is precisely the distinction phase 1 was built to hold apart, and it would have been invisible under a single "make it compliant" pass — the plugins would have been declared broken when they are not.

## Spec side — 22 pass, 1 fail

All three plugins pass P1–P9. Manifests are correctly located, correctly named, kebab-case, `.claude-plugin/` holds nothing but the manifest, every skill directory has its `SKILL.md`, skills sit under `skills/`.

Marketplace passes M1–M9 outright: required fields present, `apex-tools` is kebab-case and not reserved, every entry carries `name` and `source`, every source is the permitted `git-subdir` with `url` and `path`, and all three entry versions agree with their plugin manifests.

**X5 is the single spec-side failure.** `README.md` tells users to install from `#develop`, twice, while `marketplace.json` pins `"ref": "master"`. One string, two places.

## ⚠ Two rules passed vacuously and are recorded as such

**P6 and P7 were not exercised.** No APEX manifest declares a path field, so the `./` prefix rule and the directory-existence rule govern nothing. They are marked `vacuous` rather than `pass`.

This matters because a future manifest that adds a `skills` or `hooks` path field makes both rules live, and a log claiming they passed would have hidden that they were never tested.

## Convention side — 1 pass, 6 fail, 1 exception

| Rule | Result |
|---|---|
| D1 | fail — three plugins, three placements, no shared parent |
| D2 | fail — follows from D1; there is no `plugins/` for a grouping to sit inside |
| D3 | fail — no `$schema` in `marketplace.json` |
| D4 | fail — `author` absent on all three entries, though every plugin manifest has it |
| D5 | fail — no `category` on any entry |
| D6 | fail — all three pin `ref: master` with no `sha` |
| D7 | **exception** — `git-subdir` against own repo, deliberate per `6d045ec` |
| D8 | pass — `metadata.pluginRoot` unused, paths explicit |

**D6 is the one with a real consequence beyond tidiness.** A branch ref is a moving target: two users installing a week apart get different code under the same version number. Anthropic pins a commit alongside the ref on every third-party entry.

## D7 was not marked a defect

APEX resolves its own plugins through `git-subdir` against its own repository; Anthropic uses relative paths for same-repo plugins. The departure is real and it was chosen on purpose in commit `6d045ec`. **Recorded as `exception` with the reason attached.** The loop surfaces a decision; it does not overturn one.

## Ordering for phase 4

Six of the seven failures are additive or documentary and carry no risk: X5, D3, D5, D4, then D6. **D1 and D2 are the only ones that can break a live consumer**, because moving a plugin changes the `path` every installed copy resolves against. The manifest has to move in the same commit, and the version bumped so clients refetch.

Phase 4 therefore takes the safe five first, and reaches the move last — with the audit already recorded, so the reading survives whatever happens next.

## Goal check — **NOT MET**

Every rule is checked, which satisfies half the condition. Seven failures remain unfixed.

## Next

**Phase 4, cycle 1: X5.** Correct the two `#develop` references in `README.md` to `master`. Smallest change, zero risk, and it is the only failure on the spec side.
