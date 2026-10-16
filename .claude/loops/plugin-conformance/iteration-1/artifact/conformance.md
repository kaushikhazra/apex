# APEX — Plugin Specification Conformance

Every rule below is checked by reading a file and answering yes or no. A rule that cannot be failed that way is not in this table.

**Sources of authority, in order:** the specification first; convention second, and only where the specification is silent.

**Status:** `pass` · `fail` · `exception` (a deliberate, recorded departure) · `vacuous` (the rule applies to nothing present, so it passes without having been exercised).

---

## The result in one line

**APEX conforms to the published specification, and to the convention, with two deliberate exceptions.** No rule is failing.

| | Count |
|---|---:|
| Total rules | 31 |
| **Pass** | **29** |
| **Fail** | **0** |
| Exception | 2 |
| Unchecked | 0 |
| — spec-derived (A, B, C) | 23 → **23 pass** |
| — convention-derived (D) | 8 → **6 pass, 2 exceptions** |

**The two exceptions, D6 and D7, are one decision and it belongs to Kaushik.** APEX resolves its own plugins through `git-subdir` against its own repository — deliberate, per commit `6d045ec` — and D6 follows from that. Both close automatically if that decision is ever revisited.

## What changed in APEX

| Rule | Change |
|---|---|
| X5 | `README.md` install instructions no longer name `#develop` |
| D3 | `marketplace.json` declares `$schema` |
| D4 | `author` added to all three entries |
| D5 | `category` added to all three entries |
| D1, D2 | Three plugin directories moved under `plugins/`, renamed for the plugin each publishes, with `marketplace.json` and every version bumped in the same commit |

```
sdlc/spec-enhanced   ->  plugins/e-spec          1.2.1 -> 1.2.2
agents/crosschat     ->  plugins/crosschat       0.5.1 -> 0.5.2
ai-engineering       ->  plugins/ai-engineering  0.2.0 -> 0.2.1
```

---

## A. Plugin manifest rules

