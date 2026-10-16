# Plugin Spec Conformance

## Goal

> Bring every plugin in APEX into conformance with Anthropic's published Claude Code plugin specification, and into one convention for everything the specification leaves open.
>
> **Done** when every rule — spec-derived or convention-derived — has been checked against the actual files, item by item, and each one either passes or has been fixed.

## What counts as a rule

**File-level and concrete.** *`plugin.json` sits at `<plugin-root>/.claude-plugin/`* is a rule. *Manifests should be consistent* is not, because it cannot be failed.

Two sources, in this order of authority:

1. **The specification.** Anything Anthropic's documentation requires.
2. **The convention**, for anything the specification leaves open. Taken from Anthropic's own examples where they show one, and from observed prevalence in real plugin repositories where they do not. Never from preference.

**Conformance and consistency are not the same thing.** Three plugins at three different depths may be entirely legal and still wrong by convention. Both are in scope, and each rule records which of the two it comes from.

## The test is documentary

**Reading the files, not loading the plugins.** Loading proves a plugin is valid; it says nothing about whether it follows a convention, because both layouts load. Every rule is checked by inspecting the files it names.

## Phases

Each phase is sized to fit one cycle.

1. **Read the specification.** Extract every requirement as a file-level rule.
2. **Survey real plugin repositories.** For everything the specification leaves open, record what is actually done and how widely.
3. **Audit APEX** against the combined rule list. Pass or fail, per rule, per plugin. **Change nothing.**
4. **Onward.** Fix one failing rule per cycle, re-check it, move to the next.

**Phases 1 to 3 write only the artifact.** Nothing in APEX moves until phase 4, so the audit is taken before anything is disturbed.
