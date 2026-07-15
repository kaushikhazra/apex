# Change-Spec — Behavioral DoD + Value-Path Tracing

**Type:** Change-spec (surgical). NOT a design document. States what's broken, what exactly
changes, and how to verify.

**Target plugin:** `e-spec` (`C:/Projects/APEX/sdlc/spec-enhanced/`), current version **1.1.2**.
**Skills touched:** `requirement`, `dryrun-design`, `dryrun-code`.
**Companion edit (separate, out-of-plugin):** Velasari `go-autonomous` skill DoD-derivation.

---

## What's broken (the evidence)

Axiom M3 (Memory) shipped through the autonomous SDLC and was declared **done** with all
gates green — yet it is **not usable**:

- **Finding 1 — unreachable:** memory is `memory=False` by default and the shipped
  `axiom-cli` has no `--memory` flag (`cli.py:60`, `agent.py:68`). Every memory hook in the
  loop is behind `if self._memory is not None` (`loop.py:158/172/189`), so in the product it
  silently no-ops. The Second Brain ships with its memory off and no way to turn it on.
- **Finding 2 — disconnected (worse):** even with `memory=True`, the recalled context is
  **computed and dropped**. `loop.py:159` assembles it; `:160` uses it only to derive
  `recalled_ids` for reinforce; `assembled_context` is then **never referenced again**
  (grep-confirmed lines 155/159/160 only). It never reaches `perceive()`, never enters the
  prompt, never touches reasoning. The design explicitly says *"the loop renders the result"*
  (design.md Q2) — the loop does not. Recalled memory has **zero effect** on the answer.

**Root cause (both findings, one root):** the acceptance criteria accepted **structural
proxies** for done — "assemble_context returns a structured object", "E2E test green" — instead
of the **observable behavior** the story exists to deliver ("a remembered fact changes the
answer, exercised the way a user runs it"). The `dryrun` stages inherited the same proxy: they
checked that components matched the design, not that **data actually flows through them**. The
E2E test is green *and misleading* — it calls `assemble_context` directly and asserts its
return; the agent never uses the result.

---

## What changes

Four changes, ranked by leverage. Each names **who checks it** and **when** — an unowned
addition rots (it becomes spec that gets shortcut, which is the very failure mode here).

### (1) `requirement` — DoD must be verified the way the user runs it  *(master key)*

Add to the `requirement` skill's acceptance-criteria guidance:

- Every story's Definition of Done MUST include at least one acceptance criterion that is
  **satisfied only by exercising the feature through the interface the user actually uses** —
  CLI invocation, HTTP/web via Playwright, Chrome-extension driver, etc. Test-suite green is
  necessary but **never sufficient**.
- **Unreachability is an automatic fail:** if the feature cannot be exercised through the
  user's real interface, the story is NOT done — this is a hard stop, not a footnote. (This
  single line converts Finding 1 from a missed gap into a blocking failure.)
- The acceptance criterion states the **observable behavior** ("after storing fact X in a
  session and asking about it in a later session, the answer reflects X"), not a structural
  proxy ("method returns a non-null object").
- **Who/when:** the `requirement` author writes it; `dryrun-design` (change 4a) enforces its
  presence; `implement`/verify must demonstrate it through the real interface.

### (2) `requirement` — a generative Purpose section  *(feeds change 1)*

Add a **Purpose** section to each story, stating what the story serves — what the user does
with it, and what function it plays in the overall system. Requirement:

- The Purpose is **generative, not descriptive**: it MUST produce at least one **behavioral
  acceptance criterion** (feeds change 1). A Purpose paragraph the implementer merely skims
  changes nothing; a Purpose that yields a testable behavior closes the loop.
- **Who/when:** `requirement` author writes Purpose + derives the behavioral AC from it;
  `dryrun-design` checks that the Purpose actually produced a behavioral AC.

### (3) `requirement` — `Relates-to` links  *(fitment; lowest leverage here — do not lean on it)*

Add an optional **Relates-to: <requirement/story ids>** field giving the implementer the
story's fitment in the larger system. Honest scoping note: this is good hygiene but would NOT
have caught the M3 failure on its own. **Reconcile with the existing
`specs/dryrun-design-traceability` spec** — traceability may already be partially built there;
extend it, do not duplicate or conflict.

- **Who/when:** `requirement` author adds links; `dryrun-design` may use them for context.

### (4) `dryrun` — actually trace the value path  *(second pillar; fires before build runs)*

Split across two gates — this morning's bug was **both** a design-gate miss (wrong criteria)
and a code-gate miss (untraced flow); one fix will not cover both.

- **(4a) `dryrun-design`** — challenge the criteria against the Purpose: *"if every acceptance
  criterion passes, is the story's stated Purpose actually served?"* Flag any DoD that can be
  satisfied without delivering the behavior. Flag absence of a behavioral/reachable-through-
  interface criterion (enforces changes 1 and 2).
- **(4b) `dryrun-code`** — **trace the runtime data path end to end**, not a static match
  against design components. For the story's core value, follow the data from entry (user
  interface) to effect (observable output): does the produced/recalled/computed value actually
  **reach** the place that consumes it? A value computed and then dropped (like
  `assembled_context`) MUST be flagged. Explicitly distrust green tests that assert an
  intermediate return rather than the end behavior.

### Companion (separate local edit, NOT in the plugin)

- **`go-autonomous` DoD-derivation** (Velasari skill): update so the DoD it derives targets
  **behavioral, reachable-through-the-user-interface** outcomes — not "tests green". It sets
  the target the whole pipeline aims at; if it aims at a proxy, the improved dryruns still get
  pointed at the wrong goal.

---

## Version + redeploy

- Bump `plugin.json` version **1.1.2 → 1.2.0** (minor: non-breaking change to existing skill
  behavior, per the plugin's own semver policy). Fix the stale "Current version: 1.0.0" line in
  `README.md` while there.
- Redeploy: reinstall via `--plugin-dir` / `/plugin update e-spec` so downstream projects
  (Velasari, Axiom) pick up 1.2.0.

---

## How to verify (the M3 regression test — this is the real proof)

Do **not** remove or hand-fix the M3 code. With the improved plugin deployed:

1. Regenerate M3's `requirement.md` through the improved `requirement` skill — it must now
   carry a **Purpose** and at least one **behavioral, exercised-through-the-CLI** acceptance
   criterion ("memory recalled in a later session changes the answer").
2. Run improved `dryrun-design` against it — it MUST flag that the original criteria could pass
   without memory affecting output (change 4a).
3. Run improved `dryrun-code` against the untouched M3 code — it MUST flag **Finding 2**
   (`assembled_context` computed at `loop.py:159` and never rendered into `perceive`) and
   **Finding 1** (no `--memory` path reachable from `cli.py`) by tracing the value path
   (change 4b).
4. Let the pipeline fix both, then demonstrate the behavioral DoD **through the CLI**: store a
   fact in session A, ask in session B via `axiom-cli`, and observe the answer reflect it.

**Pass condition:** the improved pipeline, re-run on the *unmodified* M3 code, independently
rediscovers both findings and drives them to a fix where memory demonstrably informs the
agent's answer through the real interface. If it finds but cannot cleanly fix, surface for
human steer — do not force.

**Fail-is-informative:** if the re-run does NOT rediscover the findings, the methodology change
is insufficient — that outcome is itself the signal to iterate the change, before we trust it
on new specs.
