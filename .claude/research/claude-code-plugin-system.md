# Claude Code Plugin System — Research

**Date:** April 1, 2026
**Purpose:** Understand how to package APEX as a distributable Claude Code plugin.

---

## Why This Matters

APEX already has skills, hooks, and blueprints organized under `.claude/`. The Claude Code plugin system lets us package all of this into a shareable, versioned, installable unit — so any project can pull in APEX methodology without copying files.

---

## Plugin Structure

A plugin is a directory with a `.claude-plugin/plugin.json` manifest plus any combination of components:

```
apex-plugin/
├── .claude-plugin/
│   └── plugin.json          # Manifest (required)
├── skills/                   # Slash commands (e.g., /apex:spec, /apex:design)
│   ├── spec/SKILL.md
│   ├── design/SKILL.md
│   ├── requirement/SKILL.md
│   ├── implement/SKILL.md
│   ├── dryrun-code/SKILL.md
│   ├── dryrun-design/SKILL.md
│   └── ...
├── agents/                   # Custom agent definitions
├── hooks/
│   └── hooks.json            # Event handlers (pre/post tool use, stop, etc.)
├── blueprints/               # Architectural patterns (APEX-specific)
├── .mcp.json                 # MCP server integrations (optional)
├── .lsp.json                 # Code intelligence (optional)
└── settings.json             # Default config (optional)
```

### Manifest (`plugin.json`)

```json
{
  "name": "apex",
  "description": "APEX — Spec-driven SDLC methodology with skills, hooks, and blueprints",
  "version": "1.0.0",
  "author": { "name": "Kaushik Hazra" }
}
```

---

## Components APEX Would Include

| Component | Current Location | Plugin Location | Notes |
|-----------|-----------------|-----------------|-------|
| Skills (spec, design, requirement, implement, dryrun-*) | `.claude/skills/` | `skills/` | Direct move. Commands become `/apex:spec`, `/apex:design`, etc. |
| Hooks (branch guard, security, ruff, cross-module) | `.claude/hooks/` | `hooks/hooks.json` | Need to consolidate into hooks.json format |
| Blueprints | `blueprints/` | `blueprints/` | Structural patterns — may need custom loading logic |
| SDLC docs | `sdlc/` | TBD | Reference material — decide if this ships with the plugin |

---

## Distribution Options

### 1. GitHub Marketplace (Recommended)

Create a `marketplace.json` at repo root:

```json
{
  "name": "apex-marketplace",
  "owner": {
    "name": "Kaushik Hazra"
  },
  "plugins": [
    {
      "name": "apex",
      "source": "./",
      "description": "Spec-driven SDLC methodology",
      "version": "1.0.0"
    }
  ]
}
```

Users install via:
```
/plugin marketplace add kaushikhazra/apex
/plugin install apex@apex-marketplace
```

### 2. Team Distribution

Add to any project's `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "apex": {
      "source": { "source": "github", "repo": "kaushikhazra/apex" }
    }
  },
  "enabledPlugins": {
    "apex@apex": true
  }
}
```

### 3. Official Anthropic Marketplace

Submit at `claude.ai/settings/plugins/submit` for public discovery.

---

## Plugin Sources (for marketplace entries)

| Source | Syntax | Use Case |
|--------|--------|----------|
| Relative path | `"./plugins/apex"` | Monorepo |
| GitHub | `{ "source": "github", "repo": "owner/repo" }` | Public repos |
| Git URL | `{ "source": "url", "url": "https://..." }` | Self-hosted |
| Git subdirectory | `{ "source": "git-subdir", "url": "...", "path": "..." }` | Monorepo subset |
| npm | `{ "source": "npm", "package": "@org/apex" }` | npm registry |

Versioning via `ref` (tag/branch) and `sha` (pinned commit) supported.

---

## Migration Path

1. **Add manifest** — create `.claude-plugin/plugin.json` in APEX repo
2. **Restructure hooks** — current individual `.py` files → consolidated `hooks/hooks.json`
3. **Test locally** — `claude --plugin-dir ./` from APEX root
4. **Validate** — `claude plugin validate ./`
5. **Add marketplace.json** — for GitHub distribution
6. **Push and announce** — users can install immediately

---

## Open Questions

- **Blueprints loading:** Blueprints are a custom APEX concept. Need to verify if Claude Code recognizes a `blueprints/` directory in plugins, or if we need a skill that reads them on demand.
- **SDLC reference docs:** Ship with plugin or keep separate? Adds weight but provides self-contained methodology.
- **Namespace:** `/apex:spec` vs just `/spec` — plugin namespace is automatic. Consider if the prefix is desirable or if we want shorter commands.
- **Settings defaults:** What APEX-specific settings should ship as defaults (e.g., model preferences, agent configs)?

---

## References

- Claude Code Plugins docs: `code.claude.com/docs/en/plugins-reference.md`
- Plugin submission: `claude.ai/settings/plugins/submit`
