# Assumptions

Standing inputs. These may change during the run — when one does, record it in that cycle's Observe.

## What "best convention" means

**Anthropic's own examples first. Observed prevalence where the documentation is silent. Never preference.** Every convention-derived rule carries its evidence in the artifact.

## Scope

**In scope — the three plugins:**

| Plugin | Path | Version |
|---|---|---|
| `e-spec` | `sdlc/spec-enhanced` | 1.2.1 |
| `crosschat` | `agents/crosschat` | 0.5.1 |
| `ai-engineering` | `ai-engineering` | 0.2.0 |

Plus the marketplace manifest at `.claude-plugin/marketplace.json`.

**Out of scope:** `blueprints/`, `sdlc/scaled-agile` and `.claude/` are not plugins and stay untouched unless a rule genuinely reaches them.

## Constraints

- **The plugins are live.** All three are installed from `marketplace.json` at `ref: master`. Any path change keeps the manifest in lockstep in the same commit, or consumers break on their next update.
- **APEX is public.** Nothing private enters it, including in the cycle logs, which are committed here.
- **Branch:** `feature/plugin-spec-conformance`, cut from master at 85487d3.

## Known inconsistencies at the start

Recorded as observations rather than as findings. The audit decides which are non-conformance, which are convention breaches, and which are neither.

1. **Three plugins, three placements.** `sdlc/spec-enhanced` under a methodology category, `agents/crosschat` under an agent category, `ai-engineering` at the root with no category.
2. **A category folder does not mean plugin.** `sdlc/` holds `spec-enhanced`, which has a `plugin.json`, and `scaled-agile`, which does not.
3. **Two directories named blueprints.** `.claude/blueprints/` holds four, `blueprints/` holds seven.
4. **The refs disagree.** `README.md` says install from `#develop`; `marketplace.json` pins `ref: master`.
5. **`README.md` claims the repository is private.** It is public.
