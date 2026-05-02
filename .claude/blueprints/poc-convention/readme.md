# POC Convention — Blueprint

A reusable convention for **proof-of-concept experiments** that need to live as first-class projects rather than scratch folders. Defines the standard location, folder layout, README structure, lifecycle states, and the methods-in-order discipline that keeps every POC honest about cost.

This blueprint is prescriptive. It defines where a POC lives, what files it must contain, how its README is structured, when it graduates or archives, and the order in which methods are attempted. It was forged from a real evaluation and generalized into a repeatable process.

---

## What "POC" Means Here

A POC is a bounded experiment that answers a single closed question: **does X work for the role we want to assign it?** It has a definition of done, an explicit method list ranked by cost, an outcome captured in writing, and a terminal state (graduated, archived, or closed unresolved with verdict). It is not an MVP, not a prototype-on-the-way-to-shipping, and not an experimental branch inside an existing project.

A POC is its own project so that:
- It is **visible** to factory tooling that lists projects
- It is **isolatable** — its dependencies, environment, and outputs do not contaminate other projects
- It is **dispatchable** — workers can be sent to it cleanly with a known structure
- Its **closure** is observable — STATUS in the README declares the verdict without anyone having to read commit history or chase Slack

---

## When to Use This

- **Evaluating a candidate replacement** for an existing component (a new TTS model vs the current one, a new library vs the in-house implementation).
- **Validating a hypothesis** before committing engineering time (does this approach actually work on our constraints?).
- **Spike work** that may or may not graduate — using the POC convention sets the right expectation that closure is the goal, not productionization.
- **Comparing options** — one POC per option, identical structure, directly comparable outcomes.

**Not for**: ongoing exploratory work without a closed question; prototypes intended to graduate to production directly; refactors of existing projects. If a workstream cannot be answered with a verdict, it is not a POC.

---

## Prerequisites

| What | Why |
|------|-----|
| **A closed question** | The POC's job is to answer it. If the question is open-ended, the POC will sprawl. |
| **A definition of done (DOD)** | Either a concrete artifact (output file, working binary) or a documented failure path (every method attempted, what blocked it). Both close the POC. |
| **An anchored constraint set** | What environment it must run on (RAM, GPU, OS), what cost ceiling, what time-to-answer. The constraints make the verdict mean something. |
| **A baseline to compare against** | If the POC is evaluating a replacement, the existing thing is the baseline. The verdict is relative, not absolute. |

---

## Folder Convention

POCs live at the workstation top level under a `poc-` prefix:

```
C:/Projects/poc-{slug}/
```

The `poc-` prefix is not optional. It is the signal that this project is bounded, terminal, and not part of mainline product work. The slug is short, kebab-case, and names the question being answered (e.g. `poc-omnivoice`, `poc-redis-streams`, `poc-cuda-kernel`).

### Standard layout

```
poc-{slug}/
├── README.md      # the verdict — TL;DR, question, DOD, methods, outcome
├── notes.md       # the journey — chronological log of every attempt
├── src/           # all code, scripts, automation produced during the POC
├── refs/          # reference inputs the POC reads (sample data, configs)
├── out/           # all output artifacts the POC produces
├── .venv/         # python virtual env if applicable (gitignored)
└── .gitignore
```

**Setup files** (`setup.md`, install scripts) live at the root if needed. They explain how to reproduce the environment from scratch.

The split between `README.md` and `notes.md` is load-bearing:
- `README.md` is the **verdict** — written for someone arriving fresh, skimming, deciding whether to adopt or revisit. Compact, structured, conclusive.
- `notes.md` is the **journey** — written by the operator while running the POC. Free-form, chronological, dense with tool output and dead-ends. Future operators (or future-you) read it to understand *why* the verdict came out that way.

Do not collapse them. The verdict belongs in the README; the journey belongs in notes. Mixing them produces a document that serves neither audience.

---

## README Format

The README has a fixed section order. A future agent reading any POC's README knows where to find each piece without searching.

```markdown
# POC: {What is being evaluated}

**STATUS**: active | graduated | archived
**Created**: YYYY-MM-DD
**Closed**: YYYY-MM-DD   ← present only after closure

## TL;DR
One paragraph that answers the closed question. Verdict first, evidence after.

## The Question
The closed question, with anchors of comparison (the dimensions on which the answer is judged).

## Definition of Done
ONE of the following:
- (A) Concrete artifact at a known path, with verdict in this README.
- (B) Documented failure path: every method attempted, what blocked each, with concrete error output.

## Methods to try (in order)
Ranked list, cheapest-first (see Methods-In-Order Discipline below).

## Verdict
The outcome. Tables of attributes, recommendation, caveats. This is the section a future reader navigates to.

## What would change the recommendation
The conditions under which the verdict would flip. Captures the boundaries of the answer.
```

The verdict section may include sub-sections per method tried — particularly when multiple methods succeeded with different trade-offs and the recommendation is conditional on which constraint dominates.

---

## STATUS Lifecycle

