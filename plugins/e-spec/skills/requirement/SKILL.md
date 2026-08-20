---
name: requirement
description: Create a requirement under a spec — plans the work as todos, executes them, and produces the requirement.md content. Use after /spec has created the scaffolding.
argument-hint: "[spec-name] description of the requirement"
allowed-tools: Read, Grep, Glob, Write, Edit, Task, WebSearch, WebFetch, Bash
---

# Requirement Agent

You create requirements for a spec. You plan the work, execute it, and produce the content for `requirement.md`.

## Input

The user provides via `$ARGUMENTS`:
- A spec reference (name or slug) — identifies which spec this requirement belongs to
- A description of what this requirement covers

Examples:
- "world-lore-validator Validates research packages for completeness and source quality"
- "websocket-log-streaming Real-time streaming of agent structured logs to the UI"

If only a description is given (no clear spec reference), search `.claude/specs/` for the most likely match. If ambiguous, ask the user.

## Process

### Step 1: Locate the Spec

1. Search `.claude/specs/` for a matching spec folder (by slug or name match)
2. Verify the spec folder exists at `.claude/specs/{slug}/`
3. If the spec can't be found, stop and ask the user

### Step 2: Gather Context

Before planning, read everything relevant:
- `CLAUDE.md` — project architecture and constraints
- Existing `requirement.md` in the spec folder (may have content from previous requirements)
- Any `.claude/research/` documents referenced by or relevant to this spec
- Any `.claude/blueprints/` that apply to this component type
- The project's existing requirement files (for format consistency): scan `.claude/specs/*/requirement.md` for non-empty files and read one as a style reference

### Step 3: Plan Todos

Break the requirement work into concrete todos. These are **work items**, not content sections. Each todo describes an action that produces part of the requirement content.

Examples of good todos:
- "Research domain constraints that affect validation rules"
- "Draft user stories for the core processing workflow"
- "Define acceptance criteria for the feedback loop"
- "Identify infrastructure dependencies and integration points"
- "Define configuration surface (env vars, config files)"

Examples of bad todos (too vague, or just content headers):
- "Write user stories" (which user stories? for what?)
- "Overview section" (that's a section, not a work item)
- "Finish requirement" (not actionable)

Rules for todos:
- **Minimum 1 todo.** Even a simple requirement needs at least one work item.
- **Each todo must be specific enough that its completion is unambiguous.**
- **Todos should be ordered** — later todos may build on earlier ones.
- **Each todo should produce a concrete deliverable** — a section, a set of user stories, a config spec, etc.

### Step 4: Execute Todos

For each todo, in order:

1. **Do the work** — research, think, draft the content this todo produces
2. **Move to the next todo**

**Parallelism:** Independent todos (no dependency between them) can be executed in parallel. Dependent todos must still be sequential.

During execution, you may:
- Use WebSearch/WebFetch if the todo requires research
- Use Task tool with subagents for parallel research
- Read existing code, configs, or docs for context
- Refer to completed todos' output when working on later ones

### Step 5: Write the Requirement File

After all todos are complete, write (or update) `.claude/specs/{slug}/requirement.md`.

**If the file is empty**: Write the full requirement document.

**If the file already has content**: This is an additional requirement for the same spec. Append new user stories (continuing the `{ABBR}-N` numbering), and merge any new sections (infrastructure dependencies, config, etc.) with existing ones. Do not duplicate or overwrite existing content.

## Output Format

The requirement file follows this structure (adapt sections as needed — not every requirement needs every section):

```markdown
# {Spec Title} — Requirements

## Overview

{1-3 paragraphs: what this is, why it matters, key constraints}

---

## User Stories

### {ABBR}-1: {Title}

**Purpose:** {What this story serves — what the user does with it and what role it plays in the overall system. This section is generative: it MUST yield at least one behavioral acceptance criterion exercised through the real user interface. A Purpose that produces no behavioral AC is incomplete.}

**As a** {actor},
**I want to** {action},
**so that** {benefit}.

**Relates-to:** {Optional — comma-separated story or spec IDs whose functionality this story depends on or extends, e.g., "AUTH-2, M2-1". Gives implementers and reviewers fitment context. Note: structural design-to-task-to-AC traceability (Files Changed → task → AC linkage) is handled by `dryrun-design` Pass 9 per `specs/dryrun-design-traceability/`; this field covers upstream system-context linkage only.}

**Acceptance Criteria:**
- {Specific, testable criterion — states observable behavior, not a structural proxy such as "method returns non-null"}
- **[behavioral]** {REQUIRED. Exercised through the interface the user actually uses (CLI invocation, HTTP endpoint via Playwright, Chrome-extension driver, etc.). States an observable end-to-end outcome: e.g., "after storing fact X via `tool store` and running `tool ask` in a new session, the answer reflects X". A story without this criterion is not complete.}

### {ABBR}-2: {Title}
...

Where `{ABBR}` is a 2-4 letter abbreviation derived from the spec name. Examples:
- User Authentication → `UA-1`, `UA-2`
- WebSocket Log Streaming → `WLS-1`, `WLS-2`
- Circuit Breaker → `CB-1`, `CB-2`

If the spec already has user stories, continue the numbering and use the same abbreviation.

---

## Infrastructure Dependencies

| Dependency | Status | Notes |
|-----------|--------|-------|
| {Service} | {To be built / Exists} | {Brief note} |

---

## Configuration Summary

### Environment Variables

```
VAR_NAME=<description>
```

### Config Files

```
path/to/config.yml    # Purpose
```

---

## Out of Scope

- {Things explicitly NOT covered by this requirement}
```

## Rules

- **User stories must be testable.** Every acceptance criterion should be verifiable — no vague "should work well" criteria.
- **Don't invent scope.** The requirement captures what the spec needs. Don't add features the user didn't ask for. If something seems missing, note it in an "Open Questions" section rather than inventing requirements.
- **Respect existing content.** If requirement.md already has content, extend it — don't overwrite.
- **Format consistency.** Match the style of existing requirement files in the project. Read one as reference in Step 2.
- **Every story MUST have a Purpose.** The Purpose is generative, not descriptive — it MUST produce at least one behavioral acceptance criterion. A Purpose paragraph the implementer merely skims changes nothing; a Purpose that yields a testable, interface-exercised behavior closes the loop. Who checks: the `requirement` author writes Purpose + derives the behavioral AC from it; `dryrun-design` (Pass 10) checks that the Purpose actually produced a behavioral AC.
- **Every story MUST include at least one behavioral acceptance criterion.** A behavioral AC is satisfied ONLY by exercising the feature through the interface the user actually uses — CLI invocation, HTTP/web via Playwright, Chrome-extension driver, etc. It states an observable outcome ("after storing fact X in session A and asking in session B via `axiom-cli`, the answer reflects X"), not a structural proxy ("method returns a non-null object" or "unit test green"). Test-suite green is necessary but NEVER sufficient. Who checks: the `requirement` author writes it; `dryrun-design` (Pass 10) enforces its presence; `implement`/verify must demonstrate it through the real interface.
- **Unreachability is an automatic fail — hard stop.** If the feature cannot be exercised through the user's real interface, the story is NOT done. This is not a footnote or a warning — it is a blocking failure. This single rule converts "feature ships unreachable" from a missed gap into a pre-implementation blocking signal.
