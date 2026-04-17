# Web UI Design Systems — Architectural Blueprints

Prescriptive design systems for web UI work. Each entry is a complete, opinionated visual language: color tokens, typography, spacing, component shapes, and at least one reference UI kit showing the system in motion.

## What this category is

These are not generic style guides — they are **build-ready design blueprints**. Each system ships with CSS token files, HTML/CSS previews you can open in a browser, and (where available) JSX component kits wired to the tokens. When starting a new web UI project, pick the system whose personality matches the product's domain, pull its tokens in, and build consistently within that language.

## When to use

Use a design system from this category whenever you are building:
- A technical dashboard or admin panel
- A SaaS product interface
- Any web UI where visual coherence across screens matters

Do **not** invent ad-hoc colors, fonts, or spacing scales from scratch. Pick a system, follow it, extend it deliberately.

## How to use

1. **Pick** the design system that matches the project's tone and domain (see entries below).
2. **Reference tokens** — import `colors_and_type.css` as the single source of truth for all color and typography values.
3. **Reference components** — copy relevant files from `ui_kits/` as starting points; they are already wired to the CSS variables.
4. **Follow the rules** stated in the system's `README.md` — typographic hierarchy, spacing scale, color usage constraints.
5. **Do not override tokens inline** — if a value needs to change, change it in the token file, not in component-level CSS.

## Current entries

| Folder | Name | Personality | Best for |
|--------|------|-------------|----------|
| [`graphite/`](graphite/README.md) | Graphite | Warm-monochrome dark-first; JetBrains Mono + Inter; single yellow accent `#eab308`; Linear-meets-GitHub density | Technical dashboards, developer tooling UIs, ops/monitoring interfaces |

**Graphite** is a dark-first design system built around warm neutral grays and a single high-contrast yellow accent. Typography pairs JetBrains Mono (code and metrics) with Inter (prose and UI text). The overall personality sits between Linear's precision and GitHub's information density — crisp, functional, zero decoration. The `ui_kits/dashboard/` kit ships a complete reference application: sidebar, top bar, overview screen, deployments screen, settings screen, command palette, and toast system, all implemented in React JSX against the CSS token layer.

## Adding a new design system

Each new entry must follow this structure (mirrors `graphite/`):

```
{system-name}/
├── SKILL.md              — skill artifact manifest (source + fetch instructions)
├── README.md             — design system documentation (personality, rules, token reference)
├── colors_and_type.css   — all color and typography CSS custom properties
├── assets/               — logos, icons, brand marks (SVG preferred)
├── preview/              — browser-openable HTML previews per token/component category
│   ├── _base.css         — shared preview shell styles
│   ├── color-*.html
│   ├── type-*.html
│   ├── spacing-*.html
│   ├── component-*.html
│   └── brand-*.html
└── ui_kits/              — optional reference implementations
    └── {kit-name}/       — named kit (e.g. dashboard, marketing, docs)
        └── ...           — JSX/CSS/HTML components wired to token variables
```

Rules for a valid entry:
- `colors_and_type.css` must define all values as CSS custom properties — no hardcoded hex in component files.
- Preview HTML files must reference `_base.css` via relative path (`href="_base.css"`).
- `README.md` must document: color palette, typography pairing, spacing scale philosophy, and at least one usage constraint ("don't use X for Y").
- Update this `readme.md` to add the new entry to the table above.
