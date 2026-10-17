# Cross-platform mobile UX patterns

Evidence-based rules that apply to iPhone and Android alike. Sources: NN/g, Baymard, Luke Wroblewski, Steven Hoober, WCAG 2.2, Laws of UX, and Apple/Google guidance (researched 2026-10-17). Numbers marked "(verify)" are weaker evidence.

## Contents
1. Ergonomics and reach
2. Information architecture and navigation
3. Onboarding and first run
4. Permissions and notifications
5. Forms and input
6. Feedback and system status
7. Offline and poor networks
8. Content and visual hierarchy
9. Motion, microinteractions and delight
10. Gestures
11. UX writing

---

## 1. Ergonomics and reach
- **How people hold phones** (Hoober, 1,333 observations): 49% one-handed, 36% cradled, 15% two-handed. About 75% of touches are by thumb, and grips change often. Design for all three grips.
- **The center is the sweet spot.** Hoober's later research found the screen center is touched most, fastest and most accurately.
  - Put key content and actions in the middle half to two-thirds.
  - Put secondary actions along the top and bottom edges.
  - The top corners are the hardest to reach.
- **Sticky bottom primary CTA** (Add to cart, Checkout, Place order): it stays within reach on large phones. Keep it above the gesture/home-indicator inset and above the keyboard.
- **Never make a top-corner button the only way out.** Support system back and offer an in-flow or bottom alternative.
- **Keep destructive actions away from the easiest spots,** or make them undoable.
- **Leave bottom padding after long content and forms** so the last field can scroll to mid-screen.
- **Finger occlusion:** a finger hides what it touches. Show feedback (labels, values) where the finger isn't, for example above a slider thumb.
- **Target sizes:**

| Source | Minimum |
|---|---|
| NN/g | 1 x 1 cm (about 48 dp) |
| Material / Android | 48 x 48 dp, about 8 dp spacing |
| Apple HIG | 44 x 44 pt |
| WCAG 2.2 SC 2.5.8 (AA) | 24 x 24 CSS px, with a spacing exception |

  - Go bigger for primary CTAs, for apps used on the move, and for older users.
- **Fitts's law:** big, close targets are faster to hit. Make the primary action the largest target. Put paired buttons side by side (wider) rather than stacked when space allows.

## 2. Information architecture and navigation
- **Visible navigation wins.** NN/g (179 participants): on mobile, hidden navigation such as a hamburger menu was used 57% of the time versus 86% for visible or combined navigation. Discoverability dropped by more than 20%, and tasks were slower.
  - Show the top 4–5 destinations visibly.
- **Tab bar / navigation bar:**
  - 3–5 destinations, each with an icon and a 1–2 word label.
  - For exactly 2 destinations, use a segmented control or tabs instead.
  - Tabs navigate; they don't trigger actions.
  - Never disable tabs; explain empty states instead.
