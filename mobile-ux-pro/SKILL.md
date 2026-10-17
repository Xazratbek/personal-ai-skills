---
name: mobile-ux-pro
description: "Mobile app UX/UI quality for iPhone (SwiftUI/UIKit, Apple HIG, iOS 26-27 Liquid Glass) and Android (Jetpack Compose, Material 3 and M3 Expressive), plus Flutter and React Native. Covers the UX plan before code, every screen state (loading, empty, error, offline), navigation and back behavior, thumb reach, forms/OTP/keyboard, permissions and notifications, onboarding, cart/checkout/ordering, motion, haptics, accessibility, dark mode, localization, store-review rules and a severity-ranked review checklist. Use it whenever you build, design, review or fix any mobile screen, flow or component, even if the user only says 'make this screen', 'app UI', 'Compose screen', 'SwiftUI view', 'ilova dizayni', 'mobil ekran', or asks why an app feels clunky, slow or cheap. It decides what good mobile UX is; pair it with implementation skills such as material-3 or the SwiftUI skills for API depth."
---

# Mobile UX Pro

Goal: mobile apps people enjoy using. They feel native on iPhone and Android, respond fast, forgive mistakes, work for everyone, and treat users honestly. This skill is the UX layer. It decides what a screen or flow should do, then checks the result. For deep API detail, pair it with implementation skills (see "Companion skills").

Research baseline, verified 2026-10-17:
- iOS 27, Liquid Glass refined.
- Android 17 / API 37. Play requires target API 36.
- Compose BOM 2026.09 (material3 1.4 stable). Expressive components need material3 1.5 beta.

Platforms move fast. Check current docs (ctx7 or the web) before you pin a dependency version or rely on an API introduced in the last year.

## How to use this skill

1. **Name the job and the platform(s).**
   - Build: a new screen, flow or component.
   - Review: audit code, screenshots or a design.
   - Design: plan a flow before code.
   - Fix: a specific UX bug ("keyboard covers the button", "TalkBack reads nonsense", "feels slow").
2. **Find the version floor before writing code.** Look up the project's minimum OS and SDK versions, and check them against every API you plan to use (see "Version floor" below). Beautiful UI that doesn't compile for the project's users isn't done.
3. **Read only the references the task touches.** See the table below. The platform file is almost always needed. Each reference starts with a Contents list. For a narrow task, read the sections you need instead of whole files; reading everything costs time without improving the result.
4. **Make the 60-second UX plan** (next section) before you write UI code.
5. **Build with system components and platform conventions.** Use the defaults under "Writing UI code".
6. **Self-check** with `references/review-checklist.md`: a quick pass for builds, the full pass for reviews.
7. **Report honestly.** Say what you checked and what you could not check (for example, "not run on a device", "TalkBack not tested", "not compiled").

| If the task touches... | Read |
|---|---|
| iPhone, SwiftUI, UIKit | `references/ios.md` |
| Android, Compose, Views | `references/android.md` |
| Flutter, React Native/Expo, Compose Multiplatform | `references/cross-platform-frameworks.md`, plus the platform file for each look you ship |
| Navigation, onboarding, permissions, notifications, forms, loading/error/offline, gestures, motion, visual hierarchy, UX copy | `references/ux-patterns.md` |
| Accessibility (any UI work: at least skim the quick rules) | `references/accessibility.md` |
| Cart, checkout, payments, ordering, delivery or status tracking, bookings, subscriptions | `references/commerce.md` |
| More than one language, Uzbek/Russian or other locales, currency/date/phone formats, RTL | `references/localization.md` |
| Release, App Store/Play review, account deletion, vitals, rating prompts, usability testing | `references/store-and-quality.md` |
| Reviewing or auditing UI | `references/review-checklist.md` |

## The 60-second UX plan

Do this before writing UI code. For a tiny change, a mental pass is enough. For a new screen or flow, put a short version in your response: it shows the user the reasoning and catches gaps early.

