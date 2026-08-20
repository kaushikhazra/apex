# Dryrun Design Traceability — Design

## Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Two-tier matching heuristic: path-based first, then description-based — no NLP/embedding similarity | The motivating failure (`mobject-layout-coordination`) had explicit file paths in both the design and the task gap. Path matching catches these. Description matching handles cases where task.md says "implement layout coordination" without naming the file. NLP adds false positives and implementation complexity disproportionate to the failure mode. (Resolves Open Question 1 — AC-1.2, AC-1.3) |
| D2 | Body prescription detection is targeted: explicit file paths, glob patterns, and imperative file-change statements only — no exhaustive prose parsing | The `mobject-layout-coordination` failure involved "update existing `.scene` files" — an explicit, parseable reference. Exhaustive NLP scanning of every sentence would flag design rationale prose ("we chose SQLite because...") as false prescriptions. Targeted detection catches the failure class that motivated this spec without drowning the reviewer in noise. (Resolves Open Question 2 — AC-2.1) |
| D3 | `/design` and `/implement` skill changes **are folded into this spec** — not deferred to a separate spec | Open Question 3 was resolved 2026-04-25 (Kaushik): Option 2 chosen. The three skills form a single pipeline (design → dryrun-design → implement). Splitting into separate specs would leave the C1 deadlock unfixed: Pass 9 could not evaluate the Task axis if task.md is not yet created. Folding DDT-6 and DDT-7 into this spec closes the gap at the right architectural layer. (Reverses original D3 decision.) |
| D4 | New pass is Pass 9 — appended after Pass 8, not inserted between existing passes | AC-5.4 requires existing passes are not modified. Appending avoids renumbering, avoids merge conflicts with other specs that reference pass numbers, and reflects the logical dependency: Pass 9 (traceability) builds on Pass 8's task-spec alignment check. |
| D5 | Partial coverage (task found but no AC, or AC found but no task) is a Critical Gap, same as no coverage | AC-1.5 explicitly requires this. Rationale: a task without an AC means the work is done but never verified. An AC without a task means the verification exists but the work is never scheduled. Both are pipeline leaks. |
| D6 | The traceability matrix is emitted inline in the pass output section, not only in the verdict summary | AC-4.2 requires it. The matrix lets the reviewer verify that mappings are *correct*, not just *present* — a task named similarly to a file doesn't guarantee it covers the right change. |
| D7 | When no file-level prescriptions exist, the pass emits an Observation and skips — no gap, no warning | AC-4.3 requires this. Not every design prescribes specific files (e.g., pure architecture decisions). Penalizing their absence would create false negatives on valid designs. |
| D-NEW | Option 2: `/design` produces both `design.md` and `task.md` skeleton in one step; Pass 9 checks both AC axis and Task axis at design-time; `/implement` reads and advances the skeleton rather than authoring it | This closes the C1 deadlock: task.md exists before `/dryrun-design` runs, so Pass 9 can evaluate the Task axis without deferral. Anchoring task authorship to the design's Files Changed table (the only moment when the full file prescription list is available and reviewed) ensures the task list cannot drift from the design. `/implement` operating as a consumer (not author) of task.md makes any task-scope deviation a traceable, flagged event rather than a silent shortcut. |

---

## 1. Pass Positioning and Integration

**What**: Pass 9 is appended to the existing 8-pass sequence in `/dryrun-design` SKILL.md. It is titled "Pass 9: Design-to-Task-to-AC Traceability".

**Why**: AC-5.1 (separate pass), AC-5.2 (own heading, numbered consistently), AC-5.4 (Pass 1 and Pass 8 unmodified).

**How**: The pass is added as a new `### Pass 9:` section after `### Pass 8:` in SKILL.md. No existing pass text is modified. The pass number is hardcoded as 9 — not dynamic — matching the existing convention where passes 1-8 are hardcoded.

**Logical dependency**: Pass 9 runs after Pass 8 (Task Spec Alignment) because Pass 8 validates that tasks reference real design elements. Pass 9 then validates the reverse — that design file prescriptions have tasks AND ACs. Together they close the bidirectional traceability loop.