- **Preserve state per tab** (scroll position and back stack). Re-tapping the active tab scrolls to top, then pops to the tab root.
- **Flat hierarchy:** common tasks in 3 taps or fewer. Fewer, clearer choices speed decisions (Hick's law).
- **Follow platform conventions** (Jakob's law). Don't reinvent back, tabs, sheets or pull-to-refresh.
- **Search-first for large catalogs:**
  - Keep a search entry persistent.
  - Show recent searches.
  - Make results typo-tolerant and cross-script (Latin and Cyrillic).
  - Offer suggestion chips (cuisine, category).
- **Deep links:**
  - Every screen that can be shared or notified about has a URL.
  - A push notification opens the exact screen (the order tracker), not the home screen.
  - Deep links work from cold start and when logged out (sign in, then continue to the target), with a sensible back stack.
- **Bottom sheets:**
  - For short, transient tasks only.
  - Give them a visible close button (X) as well as the drag handle, and support back.
  - Never stack sheets. Don't put full product pages or complex flows in them.
- **Large screens:** move from a bottom bar to a navigation rail or sidebar. People don't look at the bottom of tablets.
- **Second-level choices** (categories in a menu): use horizontally scrolling chips or tabs, sticky under the top bar, synced with scroll position. Don't use a hidden drawer.

## 3. Onboarding and first run
- **Skip tutorial carousels.** NN/g (70 users): success was the same with or without one (91% vs 94%), but perceived difficulty was higher with it. Teach in context instead, the first time a feature matters.
- **Show value immediately.**
  - The first screen shows real content (nearby restaurants, popular items), never an empty shell.
  - Show a skeleton or content within about 1 s.
- **Defer account creation.**
  - Let people browse and build a cart as guests. Ask for identity at the point of need (checkout, saving favorites), and explain why.
  - 18–19% of shoppers abandoned a purchase because account creation was required (Baymard).
  - Guest checkout should be the most prominent option.
- **Ask only questions you'll use right away** (language, delivery address, dietary preference if it shapes the feed). Make every one skippable and show progress when there are 3 or more steps. Move appearance preferences to Settings.
- **Prefer phone and OTP sign-in** in phone-first markets (many CIS and Asian markets). Prefer passkeys or Sign in with Apple/Google elsewhere. Avoid email-plus-password as the only option.
- **Location:** show "Use my location" and "Enter address" side by side. Never block browsing on a denied permission.
- **Empty states teach:** say what will appear here and give one action ("No favorites yet. Tap ♥ on any dish to save it").
- **Reveal features when they become useful** (stats after enough data, reorder after the first order).
- **The splash screen is not onboarding.** Keep it as short as the system allows.

## 4. Permissions and notifications
- **Timing:** ask when the user triggers the feature (taps "Use my location", places an order). Never ask at first launch for something non-essential. Don't interrupt an unrelated task.
- **Give a reason.** NN/g: any reason raised grants by 12%, and the best reason beat the worst by 81%.
  - Pattern: "[App] uses your [resource] so you can [benefit]."
  - Never "for a better experience".
- **Don't burn the one-shot prompt.**
  - Android stops showing the dialog after two denials. iOS shows the system alert once.
  - A priming screen can explain first. On iOS it may have only one button that proceeds to the system alert (HIG). On Android a "Not now" that does not trigger the system dialog is fine.
- **After a denial:**
  - Explain the impact where the feature lives.
  - Offer the alternative (manual address, manual photo upload).
  - Link to the exact settings screen.
  - Don't nag, and never style "Allow" as "Recommended" or hide "Decline".
- **Notifications:**
  - The best moment is right after a transactional action: "Get live updates when your courier is on the way?" right after an order is placed.
  - Benchmarks (Airship 2025): median opt-in 53% on Android (it fell after Android 13 made the permission runtime) and 49% on iOS.
  - Separate transactional notifications (order status, security) from promotional ones (offers) into channels/categories, so users can mute promos and keep order updates.
  - NN/g's five push mistakes: asking at first launch, not saying what notifications contain, sending bursts, irrelevant content, hard to turn off.
  - Write concise, specific, actionable copy that deep-links to the right screen. Offer in-app notification settings, respect quiet hours and local time zones, and combine bursts.

## 5. Forms and input
- **Remove, defer or infer every field you can** (Wroblewski). The average checkout has about 20 form elements; good ones get down to about 12 (Baymard).
- **Layout:** single column. Labels above the fields, always visible; placeholders are not labels, because they vanish when typing. Mark required and optional fields explicitly.
- **The right keyboard for every field:**
  - Phone: phone pad.
  - Numbers / ZIP / card: number pad.
  - Email: email keyboard, autocorrect and auto-capitalize off.
  - Names: autocorrect off.
  - URL: URL keyboard.
- **IME actions:** Next between fields, Done or Go on the last field. The primary button stays visible above the keyboard, and the keyboard doesn't open by itself on page load unless the screen exists only for typing (search, OTP).
- **Autofill everywhere:**
  - iOS: `textContentType` (`.name`, `.telephoneNumber`, `.fullStreetAddress`, `.emailAddress`, `.oneTimeCode`, `.newPassword`).
  - Android: `ContentType` semantics / `autofillHints`.
  - Never block paste. Support password managers (WCAG 3.3.8).
- **OTP:**
  - iOS: `.oneTimeCode` gives the keyboard suggestion.
  - Android: SMS Retriever (no SMS permission) or the SMS User Consent API.
  - Let users paste a whole code into split boxes and auto-submit when complete.
  - When a paste or autofill delivers a full-length code, replace the field contents instead of appending to the digits already typed. Otherwise a partial entry plus a paste auto-submits a wrong code.
  - Back one backing text field with visual boxes rather than six separate fields. Autofill, paste, VoiceOver and deletion all work better that way.
  - Show a resend timer ("Resend in 0:30") and a way to change the number.
- **Phone numbers:**
  - Pre-fill the country code (+998 for Uzbekistan) with a country selector.
  - Accept any pasted format (spaces, dashes, a leading 0 or +) and normalize to E.164.
  - Show a format hint or a non-blocking mask ("+998 90 123 45 67").
  - When auto-formatting as the user types, keep the cursor where the user is editing. Jumping it to the end on every keystroke makes mid-number corrections painful.
  - Say why you need the number. More than 70% of people are reluctant to give one without a reason.
- **Validation timing** (NN/g):
  - Validate when the user leaves a field, not on every keystroke. Exception: live strength or format hints, such as password rules ticking green.
  - Show errors next to the field in text plus an icon, not color alone.
  - On submit, scroll to the first error and focus it. A summary at the top supplements inline errors but doesn't replace them.
  - Messages respond to the actual input ("Phone number is missing 2 digits", not "Invalid input").
- **Smart defaults:** the last used address, the most common payment method, the nearest time slot. Never ask for the same information twice in a flow (WCAG 3.3.7).
- **Choice controls:** segmented controls or chips for 2–5 options, pickers for longer lists, steppers with large +/- for quantity, system date/time pickers.
- **Passwords:** a show/hide toggle, no complex composition rules (prefer length), passkeys where possible.
- **Never lose input:** keep values after errors, rotation, backgrounding and process death (saved state).

## 6. Feedback and system status
- **Response-time limits** (Nielsen):
  - 0.1 s feels instant.
  - 1 s keeps the flow of thought.
  - 10 s is the limit of attention; beyond it, show progress and a way to cancel.
  - Doherty threshold: respond within about 400 ms.
- **Choosing the loading indicator** (NN/g):
  - Under 1 s: no indicator. A spinner that flashes for 200 ms is worse than nothing.
  - A single module (card, image) for 1–10 s: an inline spinner or placeholder.
  - A full screen under 10 s: a skeleton that mirrors the real layout.
  - Over 10 s, or uploads: a determinate progress bar.
  - Skeletons help layout stability; they don't replace performance work.
- **Optimistic updates** for low-risk, reversible actions (favorite, quantity change, mark as read). Roll back with a clear message if the request fails. Never for payments or irreversible actions.
- **Submit buttons:** switch to a loading state immediately, prevent double taps, and use an idempotency key so retries never duplicate an order or payment.
- **Undo beats confirmation** (NN/g):
  - Archive or delete immediately, with a snackbar Undo.
  - Keep confirmation dialogs for irreversible, high-impact actions. Make them specific ("Cancel order #1042?") with action-labeled buttons ("Cancel order" / "Keep order").
  - Frequent dialogs train people to click through without reading.
- **Error messages:**
  - Say what happened and how to fix it, in plain words. No codes, no blame ("We couldn't reach the server. Check your connection and try again").
  - Keep the user's input and offer Retry or the next step.
  - Baymard: 98% of sites lack specific error messages. This is an easy win.
- **Never use an infinite spinner.** Time out (10–30 s depending on the action), then show the error state with Retry.
- **Status tracking** (orders, deliveries, applications; NN/g's 16 guidelines):
  - The latest status first, in plain language, with the expected time.
  - A dated history below.
  - The same information in the app, push and SMS.
  - A push for each major change, deep-linked to the tracker.
- **Haptics and sound support visual feedback; they never replace it.**

## 7. Offline and poor networks
- **Offline-first architecture:**
  - The local database is the source of truth, and the UI observes it.
  - The repository syncs with the network.
  - Choose a write strategy per action: online-only (payment), queued (favorites, cart), or lazy sync.
- **Show cached content instantly** with its age ("Updated 5 min ago"). Refresh in the background.
- **Offline means a persisted cache** (Room, DataStore, SwiftData, files) that survives process death and a cold start. An in-memory cache only covers a brief connection drop. Don't call it offline support.
- **Never lose the cart or a draft.** Persist it locally and sync when online.
- **Network-only actions** (payment, placing an order): disable them while offline with an explanation. Never fail silently.
- **Connectivity UI:**
  - A slim, non-blocking banner ("You're offline. Showing saved menus").
  - Per-action messages for queued work ("Will send when you're back online").
  - Recover automatically when the connection returns.
- **Retries:** exponential backoff with a cap. Retry only connectivity and server errors, not 4xx validation or auth errors. Use WorkManager / BGTaskScheduler for deferred sync.
- **Emerging markets:** design for 2–3 GB RAM Android phones, throttled 3G and expensive prepaid data.
  - Test there, not only on a flagship.
  - Offer a data-saver mode and avoid autoplay video.
- **Images:**
  - Serve WebP or AVIF sized to the device (CDN parameters).
  - Lazy-load and cache aggressively.
  - Show a dominant-color or blurhash placeholder.
  - Never leave a broken-image icon.
- **Payload:** paginate with cursors, compress, delta-sync, and avoid chatty APIs. Use push or SSE/WebSocket for live tracking instead of tight polling.
- "Slow" must never look like "broken". Show partial content and enhance progressively.

## 8. Content and visual hierarchy
- **People scan; they don't read.**
  - Short headings, chunked cards, one idea per block.
  - Keep key facts (name, price, ETA, rating, status) in a consistent position on every card.
- **One dominant element per screen.** One primary button; secondary actions are visually quieter (tonal, outlined, text).
- **Type:**
  - Body text 16 sp / 17 pt, line height 1.3–1.5x, lines of about 45–75 characters.
  - At most 2 typefaces and 3–4 sizes per screen, built from the platform type scale.
  - No light weights at small sizes.
- **Contrast:** 4.5:1 for text, 3:1 for large text, icons and control borders (WCAG 1.4.3 / 1.4.11). Check dark mode separately.
- **Spacing:** a 4/8 grid. Related items sit closer together than unrelated ones (Gestalt proximity). Be consistent across screens.
- **Icons need text labels.** NN/g: most icons have no universal meaning. Home, search (magnifier) and close (X) are the near-universal exceptions; heart and star are often misunderstood. If it takes more than 5 seconds to think of an icon for something, use a word.
- **Imagery:**
  - Real, well-lit, consistently cropped photos at consistent aspect ratios (food and products sell by photo).
  - A designed placeholder when an image is missing.
  - Never text baked into images (it can't be localized or read by screen readers).
- **Prices:**
  - Show the currency once and consistently, with local digit grouping.
  - Show discounts as the new price plus the old one struck through.
  - Include mandatory fees where possible.
- **Never truncate essential information** (price, allergens, status). Allow two-line titles.
- **Cards:** the whole card is one tap target with one accessible label. Inner buttons (Add) get their own targets, at least 48 dp apart from other actions.
- **Carousels hide content beyond the first items.** Never make a carousel the only path to important content; add "See all".
- **Color semantics:** one accent color for interactive elements. Red only for errors and destructive actions. Green only for success. Don't use brand red as the primary action color if it reads as an error; use a container color.
- **Dark mode:** avoid pure black (#000) backgrounds for large text areas and pure white text; use the platform's dark surfaces. Recheck image edges and shadows.

## 9. Motion, microinteractions and delight
- **Purpose:** each animation should do one of these jobs:
  - Show what changed (state).
  - Show where something came from or went (continuity, shared element).
  - Confirm an action.
  - Guide attention.
  - Decorative motion on frequent paths is a cost, not a feature.
- **Timing:**
  - UI transitions take 150–300 ms.
  - Entrances decelerate (ease-out) and exits accelerate, slightly shorter (e.g. 250 ms in, 200 ms out).
  - Anything over about 400 ms feels slow when repeated.
  - Prefer springs: they are interruptible and carry gesture velocity.
- **Performance:** animate transform and opacity, not layout, especially on low-end Android. Drop heavy effects (blur, large Lottie files) on weak devices.
- **Reduce Motion / Remove animations:**
  - Swap movement for fades or instant changes.
  - No parallax, zoom or autoplay.
  - Stop infinite loops (WCAG 2.3.3, 2.2.2).
- **Never block the task.** Success screens and celebrations are tappable through. Users can act before an animation ends.
- **Peak-end rule:** design the peak and the ending.
  - Peaks: order confirmed, payment succeeded, delivered, first goal reached. Give them a clear message, a friendly animation of 1 s or less, a success haptic and the next step.
  - Endings: rating and tip after delivery, a thank-you.
  - Soften negative peaks (waiting) with visible progress and honest ETAs.
- **Celebrate real accomplishments** (first order, loyalty milestone) once, briefly and skippably. Don't copy game streaks into apps without a genuine habit loop.
- **Personality without friction:** friendly microcopy, illustrated empty states, and a light touch on loading messages are good. Jokes, delays and extra steps that block the task are bad.
- **Haptics:** for confirmations, errors and selection changes only. Light, rare, consistent, and honoring system settings. Sound is off by default.

## 10. Gestures
- **Gestures are invisible.** They have low discoverability and memorability (NN/g), and even a one-time tutorial tip is soon forgotten. Every gesture needs a visible alternative:
  - Swipe-to-delete: a Delete button in the overflow or detail screen, plus Undo.
  - Drag to reorder: Move up / Move down actions (WCAG 2.5.7).
  - Multi-finger or path gestures: a single-tap alternative (WCAG 2.5.1).
  - Shake to undo: a button, and a way to disable shake (WCAG 2.5.4).
  - Long press: never the only path to a primary action. Treat it as an accelerator.
- **Standard gestures only, with standard meanings:** tap, scroll, pull-to-refresh, swipe-back, pinch to zoom on maps and images, swipe actions on list rows. No custom gestures for core tasks.
- **Trigger on release, not on touch-down,** so users can slide off to cancel (WCAG 2.5.2).
- **System edge conflicts:**
  - Android back swipes come from both side edges; iOS back comes from the leading edge.
  - Avoid horizontal swipes that start at the screen edge, and avoid touch targets inside system gesture insets.
  - Dragging a sheet down near the top can open the notification shade.
- **Screen readers:** swipe gestures are taken by TalkBack/VoiceOver, so expose them as custom accessibility actions.
- **Teach an unusual gesture once, at the moment it helps,** with a dismissible hint, and keep the visible alternative.

## 11. UX writing
- **Be brief and specific.** Lead with what matters. Cut filler ("please", "successfully", "in order to").
- **Buttons are verbs that name the result:** "Place order", "Save address", "Delete card", not "OK", "Submit" or "Yes".
- **Follow platform case conventions:** sentence case for body text and most Android UI; title case for iOS buttons and menu items.
- **Write errors as help.** Say what happened and what to do next ("Card declined. Try another card or pay with cash"). Never blame ("You entered an invalid…").
- **Empty states** say what will appear and how to get it.
- **Confirmations** name the object and the consequence ("Delete 'Home' address? This can't be undone").
- **Use numbers and times, not vague words:** "Arrives 18:40–18:55", not "Fast delivery"; "3 left today" only if true.
- **Plain language** at about a grade 6–8 reading level. No internal jargon or status codes ("PENDING_ACK" becomes "Waiting for the restaurant to confirm").
- **Consistent vocabulary:** pick one term per concept (cart or basket, order or purchase) and use it everywhere, including notifications and support.
- **Accessible labels describe the action plus the object:** "Add Plov to cart", not "Add" or "Button".
- **Localize everything** (see `localization.md`). Write strings that survive 30–40% expansion and grammatical cases; never concatenate sentence fragments.
