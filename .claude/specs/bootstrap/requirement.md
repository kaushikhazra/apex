# e-spec:bootstrap — Requirements

## Overview

On 2026-06-09 the Aakriti project completed a full spec-driven SDLC chain (spec → requirement → design → dryrun-design PASS → implement → dryrun-code PASS, 32/32 tests green) and then failed at the first manual smoke test: `pip install -e .[dev]` aborted with "Multiple top-level packages discovered in a flat-layout". The design had chosen a flat `aakriti/` layout. APEX's `poc-convention` blueprint (lines 53–59) mandates `src/` layout. But Aakriti's `CLAUDE.md` contained no project-layout convention, Aakriti's planning doc falsely claimed "no blueprints exist yet", and no skill in the chain had a mechanism to discover applicable APEX blueprints.

The class of failure: **projects open `/e-spec:spec` without first locking structural, coding, and build conventions**. Designers operate first-principles when APEX blueprints already mandate patterns. The `/e-spec:dryrun-code` skill validates via `pytest`, which bypasses `setuptools` package discovery — so the failure was invisible until human smoke test.

`/e-spec:bootstrap` is the missing gate. It runs **once per project, before the first `/e-spec:spec`**. It detects or accepts the project stack, selects applicable APEX blueprints, writes a locked conventions table into the project's `CLAUDE.md`, then **executes the documented install + build commands** — failing hard if they don't run clean. Only a PASSED bootstrap allows spec work to begin.

The skill ships alongside the 10 existing e-spec skills at:
`C:/Projects/APEX/sdlc/spec-enhanced/skills/bootstrap/SKILL.md`

---

## User Stories

### BST-1: Stack Detection and Blueprint Selection

**As a** project author,
**I want to** invoke `/e-spec:bootstrap` (with optional explicit language and project-type args) and have the skill auto-detect the project stack from root files, then match it against APEX blueprints,
**so that** the conventions the skill writes are grounded in APEX architectural patterns rather than in-context guesswork.

**Acceptance Criteria:**
- Skill reads project root for stack signals in this priority order: `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt` (Python); `package.json` (Node); `go.mod` (Go). First match wins.
- If explicit args are provided (e.g., `/e-spec:bootstrap python poc`), args override auto-detection entirely.
- Skill enumerates blueprints by reading each `readme.md` at `C:/Projects/APEX/.claude/blueprints/*/readme.md`, extracting name and "When to Use" section.
- Blueprint matching is performed by keyword overlap between the detected stack + project-type and each blueprint's category keywords (e.g., Python + POC → `poc-convention`; spec-driven workflow → `spec-driven`).
- Selected blueprints are listed with their full paths in the skill's terminal output before any file is written.
- If no matching blueprint is found, skill emits a WARNING message but does NOT fail — it proceeds with stack-derived conventions only and notes the absence in `CLAUDE.md`.
- If stack cannot be auto-detected and no args are provided, skill stops and asks the user to supply them.

---

### BST-2: Conventions Table Written to Project CLAUDE.md

**As a** project author,
**I want to** have the skill generate a fenced conventions section in the project's `CLAUDE.md` containing a locked conventions table,
**so that** every subsequent design, implement, and dryrun agent has a single unambiguous source of truth for layout, naming, tooling, and build commands — with no need to search across blueprints.

**Acceptance Criteria:**
- Conventions section is delimited by `<!-- bootstrap-conventions -->` and `<!-- /bootstrap-conventions -->` HTML comment markers, enabling idempotency detection (BST-4) and safe merging (BST-7).
- The conventions table contains exactly the following rows, in this order:

  | Convention | What gets set |
  |---|---|
  | Stack | Language, framework, runtime version (e.g., `Python 3.11+, setuptools`) |
  | Layout | Directory structure with explicit paths; cites APEX blueprint if one mandated it (e.g., `src/` layout per `poc-convention` lines 53–59) |
  | Naming | Modules (snake_case), classes (PascalCase), functions (snake_case), constants (UPPER_SNAKE), files (snake_case) |
  | Code Style | Linter (`ruff`), formatter (`black`), type checker (`mypy`), line length |
  | Deps | Manager (pip / poetry / pip-tools), lockfile policy (`requirements.lock` / `poetry.lock`) |
  | Tests | Framework (`pytest`), test root (`tests/`), mock policy, naming convention (`test_*.py`) |
  | Build + install commands | Exact runnable commands. Bootstrap executes these — FAIL on non-zero exit. |
  | Logging | Format (structured JSON vs plain), location (`logs/`), retention policy |
  | Git | Branch model, commit message format, `.gitignore` baseline entries |
  | Blueprint refs | Each applied blueprint: `{name}: {absolute-path-to-readme.md}` |

