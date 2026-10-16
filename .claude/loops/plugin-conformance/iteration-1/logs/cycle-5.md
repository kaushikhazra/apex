# Cycle 5 — 2026-08-18 18:08 IST — fix D3, D4, D5

**Phase:** 4, second fix. **Rules:** D3 `$schema`, D4 `author`, D5 `category`. All three are additive fields in `marketplace.json`.

## Rule count

| | Cycle 4 | Cycle 5 |
|---|---|---|
| Total rules | 31 | 31 |
| Pass | 24 | **27** |
| Fail | 6 | **3** |
| Exception | 1 | 1 |
| — spec-derived | 23 pass, 0 fail | 23 pass, 0 fail |
| — convention-derived | 1 pass, 6 fail | **4 pass, 3 fail** |

## What changed

`.claude-plugin/marketplace.json` only. Three additions, no field altered or removed:

- `$schema` at the top of the document
- `author: { name: Kaushik }` on all three entries
- `category: development` on all three entries

**`source` and `version` were not touched.** `sha` is D6 and it changes what consumers receive, so it gets its own cycle.

## Which `$schema` URL, and why

The two Anthropic marketplaces disagree. `anthropics/claude-code` uses `https://json.schemastore.org/claude-code-marketplace.json`; `anthropics/claude-plugins-official` uses `https://anthropic.com/claude-code/marketplace.schema.json`.

**Took the SchemaStore one.** It is a published, maintained entry that editors actually resolve — SchemaStore carries `claude-code-marketplace.json` in its catalogue, which the phase-2 survey turned up independently. The specification notes Claude Code ignores the field at load time either way, so the only consumer is an editor, and the URL an editor can resolve is the useful one.

## ⭐ All three categories came out the same, and that was left alone

Anthropic's observed vocabulary includes `development`, `productivity`, `learning`, `security`, `design`.

A spec-driven SDLC, an agent-to-agent messaging mesh, and methods for engineering agent behaviour are all developer tooling. **All three are `development`.**

The temptation was to split them — `crosschat` into something infrastructural, `ai-engineering` into something research-shaped — so the column would look considered. **That would have been a distinction invented to fill a field.** A category that does not discriminate is still the honest answer, and the log records it rather than hiding it behind variety.

## Re-check

The file parses. Each rule was confirmed separately rather than inferred from one read:

- `$schema` present and correct → D3 `pass`
- `author` on 3 of 3 entries → D4 `pass`
- `category` on 3 of 3 entries → D5 `pass`
- `ref` still `master`, `sha` still absent on all three → D6 correctly still `fail`

That last line matters: it confirms the cycle stayed inside its scope rather than quietly picking up the next rule.

## Goal check — **NOT MET**

Three failures remain: D6, D1, D2.

## Next

**D6** — add `sha` alongside `ref` on all three sources. First change in this run with a real consequence for consumers: a commit pin means an installed client stops tracking the branch and only moves when the pin moves. It needs its own cycle, its own re-check, and a note in the artifact that the pin now has to be bumped on release.
