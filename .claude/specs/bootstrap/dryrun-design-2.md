# Design Dry-Run Report #2

**Document**: C:/Projects/APEX/.claude/specs/bootstrap/design.md
**Reviewed**: 2026-06-09
**Prior report**: dryrun-design-1.md (5 findings: 1C, 2W, 2O)
**Fix applied**: Worker 7c9b1d1f — surgical edits addressing all 5 findings

---

## Findings

None.

---

## Fix Verification — All 5 Prior Findings

### C1: Validation crash recovery — VERIFIED FIXED

**Pre-flight default**: D8 Step 4 (line 450) now writes `Validated: FAILED — validation did not complete (pre-flight)` before any commands execute. A crash at any point during D5 validation leaves this FAILED state in CLAUDE.md — never an undefined "PENDING" state.

**Pre-comparison branch ordering**: D6 decision tree (lines 309–318) places the `[PRE-COMPARISON]` branch BEFORE the identity comparison branches (lines 320–334). This is critical — if identity comparison ran first, it would strip the Validated line and exit 0 on matching content, bypassing re-validation. The ordering is correct.

**Full recovery trace verified**:
1. Bootstrap runs → D8 Step 4 writes `Validated: FAILED — validation did not complete (pre-flight)`
2. Crash during D5 (tool timeout, Bash failure, etc.)
3. CLAUDE.md left with non-terminal `FAILED` Validated line
4. User re-runs `/e-spec:bootstrap` (no flags needed)
5. D6 PRE-COMPARISON branch (line 309) detects non-terminal Validated → forces re-validation unconditionally
6. `--force` flag and content identity are both irrelevant — re-validation happens regardless
7. Validation completes → Validated line updated to PASS, FAILED, or SKIP

**Terminal vs non-terminal state definitions** (lines 312–313) are precise and exhaustive:
- Terminal: date-prefixed `… — build + install clean`, `SKIPPED (--force-skip-validation)…`
- Non-terminal: `FAILED …` (any form), `PENDING`, any unrecognized state

The "PENDING" reference on line 311 is correct — it appears only in the non-terminal detection list, ensuring backward compatibility if someone manually set that state. The skill itself never writes PENDING.

**Verdict**: Irrecoverable state eliminated. Recovery requires only a plain re-run.

### W1: Dual blueprint directory discovery — VERIFIED FIXED

**D3 discovery** (lines 130–139) now documents both glob paths:
- Primary: `C:/Projects/APEX/.claude/blueprints/*/readme.md` (non-recursive)
- Secondary: `C:/Projects/APEX/blueprints/**/readme.md` (recursive)

**Dedup rule** (lines 138–139): slug collision → primary wins. Unambiguous.

**D8 Step 3** (lines 436–437) mirrors both globs. **Decisions Log D3** (line 9) explicitly says "TWO sources."

**Error handling** (lines 142–144): each directory failing independently produces a WARNING, not a fatal error. Both failing → empty list + WARNING.

**Verdict**: No single-source references remain anywhere in the design.

### W2: `<br>` command delimiter — VERIFIED FIXED

**D4 template** (line 191): commands separated by `<br>`. **D5 step 2** (line 246): split on `<br>` (case-insensitive: `<br>`, `<br/>`, `<BR/>`). **Rationale** (line 253) explicitly documents why `<br>` over ` then `.

**Edge case — command containing literal `<br>`**: Theoretically possible (e.g., `echo "<br>"`), but no real-world build/install command contains HTML tags. The risk is orders of magnitude lower than ` then ` appearing in shell one-liners. Acceptable scope-narrowing — not a finding.

**Consistency sweep**: No residual ` then ` delimiter usage. All three ` then ` hits in the file are natural English (line 251: describing output; line 253: rationale context; line 405: terminal summary text).

**Verdict**: Delimiter collision risk reduced to negligible.

### O1: Backtick stripping — VERIFIED FIXED

**D5 step 3** (line 247): "Strip surrounding backticks (`` ` ``) and triple-backtick fences from each extracted line before execution." Explicit example provided: `` `pip install -e .[dev]` `` → `pip install -e .[dev]`.

Both single-backtick (inline code) and triple-backtick (fenced code block) cases are covered.

**Verdict**: Specification gap closed.

### O2: Detection scope statement — VERIFIED FIXED

**D2 preamble** (lines 53–54): "**v1.0 scope: Python, Node, Go only.** Auto-detection covers these three languages. Other languages (Rust, Ruby, Java, etc.) have no marker entries and will not be auto-detected — callers must supply `--language` explicitly."

Statement is bold, positioned immediately before the detection table, and explicitly names Rust as deferred. Future readers encounter the scope constraint before reading the table.

