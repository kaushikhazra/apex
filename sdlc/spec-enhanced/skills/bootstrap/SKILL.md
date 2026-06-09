---
name: bootstrap
description: Bootstrap a project — detects stack, selects APEX blueprints, writes locked conventions to CLAUDE.md, validates build+install. Run once before the first /e-spec:spec.
argument-hint: "[language] [project-type] [--force] [--force-skip-validation]"
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

# Bootstrap Agent

You bootstrap a project by detecting its stack, discovering applicable APEX blueprints, writing a locked conventions table into the project's `CLAUDE.md`, and executing the documented build + install commands to verify the project is healthy. Run this **once per project, before the first `/e-spec:spec`**.

## Input

The user provides optional arguments via `$ARGUMENTS`:

```
/e-spec:bootstrap [language] [project-type] [--force] [--force-skip-validation]
```

- `language` — Optional. `python`, `node`, or `go`. Overrides auto-detection entirely.
- `project-type` — Optional. `poc`, `service`, `library`, or `agent`. Overrides auto-detection.
- `--force` — Overwrite an existing validated conventions section when proposed content differs.
- `--force-skip-validation` — Skip build/install command execution. Writes `SKIPPED` warning to CLAUDE.md. For offline/CI environments only.

Examples:
- `/e-spec:bootstrap` — auto-detect everything
- `/e-spec:bootstrap python poc` — explicit stack + project type
- `/e-spec:bootstrap python --force` — explicit language, force overwrite
- `/e-spec:bootstrap --force-skip-validation` — skip validation (offline/CI use only)

## Process

### Step 1: Parse Arguments (BST-6)

1. Split `$ARGUMENTS` on whitespace.
2. Tokens starting with `--` are flags:
   - `--force` → set `force = true`
   - `--force-skip-validation` → set `force_skip_validation = true`
   - Any other `--` token → print `Unknown flag: {flag}. Valid flags: --force, --force-skip-validation` → exit 1
3. Remaining positional tokens (non-flag): first is `language`, second is `project_type`. Both are optional.
4. Language and project-type values are accepted as-is — no hard rejection of unrecognized values. Unknown languages proceed with minimal stack defaults.

Result: `{ language, project_type, force, force_skip_validation }` (any may be unset/absent).

### Step 2: Detect Stack (BST-1)

**v1.0 scope: Python, Node, Go only.** Other languages are not auto-detected — callers must supply `language` explicitly for unsupported stacks (Rust, Ruby, Java, etc.).

**If `language` was provided in arguments:** Use it directly. Set `source = "from args"`. Use `project_type` from args, or default to `"poc"` if not provided.

**If `language` was NOT provided:** Scan the project root for marker files in the following priority order. First match wins.

| Priority | File | Detected Stack | Default Project Type |
|----------|------|---------------|---------------------|
| 1 | `pyproject.toml` | `python` | `library` |
| 2 | `setup.py` | `python` | `library` |
| 3 | `setup.cfg` | `python` | `library` |
| 4 | `requirements.txt` | `python` | `poc` |
| 5 | `package.json` | `node` | `library` |
| 6 | `go.mod` | `go` | `service` |

Use Glob or Read to check for each file in the project root directory (the working directory where the skill is invoked).

If `project_type` was provided in arguments, it overrides the default project type from detection.

**Version extraction** (best-effort — failure does NOT block bootstrap):
- **Python** via `pyproject.toml`: read `[project].requires-python` field. If absent, version = `3.x (unspecified)`.
- **Node** via `package.json`: read `engines.node` field. If absent, version = `(unspecified)`.
- **Go** via `go.mod`: read the `go X.Y` directive (typically line 3). If absent, version = `(unspecified)`.

**If no marker found and no args provided:** Print `No stack markers found in project root. Supply language explicitly: /e-spec:bootstrap python [project-type]` → exit 1.

Result: `{ language, version, project_type, source }`.

### Step 3: Discover & Match Blueprints (BST-5)

#### Discovery

Scan two blueprint directories:

1. **Primary (SDLC-scoped):** Glob `C:/Projects/APEX/.claude/blueprints/*/readme.md` — non-recursive, one level only.
2. **Secondary (project-scoped):** Glob `C:/Projects/APEX/blueprints/**/readme.md` — recursive, all depths.

If primary directory is not accessible → log `⚠ WARNING: C:/Projects/APEX/.claude/blueprints/ not accessible — continuing without primary blueprints.` (NOT a fatal error)
If secondary directory is not accessible → log `⚠ WARNING: C:/Projects/APEX/blueprints/ not accessible — continuing without secondary blueprints.` (NOT a fatal error)
If both inaccessible → log both warnings, continue with empty blueprint list. (NOT a fatal error — BST-5 AC)

