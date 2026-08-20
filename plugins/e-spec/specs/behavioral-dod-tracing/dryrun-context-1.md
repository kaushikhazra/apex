# Dryrun-Context Report #1 — Behavioral DoD + Value-Path Tracing (e-spec 1.2.0)

**Scope**: Plugin instruction edits on branch `feature/behavioral-dod-tracing` (commit 73b1407)
**Change-spec**: `sdlc/spec-enhanced/specs/behavioral-dod-tracing/change-spec.md`
**Reviewed**: 2026-07-15

---

## Check 1: COHERENCE

**Question**: Do the new additions contradict or redundantly overlap existing content — especially Pass 9?

### New content inventory

| Location | Addition |
|----------|----------|
| `requirement/SKILL.md:103` | Purpose field in story template (generative, must yield behavioral AC) |
| `requirement/SKILL.md:109` | Relates-to field in story template (optional, system-context linkage) |
| `requirement/SKILL.md:113` | `[behavioral]` AC tag in template (mandatory, exercised through real interface) |
| `requirement/SKILL.md:162` | Rule: every story MUST have a Purpose |
| `requirement/SKILL.md:163` | Rule: every story MUST include ≥1 behavioral AC |
| `requirement/SKILL.md:164` | Rule: unreachability is automatic fail — hard stop |
| `dryrun-design/SKILL.md:194-232` | Pass 10: Behavioral DoD Challenge |
| `dryrun-code/SKILL.md:96-144` | Pass 10: Value-Path Trace |

### Pass 9 vs Pass 10 — distinguished or colliding?

**Pass 9** (dryrun-design lines 81–191) checks **structural linkage**: every file-level prescription in the design has both a task in `task.md` and an AC in `requirement.md`. It answers: *"Is prescribed work covered by tasks and ACs?"* — a completeness/traceability check.

**Pass 10** (dryrun-design lines 194–232) checks **semantic adequacy**: given the ACs that DO exist, do they prove the story's Purpose is served? It answers: *"Even if every AC passes, does the user get value?"* — a sufficiency check.

These are **clearly distinguished**. Pass 9 cannot subsume Pass 10 (tracing a file to an AC says nothing about whether that AC is behavioral vs. structural-proxy). Pass 10 cannot subsume Pass 9 (challenging the DoD says nothing about whether every file prescription has a matching task). No collision.

### Relates-to vs Pass 9 traceability — scoped correctly?

The Relates-to field (`requirement/SKILL.md:109`) explicitly disclaims overlap: *"structural design-to-task-to-AC traceability (Files Changed → task → AC linkage) is handled by `dryrun-design` Pass 9 per `specs/dryrun-design-traceability/`; this field covers upstream system-context linkage only."* Clean separation.

### Cross-file consistency of the behavioral-AC mandate

| File | States the mandate | References enforcement |
|------|-------------------|----------------------|
| `requirement/SKILL.md:113` (template) | Yes — `[behavioral]` tag with definition | Implicit (template is the guidance) |
| `requirement/SKILL.md:162` (rule) | Yes — Purpose must yield behavioral AC | `dryrun-design` Pass 10 |
| `requirement/SKILL.md:163` (rule) | Yes — behavioral AC mandatory | `dryrun-design` Pass 10 + `implement`/verify |
| `dryrun-design/SKILL.md:210-212` (Pass 10 Step 2) | Yes — checks for at least one behavioral AC | Self (this is the checker) |
| `dryrun-code/SKILL.md:103-104` (Pass 10 Step 1) | Yes — identifies entry point and observable effect from behavioral AC | Self |

**Finding**: No contradictions. No redundant overlaps. All references are consistent and point to the same definitions.

**COHERENCE VERDICT: PASS** — distinguished, not colliding.

---

## Check 2: EXECUTABILITY

**Question**: Can an agent actually execute each new rule/pass, or is it aspirational prose? Each must name who-checks-and-when.

### Requirement rules

