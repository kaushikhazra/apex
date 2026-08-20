# Dryrun Design Traceability — Requirements

## Overview

The current `/dryrun-design` skill performs 8 review passes on a design document, including requirement↔design completeness (Pass 1) and design↔task alignment (Pass 8). However, both passes operate at the *element/decision* level — not at the *file prescription* level. This means a design can prescribe specific file changes (in the "Files Changed" table and in body prose) that have no corresponding acceptance criterion in `requirement.md` and no matching task in `task.md`, and `/dryrun-design` will not flag the gap.

The consequence is severe: prescriptions without ACs are invisible to `/implement` (which works from task.md) and invisible to `/dryrun-code` (which traces ACs). Work prescribed by the design is never executed, and every downstream gate reports "READY" because none of them know the work exists.

**Evidence**: The `mobject-layout-coordination` spec shipped with `/dryrun-code` verdict READY (0 bugs, 0 gaps, all ACs traced), $4.30 spent — but the scene-file retrofit prescribed by `design.md` was never executed because no AC owned it and no task referenced it.

This spec introduces a **design-to-task-to-AC traceability check** as an explicit pass in `/dryrun-design`, ensuring that every file-level prescription in the design has both a task and an AC before the design is approved.

---

## User Stories

### DDT-1: Files Changed Table Traceability

**As a** spec author running `/dryrun-design`,
**I want** every entry in design.md's "Files Changed" table to be checked for (a) a matching item in `task.md` and (b) a matching acceptance criterion in `requirement.md`,
**so that** no prescribed file change can pass design review without implementation and verification coverage.

**Acceptance Criteria:**
- AC-1.1: When `/dryrun-design` runs and `design.md` contains a "Files Changed" table, the new traceability pass parses every row of that table and extracts the file path and change description.
- AC-1.2: For each extracted Files Changed entry, the pass searches `task.md` for a task item that references the same file path or describes the same change. If no matching task is found, the entry is reported as a traceability gap.
- AC-1.3: For each extracted Files Changed entry, the pass searches `requirement.md` for an acceptance criterion that would verify the change described. If no matching AC is found, the entry is reported as a traceability gap.
- AC-1.4: A Files Changed entry with no matching task AND no matching AC is reported as a **Critical Gap** (not a Warning).
- AC-1.5: A Files Changed entry with a matching task but no matching AC (or vice versa) is reported as a **Critical Gap** — partial coverage is not sufficient.

---

### DDT-2: Design Body Prescription Traceability

**As a** spec author running `/dryrun-design`,
**I want** specific file-change prescriptions embedded in design.md's body sections (outside the Files Changed table) to also be checked for task and AC coverage,
**so that** retrofit instructions or change directives buried in prose cannot escape the traceability gate.

**Acceptance Criteria:**
- AC-2.1: The traceability pass scans design.md body sections for prescriptive statements that reference specific files, directories, or file patterns (e.g., "update all `.scene` files", "modify `src/layout/coordinator.py`", "add a new field to `config.yaml`").
- AC-2.2: Each identified body prescription is checked against `task.md` and `requirement.md` using the same matching logic as DDT-1 (AC-1.2 and AC-1.3).
- AC-2.3: Body prescriptions with no matching task or AC are reported as Critical Gaps with the source location (section heading and/or line context from design.md).

---

### DDT-3: Traceability Gap Severity and Verdict Impact

**As a** spec reviewer reading a `/dryrun-design` report,
**I want** traceability gaps to be classified as Critical Gaps that block a PASS verdict,
**so that** a design with untraced file prescriptions cannot be approved for implementation.

**Acceptance Criteria:**
- AC-3.1: Any traceability gap (from DDT-1 or DDT-2) is emitted in the "Critical Gaps" section of the dryrun-design report, using the existing `[C{N}]` numbering format.
- AC-3.2: Each critical gap entry includes: the file path or prescription text from design.md, whether the task link is missing, whether the AC link is missing, and a suggested fix (e.g., "Add an AC to requirement.md covering {change}" or "Add a task to task.md for {file}").
- AC-3.3: The presence of any traceability gap prevents the verdict from being PASS — the verdict must be FAIL or PASS WITH WARNINGS at most (matching the existing severity rules in the dryrun-design report format).

---

### DDT-4: Traceability Mapping Display

