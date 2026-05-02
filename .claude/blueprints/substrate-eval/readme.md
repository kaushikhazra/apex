# Substrate Eval — Blueprint

A reusable method for evaluating and repairing the **substrate** of an AI agent — the layered set of always-loaded and on-demand documents (CLAUDE.md, skills, blueprints, templates) that the agent reads and executes against. Substrate eval surfaces silent divergence between layers, locates the specific layer where each rule belongs, and iterates until the system reliably produces target behavior under fresh-worker dispatch.

This blueprint is prescriptive. It defines the dispatch protocol, the convergence bar, the divergence audit, and the recognition cues for common substrate failure modes. It was forged from a real evaluation and generalized into a repeatable process.

---

## What "Substrate" Means Here

The substrate is the medium an agent executes against — not an agreement, not a spec in the upfront-design sense. It is the imperative operating substance the agent reads at runtime:

- **Always-loaded layer**: project `CLAUDE.md` (and any auto-loaded global rules).
- **On-demand layer**: skills (`SKILL.md`), templates, blueprints — loaded when invoked or when context matches their description.
- **Reference layer**: any document the substrate points an agent to follow (style guides, schemas, manifests).

A substrate is *coherent* when all layers agree on rules, structure, and naming. A substrate is *divergent* when one layer says "use path X" and another says "use path Y", or one says "do A then B in one dispatch" and another says "each step is a separate dispatch." Workers behave non-deterministically on divergent substrates — sometimes following one layer, sometimes another. Convergence under a divergent substrate is luck, not validity.

---

## When to Use This

- **After a substrate refactor** — layout change, phase restructure, skill rewrite. Workers may follow stale references from layers you didn't touch.
- **Before promoting a methodology to APEX-grade** — declare the substrate ready only after empirical convergence.
- **When workers exhibit non-deterministic behavior** under the same prompt + same project state. That is the surface signature of substrate divergence.
- **When two layers have grown independently and may have drifted** — for instance, CLAUDE.md was updated by a human while skills were updated by a worker, or vice versa.
- **Before a critical handoff** where the substrate will drive autonomous workers without human oversight.

**Not for**: debugging a single broken dispatch. Substrate eval is for *reliability across many dispatches*. A single failure may be a worker quirk; a pattern of failures across iters is substrate divergence.

---

## Prerequisites

| What | Why |
|------|-----|
| **Worker dispatch capability** | A way to launch a fresh agent with a controlled prompt against the project (any agent-as-process harness). |
| **Persistable project state** | The substrate eval mutates project files. You must be able to checkpoint, archive, and restore state between iters. |
| **A target behavior** | A workflow the substrate is supposed to drive (e.g. a multi-phase production pipeline). The eval tests whether the substrate reliably produces that behavior. |
| **Pass criteria per phase** | A small set of concrete, falsifiable checks per phase (artifact paths, file counts, content invariants). The eval is only as sharp as these criteria. |
| **An eval log** | A markdown file the agent appends to per iter: dispatch ID, cost, what changed, pass/fail score, adjustment applied. Source of truth for the convergence claim. |

---

## Core Discipline

### 1. Edit only the substrate

The eval loop tests whether the **substrate** drives target behavior. If a worker's output is wrong, do **not** fix the output by hand — that breaks the test. Identify the layer in the substrate that produced the wrong behavior and edit that layer. Then re-dispatch a fresh worker against the edited substrate. The output proves the fix.

### 2. Minimal prompt

Workers are dispatched with the smallest prompt that points at the substrate and names the goal — typically a one-paragraph task plus standard operational constraints (no sub-agents, absolute paths, no python heredocs). Do **not** add information the substrate is supposed to provide. If the worker fails for lack of information, the substrate is missing that information, and that is the finding.

### 3. Fresh worker per iter

Each iter is a fresh agent with no memory of prior iters. This isolates the substrate as the only variable across runs. Reusing a worker leaks context and contaminates the test.

### 4. Clean state per iter

Before each dispatch, restore the project to the canonical pre-phase state. Archive the previous iter's outputs to a tracked archive folder (e.g. `.tmp/eval-iter-{N}-archive/`). Workers self-orient from artifact state — leftover outputs route the worker to a different phase than intended.

### 5. The right adjustment

