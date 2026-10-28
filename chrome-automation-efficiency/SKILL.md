---
name: chrome-automation-efficiency
description: Token-efficient, accurate interaction patterns for claude-in-chrome browser automation. Use whenever driving a web page with the claude-in-chrome tools (computer, find, read_page, get_page_text, browser_batch) — especially multi-step flows like forms, uploaders, or scheduling UIs — to avoid wasted screenshots and mis-clicks caused by viewport size drift.
---

# Chrome Automation Efficiency

## The problem

Across a single claude-in-chrome session, the browser's reported viewport/window
size can drift between calls in small, unpredictable ways (e.g. `1512x771`,
`1512x772`, `1483x812`) — even with no explicit resize. If you click by pixel
coordinate (`computer` tool's `left_click` with `coordinate:[x,y]`), a coordinate
that was correct in one screenshot can land on the wrong element in the next
call. The usual defensive habit — take a screenshot before almost every click to
re-derive coordinates, then another after to confirm it landed — burns a large
number of tokens per task and still isn't fully reliable.

## The fix: interact via the accessibility tree, not pixels

**Default to `find` → `ref` → click, not `screenshot` → `coordinate` → click.**

1. Before clicking a button, link, or field, call `find` with a short
   text/semantic query describing it (e.g. `"Schedule button"`,
   `"Add Video button"`, `"email input field"`). This returns a `ref` id drawn
   from the page's accessibility tree.
2. Click (or type into) the element using that `ref`, not a coordinate pair.
   Refs are tied to the element itself, not its on-screen position, so they
   stay correct even if the reported viewport size changes between your `find`
   call and your click.
3. Reserve `computer screenshot` for cases where you genuinely need *visual*
   information the accessibility tree can't give you — e.g. picking between
   several thumbnail images that look different but have no distinguishing
   text/label, or confirming a canvas/video actually rendered. Do not take a
   screenshot just to double-check that a text field now contains what you
   typed, or that a toggle is now on — use `read_page` or `get_page_text` for
   that instead; both are far cheaper than a screenshot and don't depend on
   layout.
4. Batch independent steps into one `browser_batch` call (e.g. click a field,
   type into it, click the next field, type into it) instead of one tool call
   per step, as long as none of the steps need a visual check in between. This
   cuts round-trips on top of the token savings from (1)-(3).

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
get_page_text  (only if you need to confirm wording/state)
```

## When a screenshot is still the right call

- Choosing among visually distinct options with no reliable accessible label
  (thumbnail grids, color swatches, map pins).
- Confirming that an image/video actually uploaded and renders correctly.
- Debugging when `find` can't locate an element and you need to see what's
  actually on screen.

Even then, take one screenshot, decide, and move on — don't re-screenshot after
every subsequent step once you've confirmed the page is in the expected state.

## Net effect

Significantly fewer tokens per browser-automation task, and higher click
accuracy, because ref-based interaction doesn't break when the window size
drifts — which pixel-coordinate clicking does.