- Layout row must specify the blueprint that mandated the choice (by name and path), or state "no applicable blueprint — derived from stack defaults" if none matched.
- Build + install commands row must contain exact shell commands, not descriptions (e.g., `pip install -e .[dev]` not "run pip install").
- Blueprint refs row lists only blueprints that were selected in BST-1; empty if none matched.

---

### BST-3: Build and Install Validation Is Mandatory

**As a** project author,
**I want to** have the skill execute the documented install + build commands immediately after writing the conventions,
**so that** bootstrap only PASSes when the project can actually be installed and built — catching packaging failures like flat-layout `setuptools` errors before any spec work begins.

**Acceptance Criteria:**
- After writing the conventions section, skill executes each command in the "Build + install commands" row sequentially in the project root.
- If any command exits non-zero: skill captures the full stderr + stdout, reports the exact failing command and output, marks bootstrap as FAILED, and does NOT add the `Validated:` line to `CLAUDE.md`.
- A FAILED bootstrap leaves `CLAUDE.md` in an **unvalidated** state: the conventions section is written but the `Validated:` line reads `Validated: FAILED — {command} exited {code}. Re-run after fixing.`
- A PASSED bootstrap writes `Validated: {YYYY-MM-DD} — build + install clean` into the conventions section header.
- The `--force-skip-validation` flag bypasses execution; its use is logged as `Validated: SKIPPED (--force-skip-validation) — NOT SAFE FOR SPEC WORK` in the conventions section. This flag exists for offline/CI environments only.
- Omitting validation entirely (no flag, no execution) is NOT a valid code path — the skill must execute or skip with an explicit flag.
- Skill output clearly distinguishes PASS vs FAIL vs SKIPPED with a prominent terminal summary.

---

### BST-4: Idempotency — Protect Existing Validated Conventions

**As a** project author re-running bootstrap on an already-bootstrapped project,
**I want to** have the skill detect the existing conventions section and refuse to overwrite it without an explicit `--force` flag,
**so that** a validated conventions table cannot be accidentally destroyed by a casual re-run.

**Acceptance Criteria:**
- Before writing anything, skill checks for the `<!-- bootstrap-conventions -->` marker in project `CLAUDE.md`.
- If the marker is found AND proposed conventions are identical to existing ones: skill exits with message "Already bootstrapped — conventions unchanged. Nothing to do." and returns exit code 0.
- If the marker is found AND proposed conventions differ: skill computes and displays a diff (existing vs proposed), then exits with "Conventions differ. Re-run with --force to overwrite." and returns exit code 1.
- With `--force` flag and differing conventions: skill overwrites the fenced section, re-runs validation (BST-3), and updates the `Validated:` line accordingly.
- With `--force` flag but identical conventions: skill still exits with "Already bootstrapped — conventions unchanged." (no re-validation required).
- The `--force` flag does NOT bypass build/install validation — it only bypasses the diff-protect guard.

---

### BST-5: Blueprint Discovery — Embedding Paths for Downstream Agents

**As a** fresh-context worker arriving at a bootstrapped project,
**I want to** find exact APEX blueprint file paths in the project's `CLAUDE.md` conventions table,
**so that** I can navigate directly to the architectural patterns that govern this project without searching across the APEX codebase.

**Acceptance Criteria:**
- Skill reads `C:/Projects/APEX/.claude/blueprints/` to enumerate available blueprints (one subdirectory per blueprint).
- For each candidate blueprint, skill reads at minimum the first 30 lines of its `readme.md` to extract: display name, project-type keywords, and "When to Use" criteria.
- Blueprint-to-project matching rules:
  - `poc-convention` matches when project-type is `poc` or when the project slug starts with `poc-`.
  - `spec-driven` matches when the project contains a `.claude/specs/` directory or when project-type is `service`, `library`, or `agent`.
  - Additional blueprints at `C:/Projects/APEX/.claude/blueprints/` are matched by keyword overlap in their "When to Use" section.
- Blueprint refs row in conventions table lists each selected blueprint as: `{blueprint-name}: {absolute-path-to-readme.md}` — one entry per line within the cell.
- If `C:/Projects/APEX/.claude/blueprints/` is not accessible (path not found), skill logs a WARNING and continues without blueprint selection.
- A worker reading `CLAUDE.md` can open the blueprint path directly — no secondary search required.

---

### BST-6: Invocation Interface and Terminal Summary