**As a** spec author reviewing a `/dryrun-design` report with no traceability gaps,
**I want** the report to display the successful mappings (each Files Changed entry → its task → its AC),
**so that** I can verify the mappings are correct, not just present.

**Acceptance Criteria:**
- AC-4.1: When all Files Changed entries and body prescriptions have matching tasks and ACs, the traceability pass emits a summary table showing: `File/Prescription | Task Reference | AC Reference`.
- AC-4.2: The summary table appears in the report under a "Traceability Matrix" heading (or similar), within the pass output section — not only in the verdict summary.
- AC-4.3: If the design has no "Files Changed" table and no body prescriptions referencing specific files, the pass reports "No file-level prescriptions found — traceability check skipped" as an Observation (not a gap or warning).

---

### DDT-5: Dual-Axis Pass 9 in Dryrun-Design Skill

**As a** SDLC maintainer modifying the `/dryrun-design` skill,
**I want** the traceability check to be a distinct, numbered pass in the dryrun-design SKILL.md (not folded into existing Pass 1 or Pass 8), checking two independent axes — design↔requirement AC and design↔task skeleton — at design-time,
**so that** the check is explicitly documented, independently auditable, and cannot regress if Pass 1 or Pass 8 are modified, and the C1 deadlock (task.md not yet existing at dryrun-design time) is eliminated by the guarantee that `/design` now produces task.md before `/dryrun-design` runs.

**Acceptance Criteria:**
- AC-5.1: The `/dryrun-design` skill at `.claude/skills/dryrun-design/SKILL.md` contains a new pass (e.g., "Pass 9: Design-to-Task-to-AC Traceability") that is separate from Pass 1 (Completeness Check) and Pass 8 (Task Spec Alignment).
- AC-5.2: The new pass has its own section heading, numbered consistently with the existing pass structure.
- AC-5.3: The new pass's instructions reference the "Files Changed" table explicitly (not just "design elements") and instruct the reviewer to also scan body prose for file-level prescriptions.
- AC-5.4: The existing Pass 1 and Pass 8 are not modified — the new pass is additive.
- AC-5.5: Pass 9 checks **two axes independently**:
  - **AC axis**: every Files Changed entry (and body prescription) in design.md has a matching acceptance criterion in `requirement.md`.
  - **Task axis**: every Files Changed entry in design.md has a matching skeleton item in `task.md` (produced by `/design` in DDT-6).
- AC-5.6: The verdict for Pass 9 is "READY" only when **both** axes are fully covered. A gap on either axis alone is sufficient to block the verdict.
- AC-5.7: Pass 9 instructions note that `task.md` is expected to exist at `/dryrun-design` time (created by `/design`) — if `task.md` is absent, Pass 9 reports a Critical Gap rather than skipping.

---

### DDT-6: `/design` Skill Produces task.md Skeleton

**As a** spec author running `/design`,
**I want** the skill to output both `design.md` AND a `task.md` skeleton in a single step,
**so that** the task.md exists before `/dryrun-design` runs, eliminating the C1 deadlock and ensuring the Task axis of Pass 9 can be evaluated at design-time.

**Acceptance Criteria:**
- AC-6.1: After `/design` completes, both `design.md` and `task.md` exist in the spec folder.
- AC-6.2: `task.md` contains exactly one skeleton item per row in design.md's "Files Changed" table. Each skeleton item references the file path from that row and a one-line description of the intended change (derived from the "Change" or "Description" column of that table).
- AC-6.3: Skeleton items use the standard `[ ]` pending status from the task.md format — they are valid, parseable task entries, not comments or notes.
- AC-6.4: Each skeleton item includes the actor, action, and target per the task.md rules (e.g., "[ ] **Implementer** updates `src/foo.py` — add layout coordination hook").
- AC-6.5: If design.md has no "Files Changed" table, `/design` still creates `task.md` with a note: "No Files Changed table found — populate tasks manually after finalising design."
- AC-6.6: `/design` does **not** author free-form tasks beyond the Files Changed skeleton — free-form task expansion is the responsibility of `/implement`.

---

### DDT-7: `/implement` Reads the Skeleton, Not Authors It

