---
name: graphite-design
description: Use this skill to generate well-branded interfaces and assets for Graphite, either for production or throwaway prototypes/mocks/etc. Contains essential design guidelines, colors, type, fonts, assets, and UI kit components for prototyping.
user-invocable: true
---

Read the README.md file within this skill, and explore the other available files.

Graphite is a warm-monochrome, dark-first design system for technical dashboard products. Single accent: highlighter yellow (`#eab308`), used sparingly. Technical type pairing (JetBrains Mono display + Inter body). Small radii (4–6px). Flat surfaces — borders, never shadows.

**Core files:**
- `colors_and_type.css` — all design tokens (colors, type, spacing, radii, motion). Import this first.
- `README.md` — voice, visual foundations, iconography rules.
- `preview/*.html` — card-sized specimens for every token and component.
- `ui_kits/dashboard/` — JSX components + interactive `index.html`. Lift components from here for any dashboard UI.
- `assets/` — logos and icon references.

**When producing visual artifacts** (slides, mocks, throwaway prototypes): copy `colors_and_type.css`, the logo, and any needed JSX components out, then build static HTML files for the user to view.

**When working on production code:** read the tokens and rules, then write idiomatic CSS/JSX that references the variables rather than raw values.

**Rules that matter most:**
1. The yellow accent appears **at most once per screen**.
2. No shadows — use 1px borders for all elevation.
3. No emoji, no illustrations in product chrome.
4. Sentence case everywhere; ALL CAPS only for eyebrow labels.
5. Icons are Lucide, 1.5px stroke, inheriting `currentColor`.

If the user invokes this skill without other guidance, ask them what they want to build, ask clarifying questions, and act as an expert designer who outputs HTML artifacts or production code depending on the need.
