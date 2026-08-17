# Local Agent Skill Blueprint

A **local agent** is a Python program that runs its own agentic loop against a local
model, packaged as a Claude Code skill. A Claude session invokes it **once** and
receives **one typed result**. Claude does not supervise the loop, does not proxy tool
calls, and never sees the working content the local model produced.

This is a *skill-shaped delivery pattern* that happens to use pydantic-ai internally.
It is not one of the `pydantic/` agent shapes (`src/agents/{name}/` classes wired into
CLI/web interfaces) — see [Related Blueprints](#related-blueprints).

---

## 1. Why This Exists — The Motivating Audit

The predecessor design kept Claude **inside** the loop: the local model requested one
tool call, Claude judged it, executed it with Claude's own tools, appended the result,
and looped. An audit of a real run (building a small Python todo app) found:

| Measure | Result |
|---------|--------|
| Claude turns to supervise **3** local-model turns | ~70 |
| Turns that took no action (`thinking → text → tool` shape) | 55% — roughly **3 expensive turns per single action** |
| Generated code that reached the cloud anyway | All of it — Claude read the local model's output files back into its own context to decide what to execute |
| Human approvals the provenance log claimed | 3 |
| Human approvals that were actually deliberate | 1 |

The per-action approval gate collapsed to a blanket auto-yes within ~20 minutes — with
the system's own designer as the operator — while the log kept recording each action as
individually approved.

Moving the loop into Python collapsed **~70 turns to 1**, and the generated code never
entered Claude's context at all.

### Two principles this yields

**P1 — Fixed setup cost amortizes; per-action cost does not.**
A per-action gate scales linearly with the work and is the term that keeps the economics
upside-down. It is also what trains a human to auto-approve — which is *worse* than no
gate, because it manufactures false assurance.

**P2 — Never let the model author its own provenance.**
A model-reported "files I touched" can be fabricated. Python owns the execution log; the
model authors only a prose summary.

Both principles are structural in the design below: P1 is why there is exactly one
process invocation and no per-tool round trip; P2 is why there are **two** output models
instead of one.

---

## 2. Architecture

```
.claude/skills/<name>/
├── SKILL.md              # invocation contract Claude reads
└── scripts/
    ├── run.py            # the ONLY interface Claude sees; one JSON object on stdout
    ├── agent.py          # pydantic-ai Agent; the loop
    ├── tools.py          # plain functions; docstrings are the schema
    └── requirements.txt  # pinned deps
```

Single process, single invocation:

```
Claude session
    │  writes task text + system prompt (temp files if long)
    ▼
python scripts/run.py --task <text|path> --system <text|path> [--model] [--endpoint]
    │
    ├─ resolve args (path-or-literal)
    ├─ set OLLAMA_BASE_URL
    ├─ preflight GET <host>/api/tags
    ├─ install run-local execution log (ContextVar)
    └─ asyncio.wait_for( agent loop , 600s )
            └─ local model ⇄ tools.py (N iterations, no Claude involvement)
    ▼
exactly one JSON object on stdout  ──► Claude reads a compact result, not a transcript
```

The Python process owns the internal loop, the tool calls, the preflight probe, the
runtime execution log, and final output shaping. Claude owns only the brief and the
interpretation of one result.

---

## 3. Module Responsibilities

### `scripts/run.py` — the only Claude-facing interface

Owns:
- Parsing `--task`, `--system`, `--model`, `--endpoint`.
- Resolving `--task` and `--system` through **one shared** path-or-literal helper.
- Applying the endpoint override via `os.environ["OLLAMA_BASE_URL"]` **before** agent construction.
- The preflight probe and its classification.
- The runtime execution log (created here, installed for the run).
- Invoking the replaceable module-level runner **once**.
- Enforcing the overall timeout.
- Assembling and printing exactly one `RunResult` JSON object — success *and* failure.

Does **not** own: tool implementations, a repo-stored system prompt, or any multi-turn
Claude-facing protocol.

### `scripts/agent.py` — construction and the loop

Owns: `Agent` construction with the provider-agnostic model string, `instructions`,
`output_type=AgentSummary`, `output_retries`, tool registration, the tool-call bound, and
returning the model-authored summary.

Does **not** own: provenance fields, `RunResult` construction, endpoint classification,
or any guard.

### `scripts/tools.py` — the model's hands

Owns: the tool functions, their docstrings (which *are* the JSON schema the model sees),
appends to the shared execution log, and keeping every exception inside the function.

Does **not** own: scope checks, path fences, approval prompts, or provenance beyond the
in-memory execution log.

### `SKILL.md` — the invocation contract

Must tell Claude: `run.py` is the only entry point; `--task`/`--system` accept literal
text *or* a file path; long text goes to a temp file and the path is passed; the system
prompt is caller-supplied per invocation and is not stored in the repo; the return value
is one JSON object, not a transcript.

### Portability — `SKILL.md` must contain no absolute path to itself

A skill is a **copyable artifact**. It gets copied into another checkout, a sandbox, or a
different project — and the copy must exercise *itself*.

The defect, found in a real implementation after six review passes had signed it off:
`SKILL.md` hardcoded the invocation as

```text
python C:/Projects/second-brain/.claude/skills/local-agent/scripts/run.py --task ... --system ...
```

When the skill was copied to another checkout for testing, the copied `SKILL.md` still
pointed at the **original** `run.py`. A session in the sandbox would have silently
exercised the main repo's code while believing it was testing its own — with a green
result and no signal that anything was wrong.

The fix is to express the entry point relative to the skill's own directory, and to say so
out loud:

```text
Let DIR be the directory containing this SKILL.md.
Run: python DIR/scripts/run.py --task <value> --system <value> [--model <name>] [--endpoint <url>]

Always run the copy of `scripts/run.py` sitting beside THIS SKILL.md — never a path to
another checkout.
```

**Why every gate missed it**, which is the part that generalises: each review read
`SKILL.md` in the location it was written, where the absolute path was correct. Nothing
ever exercised the copy-and-move case. Reviews validate content **in situ** and are blind
to portability unless someone asks the question explicitly. Add it to the review checklist
rather than expecting it to surface.

Note the asymmetry: the Python was clean throughout — no absolute paths in `run.py`,
`agent.py`, `tools.py`, or the tests. The prose file is where this class of defect hides,
because prose has no import that fails and no test that turns red.

---

## 4. Decisions That Earned Their Place

Each of these was contested during review. The rationale is the load-bearing part —
copy the rationale, not just the rule.

| # | Decision | Why |
|---|----------|-----|
| D1 | `run.py` is the **only** Claude-facing interface | Claude invokes one process once and receives one structured result, rather than supervising internal agent work. This is P1 made concrete. |
| D2 | **Model-string construction only** — `Agent(f'ollama:{model}')`, endpoint via `OLLAMA_BASE_URL` | Conforms to the APEX pydantic provider-agnostic rule: never construct provider objects, never pass an API key in code. The first draft violated this by hand-building a provider; the design gate caught it. |
| D3 | Use `instructions`, not `system_prompt` | Instructions are excluded from message history, so nothing leaks across turns. Matches the house pydantic rule. |
| D4 | **Two output models, not one** | `AgentSummary` is the agent's `output_type` and carries only what the model is entitled to author. `RunResult` is assembled by `run.py` from the model summary plus Python-owned runtime state, and is **never shown to the model**. Setting `output_type=RunResult` would force the model to emit its own provenance — P2 violated. The gate caught this too. |
| D5 | The system prompt is **not stored in the repo** | The calling Claude session writes it per invocation, the way it briefs any other agent. A repo-stored prompt would make the skill single-purpose. |
| D6 | **Path-or-literal arguments**, one shared resolver, `is_file()` not `exists()` | No separate `*-file` flags to keep in sync. `exists()` would make a directory path a read error instead of literal text. Long text goes to a temp file and the path is passed — which also makes the brief auditable after the run. |
| D7 | Hard bounds in the **library's own units** | 15 successful tool calls (`UsageLimits(tool_calls_limit=15)`), 2 output-validation retries, 600s overall. Adopt the library's unit rather than inventing a counting rule — design pass 3 failed purely on "rounds" vs "successful tool calls" being different things. |
| D8 | Real cancellation, **honestly bounded** | The overall timeout uses `asyncio.wait_for`, which genuinely cancels at await points. The first implementation joined a daemon thread — the run reported a timeout while the abandoned worker kept writing files. |
| D9 | Run-local provenance via `contextvars.ContextVar` | A process-global log let a timed-out run leak its late writes into the *next* run's results. Reproduced, then fixed. |
| D10 | **Exactly one JSON object on stdout, always** — including argument errors | Subclass `ArgumentParser` so parse failures become a structured result rather than usage text on stdout. |
| D11 | Preflight probe (`GET <host>/api/tags`) | Separates "endpoint unreachable" from "model not found" instead of mapping opaque client exceptions after the first request. |
| D12 | **Tools never raise into the loop** | Every tool returns a string, including on error. A non-zero exit from `run_command` is a normal result the model reads and reacts to, not an exception that kills the run. |
| D13 | A replaceable module-level runner seam | Success paths test with `TestModel`; failure paths inject synthetics; tools are tested directly. **No unit test may require a live local model.** |
| D14 | `SKILL.md` states the entry point **relative to its own directory** — never an absolute path | A skill is a copyable artifact. A hardcoded absolute path survives the copy and silently points the copy back at the original `run.py`, so a sandbox test exercises the wrong code and passes green. Found only after six review passes had signed the skill off — see [Portability](#portability--skillmd-must-contain-no-absolute-path-to-itself). |

---

## 5. Implementation Pattern

Code below is lifted from a working implementation (44 tests, `pydantic-ai==1.62.0`).

### `agent.py` — construction and the loop

```python
"""Agent construction and default runner for the local-agent skill."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.usage import UsageLimits

from tools import edit_file, read_file, run_command, web_search, write_file


class AgentSummary(BaseModel):
    """Structured output emitted by the model."""

    summary: str


def build_agent(model_name: str, system_text: str) -> Agent:
    """Build the pydantic-ai agent with the exact tool and output contract."""

    agent = Agent(
        f"ollama:{model_name}",
        instructions=system_text,      # D3 — not system_prompt
        output_type=AgentSummary,      # D4 — never RunResult
        output_retries=2,
    )
    agent.tool_plain(read_file)
    agent.tool_plain(write_file)
    agent.tool_plain(edit_file)
    agent.tool_plain(run_command)
    agent.tool_plain(web_search)
    return agent


async def run_agent_summary(task_text: str, system_text: str, model_name: str) -> AgentSummary:
    """Run the agent once and return the model-authored summary only."""

    agent = build_agent(model_name, system_text)
    result = await agent.run(
        task_text,
        usage_limits=UsageLimits(tool_calls_limit=15),   # D7
    )
    return result.output
```

Note the tools are registered with `agent.tool_plain(function)` — plain sync functions,
no `RunContext`, docstrings as the schema. This is a deliberate divergence from the house
"I/O-bound tools must be async" guidance, recorded in the source design as an owner
decision without a stated reason. One consequence observed in practice: the tool layer
stays directly unit-testable without an event loop. **State such a divergence
explicitly** — an unstated one reads as a mistake.

### The two output models (D4)

```python
# Model-facing — the ONLY thing the model is entitled to author.
class AgentSummary(BaseModel):
    summary: str


# Python-owned assembly target — never an output_type, never shown to the model.
class RunResult(BaseModel):
    status: Literal["success", "error"]
    summary: str                 # copied from AgentSummary on success; Python-authored on failure
    files_touched: list[str]     # Python-owned
    commands_run: list[str]      # Python-owned
    error_type: str | None
    error_message: str | None
    endpoint_used: str           # actual value after defaults/overrides
    model_used: str
```

`run.py` must not trust model-supplied provenance even if the model emits it elsewhere.

### Path-or-literal resolver (D6)

```python
def resolve_text_argument(value: str, argument_name: str) -> str:
    """Resolve a literal string or existing file path into text."""

    candidate = Path(value)
    if candidate.is_file():
        try:
            with open(candidate, "r", encoding="utf-8-sig", newline="") as handle:
                resolved = handle.read()
        except UnicodeDecodeError as exc:
            raise ResolverError(f"Failed to read {argument_name} from {candidate}: {exc}") from exc
        except OSError as exc:
            raise ResolverError(f"Failed to read {argument_name} from {candidate}: {exc}") from exc
    else:
        resolved = value

    if not resolved.strip():
        raise ResolverError(f"{argument_name} resolved to empty or whitespace-only text")
    return resolved
```

`utf-8-sig` strips a BOM; `newline=""` preserves newline style. Behavior table:

| Input | Filesystem state | Resolves to | Outcome |
|-------|------------------|-------------|---------|
| `C:/temp/task.txt` | Existing UTF-8 file | File contents | Success unless empty/whitespace |
| `C:/temp/missing.txt` | No such file | The literal string | Success as literal text |
| `C:/temp/folder` | Existing directory | The literal string | Success as literal text |
| `line 1\nline 2` | Not a path | Literal multi-line string | Success |
| `""` | — | Empty string | **Error** |
| `C:/temp/zero-byte.txt` | Zero-byte file | Empty string | **Error** |

Accepted limitation: a literal string identical to an existing file path cannot be passed
literally. **Document it; do not work around it.**

### Run-local provenance (D9)

```python
@dataclass
class RuntimeLog:
    files_touched: list[str] = field(default_factory=list)
    commands_run: list[str] = field(default_factory=list)
    _seen_files: set[str] = field(default_factory=set)

    def record_file(self, path: str) -> str:
        absolute = str(Path(path).resolve())
        if absolute not in self._seen_files:
            self._seen_files.add(absolute)
            self.files_touched.append(absolute)
        return absolute

    def record_command(self, command: str) -> None:
        self.commands_run.append(command)


_RUNTIME_LOG: contextvars.ContextVar[RuntimeLog | None] = contextvars.ContextVar(
    "local_agent_runtime_log", default=None,
)


@contextlib.contextmanager
def install_runtime_log(runtime_log: RuntimeLog) -> Iterator[RuntimeLog]:
    """Install a run-local runtime log for the duration of a block."""

    token = _RUNTIME_LOG.set(runtime_log)
    try:
        yield runtime_log
    finally:
        _RUNTIME_LOG.reset(token)
```

Log rules:
- `files_touched` — absolute paths, first-use order, deduplicated. **Record attempts that
  raised**: if the tool tried to touch the file, the file was touched.
- `commands_run` — exact command string as invoked, execution order, recorded only once
  the subprocess has actually started.

A module-global list here is the bug: a run that timed out kept writing after
cancellation and its late entries surfaced in the *next* run's `files_touched`.

### Preflight classification (D11)

```python
def perform_preflight(endpoint: str, model_name: str, timeout: float = 5.0) -> PreflightResult:
    """Probe the ollama tags endpoint and verify the requested model exists."""

    tags_url = _build_tags_url(endpoint)          # scheme+netloc + "/api/tags"
    request = urllib.request.Request(tags_url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, socket.timeout, TimeoutError, OSError) as exc:
        raise ConnectionError(str(exc)) from exc          # → endpoint_unreachable
    except ValueError as exc:
        raise ConnectionError(f"Invalid JSON from preflight endpoint {tags_url}: {exc}") from exc

    available_models = [
        m.get("name") for m in payload.get("models", []) if isinstance(m, dict) and m.get("name")
    ]
    if model_name not in available_models:
        available = ", ".join(available_models) if available_models else "(none)"
        raise LookupError(                                 # → model_not_found
            f"Requested model '{model_name}' was not found. Available models: {available}"
        )
    return PreflightResult(available_models=available_models)
```

The `model_not_found` message **must list what is available** — otherwise the caller's
next move is another blind run.

### Structured argument errors (D10)

```python
class JsonArgumentParser(argparse.ArgumentParser):
    """Preserves normal help behavior; routes parse errors back to main()."""

    def error(self, message: str) -> None:
        self.print_usage(sys.stderr)      # usage stays on stderr
        raise ArgumentParseError(message)
```

Because `endpoint_used` and `model_used` are non-null even on an argument error, `run.py`
bootstraps them with a permissive `parse_known_args` pass before strict parsing:

```python
def _bootstrap_endpoint_and_model(argv):
    parser = JsonArgumentParser(add_help=False)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    try:
        namespace, _ = parser.parse_known_args(argv)
    except ArgumentParseError:
        return DEFAULT_ENDPOINT, DEFAULT_MODEL
    return namespace.endpoint, namespace.model
```

Verified behavior: missing flags, unknown flags, and missing values each produce exit code
`0`, exactly one stdout line, a single JSON object with `error_type="invalid_arguments"`,
and usage text on stderr. `--help` still behaves normally.

### Real cancellation (D8)

```python
async def _run_with_timeout(task_text, system_text, model_name, timeout_seconds) -> AgentSummary:
    # asyncio cancellation stops the agent coroutine at its await points. A sync tool
    # already executing in a worker thread cannot be interrupted; that residual window is
    # bounded by the tool's own timeout (run_command 120s, web_search 30s) and is
    # documented rather than engineered around.
    return await asyncio.wait_for(RUNNER(task_text, system_text, model_name), timeout=timeout_seconds)
```

The rejected alternative — a daemon thread with a join timeout — *reports* a timeout while
the abandoned worker keeps writing files. That is a lie in the result object, and it was
reproduced before being fixed.

### The single assembly point

```python
try:
    with install_runtime_log(runtime_log):
        task_text = resolve_text_argument(args.task, "--task")
        system_text = resolve_text_argument(args.system, "--system")
        os.environ["OLLAMA_BASE_URL"] = endpoint_used      # before construction
        perform_preflight(endpoint_used, model_used)
        summary_result = asyncio.run(
            _run_with_timeout(task_text, system_text, model_used, OVERALL_TIMEOUT_SECONDS)
        )
except ResolverError as exc:
    result = _error_result(..., error_type="input_resolution_failed", ...)
except ConnectionError as exc:
    result = _error_result(..., error_type="endpoint_unreachable", ...)
except LookupError as exc:
    result = _error_result(..., error_type="model_not_found", ...)
except Exception as exc:
    error_type, summary, error_message = _map_runner_exception(exc)
    result = _error_result(...)
else:
    result = RunResult(
        status="success",
        summary=summary_result.summary,          # model-owned
        files_touched=runtime_log.files_touched, # Python-owned
        commands_run=runtime_log.commands_run,   # Python-owned
        error_type=None, error_message=None,
        endpoint_used=endpoint_used, model_used=model_used,
    )

_print_result(result)
return 0
```

Every path — including failure — falls through to one print and exit code `0`. The exit
code is not the channel; the JSON is.

---

## 6. Tool Contracts

Plain sync functions, each returning a JSON-encoded `str`. **No tool raises out to the
loop** (D12). Docstrings are the schema the model reads — write them for the model, not
for a human maintainer.

| Tool | Signature | Rules |
|------|-----------|-------|
| `read_file` | `(path: str) -> str` | UTF-8. Missing file / non-UTF-8 → structured error string. Record the absolute path **before** reporting either outcome. |
| `write_file` | `(path: str, content: str) -> str` | Create parent dirs. Overwrite unconditionally. Return byte count *and* character count. Record path first. |
| `edit_file` | `(path: str, old: str, new: str) -> str` | Replace **exactly one** occurrence. Zero matches → error. More than one → error telling the model to add context. Preserve newline style (`newline=""`). Record path first. |
| `run_command` | `(command: str) -> str` | `shell=True`, process cwd, inherited env, 120s timeout, stdout+stderr combined. **Non-zero exit is a normal result**, not an exception. Record the command once the subprocess has started. |
| `web_search` | `(query: str, max_results: int = 5) -> str` | 30s timeout. Title, URL, snippet per hit. Zero results → structured message. Library errors → structured message. |

The "record before reporting" rule matters: a failed attempt is still evidence of intent,
and provenance that hides failed touches understates what the run reached for.

`run_command` uses `Popen` + `communicate(timeout=...)` rather than `subprocess.run` so
the command can be logged *after* the process actually starts but *before* it completes,
and so a timeout can kill and still drain output.

---

## 7. Bounds and Failure Taxonomy

| Bound | Value | Mechanism | `error_type` |
|-------|-------|-----------|--------------|
| Successful tool calls per run | 15 | `UsageLimits(tool_calls_limit=15)` → `UsageLimitExceeded` | `tool_call_limit_exceeded` |
| Structured-output validation retries | 2 | `output_retries=2` → `UnexpectedModelBehavior("Exceeded maximum retries (2) for output validation")` | `structured_output_validation_failed` |
| Overall run wall clock | 600s | `asyncio.wait_for` in `run.py` | `overall_timeout_exceeded` |

Other `error_type` values: `invalid_arguments`, `input_resolution_failed`,
`endpoint_unreachable`, `model_not_found`, `agent_run_failed`.

Rules that were hard-won:
- **Adopt the library's counting unit.** `tool_calls_limit` counts *successful* tool
  calls. One model turn may contain more than one tool call, so turns are not the unit.
  Do not layer a custom round counter on top of a package primitive — that is what design
  pass 3 failed on.
- `request_limit` is **not** used as a secondary net. It constrains model requests, not
  tool calls, and would create a second interacting cap nobody asked for.
- Failed tool attempts still appear in `files_touched` but do not consume the budget,
  because the package counts successes only. Say this out loud; it surprises readers.
- Timeout hierarchy is outer-to-inner: `600s` run, `120s` command, `30s` search. If an
  inner and outer timeout race, whichever is observed first is reported — the outer may
  mask an in-flight inner one. Documented, not engineered around.
- On any failure, `files_touched` and `commands_run` return whatever accumulated before
  the failure, including empty lists. `summary` explains the bound that was hit **without
  claiming work completed**.

---

## 8. Testing — No Live Model, Ever

The seam is one replaceable module-level function:

```python
RUNNER = run_agent_summary        # run.py module level; tests reassign it
```

| Path | Technique |
|------|-----------|
| Success | `pydantic-ai` `TestModel` — auto-generates a valid `AgentSummary` |
| Bound/exception failures | Reassign `run.RUNNER` to a synthetic coroutine that raises the target exception |
| Timeout | Reassign `RUNNER` to a slow coroutine and shrink `run.OVERALL_TIMEOUT_SECONDS` |
| Preflight classification | Stub `perform_preflight` directly |
| Tools | Call the functions directly against temp files — no model, no event loop |
| Web search | Replace the module-level `DDGS_FACTORY` seam |

**No unit test may require a live local model.** A test suite that needs the service
running is a test suite that stops being run.

Regression tests worth keeping permanently, because each maps to a bug that was actually
reproduced:
- After a timeout, a late write from the abandoned run must **not** appear in the next
  run's `files_touched`.
- After a timeout, the abandoned worker's file must not exist (real cancellation, not a
  join).
- Argument errors must produce exactly one stdout line of JSON, exit `0`, usage on stderr
  — while `--help` still prints normal help.

---

## 9. What Was Deliberately NOT Built

V1 has **no scope guard, no path containment check, no approval gate, and no provenance
file**. This is a decision, not an omission.

The reasoning: *drop any guards before we prove this works — if it fails for the guard, we
will accidentally blame the harness.* A guard failure and an architecture failure look
identical in the output. V1 exists to prove that "single Python process plus one
structured result" works. An implementation that quietly adds those controls is
**non-conforming** to this design.

**The other half, which must be stated with equal weight:** this is a v1 stance, **not a
recommendation for production**. A local model with unfenced `write_file` and
`shell=True` `run_command` is exactly as dangerous as it sounds. Before any real user
touches such a system, revisit — as its own spec, not as an implementation detail —
path containment, a scope boundary, and a durable provenance record. Note that P1 above
constrains *how* to add them: a per-action human gate is the one shape known to fail,
because it decays into auto-approval while still producing an approval log.

---

## 10. Process Lessons

- **The design gate repeatedly caught defects in the architect's own decisions**, not just
  implementer sloppiness. The blueprint-conformance contradiction and the dropped step cap
  were both authored by the reviewer's own earlier self. This is the argument for never
  skipping the dryrun on your own design.
- **Convergence came from giving each fix worker decided resolutions, not open questions.**
  Findings went 8 → 2 → 1 → 0 across four design passes; code findings 3 → 0 across two.
- **Late-stage gates need explicit instruction not to manufacture findings** to appear
  rigorous — and equally not to rubber-stamp. Without that, review rounds tail off into
  stylistic noise.
- **Verify on artifacts, never on a worker's self-reported PASS.** Every closed code bug
  above was closed by running a reproduction and reading the output, not by a claim.
- **Reviews validate content in situ and are blind to portability.** Six passes read
  `SKILL.md` where it was written, where its absolute path was correct, and none caught
  that the path breaks on copy. A gate only tests the question it was asked. If an
  artifact is meant to be copied, *ask the copy question explicitly* — nothing about
  reading the file in place will raise it.
- **Verify library semantics against the installed package, offline.** The env var name,
  the `tool_calls_limit` docstring, and the exact `UnexpectedModelBehavior` message were
  all read out of the installed `pydantic_ai` source rather than recalled. Two of the
  design findings were nothing but recalled-instead-of-read API details.

---

## 11. File Checklist

When building a new local agent skill:

- [ ] `.claude/skills/<name>/SKILL.md` — entry point, path-or-literal rule, file-wins
      warning, temp-file guidance, the JSON shape, bounds, and the documented timeout
      limitation
- [ ] **No absolute path to the skill's own files anywhere in `SKILL.md`** — entry point
      expressed relative to the skill's directory, plus an explicit "run the copy beside
      this SKILL.md" line. Check this by copying the skill elsewhere and reading the copy.
- [ ] `scripts/run.py` — CLI, resolver, env-var application, preflight, timeout, runtime
      log, single JSON assembly point
- [ ] `scripts/agent.py` — `Agent` construction, `AgentSummary` output type, tool
      registration, usage limits, runner seam
- [ ] `scripts/tools.py` — tool functions with model-facing docstrings, execution-log
      appends, no raises
- [ ] `scripts/requirements.txt` — pinned framework version and tool deps
- [ ] `scripts/test_run.py`, `test_agent.py`, `test_tools.py` — offline only
- [ ] Divergences from house pydantic conventions stated explicitly, with rationale
- [ ] The "deliberately not built" list stated with **both** halves

---

## Related Blueprints

- [`../pydantic/agents/agent_orchestrator.md`](../pydantic/agents/agent_orchestrator.md) —
  provider-agnostic model strings, `instructions` vs `system_prompt`, `tool` vs
  `tool_plain`, `TestModel`. The local agent follows those rules; it differs in *shape*
  (a skill invoked once as a subprocess, not a class wired into an interface).
- [`../pydantic/agents/agent_stateless_subagent.md`](../pydantic/agents/agent_stateless_subagent.md) —
  the in-process equivalent when there is no locality or turn-cost motivation.
- [`../multi-agent/agent-lifecycle.md`](../multi-agent/agent-lifecycle.md) — for
  long-running agents rather than one-shot invocations.
