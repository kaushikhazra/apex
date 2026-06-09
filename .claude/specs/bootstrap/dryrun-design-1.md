# Design Dry-Run Report #1

**Document**: C:/Projects/APEX/.claude/specs/bootstrap/design.md
**Reviewed**: 2026-06-09

---

## Critical Gaps (must fix before implementation)

### [C1] Validation crash → `Validated: PENDING` orphan + idempotency blocks recovery

- **Pass**: Pass 5 (Failure Path Analysis)
- **What**: Two reinforcing gaps create an irrecoverable state through normal tool failure:
  - **(a) PENDING is not a terminal state.** D4 (lines 186–191) defines three valid Validated states: `{YYYY-MM-DD} — build + install clean`, `FAILED — {command} exited {code}`, and `SKIPPED (--force-skip-validation)`. But D8 Step 4 writes `Validated: PENDING` as a placeholder before the conventions block is committed to CLAUDE.md. If the Bash tool crashes or times out during D5 validation (not a clean non-zero exit but a tool-level failure), `Validated: PENDING` persists — an undefined fourth state with no specified downstream behavior.
  - **(b) Idempotency comparison silently swallows the crash.** D6 identity comparison (line 307) strips the `Validated:` line from both sides before diffing. On re-run after a crash, the skill sees "identical content" → exits 0 with "Already bootstrapped — conventions unchanged." Even `--force` doesn't help: BST-4 AC explicitly states that identical content + `--force` still exits 0 without re-validation. The user receives a success signal but validation has never run. The **only** escape is manually editing CLAUDE.md to force a content diff.
- **Risk**: A routine Bash tool timeout (>120 s) or tool-level error during `pip install -e .[dev]` leaves CLAUDE.md in a state where validation can never be triggered through the skill's own interface. The project appears bootstrapped but the build may be broken — exactly the class of failure bootstrap was designed to prevent (per the Aakriti incident in the Overview).
- **Fix**: Two changes:
  1. Write `Validated: FAILED — validation did not complete (pre-flight)` as the **default** in D8 Step 4, before executing any commands. Update to PASS only after all commands succeed. This ensures FAILED is the safe default, not PENDING.
  2. In D6 identity comparison, when the existing block's Validated line reads anything other than the three defined terminal states (or reads `FAILED`), treat the content as **different** regardless of body identity — forcing re-validation on re-run.

---

## Warnings (should fix, may cause issues)

### [W1] Blueprint discovery scans only `.claude/blueprints/`; second APEX blueprint directory invisible

- **Pass**: Pass 2 (Data Flow Trace)
- **What**: D3 (line 123) globs `C:/Projects/APEX/.claude/blueprints/*/readme.md` exclusively. APEX has a second blueprint directory at `C:/Projects/APEX/blueprints/` containing `multi-agent/readme.md` and `web-ui-design-systems/readme.md`. These blueprints are unreachable by bootstrap. BST-5 AC also scopes to `.claude/blueprints/` only, so the design is consistent with the requirement — but D3's opening statement ("Enumerate all blueprints under `C:/Projects/APEX/.claude/blueprints/`", line 114) creates a scoping claim that is accurate for its own path but not for APEX as a whole.
- **Risk**: Future blueprints placed under `blueprints/` (outside `.claude/`) — or existing ones like `multi-agent` that become relevant to new project types — will never be discovered. A project that should match a `blueprints/`-resident blueprint gets no blueprint ref, and the absence is silent (no warning).
- **Suggestion**: Either (a) add a second glob `C:/Projects/APEX/blueprints/*/readme.md` to D3 discovery and extend the matching rules table, or (b) add an explicit design note: "Only `.claude/blueprints/` is scanned. Blueprints under `blueprints/` (e.g., `multi-agent`, `web-ui-design-systems`) are out of scope for bootstrap discovery." Option (b) at minimum documents the exclusion.

### [W2] ` then ` command delimiter has no escape mechanism and no collision guard

- **Pass**: Pass 7 (Edge Cases & Boundaries)
- **What**: D5 (line 233) splits the Build+install row on the literal string ` then ` (space-then-space). No escaping or quoting mechanism is defined. If a build command legitimately contains ` then ` — unlikely for typical `pip install` / `npm install` commands but possible in shell one-liners (e.g., `echo "build then verify" && make`) — the command would be mis-split into two fragments that individually fail.
- **Risk**: Mis-parsed commands produce confusing validation errors ("command not found: verify && make") that don't point to the real problem (a delimiter collision). The failure would be intermittent, appearing only for unusual command strings.
- **Suggestion**: Either (a) document ` then ` as a reserved delimiter with a constraint: "Build commands must not contain the literal string ` then ` — use `&&` for chaining within a single command", or (b) switch to a less ambiguous separator (e.g., ordered list entries `1. {cmd}` / `2. {cmd}` instead of inline ` then `).

---

## Observations (worth discussing)

### [O1] Build command extraction does not specify backtick stripping from markdown inline code

- **Pass**: Pass 2 (Data Flow Trace)
- The conventions template (D4, line 177) wraps each command in backticks: `` `{exact command 1}` then `{exact command 2}` ``. D5 step 2 splits on ` then `, yielding fragments like `` `pip install -e .[dev]` `` — still backtick-wrapped. D5 step 3 says "Each command is a verbatim shell string to execute", but the extracted string is a markdown-formatted code span, not a verbatim shell string. The backtick-stripping step is implied but not specified. Since SKILL.md is executed by an LLM agent (which will naturally strip formatting), this is unlikely to cause a real failure — but the specification is technically incomplete and could mislead a programmatic implementer.

### [O2] Rust (`Cargo.toml`) absent from D2 stack detection heuristic table

