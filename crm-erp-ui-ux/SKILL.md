---
name: crm-erp-ui-ux
description: Design and implement professional CRM/ERP web UI with React — app shell, data grids, forms, motion, Phosphor icons, abilities gating, and accessibility. Synthesizes ui-ux-pro-max + design-taste for operational dashboards (not marketing pages). Use when building or polishing warehouse CRM, admin panels, ERP modules, list/detail views, inline status, filters, bulk actions, or when the user mentions CRM UI, ERP UX, dashboard polish, DataTable, or operational software design.
---

# CRM / ERP UI/UX Skill

Operational software (CRM, ERP, warehouse, finance) — **not** landing pages. Prioritize scanability, permissions, dense data, and predictable workflows over hero sections and scroll storytelling.

## When to Apply

- New CRM/ERP page, module, or component
- Redesigning list/grid, editor, filters, or app shell
- Fixing alignment, motion, icons, empty/loading/error states
- Wiring UI to backend `abilities` / permissions
- Reviewing UI for accessibility or “looks unprofessional” on dashboards

**Out of scope:** marketing sites, portfolios, scroll-hijack landing pages. For those, use `design-taste-frontend` instead.

---

## 1. Design Read (mandatory, one line)

Before coding, declare:

> **Reading this as:** \<module type\> for \<role/audience\>, \<density\> operational UI, \<stack\>, accent \<color family\>.

Example: *Reading this as: import grid for warehouse managers, dense operational UI, React + CSS tokens + Phosphor, purple-navy accent.*

If ambiguous, ask **one** question: *“Should this screen prioritize density (more rows visible) or breathing room?”*

---

## 2. Three Dials (CRM defaults)

| Dial | CRM default | Range | Meaning |
|------|-------------|-------|---------|
| **DESIGN_VARIANCE** | 4 | 1–10 | 1 = symmetric tables; 8+ = asymmetric marketing (avoid in ERP) |
| **MOTION_INTENSITY** | 4 | 1–10 | 1 = static; 4–6 = micro-interactions; 8+ = scroll choreography (rare in ERP) |
| **VISUAL_DENSITY** | 7 | 1–10 | ERP lives at 6–8: compact rows, clear hierarchy, monospace for numbers |

Override only when the user asks. **Never** apply landing-page patterns (bento heroes, marquees, kinetic type) to data grids.

---

## 3. Priority Stack (from ui-ux-pro-max, CRM-adapted)

Apply in order when trade-offs appear:

| P | Area | CRM rule |
|---|------|----------|
| 1 | **Accessibility** | Contrast 4.5:1, focus rings, `aria-label` on icon-only buttons, keyboard sort/filter |
| 2 | **Touch & interaction** | Min **44×44px** hit area (`--touch-min: 44px`), 8px+ gaps, loading/disabled feedback |
| 3 | **Performance** | Skeleton matching layout, no CLS on table load, debounce search 300ms |
| 4 | **Consistency** | One icon family (Phosphor), one radius scale, semantic CSS tokens |
| 5 | **Layout** | Sidebar + topbar shell; tables scroll inside main; no horizontal page scroll |
| 6 | **Typography & color** | 16px base; tabular nums for money/qty; semantic tokens not raw hex in components |
| 7 | **Motion** | 150–300ms transitions; `transform`/`opacity` only; honor `prefers-reduced-motion` |
| 8 | **Forms** | Label above field, error below, inline validation after first submit |
| 9 | **Navigation** | Predictable back, deep links, abilities hide nav items (don’t disable-only trap) |
| 10 | **Charts** | Legends, tooltips, never color-only meaning |

Deep rule lists: [reference.md](reference.md).

---

## 4. Stack & Dependencies

Detect from `package.json`. Smart-Warehouse pattern:

- **React** + Vite (or Next.js if present)
- **Icons:** `@phosphor-icons/react` — one family, one `strokeWidth` / weight globally
- **Styling:** CSS custom properties **or** Tailwind — match existing project; don’t mix paradigms on one screen
- **Routing:** `react-router-dom` — route = module boundary
- **Motion:** CSS transitions first; add `motion/react` only if already installed

Before importing any library, verify `package.json`. Output install command if missing.

---

## 5. Design Tokens (CRM shell)

Define once in `:root` (extend, don’t replace project tokens):

