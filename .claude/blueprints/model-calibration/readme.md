# Model Calibration — Blueprint

A reusable method for evaluating any LLM's capability across the spec-driven SDLC. Run a model through each SDLC phase, score it on domain-specific rubrics, iteratively optimize prompts until you hit the model's ceiling, and produce a capability map that tells you exactly what the model can and cannot do.

This blueprint is prescriptive: it defines the phases, the rubrics, the iteration loop, and the prompt engineering playbook. It was forged from a real 6-phase evaluation of Gemma 4 E2B (2.3B params) and generalized into a repeatable process.

---

## When to Use This

- **Evaluating a new local model** — before committing to a model for any SDLC role, calibrate it.
- **Comparing models** — run two models through the same phases, same rubrics, same target feature. The capability maps are directly comparable.
- **After a model update** — new version of a model you already use? Re-calibrate to see what changed.
- **Exploring role assignment** — which model handles which SDLC step? Calibration tells you where each model earns its place.

**Not for**: Evaluating models on arbitrary benchmarks. This is SDLC-specific — it measures whether a model can write requirements, design systems, break down tasks, review designs, implement code, and review code.

---

## Prerequisites

| What | Why |
|------|-----|
| **Ollama** (or equivalent local inference) | Run the model locally with repeatable settings (temperature, context window) |
| **The model under test** | Pulled and runnable via `ollama run {model}` |
| **VH (Velasari Helper) or automation harness** | Automate prompt submission, capture raw output, run scoring. Manual is possible but slow. |
| **A target feature** | A real feature spec to use as evaluation material — requirement doc, design doc, task breakdown, implementation scope. Use something already built so you have ground truth. |
| **The spec-driven blueprint** | Familiarity with the SDLC phases defined in `blueprints/spec-driven/readme.md` — this calibration maps directly onto that lifecycle. |

### Model Configuration Baseline

Lock these for the entire evaluation so results are comparable:

```
temperature: 0.7      # or model default — document what you use
context_window: 8192   # whatever the model supports — document it
top_p: 0.9             # document
repeat_penalty: 1.1    # document
```

Change these mid-evaluation only if you're explicitly testing their effect — and document it as a variable, not a default.

---

## The Six Phases

