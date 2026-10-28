---
name: chrome-automation-efficiency
description: Token-efficient, accurate interaction patterns for claude-in-chrome browser automation; complements the general claude-in-chrome / chrome-browser skills. Use whenever driving a web page with the claude-in-chrome tools (computer, find, read_page, form_input, file_upload, browser_batch), especially repetitive multi-step flows like forms, file/video uploaders (Meta Business Suite, YouTube Studio), or scheduling UIs. Also use when clicks land on the wrong element, coordinates seem off, a file picker opened, `find` can't locate something, or a task is burning many screenshots. Covers ref-based clicking, file_upload, batching rules, verification without screenshots, and fallbacks.
---

# Chrome Automation Efficiency

## The problem

Across a single claude-in-chrome session, the browser's reported viewport/window
size can drift between calls in small, unpredictable ways (e.g. `1512x771`,
`1512x772`, `1483x812`) — even with no explicit resize. If you click by pixel
coordinate (`computer` tool's `left_click` with `coordinate:[x,y]`), a coordinate
that was correct in one screenshot can land on the wrong element in the next
call. Scrolling, a banner or toast appearing, or a list re-rendering moves
elements too, even when the size stays the same. Rule: a coordinate is valid
only against the most recent screenshot, and only if nothing has scrolled or
changed since. The usual defensive habit — take a screenshot before almost every click to
re-derive coordinates, then another after to confirm it landed — burns a large
number of tokens per task and still isn't fully reliable.

## The fix: interact via the accessibility tree, not pixels

**Default to `find` → `ref` → click, not `screenshot` → `coordinate` → click.**

1. Before clicking a button, link, or field, call `find` with a short
   text/semantic query describing it (e.g. `"Schedule button"`,
   `"Add Video button"`, `"email input field"`). This returns a `ref` id drawn
   from the page's accessibility tree.
2. Click the element using that `ref` (`computer left_click ref:"ref_123"`),
   not a coordinate pair. Refs are tied to the element itself, not its
   on-screen position, so they stay correct even if the reported viewport size
   changes between your `find` call and your click. `hover` also accepts a ref.
   - To enter text, either use `form_input ref:<ref> value:<text>`, or click
     the ref and then `computer type`. The `type` action has no `ref`
     parameter; it types into whatever element has focus.
   - If a `form_input` value doesn't seem to stick on a framework-controlled
     input (the field looks empty again, or Save stays disabled), fall back to
     click-ref + `type`.
3. Reserve `computer screenshot` for cases where you genuinely need *visual*
   information the accessibility tree can't give you — e.g. picking between
   several thumbnail images that look different but have no distinguishing
   text/label, or confirming a canvas/video actually rendered. Do not take a
   screenshot just to double-check that a text field now contains what you
   typed, or that a toggle is now on. Use `find` for the expected next-state
   element (e.g. `"Scheduled confirmation"`, `"Upload complete"`), or
   `read_page ref_id:<panel>`, which shows the field values and checked or
   expanded state the page exposes. Both are far cheaper than a screenshot
   and don't depend on layout. `get_page_text` favors main article content and
   can miss toasts, modals and dialog state, so use it only to check that a
   page loaded or to read body text.
4. Batch with `browser_batch` using a two-phase rule:
   - **Batch A, locate:** all the `find` calls you need for the current
     screen, in one batch.
   - **Batch B, act:** every click, `form_input`, `type` and `key` that uses
     refs you already have, in one batch.
   - Rule of thumb: an item may go in the batch only if every input it needs
     (ref, coordinate, text) is known *before* the batch is sent.
   - Never put a `find` and a click on its returned ref in the same batch, and
     never put a screenshot and a coordinate click derived from it in the same
     batch (coordinates in a batch refer to the screenshot taken *before* the
     call).
   - A batch stops on the first error, so put the irreversible step (Submit,
     Schedule, Publish) last. Then nothing irreversible fires if an earlier
     field failed.
   - End Batch B with a `find` for the expected next-state element, so the
     batch result already tells you whether it worked.

### Anti-pattern (avoid)

```
screenshot                                  # just to find the button
left_click coordinate:[1352, 598]           # guess from the screenshot
screenshot                                  # verify it worked
```

### Preferred pattern

```
find query:"Schedule button"                # -> ref_123
left_click ref:"ref_123"                    # position-independent
find query:"Scheduled confirmation"         # verify next state, no screenshot
```

## When a screenshot is still the right call

- Choosing among visually distinct options with no reliable accessible label
  (thumbnail grids, cover-frame pickers, color swatches, map pins).
- Confirming that an image/video preview actually renders correctly (content,
  crop, orientation). Text can't tell you this.
- Canvas-drawn content (charts, editors, maps) that isn't in the tree.
- `left_click_drag` (sliders, crop handles, reordering). It accepts only
  coordinates, so take a fresh screenshot immediately before it.
- Step 6 of the `find` fallback list below.

Not screenshot cases:
- **Upload or processing progress:** first try `find query:"progress bar"` or
  `read_page` (a progressbar often exposes its value), or `find` the
  "Uploaded"/"Processing complete" text. Poll with `computer wait` plus `find`
  in one batch.
- **CAPTCHA or bot checks:** do not try to solve them. Stop and ask the user
  to complete it.

When you do screenshot, use the cheap forms: `scale:0.5` (about a quarter of
the tokens; coordinates stay in the full-resolution frame), or `zoom` with a
`region` to read a small element. Take one screenshot, decide, and move on.
Don't re-screenshot after every later step once you've confirmed the page is
in the expected state.

## File uploads: never click the upload button

Clicking a file input or "Upload"/"Add Video" button opens a native OS file
picker that you cannot see or control. Instead: `find query:"file input"` (or
`read_page filter:"interactive"`) to get the ref of the `<input type=file>`,
then call `file_upload paths:[...] ref:<ref>`. The input is often hidden behind
a styled button, so it may show up in `find`/`read_page` but not visually.
Files must be ones shared with the session, under 10 MB combined per call.

## When refs go wrong

Refs are more robust than coordinates, but they fail in their own ways:
- **Ambiguous matches.** `find` returns up to 20 matches. "Schedule button"
  can match a nav tab, a dialog button and a hidden duplicate. Pick by role and
  context, or scope the search: get the dialog's ref, then
  `read_page ref_id:<dialog_ref> filter:"interactive"`.
- **Hidden duplicates.** `read_page` includes non-visible elements by default,
  so an off-screen copy (mobile menu, a closed drawer) can come back first.
  Prefer the match inside the currently open dialog or panel.
- **Stale refs (likely, not confirmed).** Treat refs as invalid after any
  navigation, modal open/close, tab switch, or list re-render (for example
  after each upload finishes in a multi-item flow). Re-`find` instead of
  reusing a ref from several steps ago.
- **Not in the tree.** Canvas-drawn UI, some custom widgets with no role, and
  content in cross-origin iframes may not appear in `find`/`read_page` at all.

## When `find` can't locate the element

Work down this list; stop at the first step that works:
1. Rephrase the query using the exact visible label text, or describe its role
   ("button inside the Schedule dialog").
2. `read_page filter:"interactive"`, scoped with `ref_id` to the containing
   panel if the full tree is too large.
3. `get_page_text` to check the page or step actually loaded. If not,
   `computer wait` 2-3 s and retry. Uploads and SPA transitions lag.
4. If it's in a long or virtualized list: `computer scroll`, or `scroll_to` a
   nearby ref, then `find` again.
5. Keyboard: `key "Tab"` / `key "Enter"` / `key "Escape"` when focus order is
   predictable.
6. Last resort: one `screenshot` with `scale:0.5`, then a coordinate click in
   the *next* call with no scroll or other action in between.

## Net effect

Significantly fewer tokens per browser-automation task, and higher click
accuracy, because ref-based interaction doesn't break when the window size
drifts — which pixel-coordinate clicking does.
