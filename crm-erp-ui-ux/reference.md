# CRM/ERP UI Reference

Extended rules for `crm-erp-ui-ux` skill. Read sections on demand.

---

## Spacing scale (8px rhythm)

| Token | Value | Use |
|-------|-------|-----|
| 4px | `--space-1` | Icon-text gap inside buttons |
| 8px | `--space-2` | Compact grid cell padding |
| 12px | `--space-3` | Input padding, filter chips |
| 16px | `--space-4` | Card/panel padding |
| 24px | `--space-6` | Section gaps |
| 32px | `--space-8` | Page header margin-bottom |

Dense ERP: prefer 8–12px inside tables; 16–24px between sections.

---

## Typography (operational UI)

| Role | Size | Weight | Notes |
|------|------|--------|-------|
| Page title | `--text-xl` / 1.25rem | 700 | One per page |
| Module label | `--text-xs` | 700 uppercase | Optional, 1 per page max |
| Table header | `--text-xs` | 600 uppercase | Muted color |
| Body / cell | `--text-sm` | 400–500 | Default grid text |
| KPI number | `--text-lg`+ | 700 | `tabular-nums` |
| Money | `--text-sm` | 600 | Always tabular-nums + currency suffix |

**Banned for CRM:** oversized marketing H1s, serif display fonts on data screens, gradient text headers.

---

## Color semantics

Map business meaning to tokens — never invent per-row colors.

| Semantic | Typical use |
|----------|-------------|
| `--success` | Active, received, paid, fulfilled |
| `--warning` | Pending, bron, low stock |
| `--danger` | Cancelled, overdue, error |
| `--neutral` | Draft, inactive, archived |
| `--info` | Confirmed, in progress |
| `--primary` | Primary actions, links, focus |

Status badge background: tint accent at 10–15% (`color-mix` or `--primary-light`).

---

## Component specs

### `.row-action` (grid actions)

```css
.row-actions {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  align-items: center;
  gap: 6px;
  justify-content: flex-end;
}
.row-action {
  box-sizing: border-box;
  min-height: 36px;
  height: 36px;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  border-radius: var(--radius-sm);
}
.row-action:has(svg):not(:has(*:not(svg))) {
  padding: 0;
  width: 36px;
  min-width: 36px;
}
```

### `.data-table`

- Sticky header optional for long lists
- Zebra optional — prefer hover row highlight only
- Checkbox column: fixed 40px
- Actions column: `white-space: nowrap`, `min-width: max-content`

### `ListFiltersPanel`

- Collapsed by default on mobile
- Show badge count of active filters
- “Tozalash” clears all; preserve sort/pagination

### `BulkActionsBar`

- Sticky below page header when selection &gt; 0
- Show “N ta tanlangan” + clear selection
- Primary bulk action + secondary export

### `SearchableCombobox`

- Input filters local list or debounced remote
- Highlight match substring optional
- `role="combobox"` + `aria-expanded` + listbox options

### `StatusChangeModal`

- Confirm status transition with reason/contract fields if API requires
- Show old → new status visually
- Disable submit while saving; show API error inline

### `EmptyState`

- Icon (48px), short label, one CTA button
- CTA triggers same flow as page “Yangi qo‘shish”

### `ConfirmDialog`

- Title: action verb + entity (“Buyurtmani bekor qilish?”)
- Body: irreversible consequence
- Buttons: Cancel (secondary) + Confirm (danger/primary)

---

## FX / contextual header widgets

| Mode | Where | Content |
|------|-------|---------|
| `header` | Topbar | Read-only value + optional refresh (`users_manage`) |
| `compact` | Form footer | Tabs (default active source) + conditional input |
| Full | Dashboard only if needed | Avoid duplicating compact in topbar |

Never stack duplicate controls (tabs + repeated rows + footer).

---

## Forms: field blocks

```jsx
<div className="field-block">
  <label htmlFor="client">Mijoz</label>
  <SearchableCombobox id="client" ... />
  <FieldError message={errors.client} />
</div>
```

```css
.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-block label {
  font-size: var(--text-sm);
  font-weight: 600;
}
```

Required indicator: asterisk or “(majburiy)” — pick one project-wide.

---

## Loading patterns

| Context | Pattern |
|---------|---------|
| Initial grid | 4–6 skeleton bars in table shape |
| Refetch | Opacity overlay on table, keep headers visible |
| Button submit | Disable + label “Saqlanmoqda…” or spinner icon |
| Combobox | “Yuklanmoqda…” in dropdown |

Avoid full-page spinner unless auth/bootstrap.

---

## Responsive breakpoints

| Breakpoint | CRM behavior |
|------------|----------------|
| &lt; 768px | Sidebar → drawer; table → card list OR horizontal scroll with sticky first col |
| 768–1024px | Collapsed sidebar rail optional |
| &gt; 1024px | Full sidebar; multi-column filters inline |

**Mobile tables:** If card conversion is too costly, allow horizontal scroll on `.data-table-wrap` with visible scroll hint — not ideal but acceptable for ERP.

---

## Dark mode (if supported)

- Define `--surface`, `--surface-elevated`, `--text`, `--muted` pairs
- Sidebar stays dark in both modes OR flips consistently — don’t mix random section inversions
- Table borders: visible in both themes (`border-color` token)
- Primary button: same hue family, adjusted luminance for dark bg

---

## Charts (reports module)

- Use accessible palette (max 6 series)
- Legend always visible
- Tooltip with exact values + tabular nums
- Empty chart → “Ma’lumot yo‘q” + filter hint
- Prefer bar/line over pie for operational metrics

---

## Integration with backend

Document in project API guide (e.g. `FRONTEND_API.md`):

1. Endpoint + method + ability required
2. Which UI component calls it
3. Fields hidden per ability
4. Error codes → user-facing messages

Frontend checklist per feature:

- [ ] Menu item gated
- [ ] Page CTA gated
- [ ] Field-level hide matches serializer
- [ ] 403 handled without breaking parallel loads

---

## Synthesis notes (ui-ux-pro-max + design-taste)

| Source | Adopt for CRM | Reject for CRM |
|--------|---------------|----------------|
| ui-ux-pro-max | Priority 1–3, touch targets, UX domain searches | Landing/chart-heavy defaults when irrelevant |
| design-taste v2 | Anti-slop discipline, token consistency, no emoji icons | Hero rules, bento marketing, marquee, scroll hijack |
| design-taste v1 | Touch feedback, grid over flex-math, state completeness | Purple AI aesthetic ban → use **brand** purple if project already defines it |

---

## Z-index scale (document once)

| Layer | z-index |
|-------|---------|
| Base content | 0 |
| Sticky table header | 10 |
| Sidebar | 20 |
| Topbar | 30 |
| Dropdown / combobox | 40 |
| Modal backdrop | 50 |
| Modal | 51 |
| Toast | 60 |

Do not spam `z-50` on random elements.
