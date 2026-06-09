# e-spec:bootstrap — Design

## Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | Skill lives at `sdlc/spec-enhanced/skills/bootstrap/SKILL.md` with frontmatter matching existing e-spec skills; allowed-tools: Read, Grep, Glob, Write, Edit, Bash (no Task) | BST-6 invocation interface; no sub-agents needed (CLAUDE.md L2 anti-pattern). Matches the pattern of `spec/SKILL.md`, `design/SKILL.md`, etc. |
| D2 | Stack detection uses file-based heuristics with ordered priority; first match wins; explicit args override entirely | BST-1 requires auto-detection with arg override. Priority order avoids ambiguity when multiple markers coexist (e.g., `pyproject.toml` + `requirements.txt`). |
| D3 | Blueprint discovery reads first 30 lines of each readme from TWO sources: `C:/Projects/APEX/.claude/blueprints/*/readme.md` (primary) and `C:/Projects/APEX/blueprints/**/readme.md` (secondary, recursive); matching uses keyword rules per blueprint category; primary wins on slug collision | BST-5 requires embedding exact blueprint paths. Reading 30 lines captures the "When to Use" section in all current blueprints. Two sources required — APEX blueprints span both directories. |
| D4 | Conventions table has exactly 10 rows fenced by HTML comment markers; each row cites its source blueprint | BST-2 mandates the table structure. Fencing enables idempotency (D6). Blueprint citation gives downstream agents direct paths (BST-5). |
| D5 | Build+install commands are parsed from the conventions table and executed sequentially; failure marks the table row and sets exit code | BST-3 mandates execution — not optional. Capturing failure in-place means the CLAUDE.md itself documents the broken state. |
| D6 | Idempotency via fenced-block detection with five branches: absent → append, non-terminal Validated → force re-validation (bypass identity check), identical + terminal → exit 0, different without --force → exit 1, different with --force → replace block only | BST-4 protects existing validated conventions. BST-7 requires safe merge preserving content outside the fence. Five branches cover all states exhaustively; the non-terminal pre-comparison branch ensures a crash during validation is always recoverable via plain re-run. |
| D7 | Args: `[language] [project-type] [--force] [--force-skip-validation]`; exit codes: 0/1/2; structured terminal summary | BST-6 specifies the interface. Exit code 2 dropped — requirement BST-4/BST-6 unify FAIL and diff-protect under exit 1. BST-3 `--force-skip-validation` is explicit skip, not silent omission. |
| D8 | Eight-step linear process: parse → discover → compose → read existing → write → validate → update marker → summarize | Sequential by necessity — each step depends on the prior. Matches the narrative flow of BST-1 through BST-7. |

---

## 1. Skill Structure & Frontmatter (D1)

**What**: The bootstrap skill is a single SKILL.md file at `C:/Projects/APEX/sdlc/spec-enhanced/skills/bootstrap/SKILL.md`.

**Why**: BST-6 defines the invocation interface. All e-spec skills follow the same frontmatter + Process step pattern (observed in `spec/SKILL.md`, `design/SKILL.md`, `implement/SKILL.md`).

**How**: Frontmatter block:

```yaml
---
name: bootstrap
description: Bootstrap a project — detects stack, selects APEX blueprints, writes locked conventions to CLAUDE.md, validates build+install. Run once before the first /e-spec:spec.
argument-hint: "[language] [project-type] [--force] [--force-skip-validation]"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---
```

Key differences from other e-spec skills:
- **No Task tool** — bootstrap is a single-agent, single-pass skill. No sub-agents (CLAUDE.md L2: "sub-agents are expensive").
- **No WebSearch/WebFetch** — all information comes from local files (blueprint readmes, project root markers).
- **Bash is required** — for executing build+install commands (BST-3).

The SKILL.md body follows the same structure as `spec/SKILL.md`: title, Input section, Process section (numbered steps), Output section, Rules section.

---

## 2. Stack Detection Algorithm (D2)

**What**: File-based heuristic that inspects the project root directory for stack signal files.

**Why**: BST-1 requires auto-detection with explicit-arg override. The priority order resolves ambiguity when multiple markers coexist.

**How**:

### Detection priority table

**v1.0 scope: Python, Node, Go only.** Auto-detection covers these three languages. Other languages (Rust, Ruby, Java, etc.) have no marker entries and will not be auto-detected — callers must supply `--language` explicitly. Rust (`Cargo.toml`/`Cargo.lock`) and other stacks are deferred to a future version.