From [plugins-reference](https://code.claude.com/docs/en/plugins-reference). Checked against all three plugins: `e-spec` at `sdlc/spec-enhanced`, `crosschat` at `agents/crosschat`, `ai-engineering` at `ai-engineering`.

| # | Rule | Source | e-spec | crosschat | ai-engineering |
|---|---|---|---|---|---|
| P1 | Manifest at `<plugin-root>/.claude-plugin/plugin.json` | Spec — *"Required location: `.claude-plugin/plugin.json`"* | pass | pass | pass |
| P2 | Manifest optional; name derives from directory if absent | Spec — *"The manifest is optional"* | pass | pass | pass |
| P3 | `name` present | Spec — *"`name` is the only required field"* | pass | pass | pass |
| P4 | `name` is kebab-case, no spaces | Spec — *"Unique identifier (kebab-case, no spaces)"* | pass | pass | pass |
| P5 | `.claude-plugin/` holds only the manifest; component directories at plugin root | Spec — *"All other directories … must be at the plugin root, not inside `.claude-plugin/`"* | pass | pass | pass |
| P6 | Manifest path fields start with `./` | Spec — *"All paths must be relative to the plugin root and start with `./`"* | **vacuous** | **vacuous** | **vacuous** |
| P7 | Directories named by manifest fields exist | Spec — *"Claude Code does not auto-create missing ones"* | **vacuous** | **vacuous** | **vacuous** |
| P8 | Each skill directory contains `SKILL.md` | Spec — *"Skills are directories with `SKILL.md`"* | pass | pass | pass |
| P9 | Skills sit under `skills/` | Spec — default component location table | pass | pass | pass |

**P6 and P7 are vacuous, and that is stated rather than counted as a tested pass.** No APEX manifest declares a path field — all three carry only `name`, `description`, `version`, `author` and sometimes `keywords`. The rules are satisfied because there is nothing for them to govern. If a path field is ever added, they become live.

## B. Marketplace manifest rules

From [plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces). Checked against `.claude-plugin/marketplace.json`.

| # | Rule | Source | Status |
|---|---|---|---|
| M1 | `marketplace.json` at `.claude-plugin/` in the repository root | Spec — *"Create `.claude-plugin/marketplace.json` in your repository root"* | pass |
| M2 | `name`, `owner`, `plugins` all present | Spec — Required fields table | pass |
| M3 | Marketplace `name` kebab-case, no spaces | Spec — *"kebab-case, no spaces"* | pass — `apex-tools` |
| M4 | `name` not reserved for Anthropic | Spec — reserved-names note | pass |
| M5 | `owner.name` present | Spec — Owner fields, Required = Yes | pass |
| M6 | Every entry carries `name` and `source` | Spec — *"at minimum a `name` and a `source`"* | pass — all 3 |
| M7 | Every `source` is a permitted type | Spec — *"must be of type `github`, `url`, or `git-subdir`, or a relative path"* | pass — all 3 `git-subdir` |
| M8 | `git-subdir` carries `url` and `path` | Spec — source-type table | pass — all 3 |
| M9 | Entry `version` matches the plugin's own | Spec — *"bump it on every release"* | pass — 1.2.1 / 0.5.1 / 0.2.0 all agree |

## C. Cross-manifest consistency

| # | Rule | Status |
|---|---|---|
| X1 | Each `git-subdir` `path` resolves to a real directory | pass — all 3 |
| X2 | Each resolved directory contains `.claude-plugin/plugin.json` | pass — all 3 |
| X3 | Marketplace entry `name` agrees with the plugin's own `name` | pass — all 3 |
| X4 | Any pinned `ref` names a branch that exists on the remote | pass — `master` exists |
| X5 | Install documentation names the same ref the manifest pins | **pass** — fixed |

**X5 — fixed.** `README.md` told users to install from `#develop`, twice, while `marketplace.json` pins `"ref": "master"` on all three plugins. A user following the README added the marketplace from a branch the manifest does not publish from.

Both instructions now read:

```
/plugin marketplace add kaushikhazra/apex
```

**The ref was dropped rather than changed to `#master`.** Omitting it takes the repository's default branch, which is `master` — verified, not assumed — so the instruction stays correct if that branch is ever renamed. A hardcoded `#master` would have to be found and corrected a second time.

**With this, the specification side is fully clean: 23 of 23.**

## D. Convention rules

Evidence base: four multi-plugin repositories, two of them Anthropic's own — `anthropics/claude-code`, `anthropics/claude-plugins-official`, `42Crunch-AI/claude-plugins`, `adobe/skills`. All place plugin directories under a single `plugins/` parent. No counter-example found.

| # | Rule | Evidence | Status |
|---|---|---|---|
| D1 | Plugin directories sit under one top-level `plugins/` parent | All four repositories | **pass** — fixed |
| D2 | Grouping subdirectories are permitted *inside* `plugins/` | `adobe/skills` uses `plugins/creative-cloud/<name>` | **pass** — fixed; no grouping needed at three plugins |
| D3 | `marketplace.json` declares `$schema` | Both Anthropic marketplaces declare it | **pass** — fixed |
| D4 | Entries carry `description`, `version`, `author` | Anthropic populates all three on nearly every entry | **pass** — fixed |
| D5 | Entries carry `category` | Anthropic sets it on every entry in both marketplaces | **pass** — fixed |
| D6 | `git-subdir` pins `sha` as well as `ref` | 83 of 83 `git-subdir` entries in `claude-plugins-official` pin `sha` — 100% | **exception** — consequent on D7 |
| D7 | Same-repo plugins use a relative source, not `git-subdir` | Anthropic's own entries use `"./plugins/<name>"`; **zero of 83 `git-subdir` entries point at the marketplace's own repository** | **exception** |
| D8 | `metadata.pluginRoot` unused; paths written in full | Neither Anthropic marketplace uses it | pass |

### The failures, concretely

**D1 and D2 — fixed.** The three plugins previously sat at three different depths under three different parents: a methodology category, an agent category, and the repository root. They now sit under one `plugins/` parent, each directory named for the plugin it publishes.

**The rename was part of the fix, not decoration.** `sdlc/spec-enhanced` published a plugin called `e-spec` — the directory, the manifest `name` and the marketplace entry disagreed. All three now read the same word.

**No grouping subdirectory was introduced.** `adobe/skills` uses `plugins/creative-cloud/<name>` because it has enough plugins to warrant it. Three do not, and inventing a taxonomy to demonstrate that D2 is understood would be the same failure as inventing categories to fill a column.

`sdlc/` now holds only `scaled-agile`, which is not a plugin and is out of scope. It was left alone.

**D3, D4 and D5 are fixed.** `marketplace.json` now declares `$schema` as `https://json.schemastore.org/claude-code-marketplace.json` — the URL `anthropics/claude-code` uses, preferred over the alternative in `claude-plugins-official` because SchemaStore publishes and maintains it, so editors resolve it. All three entries now carry `author` and `category`.

**On `category`, all three landed on `development`, and that is recorded rather than diversified.** Anthropic's observed vocabulary includes `development`, `productivity`, `learning`, `security` and `design`. A spec-driven SDLC, an agent messaging mesh, and methods for engineering agent behaviour are all developer tooling. Splitting them across categories to make the column look varied would have been a distinction invented to fill a field.

### D6 and D7 are one issue, not two

The `claude-plugins-official` manifest was re-read in full — 286 entries — to test whether D6 was mis-scoped. The counts:

| | Count | Pins `sha` |
|---|---:|---|
| Same-repo entries (relative string source) | 53 | 0 — a string source has no field to pin |
| External entries (object source) | 233 | **233 — every one** |
| — of which `git-subdir` | 83 | **83 — every one** |
| `git-subdir` pointed at the marketplace's own repository | **0** | — |

**D6 was not mis-scoped. It was under-explained.** Every `git-subdir` entry pins `sha`, without exception, and the reason is that `git-subdir` is used exclusively for repositories the marketplace does not control. A branch ref in someone else's repository is a moving target; a commit pin is what stops it moving.

**Nobody points `git-subdir` at their own repository.** Zero of 83. APEX is in a configuration that does not occur anywhere in a 286-entry catalogue, and it is there because of D7.

**So D6 is a consequence of D7, not an independent failure.** Take the D7 exception and D6 follows automatically: you inherit a rule written for foreign repositories. Resolve D7 — relative sources for same-repo plugins — and D6 evaporates, because a relative source cannot pin a `sha` and does not need to.

**Recorded as `exception`, consequent on D7, rather than as a failure to fix.** Fixing it in isolation would mean pinning a commit that does not yet exist: the `sha` D6 wants is the commit that contains the fix. That circularity is itself a symptom of pointing `git-subdir` at the repository you are editing.

**If the D7 decision stands and D6 is to be closed anyway**, it takes two commits: merge this branch, then a follow-up on `master` writing the merge `sha` into all three sources — and every subsequent release has to bump the pin, or consumers freeze on it.

### D7 — recorded as an exception, not a defect

APEX resolves all three of its own plugins through `git-subdir` against its own repository. Anthropic uses relative paths for plugins living in the same repository as the marketplace and reserves `git-subdir` for plugins in *other* repositories.

**This was deliberate.** Commit `6d045ec`, *"marketplace: resolve every plugin from GitHub, not from the local clone"*, chose it on purpose. The convention is recorded, the departure is recorded, and the decision stands unless Kaushik overturns it.

---

## What Kaushik owns

**One decision: D6 and D7.** APEX resolves its own plugins through `git-subdir` against its own repository, which no entry in Anthropic's 286-plugin catalogue does. It was chosen deliberately in commit `6d045ec`, *"resolve every plugin from GitHub, not from the local clone."*

- **Keep it.** Both stay as exceptions with the reason recorded. To close D6 anyway takes two commits — merge, then a follow-up on `master` writing the merge `sha` — and every release thereafter must bump the pin or consumers freeze on it.
- **Revisit it.** Relative sources for same-repo plugins, and both exceptions disappear.

**One thing outside the plugin specification**, noted here because no rule reaches it: `README.md` states *"Private repository. Internal use only."* while the repository is public.

---

## Candidates dropped

Recorded so the omission is deliberate rather than forgotten.

| Candidate | Why |
|---|---|
| "Manifests should be consistent with each other" | Cannot be failed by pointing at a file. Replaced by X1–X5. |
| "Plugins should be discoverable" | Not documented, not checkable. |
| "The repository README should be accurate" | Real, but outside the plugin specification. **Note:** `README.md` states *"Private repository. Internal use only."* while the repository is public. Tracked outside this table because no plugin rule reaches it. |
