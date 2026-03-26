# Spec-Enhanced SDLC

A portable, spec-driven development methodology. Copy this file into any project and adapt the project-specific sections to your stack.

---

## Git Flow

- `main` → `develop` → `feature/*`, `bugfix/*`, `release/*`, `hotfix/*`
- Protected branches (`main`, `develop`): no direct commits or pushes. Create a feature/bugfix branch first.
- Never check in any `temp` folder or files with `temp` prefix/suffix.

---

## Spec-Driven Development

**What**: Every feature follows a spec lifecycle before code is written.
**Where**: `.claude/specs/{feature}/` — three core documents per spec, plus review artifacts.

| Document | Purpose | Format |
|----------|---------|--------|
| `requirement.md` | User stories + acceptance criteria | Agile user stories |
| `design.md` | Architecture, data models, decisions | Free form |
| `task.md` | Implementation checklist | Bullet list, max 2 levels deep |
| `dryrun-design-{N}.md` | Design review iteration N | Structured report (gaps, warnings, verdict) |
| `dryrun-code-{N}.md` | Code review iteration N | Structured report (bugs, gaps, warnings, verdict) |

Dryrun files are numbered sequentially (1, 2, 3...) — each `/dryrun-design` or `/dryrun-code` invocation creates a new file. This tracks how many review iterations it took.

### task.md Rules

- `[ ]` pending, `[-]` in progress, `[x]` done
- Reference the requirement at the bottom of each task: `_{requirement}_`
- Every task must state the **actor** (who executes), the **action** (what gets done), and the **target** (which service/component). If a task can be read two ways — one that follows the architecture and one that shortcuts it — it **will** be shortcut.

### Fix/Change Specs

Fix/change specs (e.g., `pipeline-fix.md`): NOT a design document. Surgical instruction only — **what's broken**, **what exactly changes**, **how to verify**. No retrospectives, no option debates for decisions already made, no documenting things that aren't changing.

### Vagueness Rule

If a design document says "store in properties" or "use X field" without specifics, do NOT mark tasks as complete. Vague design = incomplete implementation. Stop and ask.

---

## File Organization

All planning and research artifacts live under `.claude/`.

| Folder | What goes here |
|--------|---------------|
| `.claude/plans/` | Implementation plans — numbered sequentially: `{NNN}-{slug}.md` (e.g., `001-development-standards.md`). Check the highest existing number before creating a new file. |
| `.claude/research/` | Research notes — numbered sequentially: `{NNN}-{slug}.md` (e.g., `013-local-architecture.md`). Check the highest existing number before creating a new file. |
| `.claude/specs/{feature}/` | Spec documents (requirement.md, design.md, task.md) |
| `.claude/blueprints/{category}/` | Architectural patterns (see below) |

---

## Blueprints — Architectural Patterns

**What**: The architect's preferred way to build a category of thing — structural decisions earned through experience.
**Where**: `.claude/blueprints/{category}/` with `readme.md` as index.
**Why**: Prescriptive, not descriptive. When building a new instance of that category, follow the blueprint. To change a decision, update the blueprint first, then apply consistently.
**What they capture**: Folder structure, wiring conventions, file-level anatomy, constraints, deployment patterns.
**Golden rule**: Blueprints teach the **pattern**, not the instance. A blueprint for "how to create a service" (with sections on adding endpoints, wiring dependencies) is correct. A blueprint for "how to create the user service" is wrong — that's a spec. If content is specific to one feature, it belongs in a spec. If it teaches how to build any instance of a category, it's a blueprint.

---

## Coding Principles

| Principle | Rule |
|-----------|------|
| SOLID, DRY, KISS | Always. But three similar lines are better than a premature abstraction. |
| Design patterns | Preferred. Free to invent new ones — discuss with team first. |
| Reuse before build | Search the web for existing libraries first. If multiple exist, present with recommendations. Only build custom if nothing fits — and that's an open-source opportunity. |
| Root cause over patch | When something seems off, investigate fully. Don't rush past problems. Thoroughness over speed. |
| Consistency sweeps | When fixing an inconsistency (e.g., port mismatch), grep the entire codebase for ALL references. Fix every one. Surface fixes leave hidden bugs. |

---

## Coding Standards

> **Configure per project.** Add your language-specific style guide, linter, formatter, and naming conventions here. The principles below are language-agnostic.

- **Comments**: inline comments sparingly, only when the *why* isn't obvious from the code. Never restate what the code does.
- **Type safety**: prefer typed interfaces for all data crossing module/service boundaries. Use your language's idiomatic validation (e.g., Pydantic for Python, Zod for TypeScript, serde for Rust).
- **Error handling**: never silence exceptions/errors. Log and re-raise, or handle explicitly. Include correlation/trace IDs in log entries for cross-service tracing.

---

## Testing

> **Configure per project.** Adapt tiers, tooling, and markers to your stack. The structure below is the pattern.

Three tiers:

| Tier | Location | What It Tests | External Deps | When to Write |
|------|----------|--------------|---------------|---------------|
| **Unit** | `tests/unit/` | Business logic — pure functions, transformations, validators | None | Every non-trivial function |
| **Functional-Integration** | `tests/functional/` | Cross-module/service flows — publish event, handler fires, expected response | External services (localhost) | Every cross-module interaction |
| **End-to-End** | `tests/e2e/` | Full user scenarios from the user's perspective | Full stack | Critical user paths |

**Rules**:
- Unit tests: no external services, no network. Test logic in isolation.
- Functional-integration tests: real services on localhost. Validates contracts, routing, handler registration.
- End-to-end tests: full system running. Test from the user's perspective.
- Test files mirror source structure.

---

## Dependencies

Every new dependency needs a reason. Prefer stdlib or existing deps over adding new ones. Pin major versions. Lock file handles exact versions.

---

## Tracking Work

Two systems, no duplication.

| System | Role | Contains |
|--------|------|----------|
| **Project tracker** | Dashboard | Status, priority, dependencies, time tracking. Links to spec files. |
| **`.claude/specs/`** | Substance | Full detail — user stories, architecture, task checklists. Source of truth. |

**Rules**:
- Tracker nodes point to spec files. Never duplicate long-form content.
- Everything is tracked — no untracked work.
- Time tracking is mandatory — every work session has a timer running.
- Create stories/tasks only when starting work, directly in "approved" or "in_progress". Mark done immediately when complete. One transition, inline with real work.

---

## Lessons Learned — Push Back on These

| # | Anti-Pattern | Rule | Principle |
|---|-------------|------|-----------|
| L1 | Bulk-populating task trackers upfront | Create parent nodes for visibility. Add tasks **only when starting work**. Mark done immediately. | Track work as you do it, not before or after. |
| L2 | Launching sub-agents for bookkeeping | Sub-agents are expensive. If a task is "just updating statuses", the process should have kept things in sync. Scope sub-agents tightly. | If it smells like waste, it is waste. |
| L3 | Task specs that describe operations without naming the actor | Every task must say **who** does **what** with **which** component. Architecturally silent tasks get shortcut implementations. | Design says *why*. Tasks say *who does what*. |
| L4 | Building custom MCP wrappers for capabilities that already exist | Search for existing MCP servers or libraries first. Only build custom MCP services for domain-specific logic, not thin wrappers around a single library call. | MCP services should contain domain logic, not `library.do_thing()`. |