The skill checks for these files in the project root, in order. First match wins.

| Priority | File(s) | Detected Stack | Default Project Type |
|----------|---------|---------------|---------------------|
| 1 | `pyproject.toml` | Python (version extracted from `requires-python` field if present) | `library` |
| 2 | `setup.py` | Python | `library` |
| 3 | `setup.cfg` | Python | `library` |
| 4 | `requirements.txt` | Python | `poc` |
| 5 | `package.json` | Node (version extracted from `engines.node` field if present) | `library` |
| 6 | `go.mod` | Go (version extracted from `go` directive) | `service` |

### Detection logic (pseudocode)

```python
STACK_MARKERS = [
    ("pyproject.toml",    "python",  "library"),
    ("setup.py",          "python",  "library"),
    ("setup.cfg",         "python",  "library"),
    ("requirements.txt",  "python",  "poc"),
    ("package.json",      "node",    "library"),
    ("go.mod",            "go",      "service"),
]

def detect_stack(project_root, arg_language=None, arg_project_type=None):
    # Explicit args override auto-detection entirely (BST-1 AC)
    if arg_language:
        return {
            "language": arg_language,
            "project_type": arg_project_type or "poc",
            "source": "args",
        }

    # Auto-detect: scan project root for marker files
    for filename, language, default_type in STACK_MARKERS:
        if exists(project_root / filename):
            return {
                "language": language,
                "project_type": arg_project_type or default_type,
                "source": f"detected from {filename}",
            }

    # No markers found, no args → cannot proceed (BST-1 AC)
    FAIL("No stack markers found in project root. "
         "Supply language explicitly: /e-spec:bootstrap python poc")
```

### Version extraction

For Python (`pyproject.toml`): read `[project].requires-python` field. If absent, report `Python 3.x` (unspecified).

For Node (`package.json`): read `engines.node` field. If absent, report `Node (version unspecified)`.

For Go (`go.mod`): read the `go X.Y` directive on line 3. If absent, report `Go (version unspecified)`.

Version extraction is best-effort — failure to extract a version does NOT block bootstrap.

---

## 3. Blueprint Discovery & Matching (D3)

**What**: Enumerate all blueprints from two APEX blueprint directories, read each readme's header and "When to Use" section, match against detected stack + project type.

**Why**: BST-5 requires embedding exact blueprint paths in CLAUDE.md so downstream agents can navigate directly. BST-1 requires blueprint selection before writing conventions.

**How**:

### Discovery

APEX maintains two blueprint directories:
- **Primary (SDLC-scoped)**: `C:/Projects/APEX/.claude/blueprints/` — flat layout, one subdirectory per blueprint.
- **Secondary (project-scoped)**: `C:/Projects/APEX/blueprints/` — nested layout (e.g., `blueprints/interfaces/cli/`, `blueprints/libs/`). Contains blueprints such as `multi-agent`, `web-ui-design-systems`, `interfaces`, `libs`.

Both directories are scanned:

```
1. Glob for: C:/Projects/APEX/.claude/blueprints/*/readme.md        (primary — non-recursive)
2. Glob for: C:/Projects/APEX/blueprints/**/readme.md               (secondary — recursive)
3. Merge results. For each matched path:
   a. Read first 30 lines
   b. Extract: display name (line 1, after "# "), "When to Use" bullet items
   c. Derive slug from parent directory name
   d. Store as candidate: { name, slug, path, keywords[] }
4. Dedup by slug: if the same blueprint slug appears in both directories, the primary
   (.claude/blueprints/) entry is authoritative and the secondary entry is discarded.
```

If `C:/Projects/APEX/.claude/blueprints/` is not accessible → log WARNING, continue without primary blueprints.
If `C:/Projects/APEX/blueprints/` is not accessible → log WARNING, continue without secondary blueprints.
If both are inaccessible → log WARNING, continue with empty blueprint list (BST-5 AC).

### Matching rules

| Blueprint | Matches When | Keywords |
|-----------|-------------|----------|
| `poc-convention` | `project_type == "poc"` OR project slug starts with `poc-` | poc, experiment, bounded, evaluation |
| `spec-driven` | `.claude/specs/` directory exists in project OR `project_type in ("service", "library", "agent")` | spec, sdlc, requirement, design, implement |
| `model-calibration` | `project_type == "calibration"` OR project slug contains `calibration` or `eval-model` | calibration, model, eval, llm |
| `substrate-eval` | `project_type == "substrate-eval"` OR project slug contains `substrate` | substrate, eval, dispatch, convergence |

