# Code Dry-Run Report #2

**Scope**: `C:/Projects/APEX/sdlc/spec-enhanced/` (restructured plugin layout)
**Design**: N/A — structural migration; target layout defined in task directive
**Reviewed**: 2026-04-27

---

## Bugs (will cause incorrect behavior)

None found.

---

## Gaps (missing implementation)

### [G1] `hooks.json` missing `matcher` on Stop event entry
- **File**: `C:/Projects/APEX/sdlc/spec-enhanced/hooks/hooks.json` (Stop block)
- **Pass**: Pass 1 — Design Conformance / Pass 7 — Contract
- **What**: The `Stop` event entry has no `matcher` field. The source `settings.json` also had no matcher on the Stop entry, which is correct — Stop is a session-level event, not a tool event. This is **not** a bug; the format mirrors the source exactly and is consistent with the Claude Code hooks spec (Stop hooks don't use matchers).
- **Design ref**: Source `settings.json` lines 65–74; Claude Code Plugins Reference — Stop event.
- **Verdict on G1**: False alarm — no gap. Stop hooks do not require a matcher.

---

## Warnings (potential issues)

### [W1] `context_change_tracker.py` references `.claude/blueprints/` pattern — path will not match after migration
- **File**: `C:/Projects/APEX/sdlc/spec-enhanced/hooks/scripts/context_change_tracker.py:18`
- **Pass**: Pass 1 — Design Conformance
- **What**: The `CONTEXT_ARTIFACTS` dict contains the pattern `r"\.claude/blueprints/"`. Projects that have migrated to a non-`.claude/` blueprints layout (e.g., a `blueprints/` top-level directory) will not trigger the tracker for blueprint edits.
- **Risk**: Silent miss — blueprint edits go untracked in `eval.md`. This is a per-project configuration concern, not a plugin bug; the hook is intentionally configurable. Flag for consumer documentation.

### [W2] `context_eval_clear.py` clears `.claude/dryrun-*.md` — pattern won't match `specs/dryrun-*.md`
- **File**: `C:/Projects/APEX/sdlc/spec-enhanced/hooks/scripts/context_eval_clear.py:16`
- **Pass**: Pass 1 — Design Conformance
- **What**: `DRYRUN_PATTERN = ".claude/dryrun-*.md"` uses a glob rooted at project CWD with `.claude/` prefix. Since this plugin now places specs under `specs/` (not `.claude/specs/`), any dryrun files in the plugin's own `specs/` folder won't be cleared by this hook.
- **Risk**: Low — the hook targets the *consumer project's* dryrun artifacts, not the plugin's own specs. However, if a consumer project also moves dryruns out of `.claude/`, the pattern will silently miss them. A comment clarifying this is runtime-relative to the consumer project CWD would reduce confusion.

### [W3] `cross_module_guard.py` has project-specific defaults (`MODULES`, `SRC_ROOT`, `IMPORT_PKG`)
- **File**: `C:/Projects/APEX/sdlc/spec-enhanced/hooks/scripts/cross_module_guard.py:16–25`
- **Pass**: Pass 8 — Code Quality
- **What**: Defaults baked to a specific project (`sb`, `src/sb/`, modules: `agent/memory/gateway/event`). When the plugin is installed in another project, the guard either silently does nothing (no `SRC_ROOT` match) or guards wrong modules.
- **Risk**: Medium — misleading behavior. Correct approach is either to document override clearly or to exit silently with a log when `SRC_ROOT` is empty/unconfigured. Currently it exits silently when `SRC_ROOT` is not in the file path, which is acceptable fallback behavior. README now documents this (after Phase B update).

### [W4] `hooks/hooks.json` — `${CLAUDE_PLUGIN_ROOT}` expansion in hook commands
- **File**: `C:/Projects/APEX/sdlc/spec-enhanced/hooks/hooks.json`
- **Pass**: Pass 7 — Contract
- **What**: The plugins reference doc confirms `${CLAUDE_PLUGIN_ROOT}` is valid in hook commands (the MCP server example uses it, and the hooks example at line 100 of the reference shows it). However, the hooks doc example uses a shell script path. There is no explicit confirmation in the docs that Python invocations (`python ${CLAUDE_PLUGIN_ROOT}/hooks/scripts/foo.py`) receive the variable expansion. If Claude Code resolves `${CLAUDE_PLUGIN_ROOT}` only for native executables and not for command strings, hooks will fail to find the scripts.
- **Risk**: Medium — if expansion fails, all 8 hooks silently do nothing (non-zero exit, blocked). Recommend testing with `--plugin-dir` after install. Alternative: use `python "$CLAUDE_PLUGIN_ROOT/hooks/scripts/foo.py"` (shell quoting) or a thin shell wrapper.

---

## Style (code quality, conventions)

### [S1] `hooks.json` — no top-level schema comment or version field
- **File**: `C:/Projects/APEX/sdlc/spec-enhanced/hooks/hooks.json`
- **What**: The file is valid per spec but lacks any `// comment` or `$schema` annotation. Minor — JSON doesn't support comments; acceptable as-is.

---

## Summary

| Bugs | Gaps | Warnings | Style |
|------|------|----------|-------|
| 0 | 0 | 4 | 1 |

**Verdict**: PASS WITH WARNINGS

No bugs. No gaps. Four warnings — W1/W2/W3 are pre-existing per-project configuration concerns that the hook scripts document with `# CONFIGURE:` comments. W4 (CLAUDE_PLUGIN_ROOT expansion in Python invocations) is the only item that warrants a post-install smoke test. All 8 scripts are correctly referenced in `hooks.json`. README "Hooks included" section is present and accurate. `.claude/` directory is fully removed. Layout matches target spec exactly.
