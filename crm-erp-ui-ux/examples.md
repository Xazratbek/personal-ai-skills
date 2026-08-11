# CRM/ERP UI Examples

Production patterns from Smart-Warehouse and reusable snippets.

---

## Abilities gate helper

```javascript
function can(session, key) {
  return Boolean(session?.abilities?.[key])
}

// Nav item
{can(session, 'orders_view') && (
  <NavLink to="/buyurtmalar">Buyurtmalar</NavLink>
)}

// Import inline status — NOT procurement_manage
{title === 'Import' && can(session, 'order_status_manage') && (
  <InlineStatusSelect ... />
)}
```

---

## Independent editor data load

```javascript
useEffect(() => {
  api.products({ page_size: 500 })
    .then((data) => setProducts(list(data)))
    .catch((err) => notify(err.message))

  if (can(session, 'clients_view')) {
    api.clients({ page_size: 500 })
      .then((data) => setClients(list(data)))
      .catch((err) => notify(err.message))
  }
}, [notify, session])
```

---

## DataTable actions column

```jsx
// DataTable.jsx — wrap actions
<td className="data-table-actions-col" onClick={(e) => e.stopPropagation()}>
  <div className="row-actions">{renderActions(row)}</div>
</td>

// App.jsx — renderActions
<>
  <button type="button" className="row-action" aria-label="Tarix" onClick={...}>
    <ClockCounterClockwise size={18} />
  </button>
  <button type="button" className="row-action" aria-label="Tahrirlash" onClick={...}>
    <PencilSimple size={18} />
  </button>
  <button type="button" className="row-action" onClick={...}>Yetkazish</button>
  <button type="button" className="row-action" onClick={...}>Bekor</button>
</>
```

---

## FxRatePanel modes

```jsx
// Topbar — read-only
<FxRatePanel session={session} notify={notify} header />

// Import / expense editor — compact tabs + input
<FxRatePanel session={session} notify={notify} compact />
```

Compact behavior:
- Default tab: Infinbank (rate in tab label)
- Qo‘lda tab: single input, placeholder `Kurs kiriting`, save on blur/Enter
- No duplicate rows, no Saqlash button, no footer in compact mode

---

## List page composition

```jsx
function ResourcePage({ title, session, ... }) {
  return (
    <>
      <PageHeader title={title} cta={canManage ? { label: 'Yangi qo‘shish', onClick } : null} />
      <ListFiltersPanel filters={listFilters} onChange={setListFilters} />
      {selectedIds.length > 0 && (
        <BulkActionsBar count={selectedIds.length} onClear={() => setSelectedIds([])}>
          <button type="button" onClick={handleBulkExport}>Eksport</button>
          {can(session, 'order_status_manage') && (
            <button type="button" onClick={handleBulkStatus}>Status o‘zgartirish</button>
          )}
        </BulkActionsBar>
      )}
      <DataTable
        columns={gridColumns}
        rows={rows}
        loading={loading}
        renderActions={renderRowActions}
        selectable
        selectedIds={selectedIds}
        onSelectionChange={setSelectedIds}
        emptyCta={canManage ? { label: '...', ctaLabel: 'Birinchi yozuvni qo‘shish', onCta } : undefined}
      />
      <TablePagination page={page} total={total} onPageChange={setPage} />
    </>
  )
}
```

---

## Status badge mapping

```javascript
const ORDER_STATUS_BADGES = {
  new: { label: 'Yangi', tone: 'info' },
  confirmed: { label: 'Tasdiqlangan', tone: 'success' },
  received: { label: 'Qabul qilindi', tone: 'success' },
  cancelled: { label: 'Bekor', tone: 'neutral' },
  bron: { label: 'Bron', tone: 'warning' },
}

<StatusBadge status={row.status} label={meta.label} tone={meta.tone} />
```

---

## Field validation block

```jsx
const nextErrors = validateClient(form)
if (Object.keys(nextErrors).length) {
  setErrors(nextErrors)
  return
}

<div className="field-block">
  <label htmlFor="name">Nomi</label>
  <input id="name" value={form.name} onChange={...} aria-invalid={Boolean(errors.name)} />
  <FieldError message={errors.name} />
</div>
```

---

## Confirm destructive action

```jsx
<ConfirmDialog
  open={deleteConfirm}
  title="Yozuvni o‘chirish?"
  message="Bu amalni qaytarib bo‘lmaydi."
  confirmLabel="O‘chirish"
  tone="danger"
  loading={deleting}
  onConfirm={handleDelete}
  onCancel={() => setDeleteConfirm(false)}
/>
```

---

## CSS tokens (Smart-Warehouse baseline)

```css
:root {
  --primary: #5b4fcf;
  --primary-dark: #4a3fb8;
  --primary-light: #ede9fe;
  --sidebar: #1a1033;
  --sidebar-hover: #2d1f52;
  --touch-min: 44px;
  font-family: "Plus Jakarta Sans", system-ui, sans-serif;
}
```

Extend tokens — don’t replace wholesale when patching existing CRM.

---

## Motion snippets

```css
.button-primary {
  transition: transform var(--transition-fast), background var(--transition-fast);
}
.button-primary:active {
  transform: scale(0.98);
}

.modal-backdrop {
  animation: fadeIn 200ms ease;
}
.modal-panel {
  animation: scaleIn 220ms cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.98); }
  to { opacity: 1; transform: scale(1); }
}
```

---

## Global search hotkey

```javascript
useEffect(() => {
  const onKeyDown = (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault()
      setSearchOpen(true)
    }
  }
  window.addEventListener('keydown', onKeyDown)
  return () => window.removeEventListener('keydown', onKeyDown)
}, [])
```

Gate result sections by ability (`clients_view`, `orders_view`, etc.).