For each readme path found:
- Derive `slug` from the parent directory name. Example: `.../poc-convention/readme.md` → slug = `poc-convention`.
- Read the first 30 lines of the readme (captures the header and "When to Use" section present in all current blueprints).
- Extract: display name (line 1, after `# `), any "When to Use" bullet items.
- Store as candidate: `{ name, slug, path }`.

**Dedup by slug:** If the same slug appears in both primary and secondary directories, the primary (`.claude/blueprints/`) entry wins — discard the secondary entry for that slug.

If an individual readme is unreadable → skip it, log `⚠ WARNING: Could not read {path} — skipping.`

#### Matching Rules

Apply all rules below — multiple blueprints can and should match simultaneously. This is expected and correct (e.g., a Python POC that uses spec-driven workflow matches both `poc-convention` and `spec-driven`).

| Blueprint | Matches When |
|-----------|-------------|
| `poc-convention` | `project_type == "poc"` OR project directory name starts with `poc-` |
| `spec-driven` | A `.claude/specs/` directory exists in the project root, OR `project_type` is one of `service`, `library`, `agent` |
| `model-calibration` | `project_type == "calibration"` OR project directory name contains `calibration` or `eval-model` |
| `substrate-eval` | `project_type == "substrate-eval"` OR project directory name contains `substrate` |
| (other blueprints found) | Keyword overlap: check if any keyword from the blueprint's "When to Use" section appears in `language` or `project_type` values |

Apply matching rules only to blueprints actually found during discovery. Use the discovered absolute paths — do not construct paths manually.

**If no blueprints matched:** Emit `⚠ No APEX blueprints matched — conventions will use stack defaults only.` (NOT a fatal error — BST-1 AC)

**Print selected blueprints to terminal BEFORE writing any file:**
```
Blueprints matched:
  poc-convention: C:/Projects/APEX/.claude/blueprints/poc-convention/readme.md
  spec-driven: C:/Projects/APEX/.claude/blueprints/spec-driven/readme.md
```

Result: list of `{ name, path }` for matched blueprints.

### Step 4: Compose Conventions Table (BST-2)

Build the fenced conventions block. Start with stack-specific defaults for all 10 rows, then apply blueprint overrides.

#### Stack-Specific Defaults

**Python defaults** (when `language == "python"` and no blueprint overrides the row):

| Convention | Default Value |
|---|---|
| Stack | `Python {version}, setuptools` |
| Layout | `src/{package_name}/` with `__init__.py`; `tests/` at project root |
| Naming | `Modules: snake_case, Classes: PascalCase, Functions: snake_case, Constants: UPPER_SNAKE, Files: snake_case` |
| Code style | `Linter: ruff, Formatter: black, Type checker: mypy, Line length: 120` |
| Deps | `Manager: pip, Lockfile: requirements.lock or [project.optional-dependencies] in pyproject.toml` |
| Tests | `Framework: pytest, Root: tests/, Naming: test_*.py, Mocks: unittest.mock` |
| Build + install | `` `pip install -e .[dev]` `` |
| Logging | `Format: structured (stdlib logging), Location: stderr, Retention: caller-managed` |
| Git | `Branch model: git-flow, Commit format: conventional, .gitignore: __pycache__/, *.pyc, .venv/, dist/, *.egg-info/` |

_Node/Go convention defaults deferred to future skill version per design.md Future Work._

**Other/unknown languages:** Use minimal placeholder defaults for all rows; source = "stack defaults (unknown stack)".

#### Blueprint Override Rules

When a matched blueprint mandates a value for a convention row, that value replaces the stack default. The Source column records the blueprint name and its discovered absolute path.

Current overrides:
- **`poc-convention`** overrides the **Layout** row → `src/` directory for all code (per poc-convention readme, standard layout section: `src/` contains all code, scripts, automation). Source: `poc-convention: {discovered-path}`.
- **`spec-driven`** does NOT override any convention row directly — it is a methodology blueprint, not a structural one. It appears in Blueprint refs only.

When two blueprints mandate conflicting values for the same row, the more specific structural blueprint wins. Log which blueprint was overridden and why.

#### Render the Fenced Block

Write the block using exactly this structure (replace `{...}` placeholders with actual values):