**Dual-axis check**: Pass 9 checks two independent axes (AC-5.5):
- **AC axis**: every Files Changed entry (and body prescription) maps to ≥1 acceptance criterion in `requirement.md`.
- **Task axis**: every Files Changed entry maps to ≥1 skeleton item in `task.md` (produced by `/design` per Section 7).

Both axes must pass for the "READY" verdict. A gap on either axis alone is sufficient to block the verdict (AC-5.6).

**task.md at dryrun-design time**: Because `/design` now produces `task.md` before `/dryrun-design` runs (DDT-6), `task.md` is **expected to exist** when Pass 9 executes. If it is absent, Pass 9 reports a Critical Gap rather than skipping (AC-5.7). The old "unlikely" framing (from the original Error Handling section) is removed — missing task.md is now the author's error, not an anticipated workflow variant.

---

## 2. Pass 9 Algorithm — Step by Step

**What**: The complete procedure the reviewing agent follows during Pass 9.

**Why**: AC-1.1 through AC-1.5 (Files Changed traceability), AC-2.1 through AC-2.3 (body prescription traceability), AC-5.3 (instructions reference Files Changed table explicitly and body scan), AC-5.5 (dual-axis), AC-5.6 (both axes required for READY), AC-5.7 (missing task.md = Critical Gap).

**How**:

### Step 1: Parse the Files Changed Table

The agent locates the "Files Changed" table in `design.md`. The canonical Files Changed format requires **at least two columns**: `File` (first) and `Change` (second). Extra columns are permitted and ignored by the parser. A table with zero data rows, missing the File column, or unparseable markdown is malformed (see Error Handling).

For each row, extract:
- **File path**: The path or pattern in the first column
- **Change description**: The description in the second column

If no "Files Changed" table exists, proceed to Step 2 (body scan). If neither table nor body prescriptions are found, emit an Observation per Section 5 and end the pass.

_Traces to: AC-1.1_

### Step 2: Scan Body Sections for File-Level Prescriptions

The agent scans all sections of `design.md` **outside** the Files Changed table for prescriptive statements that reference specific files. Detection targets (see Section 6 for full rules):

1. **Explicit file paths** — anything resembling a path with directory separators or file extensions (e.g., `src/layout/coordinator.py`, `config.yaml`)
2. **Glob patterns** — wildcard file references (e.g., `*.scene`, `src/**/*.py`)
3. **Imperative file-change statements** — action verbs + file targets (e.g., "update all `.scene` files", "add a migration to `migrations/`", "modify the schema in `models.py`")

For each detected prescription, extract:
- **Prescription text**: The relevant phrase or sentence
- **Source location**: The section heading where it was found

_Traces to: AC-2.1_

### Step 3: Check Each Prescription on Both Axes

For every prescription (from Step 1 or Step 2), apply both axes independently:

**AC Axis — match against `requirement.md`**:

Apply the two-tier matching heuristic (Section 3):
- **Tier 1 — Path match**: Search `requirement.md` for any AC whose text references the same file path, basename, or describes verification of a change to that file.
- **Tier 2 — Description match** (fallback, only if Tier 1 finds no match): Search `requirement.md` for an AC whose verification scope covers the prescribed change.

**Task Axis — match against `task.md`**:

Apply the same two-tier heuristic:
- **Tier 1 — Path match**: Search `task.md` for any task item containing the same file path, basename, directory, or glob pattern.
- **Tier 2 — Description match** (fallback, only if Tier 1 finds no match): Search `task.md` for a task whose change description semantically covers the same work as the prescription's change description.

The agent applies conservative judgment on both axes: if the match is ambiguous or the task/AC could plausibly refer to different work, it is **not** a match.

_Traces to: AC-1.2 (task match), AC-1.3 (AC match), AC-2.2 (same logic for body prescriptions), AC-5.5 (dual-axis)_

