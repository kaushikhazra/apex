# Graphite Design System

A warm-monochrome, dark-first design system for a technical dashboard product. Single accent (highlighter yellow) used sparingly against a stone-gray base. Flat surfaces, small radii, comfortable density. Personality sits between Linear's precision and GitHub's utilitarian density.

> **Working name.** "Graphite" is a placeholder — swap freely. Nothing here depends on it.

---

## Source context

**No codebase, Figma, or attached materials were provided.** This system was generated from written direction:

- Monochrome — warm grays (slight beige/stone tint)
- Dark-first, light as secondary
- Single accent: highlighter yellow (`#eab308`)
- Technical type pairing — mono display + geometric sans body
- Small corner radii (4–6px), conservative
- Comfortable density, flat (no shadows)
- Personality: "Claude-like, or GitHub if not possible"
- Target product: Web app (dashboard / SaaS)

If you have real source material (Figma links, existing codebase, brand guidelines), drop them in and I'll reconcile against them. The foundations below are deliberately opinionated so you can push back.

---

## Index

```
/
├── README.md                  ← you are here
├── SKILL.md                   ← agent-invocable skill manifest
├── colors_and_type.css        ← CSS variables: colors, type, spacing, radii, motion
├── fonts/                     ← (empty — using Google Fonts: Inter + JetBrains Mono)
├── assets/
│   ├── logo.svg               ← wordmark
│   ├── logo-mark.svg          ← glyph only
│   └── icons/                 ← Lucide (CDN-linked; see ICONOGRAPHY)
├── preview/                   ← cards shown in the Design System tab
│   ├── color-*.html
│   ├── type-*.html
│   ├── spacing-*.html
│   └── component-*.html
└── ui_kits/
    └── dashboard/
        ├── README.md
        ├── index.html         ← interactive click-through
        └── *.jsx              ← component files
```

---

## Content fundamentals

**Voice.** Direct, technical, quiet. You're writing for engineers and operators who are already inside the product. No marketing cadence.

**Casing.** Sentence case everywhere — buttons, menus, headers, table columns. Never Title Case. Never ALL CAPS except for eyebrow labels (e.g. `OVERVIEW`, `ACTIVITY`), where caps + letter-spacing do real typographic work.

**Person.** Prefer the imperative ("Connect repository", "Deploy"). Use "you" when addressing the user directly. Avoid "we" — Graphite doesn't talk about itself.

**Numbers and units.** Always include units. `142ms`, `3.2 GB`, `12 commits`. Abbreviate with a thin space: `4 KB`, not `4kb`. Time is relative for recency (`2m ago`, `yesterday`) and absolute for history (`Apr 17, 14:32`).

**Punctuation.** Oxford comma. Em-dashes with no spaces — like this. Terminal punctuation in full sentences; no period on button labels or single-phrase captions.

**Error & empty states.** State the condition, then the next action.
- ✅ `Couldn't reach registry. Retry or check your token.`
- ❌ `Oops! Something went wrong 😔 Please try again later.`

**Emoji.** Not used. Not in UI, not in copy, not in empty states. Status is carried by color dots and small icons from Lucide.

**Examples**

| Context | Graphite voice |
|---|---|
| Empty state, no projects | `No projects yet. Create one to get started.` |
| Destructive confirm | `Delete 3 branches? This can't be undone.` |
| Button | `Deploy` · `Connect repository` · `Invite teammate` |
| Eyebrow label | `ACTIVITY` · `DEPLOYMENTS` · `USAGE` |
| Status inline | `Ready · 142ms · main@a3f9e2c` |
| Toast | `Deployed to production.` |

---

## Visual foundations

### Color

Warm grayscale, 14 stops from `--stone-950` (near-black with a hint of tobacco) to `--stone-50` (bone). Hue is constant — it's a true tint ladder, so overlays stack predictably. The accent is **highlighter yellow** (`--accent-500: #eab308`) and it appears at most **once per screen** — on the primary CTA, a selected state, or a single critical datum. If you find yourself using yellow twice, one of them is wrong.

Semantic aliases (`--fg-1`, `--bg-surface`, `--border-default`, etc.) map onto the stone ladder and flip automatically in `[data-theme="light"]`. Never reference stone stops directly in components — go through the semantic layer.

### Typography

- **Display & UI chrome:** `JetBrains Mono` — weights 400/500. Used for headings, numbers in tables, metrics, timestamps, and anything that benefits from fixed-width alignment.
- **Body & long-form:** `Inter` — weights 400/500/600. Used for paragraph copy, form labels, body text.
- **Eyebrows / labels:** Mono, 11px, uppercase, `0.08em` tracking. These carry the "technical" register.

Body text is 14px (app default). Display tops out at 44px — this is a dashboard, not a landing page. Never go below 12px except for kbd/badges. Line-height is 1.5 for body, 1.1–1.25 for headings.

> ⚠️ **Font substitution flagged.** Inter and JetBrains Mono are pulled from Google Fonts. If you have licensed brand fonts, drop the `.woff2` files into `fonts/` and update the `@font-face` block in `colors_and_type.css`.

### Spacing

4px base grid. Tokens: `--space-1` (4) through `--space-20` (80). Most component padding lives in `--space-2` / `--space-3` / `--space-4`. Section spacing uses `--space-8` / `--space-12`. No arbitrary values — if a number isn't on the scale, it's wrong.

