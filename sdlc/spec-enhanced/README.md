# e-spec — Extended Spec-Driven SDLC Plugin

`e-spec` is a Claude Code plugin that packages 10 spec-driven SDLC skills under a single versioned namespace. It replaces copy-paste skill distribution across projects (FPAI, Velasari, Noteflow) with a single installable source — install once, update once, no drift between copies.

---

## Install

### Local (from disk)

```bash
claude --plugin-dir C:/Projects/APEX/sdlc/spec-enhanced
```

### From git

```
/plugin install <repo-url>#main:sdlc/spec-enhanced
```

Replace `<repo-url>` with the APEX repository URL (e.g., `https://github.com/kaushikhazra/APEX`).

---

## Namespace Gotcha

> All skills in this plugin are invoked with the `e-spec:` prefix.

| Wrong | Correct |
|-------|---------|
| `/requirement` | `/e-spec:requirement` |
| `/dryrun-design` | `/e-spec:dryrun-design` |
| `/implement` | `/e-spec:implement` |

Without the prefix, Claude Code resolves to project-local skills (if any) or returns a not-found error. The namespace prevents collision with any project-level skill of the same name.

---

## Skills

| Skill | Description |
|-------|-------------|
| `requirement` | Create a requirement under a spec — plans the work as todos, executes them, and produces the requirement.md content. Use after /spec has created the scaffolding. |
| `design` | Create a design under a spec — reads the requirement, plans the work as todos, executes them, and produces the design.md content. Use after /requirement has produced the requirements. |
| `implement` | Implement a spec — plans implementation todos with test strategy, writes task.md upfront, then executes each todo (code + unit tests). Use after /design has produced the design. |
| `spec` | Create a new spec — the .claude/specs/ folder with requirement.md, design.md, and task.md placeholders. Use when starting a new feature or work item. |
| `research` | Research any topic thoroughly using web search, then produce a structured research document in .claude/research/. Use when you need to investigate technologies, patterns, solutions, or any domain topic before making design decisions. |
| `dryrun-design` | Dry-run a design document to find gaps, missing paths, and architectural risks before implementation begins. Use when reviewing specs, design docs, or architecture decisions. |
| `dryrun-code` | Dry-run implemented code to find bugs, missing error handling, contract violations, and gaps against the design. Use after implementing a feature to validate correctness before testing. |
| `dryrun-blueprint` | Dry-run a blueprint by simulating building a new instance of that category. Finds missing steps, unclear conventions, and untestable patterns. |
| `dryrun-context` | Dry-run the project context (CLAUDE.md + blueprints) by simulating a new agent implementing a feature. Finds gaps, contradictions, and ambiguities in context engineering. |
| `dryrun-plan` | Dry-run a plan document to check completeness — are tasks actionable, decisions captured with rationale, and references valid? |

---

## Versioning

Current version: **1.0.0**

This plugin follows [semver](https://semver.org/):
- **Patch** (1.0.x): bug fixes to skill instructions, wording corrections
- **Minor** (1.x.0): new skills added, non-breaking changes to existing skill behavior
- **Major** (x.0.0): breaking changes — skill renamed, removed, or behavior fundamentally changed

To update downstream projects:

```
/plugin update e-spec
```

---

## Hooks included

Eight SDLC guardrail hooks ship with this plugin and are auto-loaded when the plugin is installed — no extra wiring or `settings.json` changes needed.

| Script | Event | What it does |
|--------|-------|-------------|
| `branch_name_validator.py` | PreToolUse (Bash) | Blocks `git checkout -b` / `git switch -c` commands that don't follow git flow naming (`feature/*`, `bugfix/*`, `hotfix/*`, `release/*`). |
| `context_change_tracker.py` | PostToolUse (Edit\|Write) | Detects edits to context artifacts (CLAUDE.md, blueprints, plans) and appends a pending checklist entry to `.claude/eval.md` so they're validated before commit. |
| `context_eval_clear.py` | PostToolUse (Bash) | Clears `.claude/eval.md` and transient dryrun reports after a `git commit` whose message includes "context evaluated". |
| `context_eval_gate.py` | Stop | Blocks the agent from stopping if `.claude/eval.md` has unchecked items; outputs a reminder to run the appropriate `/dryrun-*` skill. |
| `cross_module_guard.py` | PreToolUse (Edit\|Write) | Blocks direct cross-module imports between isolated modules; all cross-module communication must go through the configured IPC mechanism. Configure `MODULES`, `SRC_ROOT`, and `IMPORT_PKG` per project. |
| `protected_branch_guard.py` | PreToolUse (Edit\|Write\|Bash) | Blocks commits, protected-branch pushes, and source/test file edits on `main` and `develop`; forces use of feature/bugfix/hotfix/release branches. |
| `ruff_format.py` | PostToolUse (Edit\|Write) | Auto-runs `ruff check --fix` and `ruff format` on any edited `.py` file. Configure `RUFF_CMD` per project runner (uv, poetry, global). |
| `security_guard.py` | PreToolUse (Edit\|Write\|Read\|Bash) | Blocks access to sensitive files (`.env`, credentials, private keys) and destructive shell commands (`rm -rf /`, `format c:`, etc.). |

Hook configuration lives in `hooks/hooks.json` at the plugin root. Paths reference `${CLAUDE_PLUGIN_ROOT}/hooks/scripts/<script>.py` so they resolve correctly regardless of where the plugin is installed.

---

## Contributing

See `CLAUDE.md` in this directory for contributor guidance, coding principles, and the spec-driven workflow used to maintain this plugin itself.
