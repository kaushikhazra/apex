# Fix spec — e-spec hook hardening

**Author**: Velasari, 2026-08-06
**Taskyn**: task `d220651b99024428a6661ba096a6e4d9`, todo `ca8787b6c0fa48c48f7f3eff73a7858f`
**Origin**: root-cause trace of the deletion of Velasari's `.git` on 2026-08-04. CM procedural memory `39a88be5-bde2-4a68-b1c9-2ddf8e97eb11`.

This is a **fix spec**, not a design document. Three defects, what changes, how to verify. Nothing else.

---

## The incident these came from

On 2026-08-04 17:21 IST a cleanup targeting a second-brain test copy ran, in PowerShell:

```
Set-Location "C:/Projects/claude-sandbox/sb"; if (Test-Path ".claude/.self-aware") { Remove-Item ".claude/.self-aware" -Force }; if (Test-Path ".git") { Remove-Item ".git" -Recurse -Force }; ...
```

`C:/Projects/claude-sandbox/sb` did not exist. `Set-Location` raised a **non-terminating** error, the `;` chain continued, and the **relative** path `.git` resolved against the session's real cwd — `C:\Projects\ai-persona\Velasari`. The persona repo's git history was destroyed. `-Force` bypasses the Recycle Bin; nothing was recoverable. Origin had last been pushed 2026-07-24, so eleven days of history were lost.

The same cleanup had **first** been attempted in bash as `rm -rf .git` and was **blocked by `security_guard.py`**. The PowerShell form was the workaround. That is D1.

---

## D1 — `security_guard.py` never inspects PowerShell

**What's broken**

- `hooks/hooks.json`: the `security_guard.py` matcher is `"Edit|Write|Read|Bash"`. The PowerShell tool is absent.
- `hooks/scripts/security_guard.py` line 57: `if tool_name == "Bash":` — a single-value equality test.
- `DANGEROUS_COMMANDS` holds Unix-shaped patterns only (`rm -rf /`, `rm -rf .`, `rmdir /s`, `del /s /q`). No `Remove-Item`.

Net effect: every destructive PowerShell verb walks straight past the guard. This is the hole the incident actually went through.

**What changes**

1. `hooks.json` — matcher becomes `"Edit|Write|Read|Bash|PowerShell"`.
2. `security_guard.py` line 57 — becomes a membership test over both tool names. The PowerShell tool's input field is also `command`, so extraction below it is unchanged.
3. Add Windows/PowerShell destructive patterns: `Remove-Item` with `-Recurse` and/or `-Force`, `rd /s`, `rmdir /s`, `del /s`, `Clear-Content` against a repo path.
4. Add a **narrowly scoped** guard for a destructive command whose target is a **relative** path resolving to `.git`.

**Scoping constraint — do not widen this.** A blanket "block all relative-path destructive commands" rule will fire on sanctioned routine work and get switched off. `Velasari/.claude/settings.local.json` already allowlists `Bash(rm -rf .tmp/*)`. Scope the relative-path guard to high-value targets, `.git` first. A guard that gets disabled protects nothing.

---

## D2 — `context_change_tracker.py` permanently disables the review gate

**What's broken**

`hooks/scripts/context_change_tracker.py` line 60:

```python
if display_path in existing:
    return
```

The dedup key is the **bare file path**, with no state component. Once a file has *ever* appeared in `.claude/eval.md`, every later edit to it is skipped silently and the Stop-gate never arms.

Confirmed live: `C:/Users/hazra/.claude/CLAUDE.md` was logged on 2026-08-04, so the 2026-08-06 edit to it produced no entry at all. Velasari's own `CLAUDE.md` appears four times in `eval.md`; its fifth edit onward passes unreviewed. The last entry in that file is dated 2026-08-04.

Second defect in the same file: `EVAL_FILE = ".claude/eval.md"` is a **relative** path resolved against the hook process's cwd — the same defect class as the incident.

**What changes**

1. Dedup on whether an **unchecked `- [ ]` entry already exists for that path**. The invariant is *is a review already pending for this file*.

   **Date-based keying is explicitly the wrong fix** — it still swallows a second edit on the same day. Do not implement it that way.

