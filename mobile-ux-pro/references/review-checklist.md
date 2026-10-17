# Mobile UX review checklist

Use this for self-checks after building UI (quick pass: the P1 items plus the parts that touch the change) and for full audits (every section). Each item says what to look for in code. Report findings with the template in SKILL.md, ranked P1, then P2, then P3.

Severity:
- **P1 Critical:** someone can't complete the task, is excluded, loses data or money, or the store will reject the app.
- **P2 High:** real friction, confusion, lost trust, or a platform-convention break users will notice.
- **P3 Polish:** consistency, delight, minor visual issues.

## 0. Build and compatibility
- [ ] **P1** The code builds for the project's minimum OS.
  - iOS deployment target: APIs newer than it are wrapped in `if #available(…)` with an intentional fallback.
  - Android `minSdk`: `SDK_INT` checks or `@RequiresApi`, and lint `NewApi` is clean.
- [ ] **P1** No silent raise of the deployment target, `minSdk`, `compileSdk`, AGP or the Compose BOM, and no beta library pinned without telling the user.
- [ ] **P2** All referenced resources exist (strings, drawables or Material Symbols files, colors). Imports resolve. The response lists any assets the user must add.

## A. Structure and navigation
- [ ] **P1** Back behaves predictably everywhere.
  - iOS: no `navigationBarBackButtonHidden(true)` without restoring swipe-back. No custom edge gestures.
  - Android: no root `BackHandler`, no `onBackPressed` override, predictive back not broken.
- [ ] **P1** Deep links and notification taps open the right screen with a sane back stack, including from cold start and logged out.
- [ ] **P2** Primary destinations are visible (tab or nav bar with 3–5 labeled items), not hidden in a hamburger menu.
- [ ] **P2** Tab state is preserved. Re-tapping a tab scrolls to top or pops to root.
- [ ] **P2** Modals are only for short, scoped tasks. They are never stacked, always dismissible, and confirm before discarding edits.
- [ ] **P2** Platform-correct chrome: iOS uses `NavigationStack`, `TabView`, sheets with detents and a grabber. Android uses `Scaffold`, a navigation bar or `NavigationSuiteScaffold`, `ModalBottomSheet`. No iOS styling on Android or the reverse.
- [ ] **P3** Large titles on iOS top-level screens, inline on details. The M3 top app bar scroll behavior is wired.

## B. Layout, insets and reach
- [ ] **P1** Nothing important sits under system UI.
  - iOS: safe areas respected; `ignoresSafeArea` on backgrounds only.
  - Android: `enableEdgeToEdge()` with `Scaffold` `innerPadding` applied (or `contentPadding` on lists), no double padding.
- [ ] **P1** The keyboard never covers the focused field or the primary button (`imePadding()` / `.safeAreaInset`, scroll to field).
- [ ] **P2** The primary action is within thumb reach (bottom CTA or prominent placement), above the gesture inset.
- [ ] **P2** Works on the smallest phone (360 dp / 375–390 pt) and the largest, and in landscape. On tablets and foldables, content width is capped or panes are used. No `isTablet`, no portrait lock.
- [ ] **P3** Spacing follows a 4/8 grid. Margins are consistent (system margins on iOS, 16 dp on Android compact).

## C. Touch and interaction
- [ ] **P1** Every tappable element is at least 44 pt / 48 dp (`.frame(minWidth:minHeight:)` with `.contentShape`, `minimumInteractiveComponentSize()`), with about 8 dp between targets.
- [ ] **P1** Every gesture (swipe, long-press, drag) has a visible alternative plus an accessibility custom action.
- [ ] **P2** Tappables use `Button` / `clickable(role=…)`, not bare tap gestures on images or text.
- [ ] **P2** Pressed, disabled, selected and loading states are visible. Submit buttons disable while in flight.
- [ ] **P2** Undo is offered for reversible destructive actions. Confirmations only for irreversible ones, with specific action labels.
- [ ] **P3** Pull-to-refresh uses the system component (`.refreshable`, `PullToRefreshBox`).

## D. States and feedback
- [ ] **P1** No blank screens and no infinite spinners. Loading has a skeleton or spinner and times out to an error state with Retry.
- [ ] **P1** Errors keep user input and say what happened and how to fix it. No raw codes, no "Something went wrong" dead end.
- [ ] **P1** Payments and irreversible submits are idempotent and protected against double taps.
- [ ] **P2** Empty states explain and offer one action.
- [ ] **P2** Offline: cached content shown with its age, safe writes queued, network-only actions disabled with an explanation.
- [ ] **P2** Success is confirmed clearly. The peak moments (order placed, delivered) feel good.
- [ ] **P3** Optimistic updates for low-risk actions, with rollback.