- **User and goal.** Who arrives here, and what are they trying to finish? Name the one primary action.
- **Entry points.** How do people arrive? Through a tab, a push from a list, a notification deep link, a cold start, or while logged out? Each path must land on a sensible screen with a sensible back stack.
- **States.** Design every row of the state matrix below. Most apps that feel unpolished only polished the happy path.
- **Inputs.** What can you infer, default, remember or skip instead of asking?
- **Risk.** What is irreversible (payment, delete, send)? Give those a confirmation or an undo. Make everything else fast.
- **Constraints.** Check the smallest phone at the largest text size, one-handed use, a slow network, dark mode, a screen reader, and the second language or script.

### State matrix

Every data-backed screen handles each of these:

| State | What good looks like |
|---|---|
| First load | A skeleton shaped like the final layout for a full screen, or an inline spinner for one module. Never a blank screen. |
| Refresh | The system pull-to-refresh. Old content stays visible while it loads. |
| Empty | Say why it is empty and offer one next action ("No orders yet. Browse restaurants"). |
| Error | Say what happened and how to fix it, and offer Retry. Keep everything the user typed. Plain words, no codes, no blame. |
| Offline | Show cached content with its age ("Updated 5 min ago"). Queue safe writes. Disable network-only actions and say why. |
| Slow / partial | Show what you have and load the rest progressively. Never spin forever: time out and offer retry. |
| Permission denied | Explain at the feature itself, offer another path (type an address instead of GPS), and link to the exact settings screen. |
| Success | Give clear confirmation (visual, plus a haptic where it fits) and the next step. |
| Extreme content | Test long names, two-line titles, missing images, large numbers, text at 200% or more, and RTL. |

## Version floor: check it before using new APIs

The newest platform features (Liquid Glass, Material 3 Expressive, Live Updates) exist only on recent OS versions or library releases. Code that uses them without a check either fails to compile or crashes on the older phones many users still carry. So:

1. **Read the project's floor.**
   - iOS: `IPHONEOS_DEPLOYMENT_TARGET` in `*.xcodeproj/project.pbxproj`, or `platforms: [.iOS(.v17)]` in `Package.swift`.
   - Android: `minSdk`, `targetSdk` and `compileSdk` in `app/build.gradle(.kts)` or `gradle/libs.versions.toml`, plus the Compose BOM / material3 version.
   - Flutter: `ios/Podfile` platform and `android/app/build.gradle` `minSdk`. React Native/Expo: `app.json` / `Podfile` / `build.gradle`.
2. **If there is no project yet, or nothing is set,** ask, or pick a sensible floor and state it in your response. Defaults: iOS 17, Android minSdk 26 (check current adoption).
   - "Compatible with iOS 26", or "iOS 26 ga mos", means it should look and feel right on iOS 26. It does not mean "drop older versions". Make it look native on the newest OS and keep it working on the floor.
3. **Gate every API newer than the floor, and give it a fallback that still looks intentional.**
   - iOS: `if #available(iOS 26, *) { … } else { … }`, or `@available` on helper types, wrapped in a small view modifier so call sites stay clean.
   - Android: `if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.X)` with `@RequiresApi`. Prefer AndroidX compat APIs that backport for you.
   - Both platform files list the common gated APIs and fallback patterns (`ios.md` §1, `android.md` §1).
4. **Never silently raise the floor or the toolchain.** Raising the deployment target, `minSdk`, `compileSdk` or AGP, or pinning a beta library such as material3 1.5 for Expressive, is the user's decision. Propose it with the trade-off instead of doing it quietly.
5. **Say what you verified.** If you could not compile for the floor version, say so.

## Core principles, and why they matter