### Step 4: Classify Each Prescription

For each prescription, based on Step 3 results:

| AC Axis | Task Axis | Classification |
|---------|-----------|----------------|
| Yes | Yes | **Traced** — add to traceability matrix |
| Yes | No | **Critical Gap** — verification exists but work never scheduled |
| No | Yes | **Critical Gap** — work scheduled but never verified |
| No | No | **Critical Gap** — prescription is invisible to the pipeline |

_Traces to: AC-1.4 (both missing = Critical Gap), AC-1.5 (partial = Critical Gap), AC-2.3 (body prescriptions same classification), AC-5.6 (either axis gap blocks verdict)_

### Step 5: Emit Output

Based on Step 4 classifications, emit one of three outputs:

- **If any gaps exist**: Emit each as a Critical Gap entry (see Section 4 for format). _Traces to: AC-3.1, AC-3.2_
- **If all prescriptions trace**: Emit the Traceability Matrix (see Section 5 for format). _Traces to: AC-4.1, AC-4.2_
- **If no prescriptions found**: Emit Observation: "No file-level prescriptions found — traceability check skipped." _Traces to: AC-4.3_

---

## 3. Matching Heuristic — Detailed Rules

**What**: The two-tier matching rules the reviewing agent applies when checking if a task.md item or requirement.md AC covers a given file prescription.

**Why**: Open Question 1 resolution (D1). Must be precise enough that two agents reviewing the same design would reach the same conclusion, but flexible enough that reasonable phrasing variations don't create false gaps.

**How**:

### Tier 1: Path-Based Matching

A path match is found when **any** of the following hold:

1. **Exact path**: The task/AC text contains the identical file path string as the prescription (e.g., prescription: `src/layout/coordinator.py`, task: "Implement coordination logic in `src/layout/coordinator.py`").

2. **Basename match**: The task/AC text contains the file's basename (filename without directory) **and** the surrounding context makes clear it refers to the same file (e.g., prescription: `src/layout/coordinator.py`, task: "Update `coordinator.py` with layout rules" — basename matches, context confirms).

3. **Directory/glob match**: The prescription uses a directory or glob pattern, and the task/AC text references the same directory or a file within it (e.g., prescription: `src/scenes/*.scene`, task: "Retrofit all scene files in `src/scenes/`").

**Not a path match**: The task/AC mentions a *different* file in the same directory, or mentions the directory in passing without describing a change to it.

### Tier 2: Description-Based Matching

Used only when Tier 1 produces no match. A description match is found when:

1. The task/AC describes **the same logical change** as the prescription — same component, same modification, same intent — even if no file path is mentioned.
2. The agent can state in one sentence *why* this task/AC covers this prescription, and the statement is not a stretch.

**Not a description match**: The task/AC is in the same *domain* but describes different work (e.g., prescription: "add retry logic to the HTTP client", task: "implement HTTP client connection pooling" — same component, different change).

### Conservative Default

When in doubt, the agent treats the prescription as **unmatched**. The cost of a false gap (author adds a missing AC/task — 2 minutes) is far lower than the cost of a missed gap (prescribed work silently drops from the pipeline — hours/days of rework + wasted budget).

---

## 4. Gap Reporting Format

**What**: The exact format for Critical Gap entries emitted by Pass 9.

**Why**: AC-3.1 (Critical Gaps section, `[C{N}]` format), AC-3.2 (includes file path, missing links, suggested fix), AC-3.3 (blocks PASS verdict).

**How**: Each gap is emitted as a Critical Gap in the existing dryrun-design report format:

```markdown
### [C{N}] Untraced file prescription: `{file_path_or_prescription_text}`
- **Pass**: Pass 9 (Design-to-Task-to-AC Traceability)
- **What**: {Source} prescription `{path_or_text}` — "{change_description}" — has no matching {task in task.md / AC in requirement.md / task or AC in either}.
- **Risk**: This prescribed change will {not be implemented (no task) / not be verified (no AC) / silently drop from the pipeline (neither)}. Downstream gates (/implement, /dryrun-code) cannot catch work they don't know exists.
- **Fix**: {One of:}
  - "Add a task to task.md: '{suggested task text}'"
  - "Add an AC to requirement.md: '{suggested AC text}'"
  - "Add both a task and an AC covering this change"
```