```
<!-- bootstrap-conventions -->
## Project Conventions

Validated: FAILED — validation did not complete (pre-flight)

| Convention | Value | Source |
|---|---|---|
| Stack | {language} {version}, {build tool} | {source} |
| Layout | {directory structure with explicit paths} | {blueprint name + path, or "stack defaults"} |
| Naming | Modules: snake_case, Classes: PascalCase, Functions: snake_case, Constants: UPPER_SNAKE, Files: snake_case | {blueprint or "language convention"} |
| Code style | Linter: {tool}, Formatter: {tool}, Type checker: {tool}, Line length: {N} | {blueprint or "stack defaults"} |
| Deps | Manager: {tool}, Lockfile: {policy} | {blueprint or "stack defaults"} |
| Tests | Framework: {tool}, Root: `tests/`, Naming: `test_*.py`, Mocks: {policy} | {blueprint or "stack defaults"} |
| Build + install | `{command 1}`<br>`{command 2}` | {blueprint or "stack defaults"} |
| Logging | Format: {structured JSON / plain}, Location: {path}, Retention: {policy} | {blueprint or "stack defaults"} |
| Git | Branch model: {model}, Commit format: {format}, .gitignore: {baseline entries} | {blueprint or "stack defaults"} |
| Blueprint refs | {name}: `{absolute-path-to-readme.md}` | — |
<!-- /bootstrap-conventions -->
```

**Critical notes on the template:**
- The `Validated:` line is set to `Validated: FAILED — validation did not complete (pre-flight)` at this stage — BEFORE any commands are executed. This ensures a crash or tool timeout during Step 7 leaves the block in FAILED state rather than an undefined state. The line is updated to PASS/FAIL/SKIPPED in Step 7.
- If a single Build + install command: `` `pip install -e .[dev]` `` — no `<br>` needed.
- If multiple Build + install commands: `` `pip install -e .[dev]`<br>`python -m pytest --co -q` `` — each command separated by literal `<br>` tag.
- If no blueprints matched, the Blueprint refs row value is: `None — no applicable APEX blueprints matched`.
- If multiple blueprints matched, list each on a separate line within the cell: `poc-convention: \`{path}\`` followed by a newline (or HTML line break) then `spec-driven: \`{path}\``.

Result: `proposed_block` — the full fenced block as a string, ready to write.

### Step 5: Check Existing CLAUDE.md & Apply Idempotency (BST-4, BST-7)

Read the project root `CLAUDE.md`. Walk this decision tree to determine the action:

```
Read project CLAUDE.md
  │
  ├─ FILE DOES NOT EXIST
  │    → action = CREATE
  │    → Proceed to Step 6.
  │
  ├─ File exists, NO <!-- bootstrap-conventions --> marker found
  │    → action = APPEND
  │    → Proceed to Step 6.
  │
  ├─ [PRE-COMPARISON] File exists, marker found,
  │   existing Validated line is NON-TERMINAL
  │   (Non-terminal = matches "FAILED" in any form, or "PENDING", or unrecognized state)
  │   (Terminal states = date-prefixed "… — build + install clean", or "SKIPPED (--force-skip-validation)…")
  │    → Non-terminal detected. Validation did not complete on last run. Force re-validation.
  │    → The --force flag and content identity are IRRELEVANT — always proceed through.
  │    ├─ proposed_block content IDENTICAL to existing (ignoring Validated line)
  │    │    → action = SKIP_WRITE (conventions unchanged, no need to rewrite)
  │    │    → Proceed directly to Step 7 (run validation).
  │    └─ proposed_block content DIFFERS from existing (ignoring Validated line)
  │         → action = REPLACE
  │         → Proceed to Step 6.
  │
  ├─ File exists, marker found, Validated IS terminal,
  │   proposed_block content IDENTICAL to existing (excluding Validated line)
  │    → Print: "Already bootstrapped — conventions unchanged. Nothing to do."
  │    → Set claude_md_action = "no changes"
  │    → Proceed to Step 8 (emit summary), exit 0.
  │
  ├─ File exists, marker found, Validated IS terminal,
  │   proposed_block content DIFFERS, --force NOT set
  │    → Compute and display diff of existing vs proposed (excluding Validated line from both sides).
  │    → Print: "Conventions differ. Re-run with --force to overwrite."
  │    → Set claude_md_action = "no changes", validation_status = "FAIL (diff-protect)"
  │    → Proceed to Step 8 (emit summary), exit 1.
  │
  └─ File exists, marker found, Validated IS terminal,
     proposed_block content DIFFERS, --force IS set
       → action = REPLACE
       → Proceed to Step 6.
```

