# Design Dry-Run Report #2

**Document**: `.claude/specs/dryrun-design-traceability/design.md`
**Reviewed**: 2026-04-25
**Prior round**: dryrun-design-1.md — C1 (deadlock on missing task.md), W1 (column count ambiguity). Both addressed via Option 2 revision.

---

## Prior-Round Resolution Verification

### C1 (deadlock on missing task.md) — RESOLVED

Section 1 now states: "task.md is **expected to exist** when Pass 9 executes. If it is absent, Pass 9 reports a Critical Gap rather than skipping (AC-5.7)." The Error Handling section (Missing task.md) confirms: "Every Files Changed entry is reported as a Critical Gap on the **Task axis**" and "Pass 9 does **not** skip when task.md is absent — absence is a Critical Gap, not a deferral." The old "unlikely" framing is removed. D-NEW documents the architectural decision (Option 2). `/design` producing task.md (Section 7) eliminates the precondition gap.

### W1 (column count ambiguity) — RESOLVED

Step 1 (Section 2) states: "at least two columns: `File` (first) and `Change` (second). Extra columns are permitted and ignored by the parser." Error Handling echoes: "at least two columns: File, Change — extra columns are permitted." Consistent across both locations.

---

## Critical Gaps (must fix before implementation)

_None found._

---

## Warnings (should fix, may cause issues)

### [W1] Skeleton requirement-ref derivation unspecified when AC Trace column absent
- **Pass**: Pass 2 (Data Flow Trace)
- **What**: Section 7 skeleton format requires a requirement-ref link at the end of each item (e.g., `_DDT-5_`), stating "it is not optional." The derivation rules (Section 7, Skeleton Derivation) specify extracting file path from column 1 and change summary from column 2, but do not specify how `/design` determines which requirement (DDT-N or AC-N.N) maps to a given Files Changed row. This design's own Files Changed table includes an optional "AC Trace" column — but the canonical format only requires File and Change (Step 1). When AC Trace is absent, the derivation path for the requirement-ref is undefined.
- **Risk**: Different `/design` invocations may use inconsistent strategies — some may guess, some may leave placeholders, some may omit the ref. Pass 9's Task-axis matching doesn't depend on the ref (it matches by file path), so traceability is not broken. But the ref is the human-auditable link between skeleton items and requirements; inconsistent derivation reduces its value.
- **Suggestion**: Add one sentence to Section 7 Skeleton Derivation specifying the fallback: e.g., "If the Files Changed table includes an AC Trace column, use its value. Otherwise, `/design` determines the closest requirement reference by matching the change description against requirement.md ACs using the same Tier 2 heuristic from Section 3."

---

## Observations (worth discussing)

### [O1] task.md does not exist for this spec — Pass 8 limited
task.md was not found at `.claude/specs/dryrun-design-traceability/task.md`. This is expected: the `/design` skill change (DDT-6) that would produce task.md has not been implemented yet. Pass 8 (Task Spec Alignment) cannot fully evaluate. Once Section 7 is implemented and `/design` re-run on this spec, task.md will exist and a future dryrun can complete Pass 8.

### [O2] Self-dogfood section verified — all 31 ACs covered
The Files Changed table (3 rows) traces to all ACs: row 1 covers AC-1.1–1.5, 2.1–2.3, 3.1–3.3, 4.1–4.3, 5.1–5.7 (21 ACs); row 2 covers AC-6.1–6.6 (6 ACs); row 3 covers AC-7.1–7.4 (4 ACs). Total: 31 ACs across DDT-1 through DDT-7. The self-dogfood verification block at the end of the design explicitly walks through all 7 DDT stories confirming design-section coverage. No AC is untraced.

### [O3] Dual-axis logic internally consistent
Section 1 defines AC axis and Task axis. Step 3 (Section 2) applies both independently with the same two-tier heuristic. Step 4's classification table has 4 cells — only (Yes, Yes) = Traced; all three other combinations = Critical Gap. This traces cleanly to AC-5.5 (dual-axis), AC-5.6 (both required for READY), and AC-1.5/AC-1.4 (partial and full gaps). No logical inconsistency found.

### [O4] Sections 7 and 8 form a coherent producer-consumer contract
Section 7 (`/design`): writes skeleton with one `[ ]` item per Files Changed row, specific format, no free-form tasks, handles missing table with fallback note. Section 8 (`/implement`): reads skeleton without overwriting, marks `[-]`/`[x]`, appends sub-tasks additively, flags untraced work with warning comment. The immutability constraint (skeleton text not removed/renamed) preserves the traceability that Pass 9 validated. `/implement`'s untraced-work flag (AC-7.4) closes the loop for work discovered during implementation.

### [O5] Recursive self-consistency holds
This design adds Pass 9 to `/dryrun-design`. The current review uses Passes 1–8 (Pass 9 doesn't exist yet). The self-dogfood section in the design simulates what Pass 9 would find if applied to this design — 3 prescriptions, all traced on both axes. That simulation is consistent with the algorithm defined in Section 2. The design practices what it preaches, within the bootstrapping constraint.

---

## Pass-by-Pass Summary

| Pass | Result | Notes |
|------|--------|-------|
| 1. Completeness | PASS | All 31 ACs (DDT-1–7) have corresponding design sections. No requirement without design coverage. No scope creep — Future Work section defers out-of-scope items explicitly. |
| 2. Data Flow | PASS w/ warning | All data created is consumed. Prescription → classification → output flow is clear. W1: requirement-ref derivation path incomplete. |
| 3. Interface Contracts | PASS | Pass 9 ↔ design.md table format defined. Pass 9 ↔ task.md/requirement.md matching heuristic specified. /design ↔ task.md skeleton format defined. Contract violations handled (malformed table, missing files). |
| 4. State Machine | PASS | task.md item lifecycle: `[ ]` → `[-]` → `[x]`. Verdict states: both axes pass → READY; any gap → FAIL. No unreachable or dead-end states. |
| 5. Failure Paths | PASS | Malformed table (Warning), missing task.md (Critical Gap), missing requirement.md (Critical Gap), both missing (single Critical Gap), no prescriptions (Observation). All paths defined. |
| 6. Concurrency | PASS | Pipeline is strictly sequential: /design → /dryrun-design → /implement. No shared mutable state between concurrent actors. |
| 7. Edge Cases | PASS | Empty table, body-only prescriptions, glob patterns, no-prescriptions designs — all handled. /implement without skeleton falls back to original behavior (additive change). |
| 8. Task Alignment | SKIPPED | task.md does not exist (O1). Expected at this stage. |

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 0        | 1        | 5            |

**Verdict**: **PASS WITH WARNINGS**

The design is materially improved from round 1. Both prior critical issues (C1: deadlock, W1: column ambiguity) are resolved. The dual-axis Pass 9 algorithm is internally consistent and traces to all relevant ACs. Sections 7 and 8 form a coherent producer-consumer contract. The single warning (W1: requirement-ref derivation) is a minor specification gap that does not affect traceability correctness — it affects human-audit quality of skeleton items when the AC Trace column is absent.

Ready for implementation after addressing W1 or accepting the gap.
