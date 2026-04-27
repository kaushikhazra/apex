# Design Dry-Run Report #1

**Document**: `.claude/specs/dryrun-design-traceability/design.md`
**Reviewed**: 2026-04-25

---

## Critical Gaps (must fix before implementation)

### [C1] Pass 9 assumes task.md exists at dryrun-design time, but standard workflow creates it later
- **Pass**: Pass 7 (Edge Cases & Boundaries)
- **What**: The Error Handling section (design.md § "Missing task.md or requirement.md") states that task.md being missing is "unlikely" because "Pass 8 (Task Spec Alignment) would have already flagged missing task.md." Both claims are incorrect:
  1. **Workflow timing**: The standard spec-driven workflow is: `/requirement` → `/design` → `/dryrun-design` → `/implement`. The `/implement` skill "writes task.md upfront" — meaning task.md does **not** exist when `/dryrun-design` runs. This makes the "unlikely" scenario the **default** scenario.
  2. **Pass 8 behavior**: Pass 8 in SKILL.md (line 75) is conditional — `(if task.md exists)` — and silently skips when task.md is absent. It does **not** flag the absence. The design's claim that Pass 8 "would have already flagged missing task.md" is factually wrong about current SKILL.md behavior.
  
  As currently designed, Pass 9's Error Handling would fire on **every** first-run `/dryrun-design`, reporting all prescriptions as Critical Gaps (no task matches). Per the Verdict Impact rule (design.md § "Verdict Impact"), this blocks PASS verdict. The design becomes unapproved → `/implement` never runs → task.md can never be created → **deadlock**.
- **Risk**: Workflow deadlock. Pass 9 is unusable in the standard first-run review flow. Reviewers either bypass Pass 9 (defeating its purpose) or the workflow stalls indefinitely.
- **Fix**: Add a conditional clause to the Pass 9 algorithm: when task.md does not exist, **skip the task-axis matching** and emit an Observation: "task.md does not exist — task-axis traceability deferred to post-/implement re-run." The AC-axis matching against requirement.md still runs normally and reports gaps as Critical. This preserves the primary value (catching missing ACs at design time) while deferring the task check to when task.md exists. Update the Error Handling section to reflect this behavior and remove the incorrect "unlikely" claim and the incorrect assertion about Pass 8.

---

## Warnings (should fix, may cause issues)

### [W1] Files Changed table column count ambiguity
- **Pass**: Pass 3 (Interface Contract Validation)
- **What**: The algorithm (design.md § "Step 1: Parse the Files Changed Table") says "extract the file path and change description" from each row — implicitly columns 1 and 2. The Error Handling section's malformed-table suggested fix says "Fix the table format (two columns: File, Change)" — implying exactly two columns is the valid format. However, the design's **own** Files Changed table has **three** columns (`File | Change | AC Trace`), using the extra column for inline self-dogfood traceability.
- **Risk**: A strict implementation of the malformed-table check could flag designs with supplementary columns (including this design itself) as malformed. Low severity — the algorithm naturally handles extra columns (extracts first two, ignores rest) — but the Error Handling wording creates ambiguity about what constitutes "malformed."
- **Suggestion**: Clarify that the canonical Files Changed format requires **at least** two columns (File, Change). Extra columns are permitted and ignored by the parser. Update the malformed-table suggested fix from "two columns: File, Change" to "at least two columns, starting with File and Change."

---

## Observations (worth discussing)

### [O1] Tier 2 description matching is inherently subjective
The Tier 2 fallback heuristic (design.md § "Tier 2: Description-Based Matching") requires the reviewing agent to judge whether a task/AC "describes the same logical change" as a prescription. The conservative default ("treat ambiguous as unmatched") mitigates false negatives, and D1's rationale explicitly acknowledges this trade-off. Two different reviewing agents may still reach different conclusions on borderline cases. This is acceptable for a review gate — human reviewers also apply judgment — but worth noting that Pass 9 results may vary across runs on the same design.

### [O2] All 14 ACs covered — no requirement gaps, no scope creep
Pass 1 traced all 14 ACs to specific design sections:

| AC | Design Coverage |
|----|----------------|
| AC-1.1 | § "Step 1: Parse the Files Changed Table" |
| AC-1.2 | § "Step 3: Match Each Prescription Against task.md and requirement.md" — Tier 1 + Tier 2 task search |
| AC-1.3 | § "Step 3" — Tier 1 + Tier 2 AC search |
| AC-1.4 | § "Step 4: Classify Each Prescription" — No/No row → Critical Gap |
| AC-1.5 | § "Step 4" — Yes/No and No/Yes rows → Critical Gap; reinforced by D5 |
| AC-2.1 | § "Step 2: Scan Body Sections" + § "Body Prescription Detection Rules" (Section 6) |
| AC-2.2 | § "Step 3" — "from Step 1 or Step 2" applies same heuristic |
| AC-2.3 | § "Gap Reporting Format" (Section 4) — `Body section '{section_heading}'` source attribution |
| AC-3.1 | § "Gap Reporting Format" — `[C{N}]` numbering in Critical Gaps section |
| AC-3.2 | § "Gap Reporting Format" — template includes file path, missing links, suggested fix |
| AC-3.3 | § "Verdict Impact" — any Critical Gap → FAIL |
| AC-4.1 | § "Traceability Matrix Format" (Section 5) — three-column summary table |
| AC-4.2 | § "Traceability Matrix Format" — dedicated `#### Traceability Matrix` heading |
| AC-4.3 | § "When No Prescriptions Exist" — Observation, not a gap |
| AC-5.1 | § "Pass Positioning and Integration" (Section 1) — separate Pass 9 |
| AC-5.2 | § Section 1 — `### Pass 9:` heading, numbered consistently |
| AC-5.3 | § Section 1 + § "Step 1" + § "Step 2" — explicit Files Changed + body scan references |
| AC-5.4 | § Section 1 + D4 — appended after Pass 8, no existing pass text modified |