A POC is always in exactly one of three states. The state lives at the top of `README.md`.

### `active`

The POC is open. Methods are still being attempted. No verdict yet. The DOD has not been satisfied.

### `graduated`

The POC succeeded against its DOD and the answer was *yes — adopt*. The next step is integration into the consuming project (replace the old component, merge the module, swap the service). After integration, the POC folder may either:
- Stay in place as historical record (set `Closed:` date, leave files for reference)
- Move to an `_archive/` namespace if the workstation is being kept tidy

The graduate verdict is captured in the README. Do not delete the POC after graduation — the verdict is the proof of why the integration happened.

### `archived`

The POC has reached a terminal state without graduating. Three sub-cases:
1. **Negative verdict** — the candidate was tried and rejected. README captures *why*.
2. **Inconclusive** — the question could not be answered within the constraints (compute, time, dependency). README captures *what blocked* and what would unblock.
3. **Superseded** — the question was answered by a different POC or by a different decision in the meantime. README points to the supersession.

In all archived cases the README is the verdict. The folder is preserved for reference. Future POCs that overlap the question can read the archive and avoid duplicating work.

**Never delete an archived POC silently.** Archival captures a failure signal that future work should benefit from. Deletion erases the lesson.

---

## Methods-In-Order Discipline

A POC's `Methods to try` section ranks methods by **cost**, cheapest first. Cost has multiple axes:

- **Compute cost** — does this method require local GPU, an API key, paid inference?
- **Install cost** — zero local install (call a hosted endpoint) vs full pip dependency tree vs build-from-source
- **Complexity cost** — how many moving parts, how much glue code
- **Time cost** — how long does the method take to attempt end-to-end
- **Reversibility** — does this method leave residue (installed packages, downloaded weights, polluted env) that has to be cleaned up?

Order methods so that **the cheapest method that could plausibly answer the question is tried first**. If it succeeds, the POC closes without paying for more expensive methods. If it fails, you have learned something concrete about the cheap path's limits before spending more.

Typical ordering for a model/library evaluation:
1. **Hosted endpoint** (HF Space, Replicate, an API) via a thin client. Zero local footprint. Often answers "does the model do what we want?" without any install.
2. **Local pip install** — pulls dependencies into a project-local `.venv/`, runs on local hardware. Reveals real performance numbers (RTF, RAM, VRAM).
3. **Build from source / Colab / cloud GPU** — maximum control or maximum compute. Most expensive, attempted only if cheaper methods cannot answer the question.

The order is recorded in the README *before any method is run*. As methods are attempted, their outcomes are appended to the verdict. If a cheap method succeeds, expensive methods may be skipped — note the skip in the verdict (it is a feature, not an omission).

**Anti-pattern**: starting with the most expensive method "to be thorough." This burns budget answering a question the cheap path could have answered, and entangles the verdict with cost-irrelevant detail.

---

## When the POC Closes

The POC closes when EITHER:

1. **The DOD's concrete-artifact path is satisfied** — the artifact exists, the verdict can be written, the answer is yes/no/conditional.
2. **The DOD's failure path is satisfied** — every listed method has been attempted and failed, with documented blockers. The answer is "no, because…" or "unknown, because constraint X."

When closing:

1. Update `STATUS` in the README from `active` to `graduated` or `archived`.
2. Add `Closed: YYYY-MM-DD`.
3. Write the **Verdict** section. Be specific: what worked, what didn't, what numbers, what would change the answer.
4. Update `notes.md` with the closing entry — final dead-ends, late observations, anything that didn't fit the verdict.
5. If graduated: open a separate task to integrate the answer into the consuming project. The POC is not the integration.
6. If archived: leave the folder. Do not delete.

---

## Output / Artifacts

A closed POC produces:

1. **`README.md`** with STATUS, verdict, methods-and-outcomes, recommendation, conditions-that-would-change-the-recommendation.
2. **`notes.md`** with chronological journey — environment checks, API discoveries, dead-ends, observations.
3. **Concrete output artifacts** in `out/` — the binaries, audio files, reports, plots that the verdict points to.
4. **`src/`** — the code that produced the artifacts, runnable from the POC's own environment.
5. **`refs/`** — the reference inputs the POC consumed (small enough to commit, large assets gitignored with documentation in README).

A POC without artifacts is incomplete; a POC without a verdict in the README is not closed; a POC without notes is not reproducible.

---

## When to Skip the Convention

- **Five-minute curiosity experiments** that don't merit a project of their own — leave them in a personal scratch folder.
- **Tightly coupled experiments inside an active project** (e.g. trying a different algorithm in a feature branch). The branch is the POC; the project structure already provides isolation.
- **POCs the team has agreed to run as paper-only investigations** (a literature review, a back-of-envelope calculation). No code, no folder, no convention.

The convention pays off when the POC produces artifacts, may be revisited, or may inform a later integration. For ephemera, the overhead is not justified.

---

## Status

Generalized to apply to any bounded evaluation experiment with a closed question and a definition of done.
