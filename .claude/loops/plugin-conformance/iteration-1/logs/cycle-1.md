# Cycle 1 — 2026-08-18 17:32 IST — phase 1, extract the specification

**Phase:** 1 of 4. **Action:** read Anthropic's plugin documentation and extract every requirement as a file-level rule. Created `artifact/conformance.md`. **Nothing in APEX was touched.**

## Rule count

| | |
|---|---|
| Total rules | 23 |
| Pass | 0 |
| Fail | 0 |
| Unchecked | 23 |
| Open questions carried to phase 2 | 6 |

First cycle, so no movement to report against.

## Rules added

- **A. Plugin manifest — P1 to P9.** Manifest location, the single required field, kebab-case naming, the component-directory placement warning, the `./` path prefix, directory existence, and skill structure.
- **B. Marketplace manifest — M1 to M9.** File location, the three required fields, kebab-case naming, reserved names, per-entry minimums, permitted source types, `git-subdir` fields, and version bumping.
- **C. Cross-manifest — X1 to X5.** Derived from the two documents read together rather than from a single sentence, but each still names files and a comparison.

Every rule carries its documentation URL and the sentence it rests on.

## Reading the documentation was not optional

**Both documented URLs have moved.** `docs.claude.com/en/docs/claude-code/*` now 301s to `code.claude.com/docs/en/*`. Working from memory would have produced rules attributed to a stale location.

## ⭐ The finding that mattered most

**`git-subdir` is a documented, first-class source type** — *"Each plugin source must be of type `github`, `url`, or `git-subdir`, or a relative path within the marketplace repository"* — taking `url`, `path`, and optional `ref` and `sha`, with `sha` as the effective pin when both are set.

This was worth establishing early because all three APEX plugins use it. Had it turned out undocumented, the audit would have been a rewrite rather than a check. It is a check.

## Two rules that look likely to bite

Noted as *likely*, not as findings. Phase 3 decides.

- **P5** — component directories must sit at the plugin root, never inside `.claude-plugin/`. A hard warning in the specification, and the kind of thing that is easy to get wrong once and never notice.
- **P6** — every path written into a manifest field must start with `./`. APEX manifests are sparse, so this may not apply at all, which is itself a result.

## Deliberately not done

**No convention was inferred.** Six questions the specification leaves open are recorded in *Left open* and nothing more. The temptation was O1: the walkthrough uses `plugins/<plugin-name>/` and `metadata.pluginRoot` exists to support exactly that shape, which reads like the intended layout. **It is a hint, not a requirement, and phase 2 has to earn it from prevalence rather than from my reading of one example.**

**No auditing.** Extraction and audit are separated so the rule list is written without one eye on what APEX happens to do.

## Three candidates dropped

Recorded in the artifact rather than silently omitted. Two could not be failed by pointing at a file; the third — README accuracy — is real but outside the plugin specification.

## Goal check — **NOT MET**

23 rules, all unchecked. The goal requires every rule checked and every failure fixed.

## Next

**Phase 2.** Survey real plugin repositories and resolve the six open questions from observed prevalence. Anthropic's own examples carry more weight than count; a count of one is not prevalence.
