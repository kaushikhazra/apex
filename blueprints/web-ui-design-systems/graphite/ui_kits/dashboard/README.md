# Graphite Dashboard UI Kit

An interactive click-through of the Graphite web dashboard. Four screens, all static-but-clickable, demonstrating component coverage.

## Screens

1. **Overview** — landing after login. Project list as a table with status.
2. **Deployments** — deployment history for a single project; live-tailing log panel.
3. **Settings** — general project settings with form fields and destructive zone.
4. **Command palette** — `⌘K` overlay accessible from any screen.

## Components

- `AppShell.jsx` — sidebar + top bar + main content slot
- `Sidebar.jsx` / `NavItem.jsx` — left navigation
- `TopBar.jsx` — breadcrumb + search + avatar
- `Button.jsx` — primary / secondary / ghost / destructive; sm/default
- `Input.jsx` — text input with optional leading icon + trailing kbd
- `Badge.jsx` — status pill
- `Card.jsx` — bordered surface
- `Table.jsx` — dense table with sticky header
- `Tabs.jsx` — underline tabs
- `Menu.jsx` — popover menu
- `Toast.jsx` — bottom-right toast
- `CommandPalette.jsx` — ⌘K overlay
- `LogStream.jsx` — scrolling mono log lines
- `MetricCard.jsx` — card with large mono number

## Running

Open `index.html` directly — it loads React via CDN and all JSX files inline.

## Notes

All interactions are cosmetic. No real network, no real auth. Good for screenshot and prototyping; not production code.