**As a** project author,
**I want to** invoke bootstrap with optional explicit args and receive a clear terminal summary when the skill finishes,
**so that** I can verify what was detected, what was written, and whether validation passed before opening the first spec.

**Acceptance Criteria:**
- Skill accepts optional positional args: `{language}` (e.g., `python`, `node`) and `{project-type}` (e.g., `poc`, `service`, `library`, `agent`). Both are optional; either or both may be supplied.
- Skill accepts optional flags: `--force` (overwrite existing bootstrap section), `--force-skip-validation` (skip build execution with warning).
- Terminal summary printed at completion contains exactly these fields:
  - **Detected stack**: language + runtime version (or `from args: {value}`)
  - **Blueprints selected**: list of names + paths (or "none matched")
  - **CLAUDE.md**: `created` / `conventions appended` / `conventions updated (--force)` / `no changes`
  - **Validation**: `PASS` / `FAIL — {command}: {exit code}` / `SKIPPED (--force-skip-validation)`
  - **Next step**: `Run /e-spec:spec to start your first feature` (on PASS) or `Fix the validation error above, then re-run /e-spec:bootstrap` (on FAIL)
- On FAIL, the exact stderr output of the failing command is printed in full before the summary.
- Skill exits with code 0 on PASS or "no changes", code 1 on FAIL or diff-protect guard trigger.

---

### BST-7: Safe Merge with Pre-Existing CLAUDE.md Content

**As a** project author whose project already has a `CLAUDE.md` with project identity, instructions, or custom rules,
**I want to** have bootstrap append the conventions section without disturbing the existing content,
**so that** I don't lose project-specific instructions when bootstrapping.

**Acceptance Criteria:**
- If `CLAUDE.md` exists and contains content but has NO `<!-- bootstrap-conventions -->` marker: skill appends the conventions section at the end of the file, preceded by a blank line.
- If `CLAUDE.md` does not exist: skill creates it with only the conventions section (no extra content generated).
- All content above the `<!-- bootstrap-conventions -->` marker is untouched after the write.
- After writing, skill re-reads the file and verifies both `<!-- bootstrap-conventions -->` and `<!-- /bootstrap-conventions -->` markers are present at the correct positions, erroring if not.
- Skill never writes outside the `<!-- bootstrap-conventions --> ... <!-- /bootstrap-conventions -->` fenced block (no content injected elsewhere in `CLAUDE.md`).

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| APEX blueprint registry (`C:/Projects/APEX/.claude/blueprints/`) | Exists | Read-only. Skill reads `*/readme.md` for blueprint discovery. Never writes here. |
| Project root directory | Exists (caller-provided working dir) | Must be writable. Skill creates or modifies `CLAUDE.md` here. |
| Shell execution environment | Exists | Required to run install + build commands. Must support the project's package manager (pip, npm, etc.). |
| Python virtual environment (Python projects) | Caller responsibility | Skill does not create or manage the venv. If `pip install -e .[dev]` requires a venv, caller must activate it before invoking bootstrap. |

---

## Configuration Summary

### Invocation Arguments

```
/e-spec:bootstrap [language] [project-type] [--force] [--force-skip-validation]

language              Optional. e.g. python, node, go. Overrides auto-detection.
project-type          Optional. e.g. poc, service, library, agent. Overrides auto-detection.
--force               Overwrite an existing bootstrap-conventions section (requires diff to exist).
--force-skip-validation  Skip build/install command execution. Writes SKIPPED warning to CLAUDE.md.
```

### Files Written

```
{project-root}/CLAUDE.md    # Created or appended. Contains the fenced conventions section.
```

---

## Out of Scope

- Migrating existing projects that already have a `CLAUDE.md` with established (non-bootstrap) conventions — that requires a separate skill that diffs and proposes changes to live projects.
- Authoring or modifying APEX blueprints (`C:/Projects/APEX/.claude/blueprints/`). Bootstrap reads blueprints; it does not write them.
- Updating `/e-spec:design`, `/e-spec:implement`, or `/e-spec:dryrun-code` to actively consume the conventions table. Those skills benefit from the table being present in `CLAUDE.md` (they read it naturally), but wiring them to enforce it is a separate task.
- Multi-language support beyond Python. Python is the initial target. Node, Go, and others are future skill extensions.
- CI/CD pipeline configuration (GitHub Actions, GitLab CI, etc.).
- Docker or container configuration.
- Web-based interface or dashboard.
- Convention enforcement across existing source files (linting/reformatting pre-existing code to match conventions).
- Creating or managing virtual environments. Skill assumes the execution environment is caller-managed.