## E. Forms and input
- [ ] **P1** Visible labels, not placeholder-only. Errors are inline and specific, announced to screen readers, and focus moves to the first error.
- [ ] **P1** Paste and autofill are allowed. OTP autofill works (`.oneTimeCode`; SMS Retriever / User Consent).
- [ ] **P2** The correct keyboard per field. Autocorrect and capitalization are off for names, emails and codes. IME Next/Done.
- [ ] **P2** Validation on blur, not per keystroke (except live helpers).
- [ ] **P2** Phone input has a country-code default and accepts any pasted format. Fields are minimized and defaults are smart.
- [ ] **P3** Required and optional fields are marked. Helper text explains why sensitive data is needed.

## F. Typography, color, imagery
- [ ] **P1** Text scales: semantic text styles (`.font(.body)`, `MaterialTheme.typography`), sp on Android. No fixed heights or `lineLimit(1)` on essential text. Layout reflows at 200%+ (AX5 on iOS).
- [ ] **P1** Contrast is at least 4.5:1 for text and 3:1 for icons and borders, in light and dark. No color-only meaning.
- [ ] **P2** Colors come from semantic tokens (system colors / `colorScheme` roles). No hard-coded hex in views. Dark mode works.
- [ ] **P2** Icons are SF Symbols / Material Symbols with labels where meaning isn't universal. One icon set.
- [ ] **P3** One primary button per screen. Hierarchy comes from the type scale. At most 2 typefaces. No light weights at small sizes.
- [ ] **P3** Images have placeholders and consistent ratios, never broken states, and no text baked in.

## G. Accessibility
- [ ] **P1** Icon-only controls have labels (`accessibilityLabel` / `contentDescription`). Decorative images are hidden.
- [ ] **P1** Rows and cards read as one coherent announcement (`.accessibilityElement(children: .combine)` / `semantics(mergeDescendants = true)`).
- [ ] **P2** Headings are marked. Screen titles are unique. Focus order is logical. Dialogs trap focus and return it to the trigger.
- [ ] **P2** State changes are announced (added to cart, errors, results count).
- [ ] **P2** Reduce Motion / Remove animations is respected. Reduce Transparency gives custom glass or blur a solid fallback.
- [ ] **P3** Action labels are specific (`onClickLabel`, `accessibilityHint` only when needed).

## H. Motion and haptics
- [ ] **P2** Animations are purposeful, 150–300 ms, interruptible, and never block input.
- [ ] **P3** Springs or platform motion tokens are used (SwiftUI `.smooth`/`.snappy`, `MaterialTheme.motionScheme`).
- [ ] **P3** Haptics are semantic and sparse (success, error, selection, toggles), never on every tap, and never the only feedback.

## I. Permissions, notifications, privacy
- [ ] **P1** No non-essential permission at first launch. Requests come from user intent and give a reason.
- [ ] **P1** Denial degrades gracefully, with an alternative path and a settings deep link. No permission walls.
- [ ] **P2** Pickers instead of broad access (PhotosPicker / Photo Picker, LocationButton, Contact Picker).
- [ ] **P2** Notifications are split into transactional and promotional channels and deep-link to their content.
- [ ] **P1** In-app account deletion exists if accounts exist. Privacy-equivalent login if social login exists (iOS 4.8).

## J. Onboarding and conversion
- [ ] **P2** Value is shown before sign-up: guest browsing, sign-in at the point of need.
- [ ] **P2** No tutorial carousel. Contextual tips at most, skippable.
- [ ] **P2** Costs, fees and ETA are visible before commitment. No new fees at the last step (see `commerce.md`).
- [ ] **P1** No dark patterns: hidden fees, fake urgency, confirmshaming, pre-checked add-ons or tips, roach-motel cancellation.

## K. Localization
- [ ] **P2** All strings in resources. No concatenation. Platform plurals.
- [ ] **P2** Layouts survive 40% text expansion. Locale formatters for currency, dates and phone.
- [ ] **P3** start/end instead of left/right. Directional icons mirror in RTL.

## L. Performance perception
- [ ] **P2** Content or a skeleton within about 1 s. Lists are lazy with stable keys. Images are sized and cached.
- [ ] **P2** No heavy work on the main thread during scroll or startup. Release-build performance checked on a low-end device.
- [ ] **P3** Prefetch the next likely screen's data. Animations use transform and opacity.

## Report template
```
## UX review: <screen or flow> (<platform>)
**Verdict:** <one line: ship / ship after P1 fixes / needs rework>

### Critical (P1)
1. <problem>: <file:line or screen area>
   Why: <user impact + rule>
   Fix: <concrete change>

### High (P2)
...

### Polish (P3)
...

### What's already good
- ...

### Not verified
- <e.g. "not tested with TalkBack on device", "contrast estimated from code colors">
```
