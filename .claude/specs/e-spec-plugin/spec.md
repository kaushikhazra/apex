# e-spec Plugin Spec

## What it does
Bundle the 10 spec-enhanced skills as a Claude Code plugin under namespace `e-spec`.

## Why
Replace copy-paste distribution (currently FPAI, Velasari, Noteflow each have their own copies) with plugin install. Single source, versioned, no drift.

## User Stories
- (a) Kaushik installs `e-spec` in a new project with one command
- (b) APEX maintainer bumps version, downstream projects pick it up via `/plugin update`
- (c) Namespace prevents collision with project-local skills

## Acceptance Criteria
- [ ] plugin.json valid and present at `sdlc/spec-enhanced/.claude-plugin/plugin.json`
- [ ] All 10 skills present at `skills/<name>/SKILL.md`
- [ ] README.md documents install + namespace prefix gotcha
- [ ] Version is `1.0.0`
- [ ] No broken paths inside any SKILL.md body referencing old `.claude/skills/` location

## Decisions
- D1: plugin name = `e-spec` (short, ergonomic, namespace-safe)
- D2: plugin root = `C:/Projects/APEX/sdlc/spec-enhanced/` (restructure in place)
- D3: skills move from `.claude/skills/<name>/` to `skills/<name>/` (flat `skills/` folder per Claude Code plugin spec)
- D4: keep `CLAUDE.md` at plugin root for contributor guidance
- D5: `version: "1.0.0"` (without it, every commit triggers update notifications)
- D6: do NOT submit to Anthropic marketplace — git URL install sufficient