**How to detect terminal vs non-terminal Validated line:**
- **Terminal PASS:** `Validated:` line matches `Validated: YYYY-MM-DD — build + install clean` (date-prefixed, any valid date)
- **Terminal SKIP:** `Validated:` line starts with `Validated: SKIPPED (--force-skip-validation)`
- **Non-terminal:** everything else — includes `Validated: FAILED — ...`, `Validated: FAILED — validation did not complete (pre-flight)`, `Validated: PENDING`, or any unrecognized text after `Validated:`.

**Identity comparison:** Strip the entire `Validated:` line from both the proposed block and the existing block before comparing. Comparison is byte-for-byte on the remaining text between the two fence markers.

### Step 6: Write/Update CLAUDE.md (BST-2, BST-7)

Apply the action determined in Step 5:

| Action | Tool | Method |
|--------|------|--------|
| **CREATE** | Write | Create a new file containing ONLY `proposed_block`. No preamble, no extra content. The project author adds their own content above the fence later. |
| **APPEND** | Edit | Append a blank line followed by `proposed_block` at the very end of the existing file. |
| **REPLACE** | Edit | Find the exact text from `<!-- bootstrap-conventions -->` through `<!-- /bootstrap-conventions -->` (inclusive, with all content between) and replace it with `proposed_block`. All content above and below the fenced block is preserved byte-for-byte. |
| **SKIP_WRITE** | (none) | Do not write. Proceed directly to Step 7. |

**NEVER write outside the fenced block.** Do not inject content elsewhere in CLAUDE.md.

**Post-write verification** — required after every CREATE, APPEND, or REPLACE (not SKIP_WRITE):
1. Re-read `CLAUDE.md` using Read tool.
2. Grep for `<!-- bootstrap-conventions -->` — must appear **exactly once**. If zero or more than one → print `ERROR: Expected exactly 1 opening marker, found {N}` → exit 1.
3. Grep for `<!-- /bootstrap-conventions -->` — must appear **exactly once**. If zero or more than one → print `ERROR: Expected exactly 1 closing marker, found {N}` → exit 1.
4. Verify the opening marker line number is less than the closing marker line number.
5. If any check fails → print exact diagnostic → exit 1.

Set `claude_md_action` based on the action taken: `"created"`, `"conventions appended"`, `"conventions updated (--force)"`, or `"no changes"`.

### Step 7: Run Build + Install Validation (BST-3)

#### If --force-skip-validation is set

1. Update the `Validated:` line inside the fenced block in CLAUDE.md:
   - Use Edit tool to replace the `Validated: FAILED — validation did not complete (pre-flight)` line with:
     `Validated: SKIPPED (--force-skip-validation) — NOT SAFE FOR SPEC WORK`
2. Print warning: `⚠ Validation skipped. Conventions are written but NOT verified. Do not start spec work until validated.`
3. Set `validation_status = "SKIPPED"`. Proceed to Step 8.

#### Extract commands from Build + install row

1. Locate the `Build + install` row in the conventions block. Read the cell value (the middle column).
2. Split on `<br>` — case-insensitive match: `<br>`, `<br/>`, `<BR/>`, `<BR>`. This produces one or more segments.
3. For each segment, strip surrounding backtick delimiters:
   - Strip leading/trailing whitespace first.
   - If wrapped in triple-backtick fences (` ``` `), strip the fences.
   - Then strip any remaining leading/trailing single backtick (`` ` ``).
   - The resulting string is the verbatim shell command.

Examples:
- Cell value `` `pip install -e .[dev]` `` → one command: `pip install -e .[dev]`
- Cell value `` `pip install -e .[dev]`<br>`python -m pytest --co -q` `` → two commands: `pip install -e .[dev]` then `python -m pytest --co -q`

**Delimiter rationale:** `<br>` is used instead of a text delimiter (e.g., ` then `) because text delimiters cannot be escaped — a build command containing the literal delimiter string would be silently mis-split into invalid fragments.

#### Execute each command sequentially

Run each command using the Bash tool in the project root directory. Timeout: 120000ms per command.

```
for each command in extracted_commands:
  result = Bash(command, cwd=project_root, timeout=120000)
  if result.exit_code != 0 (or timeout → treat as exit_code 124):
    - Update Validated: line in CLAUDE.md using Edit tool:
        Validated: FAILED — `{command}` exited {exit_code}. Re-run after fixing.
    - Print full stdout + stderr of the failing command to terminal.
      (This output appears ABOVE the terminal summary box in Step 8.)
    - Set validation_status = "FAIL"
    - Set failing_command = command, fail_exit_code = exit_code
    - STOP executing further commands.
    - Proceed to Step 8.

if all commands pass:
  - Get current date as YYYY-MM-DD.
  - Update Validated: line in CLAUDE.md using Edit tool:
      Validated: {YYYY-MM-DD} — build + install clean
  - Set validation_status = "PASS"
  - Proceed to Step 8.
```

