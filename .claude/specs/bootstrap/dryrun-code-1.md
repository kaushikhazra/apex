# Code Dry-Run Report #1

**Scope**: `C:/Projects/APEX/sdlc/spec-enhanced/skills/bootstrap/SKILL.md` (404 lines, 24.2 KB)
**Design**: `C:/Projects/APEX/.claude/specs/bootstrap/design.md` (582 lines, 32.1 KB — PASSED dryrun-design-2)
**Reviewed**: 2026-06-09

---

## Bugs (will cause incorrect behavior)

_None found._

---

## Gaps (missing implementation)

### [G1] Validation field format undefined for diff-protect case

- **File**: `SKILL.md:371`
- **Pass**: Pass 2 — Execution Path Trace
- **What**: The terminal summary template (line 371) defines three Validation field formats:
  - `PASS`
  - `FAIL — \`{command}\`: exit {code}`
  - `SKIPPED (--force-skip-validation)`

  The diff-protect path (Step 5, lines 260–264) sets `validation_status = "FAIL (diff-protect)"` and proceeds to Step 8. There is no command and no exit code — validation was never attempted. The template provides no format for rendering the Validation field in this case. A fresh agent would need to improvise.
- **Design ref**: D7 terminal summary (design lines 396–407) — same gap. The design template also only shows two FAIL/PASS/SKIP options with no diff-protect variant.
- **Fix**: Add a fourth Validation format to the template and the status-mapping table:
  ```
  | diff-protect triggered | FAILED | not attempted — conventions differ | Re-run with --force to overwrite |
  ```

---

## Warnings (potential issues)

### [W1] Design-implementation drift — Node and Go default tables

- **File**: `SKILL.md:149–175`
- **Pass**: Pass 1 — Design Conformance
- **What**: SKILL.md includes complete stack-specific defaults tables for **Node** (lines 149–161, 9 convention rows) and **Go** (lines 163–175, 9 convention rows). The design document (D4, section 4) specifies only Python defaults. Design "Future Work" (design line 576) explicitly states: _"Multi-language defaults beyond Python — Node, Go, Rust default tables are deferred. The detection algorithm handles them (D2), but the defaults table (D4) only has Python values populated. Other stacks will use minimal placeholder defaults until their tables are authored."_
- **Risk**: A future maintainer reading design.md would believe Node/Go stacks use "minimal placeholder defaults" when the implementation provides full tables. If the design is updated independently (e.g., to add Rust defaults), the existing Node/Go tables might be missed or duplicated. The implementation is strictly *better* than the design specifies, but the documents are out of sync.
- **Fix**: Update design.md section 4 (D4) to include the Node and Go defaults tables, and remove the "Multi-language defaults beyond Python" bullet from the "Future Work" section. This makes the design match the shipped implementation.

### [W2] Status-mapping table ambiguity — diff-protect vs identical-no-change

- **File**: `SKILL.md:376–384`
- **Pass**: Pass 2 — Execution Path Trace
- **What**: The Step 8 status-mapping table has five rows. Two of them can match simultaneously when diff-protect fires:

  | Row | Condition | Summary Status |
  |-----|-----------|---------------|
  | 2 | `claude_md_action == "no changes"` (identical, no re-run) | **SUCCESS** |
  | 5 | diff-protect triggered (no --force, content differs) | **FAILED** |

  The diff-protect path (Step 5, line 263) sets `claude_md_action = "no changes"` AND `validation_status = "FAIL (diff-protect)"`. Row 2's condition checks only `claude_md_action == "no changes"` — its parenthetical "(identical, no re-run)" is a prose comment, not part of the machine-evaluable condition. A fresh agent doing top-to-bottom evaluation hits row 2 first → outputs **SUCCESS** for a case that should be **FAILED** (exit 1).

  In the identical case (Step 5, line 255–257), `claude_md_action` is also `"no changes"` but `validation_status` is never set — leaving it undefined. The only distinguishing signal is `validation_status`, but row 2 doesn't check it.
- **Risk**: Incorrect terminal summary status (SUCCESS instead of FAILED) on the diff-protect path. The exit code (1) would still be correct because Step 5 hardcodes it, but the summary box would show a contradictory SUCCESS label.
- **Fix**: Make row 2's condition unambiguous by adding a guard:
  ```
  | `claude_md_action == "no changes"` AND `validation_status` is unset | SUCCESS | ... |
  ```
  Or reorder the table so row 5 (diff-protect) is evaluated before row 2. Or give diff-protect a distinct `claude_md_action` value (e.g., `"blocked (diff-protect)"`).

---

## Style (code quality, conventions)

### [S1] Horizontal rules between process steps — inconsistent with other e-spec skills

