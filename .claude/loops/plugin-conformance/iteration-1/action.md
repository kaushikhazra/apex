# Action

**D1 and D2 — move the three plugin directories under `plugins/`. Last change, and the only one that can break a live install.**

## The move

```
sdlc/spec-enhanced   ->  plugins/e-spec
agents/crosschat     ->  plugins/crosschat
ai-engineering       ->  plugins/ai-engineering
```

**Name each directory after the plugin, not after its old parent.** The marketplace entry, the `plugin.json` `name`, and the directory should all read the same word. `sdlc/spec-enhanced` publishing a plugin called `e-spec` is the placement inconsistency and the naming inconsistency in one line.

Use `git mv` so history follows each directory.

## The same commit must carry the manifest

`.claude-plugin/marketplace.json`, all three `path` values:

```
"path": "sdlc/spec-enhanced"  ->  "path": "plugins/e-spec"
"path": "agents/crosschat"    ->  "path": "plugins/crosschat"
"path": "ai-engineering"      ->  "path": "plugins/ai-engineering"
```

**A moved directory whose manifest still points at the old path breaks every installed consumer on their next update.** These are not two changes.

## Bump every version

All three, in `plugin.json` and in the matching marketplace entry — they must stay equal, which is M9:

- `e-spec` 1.2.1 → 1.2.2
- `crosschat` 0.5.1 → 0.5.2
- `ai-engineering` 0.2.0 → 0.2.1

A consumer only refetches when the version moves. Without a bump they keep resolving a path that no longer exists.

## Then find what else pointed at the old paths

Grep the whole repository for `sdlc/spec-enhanced`, `agents/crosschat`, and `ai-engineering` as a path. Known so far:

- `README.md` — the install section names `sdlc/spec-enhanced` in the local `--plugin-dir` example and in the marketplace-manifest sentence
- `blueprints/local-agent/readme.md` — points at `ai-engineering/skills/local-model-calibration/SKILL.md`, corrected only an hour ago

**Fix every hit. A path rename that leaves stale references behind is the class of failure that produced this loop.**

## Re-check, rule by rule

- Every plugin root under `plugins/` → D1 `pass`
- Nothing beside `plugins/` claiming to be a plugin → D2 `pass`
- Each `path` resolves to a real directory → X1 still `pass`
- Each resolved directory holds `.claude-plugin/plugin.json` → X2 still `pass`
- Entry `name` equals plugin `name` → X3 still `pass`
- Entry `version` equals `plugin.json` version, all three → M9 still `pass`
- `marketplace.json` parses

**Re-check the C-section rules explicitly.** They passed before the move and this is exactly the change that can break them.

## If the goal is met

31 rules: 29 `pass`, 2 `exception`, 0 `fail`. Report the final table, the two exceptions and their reasons, and everything that changed in APEX. **Stop the loop and delete the cron.**

## One thing to leave

**`sdlc/` still holds `scaled-agile`, which is not a plugin.** After the move it holds only that. Do not delete or relocate it — no rule reaches it, and it is out of scope by `assumption.md`. Note it in the log and leave it alone.
