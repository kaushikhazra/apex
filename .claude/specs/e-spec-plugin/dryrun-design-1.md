# Design Dry-Run Report #1

**Document**: C:/Projects/APEX/.claude/specs/e-spec-plugin/spec.md
**Reviewed**: 2026-04-27

---

## Critical Gaps (must fix before implementation)

_None found._

---

## Warnings (should fix, may cause issues)

### [W1] No explicit list of the 10 skills
- **Pass**: Pass 1 (Completeness Check)
- **What**: The spec says "10 skills" and acceptance criterion AC-2 says "All 10 skills present" but the spec body never enumerates them. The implementation must infer the list from the current `.claude/skills/` directory.
- **Risk**: If a new skill is added or one is deleted before implementation, the "10" count silently drifts.
- **Suggestion**: Add an explicit list of the 10 skill names to the spec or to AC-2. Based on the current directory, these are: requirement, design, implement, dryrun-design, dryrun-code, dryrun-blueprint, dryrun-context, dryrun-plan, research, spec.

### [W2] No migration path documented for existing downstream consumers
- **Pass**: Pass 7 (Edge Cases & Boundaries)
- **What**: Decision D6 says git URL install is sufficient, but the spec doesn't address the transition from copy-paste installs in FPAI, Velasari, and Noteflow. Projects that currently have `.claude/skills/` copies would have duplicate skills (local + plugin) after install.
- **Risk**: Namespace collisions or confusion for the brief window during migration.
- **Suggestion**: Add an "Out of Scope / Migration Note" acknowledging that downstream consumers must delete their local copies when adopting the plugin. Even one sentence prevents future confusion.

### [W3] Plugin manifest format not validated against Claude Code spec
- **Pass**: Pass 3 (Interface Contract Validation)
- **What**: The spec prescribes a `plugin.json` shape with `name`, `description`, `version`, and `author` fields. Claude Code's plugin discovery protocol is not referenced — there's no confirmation this schema is the canonical format.
- **Risk**: If Claude Code expects different fields (e.g., `displayName`, `skills` array path, `minVersion`), the plugin won't load.
- **Suggestion**: Before writing plugin.json, verify the Claude Code plugin manifest spec. If the format is correct as stated, note the source in a comment or decision.

### [W4] `skills/` directory location is assumed, not verified
- **Pass**: Pass 3 (Interface Contract Validation)
- **What**: Decision D3 says "flat `skills/` folder per Claude Code plugin spec" but the Claude Code plugin spec source is not cited. The skill path convention (`skills/<name>/SKILL.md`) is an assumption.
- **Risk**: If Claude Code resolves skills differently (e.g., from root, or from a path declared in plugin.json), the plugin load fails silently.
- **Suggestion**: Cite or verify the Claude Code plugin discovery behavior for skill paths. If empirically verified, note it as such.

---

## Observations (worth discussing)

### [O1] Spec uses a non-standard format
The spec is written as a single `spec.md` rather than the three-file format (requirement.md, design.md, task.md) prescribed by the SDLC methodology. This is intentional — the feature is self-referential and the spec format is lightweight. No gap, just noting the departure.

### [O2] `CLAUDE.md` retention (D4) has no acceptance criterion
Decision D4 keeps `CLAUDE.md` at the plugin root for contributor guidance. There is no corresponding AC to verify this file exists and is accurate post-restructure. Low risk but worth an explicit check during code review.

### [O3] Path reference fix scope is underspecified
AC-5 says "No broken paths inside any SKILL.md body referencing old `.claude/skills/` location." The implementation must grep all SKILL.md bodies for `.claude/skills/` references and patch them. The scope of expected changes should be confirmed — if no SKILL.md references that path, AC-5 is trivially satisfied. If several do, it's a meaningful fix.

### [O4] git mv preserves history but only within the same repo
The spec correctly uses `git mv` (D3 implementation approach). History is preserved for `git log --follow`. This is the right call — noted as a positive architectural decision.

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 0        | 4        | 4            |

**Verdict**: PASS WITH WARNINGS

The spec is coherent and actionable. No critical gaps block implementation. Four warnings should be addressed — most importantly W3 (plugin manifest format validation) and W4 (skills path convention source). These are verifiable before plugin.json is written. W1 (enumerate skills) is low-friction to address. W2 (migration note) is documentation-only.