| Rule (file:line) | Who checks | When | Executable? |
|-------------------|-----------|------|-------------|
| Purpose must yield behavioral AC (`requirement/SKILL.md:162`) | `requirement` author writes; `dryrun-design` Pass 10 enforces | At authoring; at design review | ✓ Yes — explicit who/when |
| Behavioral AC mandatory (`requirement/SKILL.md:163`) | `requirement` author writes; `dryrun-design` Pass 10 enforces; `implement`/verify demonstrates | At authoring; at design review; at implementation | ✓ Yes — explicit who/when |
| Unreachability is automatic fail (`requirement/SKILL.md:164`) | **Not explicitly stated** | **Not explicitly stated** | ⚠ Partially — see GAP-1 below |

### Dryrun-design Pass 10

| Step | Actionable? | Evidence |
|------|-------------|----------|
| Step 1: Locate Purpose | ✓ Unambiguous — look for the field, emit Critical Gap if absent | `dryrun-design/SKILL.md:200-203` |
| Step 2: Falsification question | ✓ Provides exact question + two specific sub-checks | `dryrun-design/SKILL.md:206-212` |
| Step 3: Classify and emit | ✓ Provides exact markdown templates, counter scheme, verdict impact | `dryrun-design/SKILL.md:216-232` |

### Dryrun-code Pass 10

| Step | Actionable? | Evidence |
|------|-------------|----------|
| Step 1: Identify core value flow | ✓ Three concrete items to identify (entry point, core value, observable effect), sourced from requirement.md | `dryrun-code/SKILL.md:104-107` |
| Step 2: Trace the path | ✓ Four numbered checks, each with a pass/fail criterion and emit instruction | `dryrun-code/SKILL.md:111-116` |
| Step 3: Distrust intermediate-assertion tests | ✓ Specific check with emit level (Warning) | `dryrun-code/SKILL.md:119-121` |
| Step 4: Emit findings | ✓ Two complete markdown templates with field-level placeholders | `dryrun-code/SKILL.md:124-144` |

**EXECUTABILITY VERDICT: PASS with one minor gap** (GAP-1).

---

## Check 3: SIMULATION

### Scenario (a): Agent authors a requirement — does guidance force Purpose + behavioral AC?

**Trace**: An agent invoking `/e-spec:requirement` reads the SKILL.md. It encounters:

1. **Template** (`requirement/SKILL.md:103`): the story template has a **Purpose** field with the annotation *"This section is generative: it MUST yield at least one behavioral acceptance criterion exercised through the real user interface."* — the agent must fill it.
2. **Template** (`requirement/SKILL.md:113`): the AC list includes a `[behavioral]` tagged entry marked *"REQUIRED"* with definition and example — the agent must include it.
3. **Rule** (`requirement/SKILL.md:162`): *"Every story MUST have a Purpose... A Purpose that produces no behavioral AC is incomplete."* — reinforces template with hard language.
4. **Rule** (`requirement/SKILL.md:163`): *"Every story MUST include at least one behavioral acceptance criterion... It states an observable outcome... not a structural proxy ('method returns a non-null object' or 'unit test green')."* — explicitly names and rejects the proxy pattern.

**Would a structural-proxy-only DoD (e.g., "method returns a non-null object") be rejected?**

- At **authoring** time: the template and rules explicitly say "not a structural proxy" and give the exact anti-pattern as an example. An agent following the template would not produce one.
- At **review** time: `dryrun-design` Pass 10 Step 2 (`dryrun-design/SKILL.md:210`) asks *"Can every AC be satisfied by structural proxies... without the feature being usable through the user's real interface?"* — it would flag a proxy-only DoD as a Critical Gap.

**Result: YES — the guidance forces Purpose + behavioral AC. A structural-proxy-only DoD would be rejected at both authoring and review.** ✓

### Scenario (b): Agent runs dryrun-code Pass 10 against two defect patterns

**Pattern 1: Value computed then never consumed (the `assembled_context` pattern)**

Pass 10 Step 2, check 3 (`dryrun-code/SKILL.md:115`): *"Is the core value consumed at the right place? Trace every reference to the value after it is produced. Does it reach the component that renders/outputs it? Or is it dropped — computed into a local variable, used only for a side-effect (e.g., to derive IDs), and then never referenced again?"*