2. Anchor `EVAL_FILE` explicitly on the **session cwd / `CLAUDE_PROJECT_DIR` from the hook payload**.

   **Not** the edited file's own directory — anchoring on the file would send user-global `CLAUDE.md` edits to `C:/Users/hazra/.claude/.claude/eval.md`. Session-owns-the-review is the correct current behaviour; this change only makes it explicit rather than accidental.

---

## D3 — `context_eval_clear.py`: plumbing only, behaviour stays

**What it does today**

On any **bash** `git commit` whose message contains `"context evaluated"`, it unlinks `.claude/eval.md` and globs-deletes every `.claude/dryrun-*.md`. Relative paths, no confirmation, bash-only.

**Kaushik's decision (2026-08-06) — the delete behaviour is correct and stays.**

His reasoning, verbatim: *"after a review is done and we are satisfied with the changes, the dryrun documents are redundant… once the review is done, do we really need traceability for a non-deterministic system which evolves every 2-3 months?"* When told the same hook also removes `eval.md`, which had been surviving only because the hook was broken, he chose **full clean slate on commit** — both the reports and `eval.md` go.

**Do not change what it deletes. Do not add a preservation path. This is a settled decision, not an open question.**

**What changes — plumbing only**

1. Anchor `EVAL_FILE` and `DRYRUN_PATTERN` the same way as D2 (session cwd / `CLAUDE_PROJECT_DIR`), instead of relative-to-process-cwd.
2. Add PowerShell parity — the matcher and the `git commit` detection must also cover a commit issued through the PowerShell tool, which today silently skips the hook. Same inconsistency as D1.

---

## How to verify

### Yours (this session)

Unit tests for all three scripts. The regression test that matters most feeds the **literal incident command** through the new patterns and asserts BLOCKED:

```
Set-Location "C:/Projects/claude-sandbox/sb"; if (Test-Path ".git") { Remove-Item ".git" -Recurse -Force }
```

Also cover: a second edit to an already-logged path produces a fresh `- [ ]`; a path with a pending `- [ ]` does **not** produce a duplicate; a path whose entries are all `- [x]` **does** produce a new one.

### Velasari's (cross-session, after you report)

A worker cannot prove a PreToolUse hook fires in a live session, so this half is mine and the fix is not done until both pass:

- **(a)** Issue a PowerShell `Remove-Item` against a throwaway path under `C:/Projects/.tmp/` from the Velasari session and confirm the hook blocks it.
- **(b)** Edit a `CLAUDE.md` already logged in `eval.md` and confirm a fresh `- [ ]` entry appears — in the **right** `eval.md`, which also exercises the D2 path-anchor fix across projects.

### Open question you must answer, not assume

`hooks.json` lives in a **plugin** (`e-spec@apex-tools`, marketplace directory `C:/Projects/APEX`). Whether editing it takes effect in an already-running session, or requires a plugin/session reload, is **unverified**. Determine it empirically and state the answer in your report.

If it needs a reload and nobody checks, we ship a third guard that looks armed and isn't — which is precisely the failure shape all three of these defects share.

---

## Process requirements

- Work on a conforming **`bugfix/*`** branch. Never master — `protected_branch_guard` and `branch_name_validator` both run here.

  _Corrected 2026-08-06: this spec originally said `fix/*`, which `branch_name_validator.py` would have blocked — `VALID_PREFIXES` is `feature/, bugfix/, hotfix/, release/, milestone/`. APEX caught it and flagged rather than editing the validator to accommodate the spec. That was the right call: a guard bent to suit the work in front of it is the failure mode this whole spec exists to fix._
- Kaushik wants a **GitHub issue** opened for this work, and the fix **released with a version bump**.
- Report concrete evidence: file paths, test names and counts, exit codes, the reload answer. Not "it worked."

## Operating rule now in force

One shell command per tool invocation. Never sequence with `;`, `&&`, `||`, or newlines, in bash or PowerShell, even where your tool documentation suggests chaining. A single pipeline, a single required loop construct, and separators inside a quoted argument are fine; joining otherwise-independent commands is not. Destructive commands take absolute paths. A destructive command blocked by a hook means stop and report — never re-route through another shell.

That rule is the direct product of the incident above. It is in the user-global `CLAUDE.md` Coding Principles table and in `velhari-brief` directive 9.
