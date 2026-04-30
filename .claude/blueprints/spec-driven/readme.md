# Spec-Driven Development — Blueprint

Every feature follows a spec lifecycle before code is written. Requirements drive design. Design drives implementation. No code exists without a spec behind it.

This blueprint is prescriptive: it defines the exact sequence, the exact files, and the exact rules. Deviation is not a style choice — it is a gap.

---

## The Lifecycle

```
/spec  →  /requirement  →  /design  →  /dryrun-design  →  fix  →  /implement  →  /dryrun-code  →  fix
  │              │               │              │                        │               │
scaffold     fills           fills         finds gaps              fills task.md    finds bugs
folder    requirement.md   design.md    numbered report         + writes code    numbered report
```

| Step | Skill | Input | Output | Gate |
|------|-------|-------|--------|------|
| 1 | `/spec` | Feature description | Spec folder + 3 empty files | None |
| 2 | `/requirement` | Spec name + what to capture | `requirement.md` | Spec folder exists |
| 3 | `/design` | Spec name + focus | `design.md` | `requirement.md` has user stories |
| 4 | `/dryrun-design` | Spec name | `dryrun-design-{N}.md` | `design.md` has content |
| — | Fix design | Dryrun report findings | Updated `design.md` | Dryrun verdict is not PASS |
| 5 | `/implement` | Spec name | `task.md` + code + tests | `design.md` has content, dryrun passed |
| 6 | `/dryrun-code` | Spec name or file path | `dryrun-code-{N}.md` | Implementation complete |
| — | Fix code | Dryrun report findings | Fixed code | Dryrun verdict is not PASS |

**Minimum viable path**: `/spec` → `/requirement` → `/design` → `/implement`.
**Quality path**: Add `/dryrun-design` before implementing and `/dryrun-code` after. Both are strongly recommended for non-trivial features.

---

## File Structure

Every spec lives under `.claude/specs/{slug}/`. The slug is kebab-case, 2–4 words derived from the feature description.

```
.claude/
└── specs/
    └── {feature-slug}/
        ├── requirement.md          # User stories + acceptance criteria
        ├── design.md               # Architecture, data models, decisions
        ├── task.md                 # Implementation checklist (living doc)
        ├── dryrun-design-1.md      # First design review
        ├── dryrun-design-2.md      # Second design review (if first found gaps)
        ├── dryrun-code-1.md        # First code review
        └── dryrun-code-2.md        # Second code review (if first found bugs)
```

**Slug examples:**

| Feature description | Slug |
|--------------------|------|
| "WebSocket backend for real-time log streaming" | `websocket-log-streaming` |
| "Circuit breaker pattern for MCP service calls" | `mcp-circuit-breaker` |
| "World Lore Validator agent" | `world-lore-validator` |
| "Voiceover audio export pipeline" | `audio-export-pipeline` |

