# Design Dry-Run Report #3

**Document**: `.claude/specs/dryrun-design-traceability/design.md`
**Reviewed**: 2026-04-26
**Prior round**: dryrun-design-2.md — 0 critical, 1 warning (W1: requirement-ref derivation gap when AC Trace column absent), 5 observations.

---

## Prior-Round Resolution Verification

### W1 (requirement-ref derivation unspecified when AC Trace absent) — RESOLVED

Section 7 (Skeleton Derivation) now includes a **Requirement-ref derivation** block with a two-step rule:
1. If the Files Changed table includes an "AC Trace" column, use its value directly (pick parent story ID when multiple ACs listed).
2. If the AC Trace column is absent (fallback), `/design` matches the row's change description against `requirement.md` ACs using the Tier 2 description-based heuristic from Section 3. If no AC matches, use `_untraced_` as the ref with a warning comment (`<!-- ⚠ no requirement match found — author must assign -->`).

This is deterministic: the algorithm has exactly one path for each case, with an explicit sentinel when no match is found. The sentinel ensures the gap is visible in task.md (not silently omitted) and requires human resolution — consistent with the conservative-default philosophy stated in Section 3.

---

## Critical Gaps (must fix before implementation)

_None found._

---

## Warnings (should fix, may cause issues)

_None found._

---

## Observations (worth discussing)

### [O1] task.md items are all `[x]` — Pass 8 fully evaluated
All three skeleton items in task.md are marked `[x]` (done). Each specifies actor (**Implementer**), action (updates), and target (the specific SKILL.md file). No ambiguous tasks found. No design decisions without corresponding tasks. No tasks referencing non-existent design elements.

### [O2] Self-dogfood verification block remains accurate post-edit
The edit to Section 7 added derivation rules but did not change the Files Changed table, the self-dogfood verification block, or the AC trace mappings. The 3-row → 31-AC coverage documented in the self-dogfood section is unchanged and still correct.

### [O3] Recursive self-consistency holds through round 3
This review applies Pass 9 to the design that defines Pass 9. The three Files Changed rows all trace on both axes (see Pass 9 below). The design continues to practice what it preaches.

### [O4] The `_untraced_` sentinel creates a deliberate friction point
When `/design` cannot match a Files Changed row to any AC, the `_untraced_` ref + warning comment forces the author to either (a) add the missing AC to requirement.md or (b) manually assign the correct ref. This is intentional friction — it surfaces the gap at authoring time rather than at review time. Worth noting that Pass 9 would independently flag the same gap on the AC axis, so there is redundant detection (authoring-time + review-time), which is appropriate for a safety net.

---

## Pass-by-Pass Summary

| Pass | Result | Notes |
|------|--------|-------|
| 1. Completeness | PASS | All 31 ACs (DDT-1–7) have corresponding design sections. No requirement without design coverage. No scope creep. |
| 2. Data Flow | PASS | All data created is consumed. Prescription → classification → output flow is clear. Requirement-ref derivation now fully specified (W1 resolved). |
| 3. Interface Contracts | PASS | Pass 9 ↔ design.md table format defined. Pass 9 ↔ task.md/requirement.md matching heuristic specified. /design ↔ task.md skeleton format defined. /implement ↔ task.md consumption contract defined. Contract violations handled. |
| 4. State Machine | PASS | task.md item lifecycle: `[ ]` → `[-]` → `[x]`. Verdict states: both axes pass → READY; any gap → FAIL. No unreachable or dead-end states. |
| 5. Failure Paths | PASS | Malformed table (Warning), missing task.md (Critical Gap), missing requirement.md (Critical Gap), both missing (single Critical Gap), no prescriptions (Observation), no AC match during derivation (`_untraced_` sentinel). All paths defined. |
| 6. Concurrency | PASS | Pipeline is strictly sequential: /design → /dryrun-design → /implement. No shared mutable state between concurrent actors. |
| 7. Edge Cases | PASS | Empty table, body-only prescriptions, glob patterns, no-prescriptions designs, absent AC Trace column — all handled. |
| 8. Task Alignment | PASS | All 3 task.md items specify actor/action/target. All design decisions have corresponding tasks. No orphan tasks. |
| 9. Traceability | PASS | See below. |

### Pass 9: Design-to-Task-to-AC Traceability

#### Step 1: Files Changed Table

3 rows parsed:

| # | File | Change |
|---|------|--------|
| 1 | `.claude/skills/dryrun-design/SKILL.md` | Add Pass 9 dual-axis traceability section |
| 2 | `.claude/skills/design/SKILL.md` | Write task.md skeleton from Files Changed table |
| 3 | `.claude/skills/implement/SKILL.md` | Consume skeleton, mark items in-progress/done |

#### Step 2: Body Prescription Scan

Body sections reference the same three SKILL.md files (Sections 1, 7, 8 and the self-dogfood block). All references are to files already captured in the Files Changed table — no additional body prescriptions found. No double-counting.

#### Step 3–4: Dual-Axis Check and Classification

| File/Prescription | Task Axis | AC Axis | Classification |
|-------------------|-----------|---------|----------------|
| `.claude/skills/dryrun-design/SKILL.md` — Add Pass 9 | Task item 1: "Implementer updates `.claude/skills/dryrun-design/SKILL.md` — add Pass 9…" ✓ | AC-1.1–1.5, AC-2.1–2.3, AC-3.1–3.3, AC-4.1–4.3, AC-5.1–5.7 ✓ | **Traced** |
| `.claude/skills/design/SKILL.md` — Write task.md skeleton | Task item 2: "Implementer updates `.claude/skills/design/SKILL.md` — write task.md skeleton…" ✓ | AC-6.1–6.6 ✓ | **Traced** |
| `.claude/skills/implement/SKILL.md` — Consume skeleton | Task item 3: "Implementer updates `.claude/skills/implement/SKILL.md` — consume skeleton…" ✓ | AC-7.1–7.4 ✓ | **Traced** |

#### Traceability Matrix

| File/Prescription | Task Reference | AC Reference |
|-------------------|---------------|--------------|
| `.claude/skills/dryrun-design/SKILL.md` — Add Pass 9 dual-axis traceability | Skeleton item 1: Implementer updates dryrun-design SKILL.md | AC-1.1–1.5, AC-2.1–2.3, AC-3.1–3.3, AC-4.1–4.3, AC-5.1–5.7 (21 ACs) |
| `.claude/skills/design/SKILL.md` — Write task.md skeleton | Skeleton item 2: Implementer updates design SKILL.md | AC-6.1–6.6 (6 ACs) |
| `.claude/skills/implement/SKILL.md` — Consume skeleton | Skeleton item 3: Implementer updates implement SKILL.md | AC-7.1–7.4 (4 ACs) |

**Result**: All 3 file-level prescriptions traced to tasks and ACs. No traceability gaps.

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 0        | 0        | 4            |

**Verdict**: **PASS**

The design is clean. The single warning from round 2 (W1: requirement-ref derivation when AC Trace column absent) is resolved — Section 7 now specifies a deterministic two-step derivation with an explicit `_untraced_` sentinel as the terminal fallback. All 9 passes pass. All 31 ACs across DDT-1–7 have design coverage. All 3 file prescriptions trace on both axes. The spec is ready for `/implement`.