- **File**: `SKILL.md:45,77,127,223,280,305,358`
- **What**: SKILL.md uses `---` (horizontal rules) between each Process step. The three reference skills (`spec/SKILL.md`, `design/SKILL.md`, `implement/SKILL.md`) do not use horizontal rules between steps — they rely on heading hierarchy alone for visual separation. This is a minor structural style deviation.

---

## Summary

| Category | Count |
|----------|-------|
| Bugs | 0 |
| Gaps | 1 |
| Warnings | 2 |
| Style | 1 |

**Verdict**: **FAIL** — zero bugs, but 1 gap (G1: diff-protect Validation field format undefined), 2 warnings (W1: design drift on Node/Go defaults, W2: status-mapping ambiguity for diff-protect), and 1 style deviation (S1: horizontal rules). Per pass criterion (zero findings of any category), this does not meet the bar.

### Pass-by-Pass Coverage

| Pass | Result | Notes |
|------|--------|-------|
| 1. Design Conformance | G1, W1 found | D1–D8 mechanically walked. D1 frontmatter exact ✓. D2 detection table complete (pyproject.toml, setup.py, setup.cfg, requirements.txt, package.json, go.mod) ✓. D3 two globs + dedup ✓. D4 10 rows + fenced markers ✓ — but Node/Go defaults undocumented (W1). D5 `<br>` case-insensitive + backtick stripping ✓. D6 five branches + PRE-COMPARISON before identity ✓. D7 exit codes 0/1 only ✓ — but Validation format gap (G1). D8 eight-step linear ✓. |
| 2. Execution Path Trace | W2 found | Happy path (auto-detect → compose → create → validate → summary) traces cleanly. Diff-protect path hits status-mapping ambiguity (W2). Recovery path (crash → pre-flight FAILED → re-run → PRE-COMPARISON → re-validate) traces correctly. SKIP_WRITE path traces correctly. |
| 3. Error Path Trace | Clean | Unknown flag → exit 1 ✓. No markers + no args → exit 1 ✓. Blueprint dir inaccessible → WARNING + continue ✓. Post-write verification failure → exit 1 ✓. Bash command failure → update Validated line + print stderr + exit 1 ✓. Timeout → exit code 124 ✓. |
| 4. Input Validation | Clean | Unrecognized flags rejected ✓. Unknown language values accepted (no hard rejection) ✓. Missing language + no markers → actionable error ✓. |
| 5. Resource Management | N/A | SKILL.md is instruction text, not runtime code. No file handles or connections to manage. |
| 6. Concurrency | N/A | Single-agent, single-pass skill. No concurrency. |
| 7. Contract Violations | Clean | Tool contracts (Read, Write, Edit, Bash, Glob, Grep) used correctly per their documented interfaces. No Task tool (correctly excluded). No WebSearch/WebFetch (correctly excluded). |
| 8. Code Quality | S1 found | Self-contained (no design.md references) ✓. Rules section comprehensive ✓. Horizontal-rule style deviation (S1). |
| 9. Security | N/A | No user input reaches shell unsanitized — build commands come from the skill's own conventions table, not from external input. |

### Specific Checks (per review brief)

| Check | Result |
|-------|--------|
| Frontmatter: name, description, argument-hint, allowed-tools = `Read, Grep, Glob, Write, Edit, Bash` (no Task) | ✓ Exact match (lines 1–6) |
| Conventions table: 10 rows, fenced markers, parseable by D5 | ✓ (lines 194–211) |
| PRE-COMPARISON branch present, ordered before identity comparison | ✓ (lines 240–249, before lines 254–269) |
| `<br>` delimiter: case-insensitive (`<br>`, `<br/>`, `<BR/>`, `<BR>`) | ✓ (line 319) |
| Backtick stripping: single + triple backtick | ✓ (lines 320–323) |
| Stack detection: Python (pyproject.toml, setup.py, setup.cfg, requirements.txt) + Node (package.json) + Go (go.mod) | ✓ (lines 54–63) |
| Out-of-scope languages NOT auto-detected | ✓ (line 49: "v1.0 scope: Python, Node, Go only") |
| Blueprint discovery: TWO source globs, dedup rule | ✓ Primary non-recursive (line 85), secondary recursive (line 86), dedup by slug primary wins (line 98) |
| Exit codes: 0 and 1 only | ✓ (lines 386–389) |
| Terminal summary: 5 fields | ✓ Detected stack, Blueprints, CLAUDE.md, Validation, Next step (lines 362–374) |
| Idempotency: 5 branches | ✓ CREATE, APPEND, PRE-COMPARISON (with sub-branches), terminal+identical, terminal+differs±force (lines 230–269) |
| Recovery trace (crash → re-run) | ✓ Documented in Rules section (line 402) |
| Self-containment (no design.md references) | ✓ No references to design.md found in SKILL.md |