**As a** spec implementer running `/implement`,
**I want** the skill to consume the `task.md` skeleton created by `/design` rather than authoring `task.md` from scratch,
**so that** the task list stays in sync with the design prescription, and items already traced in Pass 9 are not silently replaced.

**Acceptance Criteria:**
- AC-7.1: When `/implement` runs and `task.md` already exists (the skeleton from `/design`), the skill does NOT overwrite or regenerate `task.md`.
- AC-7.2: `/implement` marks skeleton items `[-]` (in progress) when it begins executing them and `[x]` (done) when complete.
- AC-7.3: `/implement` may append additional sub-tasks beneath a skeleton item (one level of nesting), but must not remove or rename the skeleton item itself.
- AC-7.4: If `/implement` discovers work not covered by any skeleton item, it adds a new `[ ]` item for it **and** flags a warning that the new item was not traced by Pass 9 (indicating the design.md Files Changed table may be incomplete).

---

## Evidence: The Failure That Motivated This Spec

### The `mobject-layout-coordination` Case (April 25, 2026)

**What happened:**
1. `design.md` prescribed a scene-file retrofit — updating existing `.scene` files to use the new layout coordination system.
2. The retrofit was listed in the "Files Changed" table and described in the design body.
3. `requirement.md` had user stories and ACs covering the *new* layout coordination build rules (forward-looking), but **no AC** covering the retrofit of *existing* scene files (backward-looking).
4. `task.md` had no task for the retrofit because no AC drove its creation.
5. `/implement` executed all tasks — none mentioned the retrofit, so it was skipped.
6. `/dryrun-code` checked all ACs — all passed because none owned the retrofit. Verdict: READY. 0 bugs, 0 gaps.
7. Spec marked done. $4.30 spent. Retrofit never executed.

**Root cause:** The design mixed "build rules" (forward-looking guardrails for future files) with "apply retrofit" (backward-looking changes to existing files). The existing `/dryrun-design` passes checked at the element/decision level, not the file-prescription level, so the gap was invisible.

**Why downstream gates couldn't catch it:**
- `/implement` works from `task.md` — no task, no work.
- `/dryrun-code` traces ACs — no AC, no check.
- Only `/dryrun-design` sees the design-to-requirement-to-task triangle at the right time to flag the gap.

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| `/dryrun-design` skill (`SKILL.md`) | Exists | **Primary target** — new Pass 9 (dual-axis traceability) added |
| `/design` skill (`SKILL.md`) | Exists | **Primary target** — expanded to write both `design.md` and `task.md` skeleton (DDT-6) |
| `/implement` skill (`SKILL.md`) | Exists | **Secondary target** — updated to read skeleton rather than author `task.md` (DDT-7) |

---

## Out of Scope

- **Implementation of the skill changes** — this spec defines *what* changes; the actual SKILL.md edits are a separate dispatch.
- **Auditing existing specs** — worker projects (e.g., forward-pass-ai) may have specs with the same blind spot. That's a separate audit, not part of this spec.
- **Modifying `/dryrun-code`** — the fix is at `/dryrun-design` (upstream gate). `/dryrun-code` should not need changes if traceability is enforced earlier.
- **Modifying `requirement.md` or `task.md` templates** — this spec targets the *skill behaviours*, not static authoring templates.
- **Auto-generating placeholder ACs in `requirement.md` from Files Changed entries** — closing the AC axis gap is the author's responsibility (guided by Pass 9 feedback), not an automated injection step.

---

## Open Questions

1. **Matching heuristic**: How strict should the file-path matching be between a Files Changed entry and a task/AC? Exact path match? Substring? Semantic similarity? This is a design decision — the requirement states *that* matching must happen, not *how* fuzzy it should be.
2. **Body prescription detection scope**: Should the body scan be exhaustive (NLP-level parsing of every sentence for file references) or targeted (only explicit file paths and glob patterns)? The requirement states body prescriptions must be checked, but the detection boundary is a design decision.
3. ~~**Secondary /design skill change**: Should a separate spec be created for the `/design` skill auto-generating placeholder ACs and tasks, or should it be folded into this spec's design phase?~~ **Resolved 2026-04-25 (Kaushik)**: Folded into this spec as Option 2. `/design` now produces task.md skeleton, `/dryrun-design` Pass 9 checks both axes at design-time, and `/implement` reads the skeleton. No separate spec needed.