### Step 8: Emit Terminal Summary (BST-6)

Print the following summary to terminal. The full stderr of any failing command has already been printed above this box (Step 7).

```
─────────────────────────────────────
Bootstrap {SUCCESS | FAILED | SKIPPED}

  Detected stack : {language} {version} ({source})
  Blueprints     : {name1}: {path1}
                   {name2}: {path2}
                   (or "none matched")
  CLAUDE.md      : {created | conventions appended | conventions updated (--force) | no changes}
  Validation     : {PASS | FAIL — `{command}`: exit {code} | SKIPPED (--force-skip-validation) | FAIL (diff-protect) — not attempted, conventions differ}
  Next step      : {message}
─────────────────────────────────────
```

**Status and next-step mapping:**

| Condition | Summary Status | Next step message |
|-----------|---------------|------------------|
| `validation_status == "PASS"` | `SUCCESS` | `Run /e-spec:spec to start your first feature` |
| diff-protect triggered (no --force, content differs) | `FAILED` | `Fix the validation error above, then re-run /e-spec:bootstrap` |
| `claude_md_action == "no changes"` (identical, no re-run) | `SUCCESS` | `Run /e-spec:spec to start your first feature` |
| `validation_status == "SKIPPED"` | `SKIPPED` | `Validate first with /e-spec:bootstrap before starting spec work` |
| `validation_status == "FAIL"` | `FAILED` | `Fix the validation error above, then re-run /e-spec:bootstrap` |

**Exit codes:**
- `0` — Bootstrap SUCCESS: conventions written and validated (PASS), or "no changes" (already bootstrapped, identical), or SKIPPED (explicit flag).
- `1` — Bootstrap FAILED: bad args, validation command failed, diff-protect guard triggered, post-write verification failure.

## Rules

- **No Task tool.** Bootstrap is a single-agent, single-pass skill. No sub-agents needed — per CLAUDE.md L2: "sub-agents are expensive."
- **No WebSearch or WebFetch.** All information comes from local files (blueprint readmes, project root markers).
- **Bash is required** for executing build + install commands (BST-3). Do not skip validation unless `--force-skip-validation` is set — omitting validation entirely is NOT a valid code path.
- **Never write outside the fenced block.** All content above `<!-- bootstrap-conventions -->` and below `<!-- /bootstrap-conventions -->` is preserved byte-for-byte. Use Edit to replace block content only — never inject text elsewhere in `CLAUDE.md`.
- **The conventions table has exactly 10 rows** in this exact order: Stack, Layout, Naming, Code style, Deps, Tests, Build + install, Logging, Git, Blueprint refs.
- **`<br>` is the multi-command delimiter** in the Build + install cell (case-insensitive). It is not a display choice — it enables unambiguous splitting. Do not use ` then `, newlines, or other delimiters.
- **Backtick stripping is mandatory.** Strip single or triple backticks from each extracted command before executing. Execute the bare shell command, not the backtick-wrapped version.
- **Every error path is visible.** No silent failures, no swallowed errors. If a Bash command fails, the full stderr is printed before the summary box.
- **Stack scope: Python, Node, Go for v1.0.** Do not auto-detect Rust, Ruby, Java, or other stacks. Callers must supply `language` explicitly for unsupported stacks. Detection will fail gracefully and prompt the user.
- **Blueprint paths are absolute** in the Blueprint refs row. Use the discovered absolute path exactly as returned by Glob — not a relative path, not a slug. Downstream agents must be able to navigate directly.
- **Pre-flight Validated line protects against mid-run crashes.** The fenced block is written with `Validated: FAILED — validation did not complete (pre-flight)` BEFORE any Bash commands execute. If the skill crashes mid-validation, the next plain re-run detects the non-terminal Validated state (PRE-COMPARISON branch in Step 5) and forces re-validation automatically — no manual CLAUDE.md edit needed.
- **Bootstrap is not auto-invoked.** It is a manual one-shot skill run before the first `/e-spec:spec`. The spec-driven lifecycle is: **bootstrap → spec → requirement → design → implement**. Bootstrap is a pre-lifecycle gate, not part of the cycle.