Each phase maps to one SDLC step from the spec-driven blueprint. They run in order because later phases build on earlier artifacts (a model that can't write requirements produces poor input for the design phase).

```
Phase 1          Phase 2          Phase 3          Phase 4          Phase 5          Phase 6
Requirement  -->  Design      -->  Task        -->  Design      -->  Implement   -->  Code
Writing           Writing          Breakdown        Review           ation            Review
(generation)      (generation)     (generation)     (analysis)       (generation)     (analysis)
```

**The generation/analysis split matters.** Phases 1-3 and 5 are generative — the model creates artifacts from scratch. Phases 4 and 6 are analytical — the model critiques existing artifacts. Small models are consistently better at analysis than generation. Expect it.

---

## Phase Definitions and Scoring Rubrics

Every phase is scored on 6 criteria, each 0.0-1.0. The overall phase score is the unweighted mean. Criteria are domain-specific per phase — what makes a good requirement is different from what makes a good design review.

### Phase 1: Requirement Writing

**Input**: Feature description (2-3 sentences).
**Task**: Write a complete requirement document with user stories and acceptance criteria.
**Ground truth**: Your existing `requirement.md` for the target feature.

| # | Criterion | 0.0 | 0.5 | 1.0 |
|---|-----------|-----|-----|-----|
| R1 | **Story completeness** | Missing major user stories | Has main stories, misses edge cases | All stories present, matches ground truth scope |
| R2 | **Acceptance criteria quality** | Vague or absent ("should work") | Present but not all testable | Every criterion is specific and testable |
| R3 | **Actor specificity** | No actors named | Generic actors ("user") | Correct actors per story (developer, admin, system) |
| R4 | **Scope discipline** | Invents features not asked for | Minor scope creep | Captures exactly what was asked, uses "Out of Scope" |
| R5 | **Structure compliance** | Free-form text, no format | Partial structure | Follows requirement template (overview, stories, AC, dependencies) |
| R6 | **Dependency awareness** | Ignores infrastructure needs | Mentions some deps | Identifies infrastructure dependencies, config, env vars |

### Phase 2: Design Writing

**Input**: The requirement document (ground truth or model-generated from Phase 1).
**Task**: Write a design document covering architecture, data models, and decisions.
**Ground truth**: Your existing `design.md` for the target feature.

| # | Criterion | 0.0 | 0.5 | 1.0 |
|---|-----------|-----|-----|-----|
| D1 | **Decision traceability** | No decisions documented | Decisions listed without rationale | Every decision traces to a requirement or constraint |
| D2 | **Schema/model specificity** | "Store in database" | Mentions tables/models, vague fields | Full schemas — field names, types, relationships, access patterns |
| D3 | **Error handling design** | Not addressed | Generic "handle errors" | Specific error paths per operation, recovery strategies |
| D4 | **Component boundaries** | Monolithic description | Some separation of concerns | Clear interfaces between components, contract definitions |
| D5 | **Implementation guidance** | Abstract description only | Some code hints | Real code examples in target language, enough to implement unambiguously |
| D6 | **Requirement coverage** | Major gaps vs requirement doc | Covers main stories | Every user story has corresponding design elements |

### Phase 3: Task Breakdown

**Input**: The requirement + design documents.
**Task**: Produce an implementation task checklist with actor/action/target per task.
**Ground truth**: Your existing `task.md` for the target feature.

| # | Criterion | 0.0 | 0.5 | 1.0 |
|---|-----------|-----|-----|-----|
| T1 | **Actor/action/target** | Tasks lack actors ("implement stuff") | Some tasks have actors | Every task names who does what to which component |
| T2 | **Requirement traceability** | No references to user stories | Some tasks reference requirements | Every task links to its requirement (`_ABBR-N_`) |
| T3 | **Granularity** | One mega-task or 50 micro-tasks | Reasonable count, uneven sizing | Right-sized tasks, each is a testable unit of work |
| T4 | **Ordering logic** | Random order | Roughly logical | Dependencies reflected in order, foundational tasks first |
| T5 | **Test awareness** | No mention of testing | Tests as separate tasks | Tests are sub-tasks of implementation tasks |
| T6 | **Design fidelity** | Contradicts or ignores the design | Follows design loosely | Tasks faithfully decompose the design — no invented scope, no gaps |

### Phase 4: Design Review

**Input**: A design document (with deliberately planted issues or using the model's own Phase 2 output).
**Task**: Produce a design dry-run review identifying gaps, warnings, and observations.
**Ground truth**: Your own `/dryrun-design` of the same document.

| # | Criterion | 0.0 | 0.5 | 1.0 |
|---|-----------|-----|-----|-----|
| V1 | **True positive rate** | Misses most real issues | Catches obvious issues | Catches subtle issues — missing error paths, race conditions, contract gaps |
| V2 | **False positive rate** | Flags everything, mostly noise | Some false alarms | Low false positive rate — flagged issues are real concerns |
| V3 | **Severity accuracy** | Everything is "critical" or everything is "minor" | Rough severity calibration | Severity matches actual risk — critical = will break, warning = might break |
| V4 | **Actionability** | "Needs improvement" | Identifies what's wrong | Identifies what's wrong AND suggests a specific fix |
| V5 | **Coverage breadth** | Only checks one dimension | Checks several passes | Covers completeness, data flow, error paths, concurrency, edge cases |
| V6 | **Report structure** | Unstructured prose | Some organization | Follows dryrun report template — severity categories, verdict, summary table |

### Phase 5: Implementation

**Input**: Requirement + design + task breakdown for a single module.
**Task**: Produce working code for one module (not the whole project).
**Ground truth**: Your existing implementation of that module.

| # | Criterion | 0.0 | 0.5 | 1.0 |
|---|-----------|-----|-----|-----|
| I1 | **Correctness** | Doesn't run or produces wrong results | Runs but has bugs | Correct behavior matching design spec |
| I2 | **Design conformance** | Ignores the design, invents own approach | Follows design loosely | Implements the design faithfully — right patterns, right boundaries |
| I3 | **Error handling** | No error handling | Generic try/catch | Specific error handling per the design's error paths |
| I4 | **Code quality** | Spaghetti, magic numbers, no structure | Decent structure, some issues | Clean, SOLID, well-named, appropriate patterns |
| I5 | **Completeness** | Skeleton only | Core logic present, edges missing | Full module — happy path, error paths, edge cases |
| I6 | **Test inclusion** | No tests | Some tests, low coverage | Tests for happy path, error paths, edge cases |

**Critical rule**: Ask for ONE module at a time. Small models cannot hold an entire project in context. Pick the most testable, most self-contained module. Score that. If the model succeeds, try a module with more dependencies.

### Phase 6: Code Review

**Input**: Code to review (with known bugs planted, or using the model's own Phase 5 output).
**Task**: Produce a code dry-run review identifying bugs, gaps, warnings, and style issues.
**Ground truth**: Your own `/dryrun-code` of the same code.

| # | Criterion | 0.0 | 0.5 | 1.0 |
|---|-----------|-----|-----|-----|
| CR1 | **Bug detection** | Misses real bugs | Catches obvious bugs | Catches subtle bugs — off-by-one, resource leaks, race conditions |
| CR2 | **False positive rate** | Flags working code as buggy | Some false alarms | Low false positive rate — reported bugs are real |
| CR3 | **Severity accuracy** | All bugs same severity | Rough calibration | Accurate severity — distinguishes crash from cosmetic |
| CR4 | **Fix quality** | No fixes suggested | Vague fix direction | Specific fix with code snippet |
| CR5 | **Coverage breadth** | Only checks syntax | Checks logic + style | Checks execution paths, error handling, resources, security, contracts |
| CR6 | **Report structure** | Unstructured notes | Some organization | Follows dryrun-code report template — bugs, gaps, warnings, style, verdict |

---

## The Calibration Loop

For each phase, run this exact loop. Do not skip steps. Do not hand-wave the scoring.

```
+-------------------------------------------+
|  1. BASELINE PROBE                        |
|     Minimal prompt -> raw model output    |
|                  |                         |
|  2. SCORE ON RUBRIC                       |
|     6 criteria x 0.0-1.0 -> overall mean  |
|                  |                         |
|  3. WEAKNESS ANALYSIS                     |
|     What scored lowest? Why?              |
|                  |                         |
|  4. TARGETED PROMPT IMPROVEMENT           |
|     Address the specific weakness         |
|                  |                         |
|  5. RE-TEST AND RE-SCORE                  |
|     Same rubric, new prompt               |
|                  |                         |
|  6. PLATEAU CHECK                         |
|     Score still climbing? --yes--> go to 3|
|              |                             |
|             no                             |
|              |                             |
|  7. RECORD RESULTS                        |
|     Baseline, best, ceiling, strategies   |
+-------------------------------------------+
Max 4 iterations per phase.
```

### Step 1: Baseline Probe

Give the model the minimal prompt — just the task and input, no formatting guidance, no examples, no multi-turn tricks. This shows what the model does naturally.

```
Example baseline prompt for Phase 1:
"Write a requirement document for the following feature: {feature description}"
```

That's it. No template. No examples. No structure hints. Capture the raw output.

### Step 2: Score on Rubric

Score each of the 6 criteria for that phase. Be honest — 0.5 is fine, 0.3 is fine. Don't grade on a curve. Compare against your ground truth document.

Record as a table:

```markdown
| Criterion | Score | Notes |
|-----------|-------|-------|
| R1 Story completeness | 0.6 | Got 3 of 5 stories, missed admin-facing |
| R2 AC quality | 0.4 | Vague — "should handle errors" |
| ... | ... | ... |
| **Overall** | **0.52** | |
```

### Step 3: Weakness Analysis

Look at the lowest-scoring criteria. Ask: **why did the model fail here?**

Common root causes:
- **Context overflow** — input too long, model lost the thread
- **Format confusion** — model doesn't know what format you want
- **Missing knowledge** — model doesn't know the domain concept
- **Lazy generation** — model produced a plausible-looking skeleton with no depth
- **Template mirroring** — model echoed a template back instead of filling it

The root cause determines the fix.

### Step 4: Targeted Prompt Improvement

Apply ONE technique per iteration (see Prompt Engineering Playbook below). Changing multiple things at once makes it impossible to attribute improvement.

### Step 5: Re-test and Re-score

Same rubric, same ground truth. New score.

### Step 6: Plateau Check

Compare to previous iteration. If the score improved by < 0.02 on a second consecutive attempt, you've hit the ceiling. Record it and move to the next phase.

**Max 4 iterations.** If you haven't plateaued by iteration 4, record the best score and move on. You're either over-fitting the prompt or chasing diminishing returns.

### Step 7: Record Results

For each phase, record:

```markdown
## Phase {N}: {Name}

**Baseline**: {score} (iteration 0)
**Best**: {score} (iteration {N})
**Ceiling estimate**: ~{score}
**Iterations**: {count}

### Score progression
| Iteration | Score | Change applied |
|-----------|-------|----------------|
| 0 (baseline) | 0.52 | None — minimal prompt |
| 1 | 0.61 | Added output format bullets |
| 2 | 0.758 | Added concrete example |
| 3 | 0.78 | Added actor hint — no improvement |

### What worked
- {Technique}: {Effect}

### What didn't work
- {Technique}: {Effect}

### Ceiling analysis
{Why the model stops here — context limit, knowledge gap, etc.}
```

---

## Prompt Engineering Playbook

These are the discovered techniques, ordered by how often they help. Each is a tool — apply the one that addresses the specific weakness you identified in Step 3.

### Strategy 1: Concrete Examples Over Abstract Instructions

**When to use**: Model produces vague or generic output despite clear instructions.
**What to do**: Include one concrete example of the output format in the prompt. Not a full template — a single illustrative instance.

```
Bad:  "Write user stories with acceptance criteria"
Good: "Write user stories with acceptance criteria. Example:
       ### WLS-1: Stream Agent Logs
       **As a** developer, **I want to** see agent logs in real-time,
       **so that** I can debug without checking server files.
       **Acceptance Criteria:**
       - Log entries appear within 2 seconds of generation
       - Each entry shows timestamp, level, agent name, message"
```

**Why it works**: Small models learn format from examples faster than from descriptions. The example anchors the model's generation.

**Empirical result**: Caused the single biggest score jump observed — 0.61 to 0.758 in requirement writing.

### Strategy 2: Two-Turn Conversation

**When to use**: Model hallucinates, loses context, or produces incoherent output when given a long input document + instructions in a single prompt.
**What to do**: Split into a multi-turn conversation:

```
Turn 1 (user):    "Here is the requirement document for feature X: {full document}"
Turn 2 (assistant): "I've read the requirement document for feature X. It covers {brief summary}."
Turn 3 (user):    "Now write a design document. Include: {bullet list of what to cover}"
```

**Why it works**: The model processes the input document in turn 1 without the cognitive load of also tracking output format. The assistant turn in turn 2 forces comprehension before generation. Turn 3 arrives with the model already "holding" the input.

**Implementation**: In Ollama API, use the chat endpoint with a messages array. Pre-fill the assistant acknowledgment — the model doesn't need to generate it.

**Empirical result**: Breakthrough technique for design writing — 0.308 to 0.727. Single biggest structural improvement observed.

### Strategy 3: Bullet-Point Guidance Over Heavy Templates

**When to use**: Model produces short output that mirrors a template structure without filling in substance.
**What to do**: Replace section-by-section templates with a bullet list of what to cover.

```
Bad (template injection):
"## Decisions Log
| # | Decision | Rationale |
|---|----------|-----------|
| D1 | | |

## 1. Architecture
..."

Good (bullet guidance):
"Cover these topics:
- Key architectural decisions with rationale
- Data models with field names and types
- Error handling per operation
- Component boundaries and interfaces"
```

**Why it works**: When a small model sees a pre-filled template, it treats the structure as "mostly done" and exits early or mirrors the template back with minimal content. Bullet guidance tells the model WHAT to produce without showing it the skeleton.

**Empirical result**: Template injection consistently produced shorter, shallower output. Bullet guidance consistently produced deeper content.

### Strategy 4: Pre-fill + Guard Rails (for Review Tasks)

**When to use**: Model is reviewing/critiquing an artifact (Phases 4, 6).
**What to do**: Pre-fill the start of the review output AND add explicit guards against common failure modes.

```
Pre-fill the assistant response with:
"# Design Dry-Run Report #1\n\n**Document**: {path}\n**Reviewed**: {date}\n\n## Critical Gaps\n"

Add guard in the prompt:
"IMPORTANT: Only flag issues that are genuinely missing or broken.
A design choice you'd do differently is NOT a gap — it's a style preference.
Severity guide:
- Critical = will cause incorrect behavior or data loss
- Warning = might cause issues under specific conditions
- Observation = worth noting but not a defect"
```

**Why it works**: Pre-fill gets the model into "review mode" immediately. The severity guide and false-positive guard prevent the model from flagging everything as critical (a common small-model failure mode — hedging by over-reporting).

**Empirical result**: Design review reached 0.90 with this technique — the highest score across all phases.

### Strategy 5: Module-at-a-Time Scoping (for Implementation)

**When to use**: Model fails to produce working code for a multi-file project.
**What to do**: Identify the most self-contained, most testable module. Ask for just that module. Provide the interfaces it depends on as context, but don't ask the model to implement them.

```
"Implement the StatusTracker class.
It depends on these interfaces (already implemented, don't re-implement):
- EventBus.publish(event: Event) -> None
- Storage.save(key: str, value: dict) -> None

Implement StatusTracker with:
- track(job_id, status) -> None
- get_status(job_id) -> Status
- Handle: invalid job_id, storage failures"
```

**Why it works**: Small models cannot hold an entire project architecture in context. One module with explicit interfaces fits. The model can focus on logic instead of architecture.

### Strategy 6: Role Priming

**When to use**: As a first-attempt improvement when baseline output lacks domain awareness.
**What to do**: Open the prompt with a role statement.

```
"You are a senior software architect writing a design document for a production system."
```

**Why it works sometimes**: Activates domain-relevant patterns in the model's training. But — this is the weakest technique. It provides marginal improvement and should be combined with a structural technique (strategies 1-5), not relied on alone.

### Technique Interaction Matrix

Not all techniques combine well. Use this to plan multi-technique prompts:

| Combine? | Two-Turn | Concrete Example | Bullet Guidance | Pre-fill | Module Scope |
|----------|----------|-------------------|-----------------|----------|--------------|
| **Two-Turn** | — | Yes (example in turn 3) | Yes (bullets in turn 3) | Yes (pre-fill assistant turn) | N/A |
| **Concrete Example** | Yes | — | Yes | Yes | Yes |
| **Bullet Guidance** | Yes | Yes | — | Avoid (competing structures) | Yes |
| **Pre-fill** | Yes | Avoid | Avoid | — | N/A |
| **Module Scope** | N/A | Yes | Yes | N/A | — |

"Avoid" = they fight for the model's attention and reduce both techniques' effectiveness.

---

## Output Artifacts

A complete calibration produces these artifacts:

### 1. Phase Reports

One per phase. Location: `{eval-folder}/phases/phase-{N}-{name}.md`

Contains: the full iteration history — every prompt tried, every score, every weakness analysis, the progression table, ceiling analysis.

### 2. Capability Map

The summary artifact. Location: `{eval-folder}/capability-map.md`

```markdown
# {Model Name} — Capability Map

**Model**: {name, version, parameter count}
**Context window**: {size}
**Evaluation date**: {date}
**Target feature**: {feature used for evaluation}
**Evaluator**: {V + VH / manual}

## Scores

| Phase | SDLC Step | Baseline | Best | Ceiling | Role Fit |
|-------|-----------|----------|------|---------|----------|
| 1 | Requirement writing | 0.52 | 0.78 | ~0.78 | Assist |
| 2 | Design writing | 0.31 | 0.75 | ~0.80 | Assist |
| 3 | Task breakdown | 0.45 | 0.74 | ~0.78 | Assist |
| 4 | Design review | 0.65 | 0.90 | ~0.95 | Capable |
| 5 | Implementation | — | — | — | — |
| 6 | Code review | — | — | — | — |

## Role Fit Legend

| Label | Best Score | Meaning |
|-------|-----------|---------|
| **Autonomous** | 0.90+ | Model can do this with minimal human review |
| **Capable** | 0.75-0.89 | Model produces useful output; human refines |
| **Assist** | 0.60-0.74 | Model provides a starting point; human rewrites significantly |
| **Unfit** | < 0.60 | Not useful for this task — human effort to fix exceeds effort to write from scratch |

## Key Techniques

| Phase | Technique that unlocked best score |
|-------|-----------------------------------|
| 1 | Concrete example in prompt |
| 2 | Two-turn conversation |
| 3 | Bullet-point guidance |
| 4 | Pre-fill + false-positive guard |

## Recommendations

{Where this model fits in your workflow, what it should and shouldn't do}
```

### 3. Best Artifacts

The actual best output from each phase. Location: `{eval-folder}/best-artifacts/`

```
best-artifacts/
  requirement.md    # Best Phase 1 output
  design.md         # Best Phase 2 output
  task.md           # Best Phase 3 output
  design-review.md  # Best Phase 4 output
  {module}.py       # Best Phase 5 output
  code-review.md    # Best Phase 6 output
```

These serve as examples for future calibrations and as evidence for the scores.

### 4. Optimized Prompts

The best-performing prompt for each phase. Location: `{eval-folder}/prompts/`

```
prompts/
  phase-1-requirement.md
  phase-2-design.md
  phase-3-task.md
  phase-4-design-review.md
  phase-5-implementation.md
  phase-6-code-review.md
```

These are directly reusable — if you deploy this model for a specific SDLC role, use the optimized prompt.

### 5. Research Paper (Optional)

For models worth writing up. Location: `{eval-folder}/research/paper.md`

Structured analysis of the evaluation — findings, technique effectiveness, comparison with other models, recommendations. This is for publication or team knowledge sharing, not for the calibration process itself.

---

## Interpretation Guide

### Reading a Capability Map

**The baseline-to-best gap** tells you how prompt-sensitive the model is. A large gap (e.g., 0.31 to 0.75) means the model has the capability but needs careful prompting. A small gap (e.g., 0.65 to 0.70) means the model is either naturally good or fundamentally limited — check the ceiling.

**The best-to-ceiling gap** tells you how much headroom remains. If best equals ceiling (~0.78 = ~0.78), you've extracted everything. If best is below ceiling (0.75 vs ~0.80), more prompt work might help — but expect diminishing returns.

**The generation vs. analysis split** is the most reliable pattern. If a model scores 0.90 on review but 0.75 on generation, that's not a prompt problem — that's the model's architecture. Small models are better critics than creators. Design your workflow accordingly.

### Score Interpretation by Range

| Range | What It Means | Workflow Implication |
|-------|---------------|---------------------|
| **0.90-1.00** | Production quality | Use autonomously, spot-check output |
| **0.80-0.89** | Strong with minor gaps | Use with light human review |
| **0.70-0.79** | Useful but needs editing | Good first draft, human finishes |
| **0.60-0.69** | Starting point only | Saves some typing, but human rewrites most of it |
| **0.50-0.59** | Marginal | Might be faster to write from scratch |
| **< 0.50** | Not useful | Don't assign this task to this model |

### Comparing Models

When comparing two models on the same feature:
- Same rubrics, same ground truth, same evaluation process
- Compare **best scores**, not baselines — baselines reflect prompt sensitivity, not capability
- Compare **ceiling estimates** — this is the true capability comparison
- A model with a higher ceiling but lower best score just needs more prompt work

### Pattern: The Review Advantage

Expect review phases (4, 6) to score 0.10-0.20 higher than generation phases (1, 2, 3, 5) for models under ~10B parameters. This is structural — review is constraint satisfaction (does X meet criteria Y?), while generation is open-ended creation. If a small model scores HIGHER on generation than review, re-check your review rubric — it's probably too lenient.

### What "Plateau" Really Means

When a model's score stops climbing despite prompt changes, that's the model's ceiling for that task type at that context window. The plateau is caused by one of:

| Plateau Cause | Evidence | Can You Fix It? |
|---------------|----------|-----------------|
| **Context window limit** | Output degrades at the end, loses early instructions | Try two-turn, try shorter input |
| **Knowledge gap** | Model doesn't know domain concepts | No — fundamental model limitation |
| **Reasoning depth** | Model handles simple cases, fails on multi-step logic | No — need a larger model |
| **Format adherence** | Content is good but structure is wrong | Sometimes — try pre-fill or stronger examples |

If the cause is context or format, you might squeeze out another 0.02-0.05 with creative prompting. If the cause is knowledge or reasoning depth, stop — you've found the ceiling.

---

## Starter Templates

Use these as the **baseline probe** for each phase (iteration 0). They are intentionally minimal — the point is to see what the model does with minimal guidance.

### Phase 1: Requirement Writing — Baseline

```
Write a requirement document for the following feature:

{feature_description}

Include user stories with acceptance criteria, infrastructure dependencies, and scope boundaries.
```

### Phase 2: Design Writing — Baseline

```
Here is the requirement document for {feature_name}:

{requirement_document}

Write a design document covering architecture, data models, component boundaries, error handling, and key decisions with rationale.
```

### Phase 3: Task Breakdown — Baseline

```
Here is the requirement and design for {feature_name}:

Requirements:
{requirement_document}

Design:
{design_document}

Break this into implementation tasks. Each task should specify who does what to which component.
```

### Phase 4: Design Review — Baseline

```
Review the following design document for gaps, missing error handling, unclear boundaries, and potential issues:

{design_document}

Categorize findings by severity: critical (must fix), warning (should fix), observation (worth noting).
```

### Phase 5: Implementation — Baseline

```
Implement the {module_name} module based on this design:

{relevant_design_section}

It depends on these interfaces (already implemented):
{interface_signatures}

Include error handling and basic tests.
```

### Phase 6: Code Review — Baseline

```
Review the following code for bugs, missing error handling, resource management issues, and design conformance:

{code}

The design spec requires:
{relevant_design_section}

Categorize findings by severity: bug (will cause incorrect behavior), gap (missing implementation), warning (potential issue), style (code quality).
```

---

## Running a Calibration — Quick Reference

```
1. Choose target feature (already built, has ground truth specs)
2. Set up model (ollama pull, lock config, document settings)
3. For each phase 1-6:
   a. Run baseline probe (starter template above)
   b. Score on rubric (6 criteria, 0.0-1.0 each)
   c. Identify lowest-scoring criterion
   d. Apply ONE technique from the playbook
   e. Re-test, re-score
   f. Repeat c-e until plateau or 4 iterations
   g. Record: baseline, best, ceiling, what worked
4. Compile capability map
5. Save best artifacts + optimized prompts
6. Write recommendations
```

**Time estimate**: ~2-3 hours per phase with automation (VH), ~4-6 hours manual. Full 6-phase calibration: 1-2 days.

---

## Anti-Patterns — Push Back on These

| # | Anti-Pattern | Rule | Principle |
|---|-------------|------|-----------|
| M1 | **Changing multiple prompt variables at once** | One change per iteration. If you change the structure AND add an example AND switch to two-turn, you can't attribute the result. | Isolate variables. |
| M2 | **Grading on a curve** | Score against ground truth, not against "what you'd expect from a small model." A 0.4 is a 0.4. | Honest scores produce useful capability maps. |
| M3 | **Skipping the baseline** | Always run the minimal prompt first. The baseline-to-best gap is critical data. | You can't measure improvement without a starting point. |
| M4 | **Chasing the last 0.02** | After 4 iterations with diminishing returns, record the ceiling and move on. | Prompt engineering has diminishing returns. Know when to stop. |
| M5 | **Using different features per phase** | Same target feature, all 6 phases. Different features introduce scope variation that poisons comparison. | Control your variables. |
| M6 | **Evaluating implementation as whole-project** | Module-at-a-time. If the model fails on whole-project, that's a context limit, not a capability limit. | Test capability, not context window. |
| M7 | **Discarding "failed" prompts** | Record what DIDN'T work and why. Failed techniques are data — they reveal model limitations. | Negative results are results. |
| M8 | **Comparing models on different features** | Same feature, same rubrics, same ground truth. Otherwise it's apples to oranges. | Fair comparison requires controlled conditions. |

---

## Empirical Reference: Gemma 4 E2B (2.3B)

The first model calibrated with this method. Reference data for calibrating expectations with similarly-sized models.

| Phase | Baseline | Best | Ceiling | Key Unlock |
|-------|----------|------|---------|------------|
| 1. Requirement writing | ~0.52 | 0.78 | ~0.78 | Concrete example in prompt (0.61 to 0.758 jump) |
| 2. Design writing | ~0.31 | 0.75 | ~0.80 | Two-turn conversation (0.308 to 0.727 breakthrough) |
| 3. Task breakdown | ~0.45 | 0.74 | ~0.78 | Bullet-point guidance over templates |
| 4. Design review | ~0.65 | 0.90 | ~0.95 | Pre-fill + false-positive guard + severity guide |
| 5. Implementation | — | — | — | Module-at-a-time scoping (in progress) |
| 6. Code review | — | — | — | Pending |

**Key finding**: Review (Phase 4) scored 0.12-0.16 higher than the best generation phase. The generation/analysis split is real and significant at this parameter count.
