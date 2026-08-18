# Local Agent — Architectural Blueprints

Patterns for **local agents**: Python programs that run their own agentic loop against a
local model, packaged as a Claude Code skill, which a Claude session invokes **once** and
receives **one typed result** from.

The defining move is that the loop lives in Python, not in the cloud session. Claude
writes a brief, starts one process, and reads one JSON object. It never proxies tool
calls and never pulls the working content back into its own context.

## Blueprints

| # | Blueprint | What It Captures |
|---|-----------|-----------------|
| 1 | [Local Agent Skill](local-agent-skill.md) | Skill + `run.py`/`agent.py`/`tools.py` anatomy, two-output-model provenance rule, path-or-literal args, hard bounds in library units, real cancellation, offline test seam |

## Why This Is Its Own Category

`blueprints/pydantic/` is organised by *pydantic-ai construct* — agents, graphs, prompts —
and describes in-process classes wired into CLI or web interfaces. A local agent is a
**delivery shape**: a subprocess with a one-shot CLI contract that happens to use
pydantic-ai inside. Nesting it under `pydantic/agents/` would bury a cross-cutting
pattern inside a library-specific family. It cross-references that family instead.

## Assumed Stack

**Runtime**: Python 3.12+ · **LLM Framework**: Pydantic AI (`pydantic-ai==1.62.0` verified)
· **Local model host**: Ollama (`OLLAMA_BASE_URL`) · **Packaging**: Claude Code skill
(`.claude/skills/<name>/`)

The provider is swappable by model string alone — the patterns hold for any local host.
To decide *which* local model is fit for the work you are delegating, calibrate it first:
`ai-engineering/skills/local-model-calibration/SKILL.md`.

## The Two Principles

| Principle | Statement |
|-----------|-----------|
| P1 | **Fixed setup cost amortizes; per-action cost does not.** A per-action approval gate scales linearly with the work and decays into auto-approval — worse than no gate, because it manufactures false assurance. |
| P2 | **Never let the model author its own provenance.** Python owns the execution log; the model authors only a prose summary. |

Both are derived from a measured audit, not from taste — see
[Local Agent Skill §1](local-agent-skill.md#1-why-this-exists--the-motivating-audit).