```css
:root {
  /* Brand */
  --primary: /* one accent */;
  --primary-dark: ;
  --primary-light: ;
  --sidebar: /* dark nav */;
  --surface: ;
  --text: ;
  --muted: ;

  /* ERP semantics */
  --success: ;
  --warning: ;
  --danger: ;
  --neutral: ;

  /* Layout */
  --sidebar-width: 260px;
  --topbar-height: 72px;
  --touch-min: 44px;
  --radius-sm: 8px;
  --radius-md: 12px;

  /* Type scale */
  --text-xs: 0.75rem;
  --text-sm: 0.875rem;
  --text-base: 1rem;
  --icon-inline: 18px;

  /* Motion */
  --transition-fast: 150ms ease;
  --transition-base: 220ms cubic-bezier(0.16, 1, 0.3, 1);
}
```

**Rules:**
- Max **one** accent color; saturation &lt; 80%
- No pure `#000` / `#fff` surfaces — use off-black/off-white
- Money and quantities: `font-variant-numeric: tabular-nums`
- Status colors map to semantic tokens, not random hex per row

---

## 6. App Shell Pattern

```
┌──────────┬─────────────────────────────────────┐
│ Sidebar  │ Topbar (breadcrumb, search, user,   │
│ (nav)    │         contextual widgets)         │
│          ├─────────────────────────────────────┤
│          │ Page header (title + primary CTA)   │
│          │ Filters / bulk bar (optional)       │
│          │ Main content (table / form / tabs)  │
└──────────┴─────────────────────────────────────┘
```

- **Sidebar:** module nav; collapse to icon rail on narrow desktop; drawer on mobile
- **Topbar:** global search (Ctrl+K), notifications, user menu; **read-only KPI widgets** (e.g. FX rate pill) — no heavy forms in topbar
- **Page header:** `MODUL` eyebrow (optional, max 1 per page) + title + **one** primary action (“Yangi qo‘shish”)
- Active nav: inset border or background token — not only color change

---

## 7. Data Grids (core CRM pattern)

### Structure

```
ListFiltersPanel → BulkActionsBar (when selection) → DataTable → TablePagination
```

### DataTable requirements

| Feature | Rule |
|---------|------|
| Sort | Click header; show CaretUp/Down/UpDown icon; `aria-sort` |
| Selection | Checkbox column; indeterminate “select all” |
| Loading | Skeleton rows matching column count — not spinner-only |
| Empty | `EmptyState` with label + optional CTA |
| Actions | Wrap in `.row-actions`: `display:flex; flex-direction:row; flex-wrap:nowrap; align-items:center; gap:6px` |
| Action buttons | Uniform **36px** height; icon-only **36×36**; text buttons same height |
| Row click | Only when navigates to detail — `cursor:pointer` + hover surface |
| Status column | `StatusBadge` read-only **or** `InlineStatusSelect` when ability allows |

### Filters

- Collapsible `ListFiltersPanel`: status, client, date range
- Debounced search; show active filter count
- Map to API query params — document in integration guide

### Bulk actions

- Bar appears when `selectedIds.length > 0`
- Destructive actions → `ConfirmDialog`
- Export CSV client-side OK; status change → modal + sequential API if needed

---

## 8. Forms & Editors

### Layout

- **Modal or slide-over** for create/edit on grids; full page for complex multi-section docs
- Label **above** input; helper optional; error **below** (`FieldError`)
- Validate on submit first; then inline on blur/change

### Data loading (abilities)

```javascript
// Products: always (for line items)
api.products({ page_size: 500 })

// Clients: only if ability
if (can(session, 'clients_view')) {
  api.clients({ page_size: 500 })
}
```

Never `Promise.all` a call the user can’t access — use parallel independent loads.

### Combobox

- Searchable dropdown for long lists (clients, products)
- Keyboard: arrow keys, Enter, Escape
- Show “loading” and “no results” states

### Embedded widgets

- **Compact panels** in forms (e.g. FX rate): tabs + minimal fields; auto-save on blur/Enter when appropriate
- **Header widgets**: read-only + optional refresh for managers only

---

## 9. Permissions → UI (abilities gating)

| Pattern | Do | Don’t |
|---------|-----|-------|
| Hide vs disable | **Hide** nav items and CTAs user can’t use | Show disabled buttons that 403 on click |
| Grid actions | Gate inline status on correct ability (e.g. `order_status_manage` not `procurement_manage`) | Copy ability name from nearby feature |
| Price fields | Hide amounts when `!prices_view` | Show “***” without backend also stripping |
| Management actions | Gate FX source, manual rate, user admin on `users_manage` | Rely on `IsAuthenticated` only |

Always mirror backend permission classes in UI gates.

---

## 10. Icons & Motion

### Icons (Phosphor)