The design's self-dogfood section independently confirms 1 file prescription → 14 ACs. No design elements were found without corresponding requirements. Decisions D1–D7 all trace to ACs or Open Question resolutions.

### [O3] Recursive validation: this design introduces the pass it cannot yet be reviewed by
This is a meta-observation about the spec's self-referential nature. The design adds Pass 9 to `/dryrun-design`, but the current SKILL.md only has Passes 1–8. This dry-run therefore cannot apply Pass 9 to validate the design's own Files Changed traceability. The self-dogfood section in the design compensates by manually performing the traceability check — and it's correct (1 prescription, 14/14 ACs traced). Once Pass 9 is implemented, future designs (including any revisions to this one) will benefit from the automated check.

---

## Pass-by-Pass Notes

### Pass 1: Completeness Check
- **14/14 ACs** covered by specific design sections (see O2 matrix above).
- **0 scope creep**: All design elements (D1–D7, Sections 1–6, Error Handling, Future Work) trace to requirements or are defensive design (Error Handling) / explicit out-of-scope declarations (Future Work).
- **Open Questions resolved**: All 3 Open Questions from requirement.md are resolved — D1 (matching heuristic), D2 (body detection scope), D3 (/design skill separation).

### Pass 2: Data Flow Trace
- **Source → Transform → Destination** is well-defined:
  - `design.md` → Step 1 (parse table) + Step 2 (scan body) → prescription list
  - `task.md` + `requirement.md` → Step 3 (matching heuristic) → match results
  - Match results → Step 4 (classification) → Traced / Critical Gap
  - Classifications → Step 5 (emit output) → report entries (gaps or matrix)
- No orphan data: every piece created in Steps 1–2 is consumed in Steps 3–4 and rendered in Step 5.
- Schemas are defined: Files Changed table format (Section 2), Gap format (Section 4), Matrix format (Section 5).

### Pass 3: Interface Contract Validation
- **Agent ↔ design.md**: Files Changed table parsing is defined (Section 2, Step 1). Column extraction (file path, change description) is clear. Extra columns handled implicitly but not explicitly (→ W1).
- **Agent ↔ task.md / requirement.md**: Matching heuristic (Section 3) defines the contract. Conservative default handles ambiguity.
- **Pass 9 ↔ Passes 1–8**: `[C{N}]` counter sharing is documented (Section 4). Sequential execution by a single agent makes this a bookkeeping note, not an interface risk.
- **Contract violation handling**: Malformed table → Warning (Error Handling). Missing files → Critical Gap or skip (Error Handling). Ambiguous match → conservative unmatched (Section 3).

### Pass 4: State Machine & Transitions
- No persistent state machines. Pass 9 is a single-pass pipeline: parse → scan → match → classify → emit.
- Prescription lifecycle is linear: created in Steps 1–2, matched in Step 3, classified in Step 4, rendered in Step 5. No cycles, no unreachable states, no state disagreements.

### Pass 5: Failure Path Analysis
- **Files Changed table absent**: Handled — proceed to body scan (Step 1). ✓
- **Neither table nor body prescriptions**: Handled — Observation per Section 5. ✓
- **Malformed table**: Handled — Warning (Error Handling). ✓
- **Missing task.md**: Handled — but with workflow issues (→ C1). ⚠
- **Missing requirement.md**: Handled — Critical Gaps (Error Handling). ✓
- **Both missing**: Handled — single summary Critical Gap (Error Handling). ✓
- **Ambiguous match**: Handled — conservative default, treat as unmatched (Section 3). ✓
- **Single point of failure**: Pass 9 is a review gate, not a service — no SPOF concept applies.

### Pass 6: Concurrency & Ordering
- Single-agent, sequential execution. No concurrency. No shared mutable resources.
- Pass ordering (after Pass 8) is documented with rationale (Section 1). The dependency is logical (Pass 8 validates task→design, Pass 9 validates design→task), not data-flow — Pass 9 does not consume Pass 8's output.

### Pass 7: Edge Cases & Boundaries
- **Empty Files Changed table** (header, no data rows): Covered by malformed-table Warning ("no rows"). ✓
- **No body prescriptions**: Covered by Step 2 → falls through to Step 5 Observation. ✓
- **Prescription in both table and body**: Body scan excludes Files Changed entries (Section 6, Exclusions — "do not double-count"). ✓
- **Glob patterns in table**: Tier 1 Rule 3 (directory/glob match) handles this. ✓
- **Paths in code blocks**: Section 6, Category A detects these. ✓
- **First run with Pass 9**: Self-contained, no initialization dependency. ✓
- **task.md absent at review time**: → C1 (workflow deadlock). ⚠

### Pass 8: Task Spec Alignment
- **task.md does not exist** — pass skipped per SKILL.md conditional `(if task.md exists)`.
- This is expected: task.md is created by `/implement`, which runs after `/dryrun-design`.

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 1        | 1        | 3            |

**Verdict**: FAIL — needs revision

**C1 must be resolved before implementation.** The task.md workflow timing issue would make Pass 9 produce false Critical Gaps on every first-run `/dryrun-design`, creating a deadlock where the design can't be approved (no task.md → all prescriptions are untraced → FAIL verdict) and task.md can't be created (design not approved → /implement never runs). The fix is well-scoped: make the task-axis check conditional on task.md existing, correct the factual claims about Pass 8 behavior, and let the AC-axis check carry the first-run review.