Where `{Source}` is either "Files Changed table" or "Body section '{section_heading}'" (for body prescriptions — AC-2.3 requires source location).

**`{N}` numbering**: The `[C{N}]` counter is shared across all passes. Pass 9 gaps continue the numbering from any Critical Gaps found in Passes 1-8. For example, if Passes 1-8 produced C1-C3, the first Pass 9 gap is C4.

### Verdict Impact

Per AC-3.3 and the existing dryrun-design verdict rules:
- **Any Critical Gap** (including traceability gaps) → verdict is **FAIL — needs revision**
- Traceability gaps do not have a "Warning" tier — they are always Critical (AC-1.4, AC-1.5, AC-2.3). The rationale: a Warning implies "proceed with caution." But an untraced prescription isn't a risk to monitor — it's a guarantee of dropped work.

---

## 5. Traceability Matrix Format

**What**: The output format when all prescriptions trace successfully.

**Why**: AC-4.1 (summary table with three columns), AC-4.2 (under "Traceability Matrix" heading, in pass output section), AC-4.3 (no-prescriptions observation).

**How**:

### When All Prescriptions Trace Successfully

The pass emits a table under a dedicated heading within the Pass 9 output:

```markdown
### Pass 9: Design-to-Task-to-AC Traceability

#### Traceability Matrix

| File/Prescription | Task Reference | AC Reference |
|-------------------|---------------|--------------|
| `src/layout/coordinator.py` — Add coordination logic | Task 3.2: Implement coordinator module | AC-1.3: Coordinator processes layout requests |
| `src/scenes/*.scene` — Retrofit existing scene files | Task 4.1: Update scene files to use new layout system | AC-2.1: Existing scenes use updated layout |
| Body §Migration Strategy: "run `migrate.py` on deployment" | Task 5.3: Add migration step to deploy script | AC-3.2: Migration runs automatically on deploy |

**Result**: All {count} file-level prescriptions traced to tasks and ACs. No traceability gaps.
```

The "File/Prescription" column uses:
- For Files Changed entries: `` `{path}` — {change description} ``
- For body prescriptions: `Body §{section_heading}: "{prescription text}"`

### When No Prescriptions Exist

```markdown
### Pass 9: Design-to-Task-to-AC Traceability

No file-level prescriptions found (no "Files Changed" table and no body sections referencing specific files). Traceability check skipped.
```

This is emitted as an **Observation** (`[O{N}]`) — not a gap, not a warning.

---

## 6. Body Prescription Detection Rules

**What**: The specific patterns the reviewing agent looks for when scanning design.md body sections.

**Why**: AC-2.1 (scan for prescriptive statements referencing specific files), D2 (targeted detection, not exhaustive NLP).

**How**:

### Detection Targets

The agent scans for three categories of body prescription:

**Category A — Explicit file paths**: Any text that resembles a file or directory path:
- Contains a file extension (`.py`, `.yaml`, `.md`, `.scene`, `.ts`, `.json`, etc.)
- Contains path separators (`/` or `\`)
- Is formatted as inline code (`` `path` ``) or appears in a code block
- Examples: `` `src/models/user.py` ``, `config/settings.yaml`, `the handler in routes/api.ts`

**Category B — Glob patterns**: Wildcard file references:
- Contains `*`, `**`, or `?` combined with path-like text
- Examples: `*.scene`, `src/**/*.py`, `tests/test_*.py`

**Category C — Imperative file-change statements**: Action verb + file/directory target:
- Verb phrases: "update", "modify", "add to", "remove from", "create", "delete", "refactor", "rename", "move", "retrofit", "migrate"
- Combined with a file target from Category A or B
- Examples: "update all `.scene` files", "add a new column to `schema.sql`", "modify the handler in `routes/api.ts`"

### Exclusions (Not Prescriptions)

The agent does **not** flag:
- **References in rationale**: "We chose this approach because `coordinator.py` was becoming too large" — this describes a reason, not a prescribed change.
- **Existing state descriptions**: "Currently, `config.yaml` contains the database URL" — this describes what is, not what should change.
- **Examples and comparisons**: "Similar to how `auth.py` handles tokens" — this is an analogy, not a prescription.
- **Files Changed table entries**: These are handled separately in Step 1; do not double-count.

### Disambiguation Rule

When a file reference is ambiguous between prescription and description, the agent checks for imperative/prescriptive language:
- **Prescriptive** (flag it): "The migration script **must** update `schema.sql`", "Ensure `config.yaml` includes the new key", "Retrofit existing `.scene` files"
- **Descriptive** (skip it): "The current `schema.sql` defines three tables", "`config.yaml` is read at startup"

---

## 7. `/design` Skill — task.md Skeleton Generation

**What**: The `/design` skill at `.claude/skills/design/SKILL.md` is modified to write both `design.md` and a `task.md` skeleton in a single step.

**Why**: AC-6.1 through AC-6.6 (DDT-6). Closes C1 deadlock: task.md exists before `/dryrun-design` runs, enabling Pass 9 to evaluate the Task axis at design-time.

**How**:

After writing `design.md`, the `/design` skill inspects the resulting Files Changed table and writes `task.md` to the same spec folder with the following rules:

### Skeleton Derivation

**One skeleton item per Files Changed row** (AC-6.2). For each row in the Files Changed table:
- Extract the file path from column 1
- Extract the change summary from column 2
- Derive a one-line task description: `actor updates/creates/modifies {file path} — {change summary, abbreviated to ≤ 10 words}`

**Item format** (AC-6.3, AC-6.4): Each item uses the standard `[ ]` pending status and names actor, action, and target explicitly:

```markdown
- [ ] **Implementer** updates `.claude/skills/dryrun-design/SKILL.md` — add Pass 9 dual-axis traceability section. _DDT-5_
- [ ] **Implementer** updates `.claude/skills/design/SKILL.md` — write task.md skeleton from Files Changed table. _DDT-6_
- [ ] **Implementer** updates `.claude/skills/implement/SKILL.md` — consume skeleton, mark items in-progress/done. _DDT-7_
```

The requirement-ref link at the end of each item (`_DDT-N_` or `_AC-N.N_`) traces the skeleton item to its driving requirement — it is not optional.

**Requirement-ref derivation**: `/design` determines the requirement-ref for each skeleton item as follows:
1. **AC Trace column present**: If the Files Changed table includes an "AC Trace" column, use its value directly — the author has already mapped the row to its requirement(s). Pick the parent story ID (e.g., `DDT-5`) when the column lists multiple ACs under one story.
2. **AC Trace column absent** (fallback): `/design` matches the row's change description against `requirement.md` ACs using the same Tier 2 description-based heuristic defined in Section 3 — find the AC whose verification scope most closely covers the prescribed change, then use its parent story ID as the ref. If no AC matches, use `_untraced_` as the ref and append `<!-- ⚠ no requirement match found — author must assign -->` on the same line.

**No Files Changed table** (AC-6.5): If `design.md` has no Files Changed table, `/design` still creates `task.md` with a single note item:

```markdown
- [ ] **Author** populates task.md manually — no Files Changed table found in design.md. _manual_
```

**Scope limit** (AC-6.6): `/design` authors only the Files Changed skeleton. It does not add free-form tasks, implementation notes, or sub-tasks. Free-form expansion is `/implement`'s responsibility.

---

## 8. `/implement` Skill — Skeleton Consumption

**What**: The `/implement` skill at `.claude/skills/implement/SKILL.md` is modified to consume the `task.md` skeleton rather than author `task.md` from scratch.

**Why**: AC-7.1 through AC-7.4 (DDT-7). Ensures task items that were traced by Pass 9 are not silently replaced, renamed, or bypassed during implementation.

**How**:

### Skeleton-First Behavior (AC-7.1)

When `/implement` runs and `task.md` already exists, the skill does **not** overwrite or regenerate it. It reads the existing skeleton and treats each `[ ]` item as a unit of work to be executed.

### Item Lifecycle (AC-7.2)

As `/implement` executes:
- **Before starting** a skeleton item: mark it `[-]` (in progress)
- **After completing** a skeleton item: mark it `[x]` (done)

### Sub-Task Appending (AC-7.3)

`/implement` may append sub-tasks beneath a skeleton item to capture finer-grained steps. Sub-tasks use one level of nesting and the same status markers. The skeleton item itself — its text, its requirement-ref link — must not be removed or renamed. Sub-tasks are additive only.

Example:
```markdown
- [-] **Implementer** updates `.claude/skills/dryrun-design/SKILL.md` — add Pass 9 dual-axis traceability section. _DDT-5_
  - [x] Add `### Pass 9:` block after `### Pass 8:` in SKILL.md
  - [-] Write AC-axis matching instructions (Steps 1–3)
  - [ ] Write Task-axis matching instructions (Step 3 continued)
  - [ ] Write dual-axis classification table (Step 4)
  - [ ] Write output format instructions (Step 5)