1. **Native beats novel.** People spend most of their time in other apps (Jakob's law), so platform conventions are usability you get for free. Use the system's navigation, back, sheets, tab bar, pickers, share sheet and search. Build custom only when it clearly earns its place.
2. **One primary action per screen.** Make it visually dominant and easy to reach: lower-middle of the screen, or a sticky bottom CTA kept above the gesture area and the keyboard.
3. **Fast is a feature.** Give feedback within 100 ms of a tap. Show content or a skeleton within about 1 s. Show progress for anything over 10 s. Use optimistic updates for low-risk, reversible actions, never for payments.
4. **Forgive instead of interrogating.** Offer Undo instead of "Are you sure?". Confirm only irreversible or high-impact actions, and name the action ("Delete address 'Home'?"). Never lose user input.
5. **Respect the user's settings.** Text size, dark mode, Reduce Motion / Remove animations, Reduce Transparency, contrast, haptics off, and language are normal configurations, not edge cases.
6. **Value before commitment.** Let people browse and try before signing up. Ask for a permission when its feature is used, with a reason. Ask for a rating after a success.
7. **Every gesture has a visible twin.** Swipe, long-press and drag are shortcuts. They must never be the only way to do something.
8. **Honest by design.** No hidden fees, fake urgency, confirmshaming, pre-checked add-ons or hard-to-delete accounts. Trust keeps users longer than tricks do.
9. **Accessible by default.** Labels, roles, 44 pt / 48 dp targets, contrast, focus order and scalable text are part of "done", not a later pass.
10. **Delight at the peaks, restraint everywhere else.** People judge an experience by its peak and its end. Invest in the moments that matter (order placed, goal reached, first success). Keep frequent paths quiet and quick.

## Platform quick map

| Concern | iPhone (HIG) | Android (Material 3) |
|---|---|---|
| Min touch target | 44x44 pt | 48x48 dp |
| Body text | 17 pt `.body`; Dynamic Type up to AX5 (~310%) | 16 sp `bodyLarge` / 14 sp `bodyMedium`; nonlinear scaling to 200% |
| Text sizing | Text styles; `@ScaledMetric` for sizes tied to text | `sp` for text only; `dp` for layout |
| Top-level nav | Floating glass tab bar, 5 or fewer tabs; sidebar-adaptable on iPad | Navigation bar with 3-5 items and labels; `NavigationSuiteScaffold` gives a rail or drawer on wide windows |
| Back | Edge-swipe pop and the nav-bar back button. Never break them. | System back gesture with predictive back. No custom on-screen back button. |
| Primary action | Toolbar `.prominent` item, bottom CTA, `.glassProminent` | One FAB per screen, or a bottom CTA / filled button |
| Transient choice | Sheet with detents (`.medium`, `.large`) and a grabber | `ModalBottomSheet` with a drag handle |
| Destructive confirm | `.confirmationDialog` anchored to its source (choices); `.alert` (critical) | `AlertDialog`; prefer a snackbar with Undo |
| Brief feedback | Inline state change, symbol effect, haptic | `Snackbar` with at most one action; avoid Toast |
| Color | Semantic system colors plus one tint. Brand color in content, not on bars. | `MaterialTheme.colorScheme` roles; dynamic color plus a brand fallback |
| Icons | SF Symbols, weight matched to text | Material Symbols as vector XML; avoid `material-icons-extended` |
| Motion | Springs (`.smooth`, `.snappy`); zoom transitions | `MotionScheme` springs; shared elements; predictive-back preview |
| Haptics | `.sensoryFeedback(.success, trigger:)` | `LocalHapticFeedback`: `Confirm`, `Reject`, `ToggleOn`... |
| Edges | Safe areas: backgrounds full-bleed, controls inside | Edge-to-edge enforced: `WindowInsets`, `Scaffold` `innerPadding` |
| Settings-style lists | `Form` / `List` with `.insetGrouped` | `ListItem` rows in a `LazyColumn` |

When you build for both platforms, keep the product identical: same flows, content, brand and copy. Let the chrome follow each platform: navigation, back, dialogs, type, icons, haptics. An iOS-looking app on Android, or the reverse, feels foreign to both audiences.

## Rules by priority

These are the condensed rules. The references hold the details and the evidence.

### P1 Critical: people get stuck or excluded
- Touch targets are at least 44 pt / 48 dp, with about 8 dp between neighbors. The visual can be smaller than the hit area.
- Every icon-only control has an accessible label. Decorative images are hidden from screen readers.
- Text scales with the system setting and nothing clips at the largest size. No fixed heights on text containers, no `lineLimit(1)` / `maxLines = 1` on essential text.
- Contrast is at least 4.5:1 for text and 3:1 for icons and control borders. Meaning never relies on color alone.
- Back always works and is predictable. Deep links open the right screen with a sane back stack, including from cold start and when logged out.
- No task is blocked by a sign-up wall, a permission wall, or an animation that must finish.
- The keyboard never covers the focused field or the primary button.
- Payments and other irreversible submits are idempotent: a double tap or retry never creates two orders.
- The code builds for the project's minimum OS. APIs newer than the floor are gated with `#available` / `SDK_INT` checks and have a fallback.

### P2 High: friction, confusion, lost trust
- Every state in the state matrix is designed.
- Forms use the right keyboard, autofill hints, OTP autofill, labels above fields, validation on blur, and specific inline errors, and they keep user input.
- Permissions are requested in context with a clear reason, and denial degrades gracefully.
- Undo beats confirmation. Confirmations name the action ("Delete", not "OK").
- Costs, fees and ETA are visible before commitment. No new fees at the last step.
- Offline: reads come from cache, safe writes are queued, network-only actions are disabled with a reason.
- Navigation is flat (common tasks take 3 taps or fewer), tab state is preserved, and re-tapping a tab scrolls to top or pops to root.

### P3 Polish: the difference between fine and loved
- Motion is purposeful: 150-300 ms for UI transitions, springs, interruptible, and it respects Reduce Motion.
- Haptics are rare and semantic (success, error, selection) and never the only feedback.
- Hierarchy comes from system type styles and a 4/8 spacing grid. One accent color for actions.
- Dark mode is checked separately for contrast. Images have placeholders, consistent aspect ratios and no broken states.
- Celebrations happen at real peaks only, and they are short and skippable.
- Copy is short, specific and human: verbs on buttons, sentence case, no jargon, no blame.

## Writing UI code: defaults that prevent most UX bugs

**SwiftUI** (details in `references/ios.md`)
- Start from `NavigationStack`, `TabView`, `.toolbar`, `.sheet`, `.searchable`, `List`/`Form`, `Menu`, `ShareLink`, `ContentUnavailableView`. They inherit Liquid Glass, Dynamic Type, dark mode and accessibility.
- Use semantic fonts (`.font(.body)`) and `@ScaledMetric`. No `.system(size:)` for content.
- Use semantic colors (`Color(.systemBackground)`, `.foregroundStyle(.secondary)`) and asset colors with light, dark and high-contrast variants.
- Use `Button` rather than `.onTapGesture`. Give small visuals `.frame(minWidth: 44, minHeight: 44)` plus `.contentShape(.rect)`.
- Put `.ignoresSafeArea()` on the background only. Use `.safeAreaInset(edge: .bottom)` for sticky CTAs.
- Don't add custom bar backgrounds, glass in the content layer, or glass on glass.
- Gate iOS 26+ glass APIs (`.glassEffect`, `.buttonStyle(.glassProminent)`, `safeAreaBar`, `Button(role: .close)`…) behind `#available` when the deployment target is lower. Fall back to `.borderedProminent` and materials.
- Use `.sensoryFeedback`, `withAnimation(.smooth)`, and branch on `accessibilityReduceMotion`.

**Jetpack Compose** (details in `references/android.md`)
- Call `enableEdgeToEdge()`. Use `Scaffold` and always apply `innerPadding`; for lists, pass it as `contentPadding`. Add `imePadding()` for forms.
- Read colors from `MaterialTheme.colorScheme` and type from `MaterialTheme.typography`. No hex in composables. Use dynamic color with a brand fallback, and support light and dark.
- Use `sp` for text only. Use `heightIn(min = …)`, never fixed heights for text.
- Use `Modifier.clickable(onClickLabel = …, role = Role.Button)`. Give icons a `contentDescription` (`null` if decorative). Use `semantics(mergeDescendants = true)` on rows.
- Give `LazyColumn` items a `key` and a `contentType`. Use `collectAsStateWithLifecycle()`.
- Use `BackHandler`/`PredictiveBackHandler` only with state-bound `enabled`. Never at the root.
- Use `LocalHapticFeedback` with `Confirm`/`Reject`. Use `SnackbarHostState` for undo.
- Check `minSdk` before using API-gated features (dynamic color 31, `POST_NOTIFICATIONS` 33, `UiModeManager.getContrast` 34, `ProgressStyle` 36). Expressive components need an explicitly pinned material3 1.5.x. Don't swap the BOM version silently.

**Flutter / React Native**: see `references/cross-platform-frameworks.md`. The same rules apply. The traps are text scaling, safe areas, accessibility props, and platform-adaptive chrome.

## Reviewing UI

When asked to review or audit (code, screenshot or design):
1. Read `references/review-checklist.md` and the relevant platform file.
2. Walk the main flow as the user would, then walk the state matrix, then the accessibility and settings matrix.
3. Report findings ranked by severity, using this format:

```
## UX review: <screen or flow>
**Verdict:** <one line>

### Critical (P1)
1. <problem>: <where: file:line or screen area>
   Why it matters: <user impact, with the rule>
   Fix: <concrete change, with code if useful>

### High (P2)
...
### Polish (P3)
...
### What's already good
- <keep these>

### Not verified
- <what you could not check, e.g. "not run with TalkBack">
```

Prefer a few high-impact findings with concrete fixes over a long list of nitpicks. If the user asks you to fix the issues, fix P1 first and say which ones remain.

## Companion skills

If these skills are installed, load them for implementation depth. This skill still sets the UX bar.
- Android: `material-3` (components, tokens, theming), `android-development` (architecture), `compose-*` skills (state, performance, animation, tests), `using-chrisbanes-skills` (routes Kotlin/Compose work), `gradle-run` (before running Gradle).
- iPhone: `axiom-swiftui` (build and fix SwiftUI), `swiftui-pro` (review SwiftUI code), `design` (Liquid Glass, haptics, animation, SF Symbols).
- Visual exploration: `ui-ux-pro-max` (palettes, font pairings, styles), `stitch-generate-design` / `enhance-prompt` (screen generation), `imagegen-frontend-mobile` (concepts).

## Anti-patterns that make an app feel cheap

- A sign-up wall before any value, or a tutorial carousel on first launch.
- A permission prompt on first launch with no context, or a "You must allow" wall.
- A blank screen or an endless spinner instead of a skeleton, cached content or an error with Retry.
- Placeholder text used as the label, an error shown only at the top of a form, or a cleared form after an error.
- Icon-only buttons without labels, tiny targets, or gray-on-gray text.
- A custom back button that breaks swipe-back or predictive back. A hamburger menu hiding the main sections.
- Hard-coded colors that break dark mode. Fixed font sizes that ignore the user's text size.
- Confirmation dialogs for everything, Toasts for important messages, alerts for plain information.
- Haptics on every tap, decorative animation on frequent paths, bounce with no Reduce Motion fallback.
- Fees revealed at the last step, a pre-selected high tip, fake scarcity.
- An iOS-styled UI shipped on Android or a Material UI shipped on iPhone. Mixed icon sets.