**Verdict**: Scope documented at point of use.

---

## Consistency Sweep

Checked for residual artifacts from pre-fix1 design:

| Pattern | Hits | Assessment |
|---------|------|------------|
| `PENDING` (as written state) | 0 | Line 311 references PENDING only in the non-terminal detection list — correct usage. Skill never writes PENDING. |
| ` then ` (as delimiter) | 0 | Three hits are all natural English or rationale text. No active delimiter usage. |
| Single-source blueprint glob | 0 | All references to blueprint discovery include both primary and secondary paths. |

No consistency issues found.

---

## Pass-by-Pass Summary

### Pass 1: Completeness Check
- All 7 user stories (BST-1 through BST-7) have corresponding design elements (D1–D8).
- No design elements lack a corresponding requirement.
- Detection scope (Python/Node/Go) documented per fix1 O2.
- **No gaps found.**

### Pass 2: Data Flow Trace
- Stack detection (D2) → blueprint matching (D3, dual-source) → conventions composition (D4) → CLAUDE.md write (D6) → command extraction (D5, `<br>` split + backtick strip) → validation → Validated line update.
- Data flow is complete and traceable end-to-end.
- **No gaps found.**

### Pass 3: Interface Contract Validation
- Fenced-block contract (`<!-- bootstrap-conventions -->` / `<!-- /bootstrap-conventions -->`) well-defined.
- Tool interface (Read, Write, Edit, Bash, Glob, Grep) appropriate for all operations.
- Argument interface (D7) matches BST-6 ACs.
- **No gaps found.**

### Pass 4: State Machine & Transitions
- D6 decision tree: 6 exhaustive branches (absent, no-marker, non-terminal-identical, non-terminal-differs, terminal-identical, terminal-differs-no-force, terminal-differs-force). All branches have defined exits.
- Validated lifecycle: pre-flight FAILED → {PASS, FAILED, SKIPPED}. Pre-flight default ensures crash safety.
- Pre-comparison branch correctly prevents identity comparison from swallowing non-terminal states.
- **No gaps found.**

### Pass 5: Failure Path Analysis
- Argument errors: exit 1 with message.
- No stack detected: exit 1 with message.
- Blueprint directories inaccessible: WARNING, continue.
- File I/O errors: exit 1 with exact error.
- Validation command failure: update Validated to FAILED, exit 1.
- Validation crash/timeout: pre-flight FAILED persists → re-run recovers via pre-comparison branch.
- **No gaps found.**

### Pass 6: Concurrency & Ordering
- Single-agent, strictly sequential (D8: 8 linear steps). No concurrency concerns.
- **No gaps found.**

### Pass 7: Edge Cases & Boundaries
- Empty project: handled (exit 1).
- Empty blueprint directories: handled (WARNING, continue).
- First run (no CLAUDE.md): handled (create).
- Re-run identical + terminal: exit 0.
- Re-run identical + non-terminal: force re-validation.
- `<br>` in command argument: negligible risk, acceptable scope-narrowing.
- **No gaps found.**

### Pass 8: Task Spec Alignment
- Single implementation file (`SKILL.md`) matches single task in task.md.
- Actor, action, target all specified. AC refs: BST-1..BST-7.
- **No gaps found.**

### Pass 9: Design-to-Task-to-AC Traceability

#### Files Changed Table

| File | Change | AC Trace |
|------|--------|----------|
| `sdlc/spec-enhanced/skills/bootstrap/SKILL.md` | New file — complete bootstrap skill | BST-1, BST-2, BST-3, BST-4, BST-5, BST-6, BST-7 |

#### Body Prescriptions Scan

All design section references verified:
- D1 (line 20): `SKILL.md` path — same file as Files Changed. No double-count.
- D3 (lines 131–132): Blueprint readme paths — runtime read targets, not implementation artifacts.
- D4 (lines 177–195): `CLAUDE.md` template — runtime output, not implementation artifact.
- Cross-cutting (line 557): `sdlc/spec-enhanced/skills/bootstrap/` — same directory as Files Changed file.

No untraced body prescriptions.

**Result**: All prescriptions traced. No traceability gaps.

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 0        | 0        | 0            |

**Verdict**: PASS

All 5 findings from dryrun-design-1 have been verified fixed. The pre-flight FAILED default + pre-comparison branch ordering eliminates the crash-recovery gap (C1). Dual-source blueprint discovery with unambiguous dedup resolves W1. The `<br>` delimiter, backtick stripping, and detection scope statement close W2, O1, and O2 respectively. Consistency sweep found no residual artifacts from the pre-fix design.