```

### Untraced Work (AC-7.4)

If `/implement` discovers work not covered by any skeleton item, it:
1. Adds a new `[ ]` item for it in `task.md`
2. Appends a warning comment on the same line: `<!-- ⚠ not in Pass 9 skeleton — design.md Files Changed may be incomplete -->`

This ensures that any task-scope drift from the design is visible in the task file and not silently absorbed.

---

## Error Handling

### Malformed Files Changed Table

If `design.md` contains a "Files Changed" heading but the table is malformed (no rows, missing File column, unparseable markdown), the agent emits a **Warning**:

```markdown
### [W{N}] Malformed Files Changed table
- **Pass**: Pass 9 (Design-to-Task-to-AC Traceability)
- **What**: The "Files Changed" table exists but could not be parsed — {reason}.
- **Risk**: File prescriptions may exist but cannot be verified for traceability.
- **Suggestion**: Fix the table format (at least two columns: File, Change — extra columns are permitted) and re-run.
```

### Missing task.md

Because `/design` produces `task.md` before `/dryrun-design` runs (DDT-6), `task.md` is **expected to exist** at Pass 9 time. If it is absent:

- Every Files Changed entry is reported as a Critical Gap on the **Task axis**:
  > "task.md not found — all Files Changed entries are untraced on the task axis. The `/design` skill is required to produce task.md before `/dryrun-design` runs. If this is a manual design, create task.md with one `[ ]` skeleton item per Files Changed row before re-running."
- The AC axis check **still runs normally** and reports gaps as Critical.
- Pass 9 does **not** skip when task.md is absent — absence is a Critical Gap, not a deferral.

### Missing requirement.md

- Every Files Changed entry is reported as a Critical Gap with "no requirement.md found — all prescriptions are untraced on the AC axis."

### Both Missing

A single Critical Gap summarizes: "Neither task.md nor requirement.md exists — all file prescriptions are untraceable." Individual per-entry gaps are not duplicated.

---

## Files Changed

| File | Change | AC Trace |
|------|--------|----------|
| `.claude/skills/dryrun-design/SKILL.md` | Add "Pass 9: Design-to-Task-to-AC Traceability" section after Pass 8. The new section contains: (a) instructions to parse the Files Changed table (at least two columns: File, Change; extra columns ignored), (b) instructions to scan body sections for file-level prescriptions, (c) dual-axis check — AC axis (requirement.md) and Task axis (task.md) evaluated independently using two-tier matching heuristic, (d) classification rules (both axes must pass for Traced; either failing = Critical Gap), (e) gap output format using `[C{N}]` template, (f) Traceability Matrix format for full success, (g) no-prescriptions Observation, (h) missing task.md = Critical Gap (not skip), (i) traceability gaps block PASS verdict. Existing Passes 1-8 unmodified. | AC-1.1, AC-1.2, AC-1.3, AC-1.4, AC-1.5, AC-2.1, AC-2.2, AC-2.3, AC-3.1, AC-3.2, AC-3.3, AC-4.1, AC-4.2, AC-4.3, AC-5.1, AC-5.2, AC-5.3, AC-5.4, AC-5.5, AC-5.6, AC-5.7 |
| `.claude/skills/design/SKILL.md` | After writing design.md, write task.md skeleton to the same spec folder: one `[ ]` item per Files Changed row, format `**Implementer** {verb} {file} — {change summary}. _{requirement-ref}_`. If no Files Changed table exists, write a single manual-populate note item. Do not author free-form tasks beyond the skeleton. | AC-6.1, AC-6.2, AC-6.3, AC-6.4, AC-6.5, AC-6.6 |
| `.claude/skills/implement/SKILL.md` | When task.md already exists, do not overwrite or regenerate it. Read skeleton items; mark `[-]` when starting, `[x]` when done. May append sub-tasks beneath skeleton items (one level deep). If work is discovered that has no skeleton item, add a new `[ ]` item with an untraced-work warning comment. | AC-7.1, AC-7.2, AC-7.3, AC-7.4 |

### Self-Dogfood Verification

This design prescribes exactly **3 file changes**. The traceability is complete:

| File/Prescription | Task Reference | AC Reference |
|-------------------|---------------|--------------|
| `.claude/skills/dryrun-design/SKILL.md` — Add Pass 9 dual-axis traceability | Files Changed row 1 → skeleton item 1 | AC-1.1–1.5, AC-2.1–2.3, AC-3.1–3.3, AC-4.1–4.3, AC-5.1–5.7 |
| `.claude/skills/design/SKILL.md` — Write task.md skeleton | Files Changed row 2 → skeleton item 2 | AC-6.1–6.6 |
| `.claude/skills/implement/SKILL.md` — Consume skeleton | Files Changed row 3 → skeleton item 3 | AC-7.1–7.4 |

- **DDT-1** (AC-1.1–1.5): Covered by Pass 9 algorithm Steps 1, 3, 4 — Files Changed parsing, matching, classification.
- **DDT-2** (AC-2.1–2.3): Covered by Steps 2, 3, 4 — body prescription scanning and classification.
- **DDT-3** (AC-3.1–3.3): Covered by Section 4 gap format and verdict impact rule.
- **DDT-4** (AC-4.1–4.3): Covered by Section 5 traceability matrix format and no-prescriptions observation.
- **DDT-5** (AC-5.1–5.7): Covered by Section 1 (positioning, dual-axis, missing task.md = Critical Gap) and first Files Changed row.
- **DDT-6** (AC-6.1–6.6): Covered by Section 7 `/design` skill modification and second Files Changed row.
- **DDT-7** (AC-7.1–7.4): Covered by Section 8 `/implement` skill modification and third Files Changed row.

No Files Changed entry lacks an AC trace. No AC from DDT-1 through DDT-7 lacks a Files Changed entry. The design satisfies the discipline it introduces.

---

## Future Work (Out of Scope)

- **Existing spec audit**: Scanning worker project specs (e.g., `forward-pass-ai`) for the same blind spot the `mobject-layout-coordination` failure exposed. Separate sweep, not part of this spec.
- **`/dryrun-code` changes**: The fix is upstream at `/dryrun-design`. If traceability is enforced at design review, `/dryrun-code` should not need changes. If experience shows otherwise, that's a separate spec.
- **Template changes to `/requirement`**: This spec targets skill behaviours, not static authoring templates.
- **Cross-spec traceability**: Checking whether prescriptions in one spec's design.md are covered by *another* spec's tasks/ACs (e.g., shared infrastructure). Out of scope — each spec is self-contained for traceability purposes.