```jsx
import { PencilSimple, ClockCounterClockwise, Plus } from '@phosphor-icons/react'

<PencilSimple size={18} aria-hidden="true" />
<button aria-label="Tarixni ko‘rish"><ClockCounterClockwise size={18} /></button>
```

- **Never** emoji as UI icons
- Icon-only buttons **must** have `aria-label`
- Inline icons: 16–18px; toolbar: 18–20px; empty states: 32–48px
- One weight/style per hierarchy level

### Motion (CRM-safe)

| Element | Animation |
|---------|-----------|
| Button press | `transform: scale(0.98)` or `-translate-y-px` 150ms |
| Modal | fade + scale from 0.98, 200ms |
| Sidebar | width/transform 220ms |
| Toast | slide + fade 250ms |
| Table row hover | background color only — no row height change |
| Skeleton | shimmer optional; respect reduced motion |

**Banned in grids:** row height animation, layout-shifting hover, decorative infinite loops on data rows.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Optional GSAP/`motion/react` only for dashboard charts or onboarding — isolate in client leaf components with cleanup.

---

## 11. Status & Feedback

### StatusBadge tones

`success` | `warning` | `danger` | `neutral` | `info` — map domain statuses consistently (e.g. `confirmed`, `received`, `cancelled`).

### Notifications

- Toast for success/error after mutations
- Inline banner for page-level errors
- Skeleton → content; never flash empty then load without skeleton

### ConfirmDialog

- Delete, cancel order, bulk status — explicit title + consequence text
- Primary destructive = danger token; focus trap in modal

---

## 12. CRM Anti-Patterns (forbidden)

| Anti-pattern | Why |
|--------------|-----|
| Marketing hero on list pages | Wastes vertical space |
| 3 equal feature cards on dashboard | Landing trope; use KPI row + tables |
| Decorative progress bars on every row | Noise; use badge or number |
| Vertical stack of row action buttons | Use horizontal `.row-actions` + `nowrap` |
| Full FX form in topbar | Clips/overflows; use read-only pill |
| `flex-wrap: wrap` on action column | Causes vertical button stack |
| Generic `Promise.all` for gated APIs | Breaks entire editor on 403 |
| Placeholder-as-label | Fails accessibility |
| Purple AI gradient slop on ERP | Use restrained brand accent |
| Inter as “premium” default | Match project font or Plus Jakarta / Geist / system UI stack |

---

## 13. Optional: ui-ux-pro-max Search

When installed at `~/.claude/skills/ui-ux-pro-max/`:

```bash
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" "dashboard data table filter" --domain ux
python "${CLAUDE_PLUGIN_ROOT}/.claude/skills/ui-ux-pro-max/scripts/search.py" "react list performance" --stack react
```

Use results to supplement — CRM rules in this skill **override** landing-page advice from generic searches.

---

## 14. Pre-Flight Checklist (CRM)

Before shipping UI:

**Structure**
- [ ] App shell: sidebar + topbar + page header hierarchy clear
- [ ] One primary CTA per page header
- [ ] Filters map to API; search debounced

**Grid**
- [ ] Skeleton, empty (+ CTA), error states
- [ ] Actions horizontal, 36px height, `nowrap`
- [ ] Sort icons + `aria-sort`
- [ ] Icon buttons labeled

**Forms**
- [ ] Labels above, errors below
- [ ] Abilities gate API loads and fields
- [ ] Loading/saving disabled states

**Visual**
- [ ] Tokens used (no random hex)
- [ ] Tabular nums on money/qty
- [ ] Focus rings visible
- [ ] Contrast AA on sidebar + table

**Motion**
- [ ] 150–300ms max on interactions
- [ ] No layout shift on hover
- [ ] `prefers-reduced-motion` respected

**Permissions**
- [ ] UI gates match backend permission classes
- [ ] Hidden nav for forbidden modules

---

## 15. Project Patterns (Smart-Warehouse reference)

When working on Smart-Warehouse or similar Django REST + React CRM:

| Concern | Location / pattern |
|---------|-------------------|
| Integration contract | `FRONTEND_API.md` |
| Abilities | `can(session, 'ability_key')` |
| Grid pages | `ResourcePage`, `listFilters.js`, `DataTable.jsx` |
| FX widget | `FxRatePanel` `header` (topbar) vs `compact` (editor) |
| Client detail tabs | `ClientDetailPage.jsx` |
| Global search | `GlobalSearch.jsx`, Ctrl+K |

Concrete snippets: [examples.md](examples.md).

---

## Additional Resources

- [reference.md](reference.md) — component specs, spacing scale, chart/table UX, dark mode
- [examples.md](examples.md) — copy-paste patterns from production CRM code