Substrates are layered. When a rule is missing or wrong, the question is not just *fix it* but *fix it where*. Use the **scope test**: would a worker doing a different phase need this rule? If yes → CLAUDE.md (always-loaded). If no → the specific skill or blueprint that owns the phase. Misplacing rules either bloats the always-loaded layer (which agents start to generalize over instead of binding to) or hides them behind on-demand loads that won't fire when needed.

---

## The Procedure

### Step 1 — Map the substrate

Enumerate the layers the agent will read:

1. The project's `CLAUDE.md`
2. Every skill the workflow invokes (each `SKILL.md`)
3. Every blueprint, template, or referenced document those skills depend on
4. Any manifest or structured document the substrate uses as a source of truth

Record the path of each. This is the surface area you may edit.

### Step 2 — Decompose the workflow into phases

Identify the discrete phases of the target workflow. A phase is a unit of work that produces a specific class of artifact. Examples: research, authoring, audit, code generation, code audit. **Audit phases are separate from author phases** — pairing a writer skill with an auditor skill in one dispatch causes context bias (the auditor rationalizes the writer's choices). Default to one phase per dispatch; chain only when both skills serve the same concern (e.g. two auditors that cross-reference each other).

### Step 3 — Define pass criteria per phase

For each phase, write a checklist of concrete checks (typically 8–12). Each check must be a binary observable — file exists at canonical path, file count equals manifest length, no edits outside the expected scope, worker invokes only the named skill, etc. Avoid subjective criteria; the eval is reproducible only if scoring is mechanical.

### Step 4 — Pre-phase state per phase

For each phase, define the canonical pre-phase state: which upstream artifacts must exist, which downstream artifacts must NOT exist. Workers self-orient from state — if you remove an upstream artifact thinking "different phase test", a worker will redo whichever phase produces that artifact.

### Step 5 — Dispatch and score

For each iter, in order:

1. Restore pre-phase state.
2. Dispatch a fresh worker with the minimal prompt (task + operational constraints). Record dispatch ID, model, budget.
3. On completion, harvest the output. List every file the worker created or modified.
4. Score against the pass criteria. Mechanical: each check is PASS or FAIL.
5. Append to the eval log: iter number, dispatch ID, cost, turns, what the worker did, pass count, gaps surfaced.

### Step 6 — Adjustment on failure

If any pass criterion failed:

1. Identify which substrate layer produced the wrong behavior. The worker's tool calls and output paths usually pinpoint it.
2. Apply the scope test (Discipline 5) to determine the correct layer.
3. Edit that layer. Document the edit in the eval log: which file, which lines, what changed, why.
4. Archive the failed output to a tracked archive folder.
5. Restore pre-phase state.
6. Dispatch the next iter.

### Step 7 — Convergence bar

A phase converges when **3 consecutive iters PASS all criteria**. Two PASS in a row is "good"; three is APEX-grade (95%+ accuracy in the pilot). Two-in-a-row has been observed to mask a latent divergence that the third iter exposed.

Do not skip the third iter. The convergence bar is the empirical claim of substrate sufficiency.

### Step 8 — Cross-layer divergence audit

Before declaring the substrate APEX-grade, run a final audit across layers:

1. For each path/identifier referenced in CLAUDE.md, search every skill and blueprint for divergent references.
2. For each rule expressed in CLAUDE.md, check that no skill contradicts it.
3. For each rule in a skill, check that CLAUDE.md does not generalize it differently.

Convergence under a still-divergent substrate is luck. The audit catches divergences that did not happen to surface in the pilot iters but would surface eventually.

---

## Convergence Bar

| Bar | Meaning | When to use |
|-----|---------|-------------|
| 1 PASS | First contact succeeded | Throwaway exploration; not a substrate claim |
| 2 consecutive PASS | "Good" — substrate likely sufficient | Internal use, single-team workflows, where re-fix is cheap |
| 3 consecutive PASS | **APEX-grade** — 95%+ confidence | Methodology promotion, distributable substrates, autonomous-worker handoffs |
| 3 PASS + cross-layer audit clean | **APEX-grade verified** | Production gates, public methodology releases |

Always state the bar achieved when reporting an eval result.

---

## Substrate Divergence Patterns to Watch For

A future agent running substrate eval will recognize these patterns by their surface signatures.

### Skill drift

A skill encodes paths, names, or layouts that have since changed in CLAUDE.md. Surface signature: worker writes to a path the project has migrated away from; same prompt, same state produces correct behavior in some iters and incorrect in others depending on which layer the worker weights more heavily. **Fix**: rewrite the skill to align with CLAUDE.md.

### Migration asymmetry

Skills that read paths from a manifest or structured document inherit layout migrations automatically; skills that hardcode paths drift on every layout change. Surface signature: after a refactor, some skills work on first contact while others fail — the failing ones are the hardcoded ones. **Fix**: rewrite hardcoded paths to manifest-driven discovery.

### Audit chaining ambiguity

A phase has both an author skill and an auditor skill. The substrate says "Phase X has both" but a worker may interpret that as "run both in one dispatch" or as "run author, return, dispatcher will run auditor next." Surface signature: same prompt, same state — one iter chains, another doesn't. **Fix**: state the chaining rule explicitly at the phase entry, not just in a general preamble. Belt-and-suspenders rule placement: rules at the entry where they apply bind more tightly than rules in a preamble.

### Self-orientation routing

Workers infer "next phase" from artifact state. If the dryrun-1.md report from a previous phase is missing, the worker will redo that phase rather than the one you intended to test. Surface signature: a worker dispatched for Phase N produces Phase N-1 output. **Fix**: ensure all upstream artifacts are in canonical pre-phase state before each dispatch. Do not test Phase N standalone with Phase N-1 artifacts removed — the worker self-routes back.

### Context bias from chaining

A writer skill and auditor skill chained in one dispatch produces a worker that may emergently "fix" audit findings inline rather than report them. This looks helpful but is a tradeoff: the auditor reads the writer's choices and rationalizes them rather than flag them. Surface signature: the audit report contains fewer findings than an independent audit would, and the worker reports a "READY" verdict after self-remediation. **Fix**: split into separate dispatches. Independence is what makes audits valuable.

### Auditor non-determinism

The same auditor on the same input produces different verdicts and different findings across runs. The findings are stable in *which structural classes of issues exist* but vary in *which specific items are surfaced*. Surface signature: iter N audit verdict is BLOCKED, iter N+1 is NEEDS_FIXES, both on the same input. **Mitigation**: do not rely on a single audit pass as a green-light signal. Either run audits multiple times and take the worst, or tighten severity rules in the audit's `checks.md` to reduce judgment variance.

### Bloated CLAUDE.md

When too many phase-specific rules accumulate in CLAUDE.md (the always-loaded layer), agents start *generalizing* the contents instead of binding to specific rules. The on-demand value of skills erodes. Surface signature: workers begin to mix rules from different phases, or invent rules consistent with the spirit of CLAUDE.md but not its letter. **Fix**: demote phase-specific rules into the relevant skill. Apply the scope test (Discipline 5) systematically.

### Convergence under conflicting substrate is luck

When two layers disagree, convergence in two-in-a-row is the worker happening to weight the same layer twice. Run the third iter; run the cross-layer divergence audit. Two iters are not a sufficient claim.

---

## Output / Artifacts

A completed substrate eval produces:

1. **The eval log** — full iter table (dispatch ID, cost, turns, pass/fail, adjustment applied), phase closures, final convergence summary.
2. **The repaired substrate** — CLAUDE.md, skills, blueprints, templates, all coherent and at canonical paths.
3. **A divergence-audit report** — what was checked across layers, what was found.
4. **The bar achieved** — 1, 2, 3, or 3+audit, stated explicitly.

The eval log is the empirical record that justifies the convergence claim. Without it, "the substrate is APEX-grade" is an unsupported assertion.

---

## When the Substrate Cannot Be Made APEX-Grade

If iters keep failing in different ways across many cycles, the substrate may be conceptually broken — phases may overlap, rules may genuinely conflict by design, or the workflow may need redesign rather than substrate repair. Surface signatures: failures shift from one layer to another with each fix; cross-layer audit produces dozens of findings; convergence is never reached within budget.

Stop the eval and surface the structural problem to the human owner. Substrate eval validates a *coherent design*; it cannot rescue an incoherent one.

---

## Status

Generalized to apply to any project with layered agent substrates.