- **Pass**: Pass 1 (Completeness Check)
- The D2 detection priority table (lines 56–65) covers Python (4 marker files), Node (1), and Go (1). Rust (`Cargo.toml` / `Cargo.lock`) has no entry. BST-1 AC explicitly lists only Python/Node/Go markers, so the design faithfully implements the stated requirement — there is no design-vs-requirement gap. However, if the intended detection scope includes Rust alongside the other three, both the requirement's BST-1 AC and the design's D2 table would need a `Cargo.toml → Rust, "library"` row and an entry in the D4 stack-specific defaults (even if minimal placeholder defaults, consistent with Node/Go's current treatment).

---

## Pass-by-Pass Summary

### Pass 1: Completeness Check
- All 7 user stories (BST-1 through BST-7) have corresponding design elements (D1–D8).
- No design elements lack a corresponding requirement (no scope creep detected).
- **Gap found**: O2 — Rust absent from detection table (requirement-level, not design-level).

### Pass 2: Data Flow Trace
- Stack detection result (D2) → blueprint matching (D3) → conventions composition (D4) → CLAUDE.md write (D6) → command extraction (D5): data flow is complete and traceable.
- **Gap found**: W1 — second blueprint directory invisible. O1 — backtick stripping unspecified in command extraction path.

### Pass 3: Interface Contract Validation
- Single-agent skill with no cross-component boundaries beyond tool calls (Bash, Read, Write, Edit, Glob, Grep). Tool contracts are implicit via the e-spec platform. No custom interfaces to validate.
- The fenced-block contract (`<!-- bootstrap-conventions -->` / `<!-- /bootstrap-conventions -->`) between bootstrap and downstream agents is well-defined (D4, D6).
- **No gaps found.**

### Pass 4: State Machine & Transitions
- D6 decision tree defines 5 exhaustive branches for CLAUDE.md state (absent, present-no-marker, present-identical, present-differs-no-force, present-differs-force). All branches have defined exits.
- Validation lifecycle has 4 states: PENDING → {PASS, FAILED, SKIPPED}. All transitions are defined.
- **Gap found**: C1(a) — PENDING is not a terminal state but can persist as one after a crash.

### Pass 5: Failure Path Analysis
- Argument errors: handled (exit 1 with message).
- No stack detected: handled (exit 1 with message).
- Blueprint directory inaccessible: handled (WARNING, continue).
- File I/O errors: handled (exit 1 with exact error).
- Validation command failure: handled (update Validated to FAILED, exit 1).
- **Gap found**: C1(b) — tool-level crash during validation has no recovery path. Re-run triggers idempotency exit-0, silently bypassing validation.

### Pass 6: Concurrency & Ordering
- Single-agent, strictly sequential (D8: 8 linear steps). No concurrency. No shared mutable state. No race conditions possible.
- **No gaps found.**

### Pass 7: Edge Cases & Boundaries
- Empty project (no stack markers, no args): handled (exit 1).
- Empty blueprint directory: handled (WARNING, continue).
- First run (no CLAUDE.md): handled (create new file).
- Re-run (identical content): handled (exit 0, no-op).
- **Gap found**: W2 — ` then ` delimiter collision in unusual command strings.

### Pass 8: Task Spec Alignment
- task.md has one task: "**Implementer** creates `sdlc/spec-enhanced/skills/bootstrap/SKILL.md`" — actor (Implementer), action (creates), target (SKILL.md). Requirement refs: BST-1..BST-7. ✓
- Single-file implementation makes one task appropriate. Files Changed table also has one row.
- **No gaps found.**

### Pass 9: Design-to-Task-to-AC Traceability

#### Files Changed Table

| File | Change | AC Trace |
|------|--------|----------|
| `sdlc/spec-enhanced/skills/bootstrap/SKILL.md` | New file — complete bootstrap skill | BST-1, BST-2, BST-3, BST-4, BST-5, BST-6, BST-7 |

#### Body Prescriptions Scan

Scanned all design sections outside the Files Changed table for Category A/B/C prescriptions:

- **D1 (line 20)**: References `C:/Projects/APEX/sdlc/spec-enhanced/skills/bootstrap/SKILL.md` — same file as Files Changed row. No double-count.
- **D3 (line 123)**: References `C:/Projects/APEX/.claude/blueprints/*/readme.md` — runtime read target, not a file changed by implementation.
- **D4 (lines 163–181)**: Template block showing `CLAUDE.md` content — runtime output, not implementation artifact.
- **D1 (line 40)**: References `spec/SKILL.md`, `design/SKILL.md`, `implement/SKILL.md` — existing pattern references, not files being modified.
- **Cross-Cutting (line 519)**: References `sdlc/spec-enhanced/skills/bootstrap/` — same directory as the Files Changed file.

No body prescriptions found that are untraced.

#### Traceability Matrix

| File/Prescription | Task Reference | AC Reference |
|-------------------|---------------|--------------|
| `sdlc/spec-enhanced/skills/bootstrap/SKILL.md` — New file: complete bootstrap skill | task.md line 3: "Implementer creates `sdlc/spec-enhanced/skills/bootstrap/SKILL.md`" | BST-1, BST-2, BST-3, BST-4, BST-5, BST-6, BST-7 |

**Result**: All 1 file-level prescription traced to task and ACs. No traceability gaps.

---

## Summary

| Critical | Warnings | Observations |
|----------|----------|--------------|
| 1        | 2        | 2            |

**Verdict**: FAIL — needs revision

The single Critical gap (C1) is a compounding failure: a routine tool crash during validation creates an irrecoverable state where re-running the skill silently exits with success but validation has never completed. This directly undermines the skill's core purpose (catching build failures before spec work). The fix is surgical — change the default Validated state from PENDING to a pre-flight FAILED, and make the idempotency check treat non-terminal validation states as "content differs."