Matching is deterministic — no LLM judgment. The skill checks conditions in the table above; a blueprint either matches or it doesn't.

### Multiple matches

Multiple blueprints CAN match simultaneously. This is expected and correct. Example: a Python POC using the spec-driven SDLC chain matches both `poc-convention` and `spec-driven`. Both are listed in the Blueprint refs row.

### No matches

If no blueprint matches → emit WARNING but continue (BST-1 AC). The conventions table is populated with stack-derived defaults only, and the Blueprint refs row reads: `None — no applicable APEX blueprints matched`.

---

## 4. Conventions Table Schema (D4)

**What**: A fenced markdown table written into the project's `CLAUDE.md` with exactly 10 rows.

**Why**: BST-2 mandates the table structure. The fenced markers enable idempotency detection (BST-4) and safe merge (BST-7).

**How**:

### Fenced block structure

```markdown
<!-- bootstrap-conventions -->
## Project Conventions

Validated: {validation-status}

| Convention | Value | Source |
|---|---|---|
| Stack | {language} {version}, {build tool} | {source: "detected from {file}" or "from args"} |
| Layout | {directory structure with explicit paths} | {blueprint name + path, or "stack defaults"} |
| Naming | Modules: snake_case, Classes: PascalCase, Functions: snake_case, Constants: UPPER_SNAKE, Files: snake_case | {blueprint or "language convention"} |
| Code style | Linter: {tool}, Formatter: {tool}, Type checker: {tool}, Line length: {N} | {blueprint or "stack defaults"} |
| Deps | Manager: {tool}, Lockfile: {policy} | {blueprint or "stack defaults"} |
| Tests | Framework: {tool}, Root: `tests/`, Naming: `test_*.py`, Mocks: {policy} | {blueprint or "stack defaults"} |
| Build + install | `{exact command 1}`<br>`{exact command 2}` | {blueprint or "stack defaults"} |
| Logging | Format: {structured JSON / plain}, Location: {path}, Retention: {policy} | {blueprint or "stack defaults"} |
| Git | Branch model: {model}, Commit format: {format}, .gitignore: {baseline entries} | {blueprint or "stack defaults"} |
| Blueprint refs | {name}: `{absolute-path-to-readme.md}` | — |
<!-- /bootstrap-conventions -->
```

### Validation status line

The `Validated:` line sits between the section heading and the table. It is updated by the validation step (D5):

- On PASS: `Validated: {YYYY-MM-DD} — build + install clean`
- On FAIL: `Validated: FAILED — {command} exited {code}. Re-run after fixing.`
- On SKIP: `Validated: SKIPPED (--force-skip-validation) — NOT SAFE FOR SPEC WORK`

### Stack-specific defaults (Python)

When language is Python and no blueprint overrides a row, these defaults apply:

| Convention | Default Value |
|---|---|
| Stack | `Python 3.11+, setuptools` |
| Layout | `src/{package_name}/` with `__init__.py`; `tests/` at project root |
| Naming | Modules: snake_case, Classes: PascalCase, Functions: snake_case, Constants: UPPER_SNAKE, Files: snake_case |
| Code style | Linter: `ruff`, Formatter: `black`, Type checker: `mypy`, Line length: 120 |
| Deps | Manager: `pip`, Lockfile: `requirements.lock` or `[project.optional-dependencies]` in pyproject.toml |
| Tests | Framework: `pytest`, Root: `tests/`, Naming: `test_*.py`, Mocks: `unittest.mock` |
| Build + install | `pip install -e .[dev]` |
| Logging | Format: structured (stdlib `logging`), Location: stderr, Retention: caller-managed |
| Git | Branch model: git-flow, Commit format: conventional, .gitignore: `__pycache__/`, `*.pyc`, `.venv/`, `dist/`, `*.egg-info/` |

### Blueprint override rules

When a matched blueprint mandates a value for a convention row, that value replaces the stack default. The Source column records the blueprint name and path.

Specific overrides from current blueprints:

- **`poc-convention`** overrides Layout → `src/` layout (readme.md lines 53–59: `src/` directory for all code). Source: `poc-convention: C:/Projects/APEX/.claude/blueprints/poc-convention/readme.md`
- **`spec-driven`** does NOT override any convention row directly — it is a methodology blueprint, not a structural one. It appears in Blueprint refs only.

If two blueprints mandate conflicting values for the same row, the more specific structural blueprint wins (e.g., `poc-convention` Layout beats a hypothetical `spec-driven` Layout). The skill logs which blueprint was overridden and why.

---

## 5. Build + Install Validation (D5)

**What**: After writing the conventions to CLAUDE.md, parse the Build + install row and execute each command sequentially.

**Why**: BST-3 — the entire motivation for this skill. The Aakriti failure was a `setuptools` flat-layout error invisible to `pytest` but fatal to `pip install -e .[dev]`. Validation catches this class of failure before spec work begins.

**How**:

### Command extraction

1. Read the Build + install row from the conventions table.
2. Split the cell value on `<br>` (HTML line-break tag, case-insensitive: `<br>`, `<br/>`, `<BR/>`) to get individual command lines. Each line is one command. A single-command row has no `<br>` and yields one item.
3. Strip surrounding backticks (`` ` ``) and triple-backtick fences from each extracted line before execution. Example: `` `pip install -e .[dev]` `` → `pip install -e .[dev]`.
4. Each resulting string is a verbatim shell command to execute.

Example: `` `pip install -e .[dev]` `` → one command: `pip install -e .[dev]`.
`` `pip install -e .[dev]`<br>`python -m pytest --co -q` `` → two commands: `pip install -e .[dev]` then `python -m pytest --co -q`.

> **Delimiter rationale**: `<br>` is used instead of a text delimiter (e.g., ` then `) because text delimiters cannot be escaped — a build command containing the literal delimiter string would be silently mis-split into invalid fragments.

### Execution flow

```
for each command in build_install_commands:
    result = Bash(command, cwd=project_root, timeout=120000)
    if result.exit_code != 0:
        # Capture full stdout + stderr
        update_validation_line(
            f"FAILED — `{command}` exited {result.exit_code}. Re-run after fixing."
        )
        print_stderr_in_full(result.stderr)
        EXIT 1
    end
end

# All commands passed
update_validation_line(f"{YYYY-MM-DD} — build + install clean")
EXIT 0
```

### --force-skip-validation flag

When present:
- Skip all command execution.
- Write validation line: `Validated: SKIPPED (--force-skip-validation) — NOT SAFE FOR SPEC WORK`
- Log warning to terminal: `⚠ Validation skipped. Conventions are written but NOT verified. Do not start spec work until validated.`
- Exit 0 (skill succeeded; validation was explicitly skipped, not failed).

### Timeout

Each command gets 120 seconds (Bash tool default). If a command times out, treat it as exit code 124 (timeout) and report accordingly.

---

## 6. Idempotency & Safe Merge (D6)

**What**: Before writing anything, detect whether a bootstrap-conventions block already exists in CLAUDE.md and apply the correct branch.

**Why**: BST-4 protects validated conventions from accidental overwrite. BST-7 ensures pre-existing CLAUDE.md content is preserved.

**How**:

### Pre-write decision tree

```
Read project CLAUDE.md
  ├─ File does not exist
  │    → Create CLAUDE.md with just the conventions block (BST-7 AC)
  │    → Proceed to validation (D5)
  │
  ├─ File exists, NO <!-- bootstrap-conventions --> marker
  │    → Append conventions block at end of file, preceded by blank line (BST-7 AC)
  │    → Proceed to validation (D5)
  │
  ├─ [PRE-COMPARISON] File exists, marker found,
  │   existing Validated line is NON-TERMINAL
  │   (matches: "FAILED …" in any form, or "PENDING", or any unrecognized state)
  │   (terminal states are: date-prefixed "… — build + install clean", or "SKIPPED (--force-skip-validation)…")
  │    → Non-terminal Validated detected — validation did not complete on last run.
  │    → Re-validation is unconditional: --force flag and content identity are irrelevant.
  │    ├─ Proposed content IDENTICAL to existing (ignoring Validated line)
  │    │    → Skip write (conventions unchanged) → Proceed directly to validation (D5)
  │    └─ Proposed content DIFFERS from existing (ignoring Validated line)
  │         → Replace fenced block only (BST-7 AC) → Proceed to validation (D5)
  │
  ├─ File exists, marker found, existing Validated line IS terminal,
  │   proposed content IDENTICAL to existing
  │    → Print: "Already bootstrapped — conventions unchanged. Nothing to do."
  │    → Exit 0 (BST-4 AC)
  │
  ├─ File exists, marker found, existing Validated line IS terminal,
  │   proposed content DIFFERS, --force NOT set
  │    → Compute and display diff (existing vs proposed)
  │    → Print: "Conventions differ. Re-run with --force to overwrite."
  │    → Exit 1 (BST-4 AC)
  │
  └─ File exists, marker found, existing Validated line IS terminal,
     proposed content DIFFERS, --force IS set
       → Replace fenced block only; all content outside fence preserved (BST-7 AC)
       → Proceed to validation (D5)
```

**Recovery trace (C1)**: If validation crashes mid-run, the block is left with `Validated: FAILED — validation did not complete (pre-flight)` (written by D8 Step 4 before any commands execute). On re-run, the pre-comparison branch above detects a non-terminal Validated line → forces through to validation regardless of content identity or --force. Recovery requires only a plain re-run — no manual CLAUDE.md edit needed.

### Identity comparison

"Identical" means the text between `<!-- bootstrap-conventions -->` and `<!-- /bootstrap-conventions -->` markers is byte-for-byte equal to the proposed block, **excluding the Validated: line** (which changes on each validation run). The comparison strips the `Validated:` line from both sides before diffing. This comparison is only reached after the pre-comparison branch above has confirmed the existing Validated line is terminal.

### Post-write verification

After every write (create, append, or replace):
1. Re-read CLAUDE.md via Read tool.
2. Grep for `<!-- bootstrap-conventions -->` — must appear exactly once.
3. Grep for `<!-- /bootstrap-conventions -->` — must appear exactly once.
4. Verify the opening marker appears before the closing marker.
5. If any check fails → error with exact diagnostic, exit 1.

### Content outside the fence

The skill NEVER writes outside the fenced block (BST-7 AC). All content above `<!-- bootstrap-conventions -->` and below `<!-- /bootstrap-conventions -->` is preserved byte-for-byte.

When creating a new CLAUDE.md (file does not exist), the file contains ONLY the fenced block — no preamble, no extra content. The project author adds their own content above the fence later.

---

## 7. Invocation Interface & Terminal Summary (D7)

**What**: Argument parsing, flag handling, exit codes, and the structured terminal summary.

**Why**: BST-6 specifies the exact interface and summary format.

**How**:

### Argument parsing

```
/e-spec:bootstrap [language] [project-type] [--force] [--force-skip-validation]
```

Parsing rules:
1. Split `$ARGUMENTS` on whitespace.
2. Tokens starting with `--` are flags: `--force`, `--force-skip-validation`.
3. Remaining positional tokens: first is `language`, second is `project_type`. Both optional.
4. If unrecognized flag → print error, exit 1.
5. Valid language values: `python`, `node`, `go` (extensible — no hard rejection of unknown values; treat unknown as literal and proceed with stack defaults).
6. Valid project-type values: `poc`, `service`, `library`, `agent` (extensible — unknown values accepted, used for blueprint matching).

### Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success (conventions written + validation PASS), or "nothing to do" (identical conventions), or success with `--force-skip-validation` |
| 1 | Failure: bad args, validation FAIL, diff-protect guard triggered, post-write verification failure |

Two codes only. Simpler than the three-code scheme initially considered — the terminal summary provides all the diagnostic detail needed to distinguish failure modes.

### Terminal summary format

Printed after all work is complete (or on failure):

```
─────────────────────────────────────
Bootstrap {SUCCESS | FAILED | SKIPPED}

  Detected stack : {language} {version} ({source})
  Blueprints     : {name1}: {path1}
                   {name2}: {path2}
                   (or "none matched")
  CLAUDE.md      : {created | conventions appended | conventions updated (--force) | no changes}
  Validation     : {PASS | FAIL — {command}: exit {code} | SKIPPED (--force-skip-validation)}
  Next step      : {Run /e-spec:spec to start your first feature | Fix the validation error above, then re-run /e-spec:bootstrap}
─────────────────────────────────────
```

On FAIL, the full stderr of the failing command is printed ABOVE the summary box (BST-6 AC).

---

## 8. Process Flow (D8)

**What**: The end-to-end executable sequence as SKILL.md Process steps.

**Why**: Ties D1–D7 together into a linear, implementable flow. Each step maps to one or more user stories.

**How**:

### Step 1: Parse Arguments (BST-6)

1. Parse `$ARGUMENTS` per D7 rules.
2. Extract: `language`, `project_type`, `force`, `force_skip_validation`.
3. If unrecognized flags → print error + exit 1.

### Step 2: Detect Stack (BST-1)

1. If `language` arg provided → use it (source: "from args").
2. Else → scan project root for marker files per D2 priority table.
3. If no markers and no args → print error asking user to supply language, exit 1.
4. Result: `{ language, version, project_type, source }`.

### Step 3: Discover & Match Blueprints (BST-5)

1. Glob `C:/Projects/APEX/.claude/blueprints/*/readme.md` (primary, non-recursive).
2. Glob `C:/Projects/APEX/blueprints/**/readme.md` (secondary, recursive).
3. Merge and dedup by slug per D3 dedup rule (primary wins on collision).
4. Read first 30 lines of each.
5. Apply matching rules per D3 table.
6. Result: list of `{ name, path }` for matched blueprints.
7. Print selected blueprints to terminal (BST-1 AC: "listed before any file is written").

### Step 4: Compose Conventions Table (BST-2)

1. Start with stack-specific defaults for all 10 rows (per D4 defaults table).
2. For each matched blueprint, apply overrides (per D4 override rules).
3. Populate the Blueprint refs row with all matched blueprints.
4. Render the full fenced markdown block (per D4 template).
5. Set `Validated:` line to pre-flight default: `Validated: FAILED — validation did not complete (pre-flight)`. This is written BEFORE any commands are executed so that a crash or tool timeout during D5 validation leaves the block in FAILED state rather than an undefined state. The line is updated to PASS only after all validation commands succeed (D8 Step 7).

### Step 5: Check Existing CLAUDE.md & Apply Idempotency (BST-4, BST-7)

1. Read project-root `CLAUDE.md` (or note its absence).
2. Walk the D6 decision tree.
3. If "nothing to do" → emit summary, exit 0.
4. If "diff-protect" → emit diff + summary, exit 1.
5. Otherwise → proceed to write.

### Step 6: Write/Update CLAUDE.md (BST-2, BST-7)

1. Create new file, append to existing, or replace fenced block — per D6 branch.
2. Use Write tool (new file / full rewrite) or Edit tool (append / replace block).
3. Post-write verification per D6 rules.

### Step 7: Run Build + Install Validation (BST-3)

1. If `--force-skip-validation` → update `Validated:` line to SKIPPED, skip to Step 8.
2. Parse Build + install row → extract commands.
3. Execute each command sequentially per D5 flow.
4. On failure → update `Validated:` line to FAILED, print stderr, proceed to Step 8 with FAIL status.
5. On success → update `Validated:` line to `{YYYY-MM-DD} — build + install clean`.

### Step 8: Emit Terminal Summary (BST-6)

1. Compose summary per D7 template.
2. Print to terminal.
3. Exit with appropriate code (0 or 1).

### Process flow diagram

```
┌──────────────┐
│ Parse args   │ ← Step 1
└──────┬───────┘
       ▼
┌──────────────┐
│ Detect stack │ ← Step 2
└──────┬───────┘
       ▼
┌────────────────────┐
│ Discover blueprints│ ← Step 3
└──────┬─────────────┘
       ▼
┌────────────────────┐
│ Compose conventions│ ← Step 4
└──────┬─────────────┘
       ▼
┌────────────────────┐     ┌─────────────┐
│ Check CLAUDE.md    │────▶│ Exit 0 or 1 │ (identical or diff-protect)
│ (idempotency)      │     └─────────────┘
└──────┬─────────────┘
       ▼ (proceed to write)
┌────────────────────┐
│ Write/Update       │ ← Step 6
│ CLAUDE.md          │
└──────┬─────────────┘
       ▼
┌────────────────────┐     ┌──────────────────┐
│ Validate build     │────▶│ Update Validated: │
│ + install          │     │ line (PASS/FAIL/  │
└──────┬─────────────┘     │ SKIP)             │
       ▼                   └──────────────────┘
┌────────────────────┐
│ Terminal summary   │ ← Step 8
│ + exit code        │
└────────────────────┘
```

---

## Error Handling

### Argument errors
- Unrecognized flags → print "Unknown flag: {flag}. Valid flags: --force, --force-skip-validation" → exit 1.
- No stack detected and no args → print "No stack markers found. Supply language: /e-spec:bootstrap python [project-type]" → exit 1.

### Blueprint discovery errors
- `C:/Projects/APEX/.claude/blueprints/` not accessible → WARNING log, continue without primary blueprints. NOT a fatal error (BST-5 AC).
- `C:/Projects/APEX/blueprints/` not accessible → WARNING log, continue without secondary blueprints. NOT a fatal error.
- Both directories inaccessible → WARNING log, continue with empty blueprint list (BST-5 AC).
- Individual blueprint readme unreadable → skip that blueprint, WARNING log.

### File I/O errors
- Cannot read project CLAUDE.md (permission error, not "file not found") → print exact error → exit 1.
- Cannot write project CLAUDE.md → print exact error → exit 1.
- Post-write verification fails (markers not found or duplicated) → print diagnostic → exit 1.

### Validation errors
- Build command exits non-zero → capture full output, update Validated line to FAILED, report exact command + exit code + stderr → exit 1. The conventions block remains written but unvalidated.
- Build command times out (>120s) → treat as exit code 124, same FAIL path.

### No error silencing
Every error path produces a visible, actionable message. The skill never swallows an error or exits silently.

---

## Cross-Cutting Concerns

### Interaction with /e-spec:spec
Bootstrap is NOT auto-invoked by `/e-spec:spec`. It is a manual one-shot skill run before the first spec. The spec-driven lifecycle is: **bootstrap → spec → requirement → design → implement**. Bootstrap is a pre-lifecycle gate, not part of the cycle.

### Interaction with other /e-spec:* skills
Bootstrap does not modify any existing e-spec skill. Other skills benefit from the conventions table being present in CLAUDE.md (they read it naturally in their "Gather Context" step), but no wiring changes are needed. This is explicitly out of scope per the requirement.

### APEX-level vs project-level
The skill SKILL.md lives in APEX (`sdlc/spec-enhanced/skills/bootstrap/`). The conventions table it writes lives in the TARGET PROJECT's CLAUDE.md (the project root where the skill is invoked). The skill reads APEX blueprints but never writes to APEX.

### Windows path handling
All paths in the skill use forward slashes in markdown output for readability, but the skill uses whatever path format the Glob/Read/Write tools return. Blueprint paths embedded in CLAUDE.md use the absolute path as returned by Glob.

---

## Files Changed

| File | Change | AC Trace |
|------|--------|----------|
| `sdlc/spec-enhanced/skills/bootstrap/SKILL.md` | New file. The complete bootstrap skill: frontmatter (D1) + Process steps implementing D2–D8 + Rules section. | BST-1, BST-2, BST-3, BST-4, BST-5, BST-6, BST-7 |

One file. The entire skill is self-contained in SKILL.md — no supporting files, no library code, no config. The skill reads blueprints and writes to the target project's CLAUDE.md at runtime; those are runtime artifacts, not files changed by implementation.

---

## Future Work (Out of Scope)

- **Multi-language defaults beyond Python** — Node, Go, Rust default tables are deferred. The detection algorithm handles them (D2), but the defaults table (D4) only has Python values populated. Other stacks will use minimal placeholder defaults until their tables are authored. _(requirement Out of Scope)_
- **CI/CD pipeline configuration** — bootstrap does not generate GitHub Actions, GitLab CI, or any pipeline config. _(requirement Out of Scope)_
- **Docker or container configuration** — not generated, not validated. _(requirement Out of Scope)_
- **Convention enforcement on existing source files** — bootstrap writes conventions, it does not reformat or lint existing code to match. _(requirement Out of Scope)_
- **Virtual environment creation** — bootstrap assumes the caller has activated the correct environment. _(requirement Out of Scope: "Skill assumes the execution environment is caller-managed")_
- **Auto-invocation from /e-spec:spec** — bootstrap is manual. Wiring it as a gate into the spec lifecycle is a separate task. _(cross-cutting concern, not in scope)_
- **Updating other /e-spec:* skills to enforce conventions** — they benefit passively from CLAUDE.md; active enforcement is a separate task. _(requirement Out of Scope)_