**Fix/change specs** (e.g., `pipeline-fix.md`) live in the spec folder but are NOT design documents. See [Fix/Change Specs](#fixchange-specs) below.

---

## Step 1 — `/spec`: Scaffold the Folder

**What it does**: Creates `.claude/specs/{slug}/` with three empty placeholder files — `requirement.md`, `design.md`, `task.md`. Nothing else. No content is written.

**Input**: A description of the feature you're building.

```
/spec WebSocket backend for real-time agent log streaming
/spec World Lore Validator agent
/spec Voiceover audio export pipeline
```

**Output**:
```
.claude/specs/websocket-log-streaming/
  requirement.md   (empty)
  design.md        (empty)
  task.md          (empty)
```

**Rules**:
- One spec = one folder. No exceptions.
- Do not write content into the files during this step. They are placeholders.
- If the folder already exists, stop — do not overwrite.

---

## Step 2 — `/requirement`: Write the Requirements

**What it does**: Reads the project context, plans the requirement work as todos, executes them, and writes `requirement.md` with user stories and acceptance criteria.

**Gate**: The spec folder must exist from `/spec`.

**Input**: Spec name + what this requirement covers.

```
/requirement websocket-log-streaming Real-time streaming of agent structured logs to the UI
/requirement world-lore-validator Validates research packages for completeness and source quality
```

**Output**: `.claude/specs/{slug}/requirement.md` — structured as:

```markdown
# {Spec Title} — Requirements

## Overview
{1-3 paragraphs: what this is, why it matters, key constraints}

## User Stories

### {ABBR}-1: {Title}

**As a** {actor},
**I want to** {action},
**so that** {benefit}.

**Acceptance Criteria:**
- {Specific, testable criterion}
- {Another criterion}

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|

## Configuration Summary

### Environment Variables
VAR_NAME=<description>

## Out of Scope
- {Things explicitly NOT covered}
```

**Abbreviation convention**: 2–4 letters from the spec name, used to number all stories. Examples: `WLS-1`, `WLS-2` for WebSocket Log Streaming; `CB-1` for Circuit Breaker; `VLV-1` for Voiceover.

**Rules**:
- Every acceptance criterion must be testable. "Should work well" is not a criterion.
- Don't invent scope. Capture what was asked for. If something seems missing, add an "Open Questions" section.
- If `requirement.md` already has content, extend it — continue the numbering, merge new sections. Never overwrite existing content.

---

## Step 3 — `/design`: Write the Design

**What it does**: Reads the requirements, plans the design work as todos, executes them, and writes `design.md` with architecture, data models, decisions, and error handling.

**Gate**: `requirement.md` must have user stories. If empty, run `/requirement` first.

**Input**: Spec name + optional focus area.

```
/design websocket-log-streaming
/design mcp-circuit-breaker Retry and fallback strategies
/design world-lore-validator Data model and validation rules
```

**Output**: `.claude/specs/{slug}/design.md` — structured as:

```markdown
# {Spec Title} — Design

## Decisions Log

| # | Decision | Rationale |
|---|----------|-----------|
| D1 | {What was decided} | {Why — grounded in requirements or constraints} |

## 1. {Major Design Area}

**What**: The design decision and structure
**Why**: Traceability to requirement ({ABBR}-N) or architectural constraint
**How**: Enough detail to implement unambiguously — schemas, flows, code examples

## 2. {Next Design Area}
...

## Error Handling
{How failures are detected, handled, and recovered from}

## Files Changed

| File | Change |
|------|--------|
| {path} | {What changes and why} |

## Future Work (Out of Scope)
- {Things intentionally deferred, with brief rationale}
```

**Rules**:
- Decisions log is mandatory. Every non-obvious decision gets an entry.
- Every design decision must trace back to a requirement (`{ABBR}-N`) or an architectural constraint.
- Code examples use real language syntax (Python, TypeScript, SQL). Not pseudocode.
- "Store in the database" is not a design. Specify the schema, table, field names, and access pattern.
- If `design.md` already has content, extend it. Never overwrite.

**The vagueness rule**: If the design says "store in properties" or "use X field" without specifics, do NOT proceed to implementation. Vague design = incomplete design. Stop and clarify. Marking implementation tasks complete against a vague design produces broken software.

---

## Step 4 — `/dryrun-design`: Review the Design

**What it does**: Simulates executing the design in the reviewer's head — tracing data flows, state transitions, failure paths, interface contracts — and surfaces what's missing, broken, or underspecified.

**Gate**: `design.md` must have substantive content.

**Input**: Spec name or path to design document.

```
/dryrun-design websocket-log-streaming
/dryrun-design .claude/specs/world-lore-validator/design.md
```

**Output**: `.claude/specs/{slug}/dryrun-design-{N}.md` — where N is the next iteration number.

### What the dry-run checks

| Pass | What It Checks |
|------|---------------|
| 1. Completeness | Does every user story / acceptance criterion have a design element? |
| 2. Data Flow | Is every piece of data created, transformed, stored, and consumed consistently? |
| 3. Interface Contracts | Are cross-component boundaries explicitly defined on both sides? |
| 4. State Machines | Are all states, transitions, and terminal states accounted for? |
| 5. Failure Paths | Does every failable operation have a defined error path, retry strategy, blast radius? |
| 6. Concurrency | Are there race conditions, ordering assumptions, or deadlocks? |
| 7. Edge Cases | Empty inputs, boundary values, cold starts, partial deployments? |
| 8. Task Alignment | If task.md exists: does every task name actor, action, and target? |

### Report structure

```markdown
# Design Dry-Run Report #{N}

**Document**: {path}
**Reviewed**: {date}

## Critical Gaps (must fix before implementation)
### [C1] {title}
- **Pass**: {which pass}
- **What**: {specific gap}
- **Risk**: {what breaks if not fixed}
- **Fix**: {suggested resolution}

## Warnings (should fix, may cause issues)
### [W1] {title}
...

## Observations (worth discussing)
### [O1] {title}
...

## Summary
| Critical | Warnings | Observations |
|----------|----------|--------------|
| {count}  | {count}  | {count}      |

**Verdict**: PASS / PASS WITH WARNINGS / FAIL — needs revision
```

### Iteration tracking

Each `/dryrun-design` invocation creates a new numbered file. `dryrun-design-1.md` is the first pass. If you fix gaps and run again, `dryrun-design-2.md` is created. The count of dryrun files in a spec folder reflects how many review cycles the design needed — it is a quality signal, not a shame record.

**When to stop**: Once the verdict is `PASS` or `PASS WITH WARNINGS` and all critical gaps are resolved, proceed to `/implement`.

---

## Step 5 — `/implement`: Write the Code

**What it does**: Reads requirements and design, plans implementation as todos (with test strategy for each), writes `task.md` upfront with all tasks as `[ ]`, then executes todos — each producing code + unit tests.

**Gate**: `design.md` must have substantive content. Dryrun should have passed (or you accept the risk).

**Input**: Spec name + optional focus area.

```
/implement websocket-log-streaming
/implement mcp-circuit-breaker Retry and fallback only
/implement world-lore-validator
```

**Output**:
- `task.md` written upfront with all tasks as `[ ]`
- Working code for each todo
- Unit tests for each todo (90% coverage target)
- `task.md` updated inline (`[-]` while in progress, `[x]` when done)

---

## task.md — The Living Checklist

`task.md` is written at the start of `/implement` and updated in real time as work proceeds. It is the single source of truth for implementation progress.

### Status markers

| Marker | Meaning |
|--------|---------|
| `[ ]` | Pending — not started |
| `[-]` | In progress — being worked on now |
| `[x]` | Done — code written and tests passing |

### Required structure for every task

Every task must state three things:

1. **Actor** — who executes (which service, agent, component, or person)
2. **Action** — what gets done (implement, add, wire, refactor, configure)
3. **Target** — which component, file, or system

At the end of each task: a requirement reference `_{ABBR}-N_` linking it back to the user story it satisfies.

```markdown
# {Spec Title} — Tasks

## 1. {Section Title}

- [ ] {Actor} implements {target} — _{ABBR}-N_
  - [ ] {Sub-task detail}
  - [ ] {Sub-task detail}
- [ ] {Actor} wires {component} to {service} — _{ABBR}-N_
```

### Good vs bad tasks

| ❌ Bad | ✅ Good |
|-------|--------|
| `- [ ] Write models` | `- [ ] Agent writes ResearchJob, JobStatus models in src/models.py — _WLS-1_` |
| `- [ ] Implement daemon` | `- [ ] Consumer daemon wires RabbitMQ listener in daemon.py with prefetch=1 — _WLS-2_` |
| `- [ ] Error handling` | `- [ ] WebSocket handler catches disconnect and publishes StatusUpdate(failed) to queue — _WLS-3_` |
| `- [ ] Tests` | (Tests are sub-tasks of the implementation task, not separate items) |

**The shortcut test**: If a task can be read two ways — one that follows the architecture and one that shortcuts it — it **will** be shortcut. Be explicit about which layer owns the work.

### Nesting rules

- Maximum 2 levels deep
- Sub-tasks are detail within a single unit of work, not separate features
- Do not nest tasks purely for visual grouping

### The living document contract

- Write all tasks as `[ ]` before writing any code
- Mark `[-]` the moment you start a task
- Mark `[x]` the moment the tests pass — not "when I think it's done"
- `task.md` should reflect real-time state, not retroactive bookkeeping

---

## Step 6 — `/dryrun-code`: Review the Code

**What it does**: Simulates executing the code — tracing call chains, error paths, resource management, contract violations — and surfaces bugs, gaps, and design deviations before testing.

**Gate**: Implementation complete (or partially complete, for incremental review).

**Input**: Spec name, file path, or folder path.

```
/dryrun-code websocket-log-streaming
/dryrun-code src/agents/world_lore_validator/
/dryrun-code src/services/circuit_breaker.py
```

**Output**: `.claude/specs/{slug}/dryrun-code-{N}.md` — where N is the next iteration number.

### What the dry-run checks

| Pass | What It Checks |
|------|---------------|
| 1. Design Conformance | Does the code implement the design? Are there undesigned behaviors? |
| 2. Execution Path | Trace happy path end-to-end — correct order, correct data, correct returns? |
| 3. Error Paths | Every failable operation — caught? Handled? Or silently swallowed? |
| 4. Input Validation | None/null, empty, boundary values, type assumptions? |
| 5. Resource Management | Connections, files, handles — opened AND closed on all paths? |
| 6. Concurrency | Async correctness, shared mutable state, deadlocks? |
| 7. Contract Violations | External calls — all response states handled? Timeouts? Schema validation? |
| 8. Code Quality | SOLID, DRY, KISS violations, magic numbers, logging levels, TODO comments? |
| 9. Security | User input reaching shell/SQL/file paths, secrets in logs? |

### Report structure

```markdown
# Code Dry-Run Report #{N}

**Scope**: {file or folder}
**Design**: {design doc path}
**Reviewed**: {date}

## Bugs (will cause incorrect behavior)
### [B1] {title}
- **File**: {path}:{line}
- **Pass**: {which pass}
- **What**: {the bug}
- **Impact**: {what goes wrong}
- **Fix**: {exact fix, with code if short}

## Gaps (missing implementation)
### [G1] {title}
- **File**: {path}:{line} (or "missing file")
- **Design ref**: {section in design doc}

## Warnings (potential issues)
### [W1] {title}
- **Risk**: {when this becomes a problem}

## Style (code quality, conventions)
### [S1] {title}

## Summary
| Bugs | Gaps | Warnings | Style |
|------|------|----------|-------|
| {count} | {count} | {count} | {count} |

**Verdict**: PASS / PASS WITH WARNINGS / FAIL — has bugs or critical gaps
```

### Iteration tracking

Same pattern as design dryruns — each invocation creates a new numbered file. `dryrun-code-1.md` for first review, `dryrun-code-2.md` after fixes, and so on.

**When to stop**: Once the verdict is `PASS` or `PASS WITH WARNINGS` with no bugs or critical gaps, the feature is ready for integration testing.

---

## Fix/Change Specs

When bugs or design gaps require targeted changes, document them as a fix spec in the spec folder (e.g., `.claude/specs/{slug}/pipeline-fix.md`).

**A fix spec is NOT a design document.** It is surgical instruction only:

```markdown
# {Slug} — Fix: {Short Description}

## What's Broken
{Exact description of the problem — reference the dryrun finding [C1], [B2], etc.}

## What Changes
{Exactly what needs to change — files, functions, data structures, behavior.
Be precise enough that there's only one correct interpretation.}

## How to Verify
{Specific steps to confirm the fix works — test cases, expected outputs, behaviors to check.}
```

**What a fix spec is NOT**:
- A retrospective on why it broke
- An options analysis for decisions already made
- Documentation of things that aren't changing
- A mini design document with sections on background and context

If a fix is large enough to require architecture decisions, it has grown into a proper spec revision — update `design.md` directly and run `/dryrun-design` again.

---

## Tracking Work — Two Systems, No Duplication

| System | Role | Contains |
|--------|------|----------|
| **Project tracker (Taskyn / Jira / etc.)** | Dashboard | Status, priority, dependencies, time tracking. Links to spec files. |
| **`.claude/specs/`** | Substance | Full detail — user stories, architecture, task checklists. Source of truth. |

**Rules**:
- Tracker nodes link to spec files. Never duplicate long-form content in the tracker.
- Everything tracked — no untracked work.
- Time tracking is mandatory — every work session has a timer running.
- Create tracker tasks only when starting work, directly in "approved" or "in progress". Mark done immediately when complete. One transition, inline with real work.

---

## Anti-Patterns — Push Back on These

| # | Anti-Pattern | Rule | Principle |
|---|-------------|------|-----------|
| A1 | **Skipping dryrun before implementing** | A design review costs 2 minutes. A missed failure path costs 2 days of debugging. Run `/dryrun-design` before committing to implementation. | Find gaps on paper, not in production. |
| A2 | **Skipping dryrun after implementing** | `/dryrun-code` is not "optional for simple features." Simple features have edge cases too. Run it. | Unreviewed code is unfinished code. |
| A3 | **Vague task specs without actor/action/target** | If a task says "implement error handling" — who? in what component? which error? That task will be shortcut. Name the actor, action, and target. | Tasks say *who does what*. Design says *why*. |
| A4 | **Bulk-populating the task tracker upfront** | Don't create 30 tasks in the tracker before writing any code. Create parent nodes for visibility; add granular tasks only when starting work. Mark done immediately. | Track work as you do it, not before or after. |
| A5 | **Writing code before requirements exist** | Design cannot proceed without requirements. Implementation cannot proceed without design. The gates exist for a reason — don't skip them. | Every line of code traces to a user story. |
| A6 | **Treating task.md as post-hoc documentation** | `task.md` is written upfront and updated in real time. If you finish implementation and then write `task.md`, you've broken the contract. | `task.md` is a living document, not a changelog. |
| A7 | **Marking tasks done before tests pass** | A task is done when its tests pass — not when "I think the code is right." `[x]` means tested and confirmed. | Done means done. |
| A8 | **Inventing scope in requirements** | Requirements capture what was asked for. If something seems missing, add it to "Open Questions" — don't invent user stories. | Unasked-for features are unvalidated assumptions. |
| A9 | **Writing fix specs as mini design docs** | A fix spec answers three questions: what's broken, what changes, how to verify. No background, no options analysis, no retrospective. | Surgical fixes need surgical documents. |
| A10 | **Proceeding past a FAIL dryrun verdict** | If the dryrun says FAIL, fix the gaps before proceeding. A FAIL is not a suggestion. | A known gap is a known bug. |

---

## Quick Reference — Which Skill Does What

| Skill | Use When | Don't Use When |
|-------|----------|----------------|
| `/spec` | Starting a new feature | The feature already has a spec folder |
| `/requirement` | Capturing what to build | You haven't created the spec folder yet |
| `/design` | Deciding how to build it | requirement.md is empty |
| `/dryrun-design` | Before writing any code | The design is a stub or placeholder |
| `/implement` | Writing code against a design | design.md is empty or vague |
| `/dryrun-code` | After completing a feature or module | The code is incomplete; wait until a unit is done |
| `/research` | Evaluating technologies, comparing options | You already know what to use |
| `/dryrun-blueprint` | Validating a new blueprint before publishing | The blueprint is a draft concept |

---

## Real Examples from Our Projects

These specs illustrate the methodology applied across different domains.

### Velhari — World Lore Validator

**Spec**: `.claude/specs/world-lore-validator/`
**What it demonstrates**: A validation agent spec with multiple user story types (author-facing, system-facing), clear infrastructure dependencies (Storage MCP, Lore Graph MCP), and a data flow design that traces research packages from ingestion through scoring to feedback.

Illustrates:
- Multi-actor requirement: the "author" story and the "system" story are distinct
- Design sections numbered and sequenced: data model → processing pipeline → scoring algorithm → feedback loop
- Error handling designed explicitly for each external call (MCP failures, invalid packages)

### Voiceover — Audio Export Pipeline

**Spec**: `.claude/specs/audio-export-pipeline/`
**What it demonstrates**: A background processing pipeline spec where the design must handle long-running async operations, queue management, and progress streaming to the UI.

Illustrates:
- Out-of-scope section actively used (real-time preview excluded, deferring to future spec)
- Fix spec used after dryrun-code found a resource leak in the FFmpeg subprocess handler
- Two dryrun-design iterations: first pass surfaced missing error path for disk-full condition

### Taskyn — CQRS Write Pipeline

**Spec**: `.claude/specs/cqrs-write-pipeline/`
**What it demonstrates**: A spec where the design references an existing blueprint (`blueprints/multi-agent/cqrs-bridge.md`) rather than reinventing the pattern, showing the spec-plus-blueprint composition.

Illustrates:
- Design decisions log referencing architectural constraints from CLAUDE.md, not just requirements
- task.md tasks that explicitly name the "backend sole writer" constraint in every data-mutating task
- `/dryrun-design` Pass 3 (Interface Contracts) surfacing a missing contract between the event bus and the write service

---

## What This Blueprint Is Not

- **Not a project management framework.** This is an engineering methodology — how to go from idea to shipped code. Standup ceremonies, sprint planning, and release processes are out of scope.
- **Not a code review process.** Dryrun is a pre-implementation review of design and a pre-testing review of code. It complements — it does not replace — peer code review, CI pipelines, or integration testing.
- **Not a waterfall.** The spec lifecycle is lightweight. A `/spec` + `/requirement` + `/design` + `/implement` cycle for a small feature takes hours, not weeks. The discipline is what makes speed sustainable.