The emit template (`dryrun-code/SKILL.md:128-133`) is purpose-built for this exact pattern: *"`{variable_name}` is assembled/computed at line {N} but is never referenced again after line {M}."*

**Would it flag `assembled_context` at `loop.py:159`?** Yes — the agent traces the value, finds it's used only to derive `recalled_ids` at `:160`, and is never referenced again. This matches the "used only for a side-effect (to derive IDs), and then never referenced again" description verbatim. **FLAGGED.** ✓

**Pattern 2: Feature with no reachable user entry point (memory=False, no --memory flag)**

Pass 10 Step 2, check 1 (`dryrun-code/SKILL.md:113`): *"Is the entry point reachable from the user's real interface? (e.g., does the CLI expose a flag to enable the feature? Does the HTTP route exist?) If not, emit a Bug — the feature is unreachable."*

The emit template (`dryrun-code/SKILL.md:138-144`): *"The feature requires {flag/parameter/route} to activate, but {cli / API / browser interface} exposes no such path."*

**Would it flag memory defaulting to False with no CLI flag?** Yes — the agent checks whether the CLI exposes `--memory`, finds it doesn't (`cli.py:60`), and confirms every memory hook is behind `if self._memory is not None` (`loop.py:158/172/189`). This matches "the feature requires {flag} to activate, but {CLI} exposes no such path." **FLAGGED.** ✓

**SIMULATION VERDICT: PASS** — both scenarios are caught by the instructions as written.

---

## Check 4: VERSION

| Location | Expected | Actual | Match |
|----------|----------|--------|-------|
| `plugin.json:3` | `"version": "1.2.0"` | `"version": "1.2.0"` | ✓ |
| `README.md:58` | `Current version: **1.2.0**` | `Current version: **1.2.0**` | ✓ |

**VERSION VERDICT: PASS**

---

## Gaps / Ambiguities / Contradictions

### GAP-1 (Minor): Unreachability rule missing explicit who/when

- **File**: `requirement/SKILL.md:164`
- **What**: The rule *"Unreachability is an automatic fail — hard stop"* does not include a *"Who checks / when"* annotation, unlike the two adjacent rules at lines 162-163 which both have explicit *"Who checks:"* sentences.
- **Impact**: Low — enforcement IS covered elsewhere: `dryrun-design` Pass 10 Step 3 (`dryrun-design/SKILL.md:226`) checks unreachability during design review, and `dryrun-code` Pass 10 Step 2 check 1 (`dryrun-code/SKILL.md:113`) checks it during code review. But the requirement rule itself is stylistically inconsistent with its neighbors and an agent reading ONLY the requirement skill could treat unreachability as advisory rather than enforced.
- **Fix**: Append to line 164: *"Who checks: `dryrun-design` (Pass 10) and `dryrun-code` (Pass 10) both enforce this — `dryrun-design` flags absence of an interface path in the design, `dryrun-code` verifies the entry point exists in code."*

No contradictions found. No redundant overlaps found. No other gaps or ambiguities found.

---

## Summary

| Check | Result |
|-------|--------|
| Coherence | **PASS** — Pass 9 (structural traceability) and Pass 10 (behavioral adequacy) are clearly distinguished; Relates-to explicitly defers to Pass 9; no contradictions or collisions |
| Executability | **PASS** — all new passes have step-by-step instructions, emit templates, and verdict-impact rules; one minor style gap (GAP-1) |
| Simulation | **PASS** — both the proxy-only DoD and the computed-then-dropped / unreachable-feature patterns are caught |
| Version | **PASS** — plugin.json and README both read 1.2.0 |

---

## VERDICT: **PASS** — redeploy-ready

One minor style inconsistency (GAP-1) noted for optional cleanup. It does not affect functional correctness — the unreachability check is enforced by both dryrun-design Pass 10 and dryrun-code Pass 10 regardless of the missing annotation on the requirement rule.