### Backgrounds

- **Solid.** Near-universally. `--bg-app` for the page, `--bg-surface` for panels, `--bg-raised` for cards.
- **No gradients** in chrome. The one exception: the log/terminal fade-out at the bottom of a scrolling region — a 40px gradient from transparent to `--bg-surface`.
- **No illustrations, no patterns, no photography** in the product surface. Marketing surfaces (not covered in this kit) may use a single 1px grid overlay at 6% opacity; nothing more.
- **Full-bleed imagery:** avoided. Screenshots inside the product appear inside a bordered frame with a 1px `--border-default`.

### Borders

1px, `--border-default` for structure, `--border-subtle` for hairlines inside cards. Borders carry the entire visual hierarchy — no shadows. Focus rings use a 2-part box-shadow (2px bg-app + 2px accent) so focus is unambiguous on any surface.

### Shadows

None, by design. The `--elev-*` tokens exist but resolve to `none` or `0 0 0 1px var(--border-*)`. If a component needs to feel "raised," swap its border from subtle → default. That's the only elevation step.

### Radii

`3 / 4 / 6 / 8` px. Buttons and inputs are 4px. Cards are 6px. Modals are 8px. Pills (status, filter chips) are fully rounded.

### Motion

Restrained. Three durations (`100 / 160 / 240 ms`) and two eases (`ease-out`, `ease-in`). Use only for:
- Hover color transitions (100ms)
- Menu/popover enter (160ms, fade + 4px translate)
- Modal enter (240ms, fade + 8px translate)

No bounces. No spring physics. No decorative animation. `prefers-reduced-motion` should kill all transitions.

### Hover & press

- **Hover:** surface shifts to `--bg-hover` (one step warmer). No scale, no shadow. For text links, color shifts from `--fg-1` → `--fg-accent`.
- **Press:** surface shifts to `--bg-active`. No transform.
- **Selected:** 1px left border in `--accent-500`, background `--bg-hover`, text `--fg-1`.
- **Disabled:** opacity 0.4, cursor `not-allowed`, no hover response.

### Transparency & blur

Used only for **menus and modals' backdrops** — `rgba(13, 12, 10, 0.6)` + `backdrop-filter: blur(4px)`. Never on cards, panels, or inline chrome. Blur is a modal signal; don't dilute it.

### Imagery (when present)

- Screenshots: B&W or warm-neutral with slight grain at 4% opacity.
- Avatars: flat stone-200 background with initials in mono; no photos by default.
- Charts: single color (accent) + stone-500 for comparison series. No rainbow palettes.

### Cards

Border-only. 1px `--border-default`. 6px radius. Padding `--space-4` or `--space-6` depending on density. No header separator unless the card has a distinct toolbar row.

### Fixed elements

- Top nav: 48px, sticky, 1px bottom border.
- Sidebar: 240px, fixed, 1px right border.
- Bottom status bar (optional): 28px mono-font bar pinned to viewport bottom — for the "deploy terminal" aesthetic.

---

## Iconography

**Icon system:** [Lucide](https://lucide.dev) — 1.5px stroke weight, 16px default, 20px for nav, 14px inline with text. Loaded from CDN:

```html
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
<script>lucide.createIcons();</script>
```

Icons appear in `<i data-lucide="chevron-right">`. Colors inherit from `currentColor` so they sit in `--fg-2` by default.

> **Icon substitution flagged.** Lucide was chosen as the closest match to a clean technical-dashboard set. If you have brand-specific icons, drop SVGs into `assets/icons/` and reference them locally.

**No emoji.** Not in UI, not in copy, not in notifications. Status is carried by:
- A 6px color dot (`--status-success` / `warning` / `danger`)
- A Lucide icon at 14px
- A mono-caps eyebrow (`READY` / `FAILED`)

**Unicode as icon.** Only for:
- `→` `←` `↑` `↓` in inline prose ("Use → to advance")
- `·` as a separator in metadata (`main · 142ms · 3m ago`)
- `⌘ ⇧ ⌥ ⌃ ↵ ⎋` for keybindings inside `<kbd>`

**Logos:** `assets/logo.svg` (wordmark) and `assets/logo-mark.svg` (glyph). Both monochrome — they inherit `currentColor`. Never applied over the accent color.

---

## Components (see `preview/` and `ui_kits/dashboard/`)

- Buttons — primary, secondary, ghost, destructive; default and small
- Inputs — text, search, with leading icon, disabled, focused
- Badges — status pill, count pill, filter chip
- Cards — bordered surface with optional toolbar
- Tables — dense rows, mono-font numerics, sticky header
- Menus — popover, keyboard nav
- Tabs — underline style, mono labels
- Navigation — sidebar items with selected state
- Toasts — bottom-right, auto-dismiss, 1px border
- Modals — 560px default, backdrop blur

---

## Caveats

1. **No source material.** Everything here is generated from direction, not reconciled against real screens or brand assets.
2. **Fonts are substitutes** — Inter + JetBrains Mono via Google Fonts. Replace if you have licensed brand fonts.
3. **Icons are Lucide** via CDN. Replace if you have a proprietary icon set.
4. **Light mode is a courtesy** — tokens flip correctly, but only dark mode has been visually exercised in the UI kit.
5. **Marketing surfaces, mobile, and docs sites are not covered** — you asked for a web-app dashboard only.
