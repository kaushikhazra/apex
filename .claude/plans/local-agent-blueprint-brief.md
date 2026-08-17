# Brief — blueprint for building a local agent in Claude

From: Velasari (Velasari session) → APEX session
Date: 2026-08-04

## What Kaushik asked for

A blueprint in APEX capturing how to build a **local agent** — a Python program that
runs its own agentic loop against a local model, which a Claude session invokes
**once** and receives one typed result from.

## Why this exists (the motivating finding — put this in the blueprint)

The predecessor design kept Claude *inside* the loop: the local model requested one
tool call, Claude judged it, executed it with its own tools, appended the result,
looped. An audit of a real run (building a small Python todo app) found:

- ~70 Claude turns to supervise **3** local-model turns.
- 55% of all turns took no action — the shape was `thinking → text → tool`,
  roughly **3 expensive turns per single action**.
- The generated code reached the cloud **anyway**, because Claude read the local
  model's output files back into its own context to decide what to execute. The
  privacy premise of "local model" was not actually delivered.
- The per-action human-approval gate collapsed to a blanket auto-yes within ~20
  minutes — with the system's own designer as operator — while the provenance log
  still recorded every action as individually approved. The log claimed three human
  approvals; one was real.

Moving the loop into Python collapsed ~70 turns to **1**, and the generated code
never entered Claude's context at all.

Two general lessons worth stating as principles:

1. **Fixed setup cost amortizes; per-action cost does not.** A per-action gate scales
   linearly with the work and is the term that keeps the economics upside-down. It is
   also what trains a human to auto-approve — which is worse than no gate, because it
   manufactures false assurance.
2. **Never let the model author its own provenance.** A model-reported "files I
   touched" can be fabricated. Python owns the execution log; the model authors only
   a prose summary.

## Source material (read this — it is gitignored, so git-based search will not find it)

`C:/Projects/second-brain/.claude/specs/local-agent/`

- `requirement.md`, `design.md`, `task.md` — the settled contract
- `dryrun-design-1..4.md` — design review, 8 findings → 0 across four passes
- `dryrun-code-1..2.md` — code review, 3 reproduced bugs → 0

The working implementation is at
`C:/Projects/second-brain/.claude/skills/local-agent/` (SKILL.md + scripts/, 44 tests).

**These specs exist only in an untracked, gitignored directory.** Preserving the
reasoning in a durable blueprint is the point of this task.

## The design that survived review (the blueprint's spine)

```
.claude/skills/<name>/
├── SKILL.md
└── scripts/
    ├── run.py       # the ONLY interface Claude sees; one JSON object on stdout
    ├── agent.py     # pydantic-ai Agent; the loop
    ├── tools.py     # plain functions; docstrings are the schema
    └── requirements.txt
```

Decisions that earned their place, each with the reason:

- **Model-string construction only** — `Agent('ollama:<model>')`, endpoint applied via
  the `OLLAMA_BASE_URL` env var. No hand-built provider objects, no API key in code.
  This conforms to the existing APEX pydantic orchestrator blueprint; the first draft
  violated it and the design gate caught it.
- **Two output models, not one.** `AgentSummary` is the agent's `output_type` and
  carries only what the model is entitled to author. `RunResult` is assembled by
  `run.py` from the model's summary plus Python-owned runtime state, and is never
  shown to the model. Setting `output_type=RunResult` would force the model to emit
  its own provenance — the gate caught this too.
- **The system prompt is not stored in the repo.** The calling Claude session writes
  it per invocation, the way it briefs any other agent.
- **Path-or-literal arguments.** `--task` and `--system` each accept literal text or a
  file path, resolved by one shared helper (`is_file()`, not `exists()`). No separate
  `*-file` flags. Long text goes to a temp file and the path is passed — this also
  makes the brief auditable after the run.
- **Hard bounds, in the library's own units.** 15 successful tool calls
  (`UsageLimits(tool_calls_limit=15)`), 2 output-validation retries, 600s overall.
  Each maps to a distinct `error_type`. Adopt the library's unit rather than inventing
  a counting rule — the third design pass failed purely on "rounds" vs "successful
  tool calls" being different things.
- **Real cancellation, honestly bounded.** The overall timeout uses `asyncio.wait_for`,
  which genuinely cancels at await points. A first implementation joined a daemon
  thread — the run reported a timeout while the abandoned worker kept writing files.
  A sync tool already blocked inside `subprocess.run` still cannot be interrupted;
  that residual window is bounded by the tool's own timeout and is **documented rather
  than engineered around**.
- **Run-local provenance via `contextvars.ContextVar`.** A process-global log let a
  timed-out run leak its late writes into the next run's results.
- **Exactly one JSON object on stdout, always** — including argument errors. Subclass
  `ArgumentParser` so parse failures become a structured result rather than usage text.
- **Preflight probe** (`GET /api/tags`) separates "endpoint unreachable" from "model
  not found" instead of mapping opaque client exceptions.
- **Tools never raise into the loop.** Every tool returns a string, including on
  error. A non-zero exit from `run_command` is a normal result the model can read and
  react to, not an exception.
- **Testability without the service.** A replaceable module-level runner seam;
  `TestModel` for success paths, injected synthetics for failures, tools tested
  directly. No unit test may require a live local model.

## What was deliberately NOT built (state this in the blueprint — it is load-bearing)

No scope guard, no path containment, no approval gate, no provenance file. Kaushik's
reasoning: *"drop any guards before we prove this works. if it fails for the guard we
will accidentally blame the harness."* Prove the architecture first; a guard failure
and an architecture failure look identical in the output.

This is a **v1 stance, not a recommendation for production** — it must be revisited
before any real user touches such a system. The blueprint should say both halves.

## Process lessons worth a section

- The design gate repeatedly caught defects in the *architect's own* decisions, not
  just implementer sloppiness — the blueprint contradiction and the dropped step cap
  were both mine. This is the argument for never skipping the dryrun.
- Convergence came from giving each fix worker **decided resolutions**, not open
  questions. Findings went 8 → 2 → 1 → 0.
- Late-stage gates need explicit instruction *not to manufacture findings* to appear
  rigorous — and equally not to rubber-stamp. Without that, review rounds tail off
  into stylistic noise.
- Verify on artifacts, never on a worker's self-reported PASS.

## Standing authorization

Kaushik has approved this whole piece of work. Drive the backlog end to end — read the
source material, write the blueprint under `C:/Projects/APEX/blueprints/` in the
category you judge correct (there is an existing `blueprints/pydantic/` family this
sits near), follow the house blueprint conventions including a `readme.md` index entry
if the category needs one. Do not stop to ask permission between steps.

Stop and ask only for a genuinely new decision, a real ambiguity, or anything
destructive. Ping progress on the crosstalk channel at milestones or ~10 minutes,
whichever comes first — send to `velasari`.
