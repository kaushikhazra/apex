# Skills — Blueprint-to-Skill Conversion

Each blueprint in `.claude/blueprints/` can be promoted to a distributable Claude Code skill. This directory is the staging area.

## Pattern: Skill per Blueprint

A skill is a self-contained unit Claude auto-activates when context matches its description. Blueprints already contain the right content — the conversion is mainly about packaging them for distribution and writing a trigger-oriented description.

## Directory Layout

```
skills/
  <name>/
    SKILL.md          ← required: frontmatter (name, description) + full blueprint body
    <support-files>   ← optional: templates, examples referenced by SKILL.md
  README.md           ← this file
dist/
  <name>.zip          ← distributable artifact, ready to install
```

SKILL.md lives at the root of the staging dir and must inflate to the root of the installed skill dir.

## Building a Zip

```bash
cd skills/<name>
zip -r ../../dist/<name>.zip .
```

Verify contents before distributing:

```bash
unzip -l ../../dist/<name>.zip
```

## Installing a Skill

```bash
unzip -d ~/.claude/skills/ dist/<name>.zip
```

Claude Code picks up skills from `~/.claude/skills/` automatically on next session start.

## SKILL.md Format

```markdown
---
name: <kebab-case-name>
description: |
  <trigger-oriented description — max ~1400 chars>
  Use when... / Invoke when Kaushik... / Trigger on requests like X, Y, Z.
  NOT: what's inside the skill. YES: when to activate it.
---

# Title

<full blueprint body>
```

The `description` frontmatter is the ONLY thing Claude reads for matching — make it concrete and trigger-specific.

## When to Promote a Blueprint to Skill Form

Promote when ALL of these are true:
- The blueprint is stable (not actively being revised)
- You've run it at least once on a real project
- You want it auto-activating across multiple sessions or machines
- The content is self-contained (no hard local paths that break on other machines)

Do NOT promote a blueprint that's still evolving — edit the source in `.claude/blueprints/` first, then re-package.

## Source of Truth

**Blueprints** (`.claude/blueprints/`) are the authoring home. Skills (`skills/`) are read-only packaging output. If content needs updating, edit the blueprint, then rebuild the zip.
