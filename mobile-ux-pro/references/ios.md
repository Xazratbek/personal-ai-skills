# iPhone: Apple HIG, Liquid Glass, SwiftUI

Verified 2026-10-17 against Apple HIG pages, Apple docs and WWDC25/26 sessions. Items marked "(verify)" came from secondary sources or could change. Check them in current docs before relying on them.

## Contents
1. Platform status
2. Liquid Glass
3. Layout
4. Navigation and modality
5. Search
6. Controls, menus, alerts
7. Typography
8. Color and dark mode
9. SF Symbols
10. Motion and haptics
11. iOS accessibility APIs
12. System integration
13. Permissions and privacy
14. SwiftUI defaults and test matrix

---

## 1. Platform status
- **iOS 26** (Sept 2025) introduced Liquid Glass.
- **iOS 27** (WWDC26, June 2026; released Sept 2026) refines it rather than replacing it:
  - Glass now diffuses busy content behind it.
  - A new user-facing slider runs from ultra clear to fully tinted.
  - Apps rebuilt with Xcode 27 get the updated look without code changes.
- The opt-out key `UIDesignRequiresCompatibility` is ignored when you link against the iOS 27 SDK. Plan for no opt-out.
- **App Store submissions** need Xcode 26 / the iOS 26 SDK or later (since Apr 28, 2026).
- **UIKit apps** must adopt the UIScene lifecycle before building with the iOS 27 SDK, or they fail to launch. SwiftUI-lifecycle apps are unaffected.
- **Launch screen**: provide a static launch screen that looks like the first screen. No text, no splash branding unless it is part of that first screen.

### Deployment target and API gating
- **Find the floor:** `IPHONEOS_DEPLOYMENT_TARGET` in `project.pbxproj`, or `platforms:` in `Package.swift`.
  - If neither exists, use iOS 17 unless the user says otherwise, and state it.
  - "Make it iOS 26-compatible" means it should look native on iOS 26 and still run on the floor.
- **When APIs arrived** (check exact availability in Apple docs when unsure):

| Floor needed | APIs |
|---|---|
| iOS 27 | `TabRole.prominent`, `ToolbarOverflowMenu`, `swipeActionsContainer()`, `.topBarPinnedTrailing`, navigation-bar minimize behavior |
| iOS 26 | `glassEffect`, `GlassEffectContainer`, `.buttonStyle(.glass/.glassProminent)`, `tabBarMinimizeBehavior`, `tabViewBottomAccessory`, `scrollEdgeEffectStyle`, `backgroundExtensionEffect`, `safeAreaBar`, `ToolbarSpacer`, `Button(role: .close/.confirm)`, `searchToolbarBehavior`, SF Symbols Draw effects |
| iOS 18 | `Tab` / `Tab(role: .search)` in `TabView`, `.navigationTransition(.zoom)` + `matchedTransitionSource`, `TextField(text:selection:)`, `.presentationSizing`, wiggle/breathe/rotate symbol effects, `@Entry` |
| iOS 17 | `@Observable`, `.sensoryFeedback`, `ContentUnavailableView`, `.symbolEffect` (bounce/pulse/scale), `.smooth/.snappy/.bouncy` springs, `.spring(duration:bounce:)`, `scrollTargetBehavior`, `containerRelativeFrame` |

- **Gating pattern:** keep call sites clean with small wrappers, and make sure the fallback looks intentional, not broken.

```swift
extension View {
    /// Liquid Glass on iOS 26+, standard prominent style before.
    @ViewBuilder func primaryActionStyle() -> some View {
        if #available(iOS 26, *) {
            self.buttonStyle(.glassProminent)
        } else {
            self.buttonStyle(.borderedProminent)
        }
    }

    /// Glass for a floating control on iOS 26+, material capsule before.
    @ViewBuilder func floatingControlBackground() -> some View {
        if #available(iOS 26, *) {
            self.glassEffect(.regular.interactive(), in: .capsule)
        } else {
            self.background(.regularMaterial, in: .capsule)
        }
    }
}
```

- Put `@available(iOS 26, *)` on helper types that only exist for the new look. Use `if #unavailable(iOS 26)` for old-only workarounds.
- For screens that differ a lot (a custom tab bar before iOS 26 versus the system floating bar after), branch at the container level rather than per modifier.
- If you can, typecheck against the floor: `xcodebuild -destination 'generic/platform=iOS'` with the project's deployment target, or `swiftc -typecheck -target arm64-apple-ios17.0`. Otherwise, say it wasn't checked.

## 2. Liquid Glass

### Where glass belongs
- Glass is a functional layer for navigation and controls: tab bars, toolbars, sidebars, sheets, popovers, menus and alerts. It floats above the content layer.
- Never use glass in the content layer. No glass cards in a list. Content uses standard materials (`.ultraThinMaterial` … `.thickMaterial`) or plain backgrounds.
- Standard SwiftUI and UIKit components adopt glass automatically. The best adoption path is to use system components, rebuild with the latest SDK, and not hard-code control metrics.
- Put custom glass only on the few most important floating controls. Overuse distracts from content.

### Variants
- **Regular** (default): blurs and adjusts luminosity for legibility. Use it where there is text or busy content behind.
- **Clear**: highly translucent. Use it only over rich media (photo, video). Over bright content, add a dark dimming layer of about 35% opacity.
- Both variants adapt to Reduce Transparency, Increase Contrast and, on iOS 27, the user's glass slider.

### SwiftUI API (iOS 26+)
- `.glassEffect(_ glass: Glass = .regular, in: some Shape = .capsule)`.
  - Glass styles: `.regular`, `.clear`, `.identity`, `.tint(_:)`, `.interactive()`.
  - Example: `.glassEffect(.regular.tint(.orange).interactive(), in: .rect(cornerRadius: 16))`.
  - Apply it after layout and appearance modifiers (frame, padding).
- `GlassEffectContainer(spacing:)` wraps nearby glass views. Glass cannot sample other glass, so a container gives them one shared sampling region and renders faster. Never put neighboring glass elements in separate containers.
- Morphing: `glassEffectID(_:in:)` with a `@Namespace`. Merging: `glassEffectUnion(id:namespace:)`. Transitions: `glassEffectTransition(.matchedGeometry)`, the default when nearby, or `.materialize`.
- Buttons: `.buttonStyle(.glass)` and `.buttonStyle(.glassProminent)`. Prefer these over hand-built glass buttons.
- UIKit: `UIGlassEffect` in a `UIVisualEffectView`; `UIBackgroundExtensionView`.

### Tab bar
- The tab bar floats over content on glass.
- Minimize on scroll: `.tabBarMinimizeBehavior(.onScrollDown)`.
- Accessory above the bar, such as a mini player or an active-order pill: `.tabViewBottomAccessory { }`. Read `\.tabViewBottomAccessoryPlacement` to adapt when it collapses inline.
- Search tab: `Tab(role: .search)` with `.searchable` on the `TabView`. It sits at the trailing end.
- iOS 27 adds `TabRole.prominent` to visually separate one key tab, such as Cart or Create.
- Tabs navigate; they never perform actions (use a toolbar for actions).
  - Never hide or disable tabs. Explain empty sections instead.
  - Labels are one word where possible. Tab bars use filled SF Symbols automatically.
  - Use badges only for critical, current information.
  - Keep about 5 tabs or fewer on iPhone and avoid a "More" tab.

### Toolbars
- Toolbars are glass and group their items.
  - `ToolbarSpacer(.fixed)` splits groups; `ToolbarSpacer(.flexible)` pushes them apart.
  - Aim for 3 groups or fewer.
- Use `.prominent` for the one key action (Done, Submit), on the trailing side.
- Remove custom toolbar backgrounds and tinted bars. They fight the system effect. Brand color belongs in the content.
- Use icons for familiar actions. Don't mix text and icons in one shared group.
- Hide the whole `ToolbarItem`, not the view inside it. Otherwise an empty glass blob is left behind.
- Titles stay under about 15 characters and never repeat the app name.
- Use the standard Back and Close symbols, not the words "Back" or "Close".
- iOS 27 adds `ToolbarOverflowMenu` and `.topBarPinnedTrailing` placement (verify signatures in your SDK).

### Scroll edge effects
- `.scrollEdgeEffectStyle(.automatic | .soft | .hard, for: .top)` sits under floating bars instead of a solid or semi-opaque fill.
  - Prefer `.automatic`.
  - Use `.hard` for dense UIs.
  - `.soft` needs legibility testing.
- Use one edge effect per view.
- Extend full-bleed backgrounds under bars. `backgroundExtensionEffect()` mirrors and blurs a hero image under a sidebar.

### Sheets, menus and controls on glass
- Partial-height sheets are inset glass. At full height they become opaque.
  - Remove custom `presentationBackground` materials.
  - Check content near the larger corner radius.
- `confirmationDialog` and action sheets morph out of their source control, so anchor them on the triggering button.
- Menus have per-item icons. Use icons for every item in a group, or none.
- Controls are rounder and taller, and bordered buttons are capsules. Use `.rect(corner: .containerConcentric)` so nested corners match.
- List and Form rows are taller. Section headers are title case, not all caps.

### Don'ts
- Glass on glass, glass in content, a custom background behind bars, `.blur`/`.opacity` on glass views, heavy tint.
- Clear glass over bright content without dimming.
- Hard-coded control sizes. `rotationEffect` on glass (it distorts mid-animation).
- Shipping without testing every screen with Reduce Transparency, Increase Contrast, dark mode and both extremes of the iOS 27 glass slider, on a real device.

## 3. Layout
- **Respect safe areas.** They protect content from the Dynamic Island, status bar, Home indicator, tab bar and toolbars.
  - Put `.ignoresSafeArea()` on backgrounds only. Controls and text stay inside.
  - Use `.safeAreaInset(edge: .bottom) { CTA }` for sticky actions so lists scroll above them.
- Never place tappable content in the Dynamic Island zone. Never hard-code device sizes or insets.
- **Device widths (portrait, pt):**
  - 390–402: iPhone 16e, 15/16, 17/17 Pro.
  - 420: iPhone Air.
  - 430–440: Plus / Pro Max.
  - Test the smallest and the largest.
- **Margins:** prefer system margins (`.padding()`, `.scenePadding()`, `.contentMargins`, `readableContentGuide`) over hard-coded 16/20 pt. Limit line length on wide layouts.
- **Size classes, not devices.** Decide layout by compact/regular size class, never by device idiom or orientation.
  - Keep functionality constant across sizes; only the amount shown changes.
  - On large widths use `.tabViewStyle(.sidebarAdaptable)` or `NavigationSplitView`.
  - iPadOS 26+ windows resize freely.
- **Landscape iPhone** has compact height. Don't waste it on big headers.
- **Adaptive building blocks:** `ViewThatFits`, `containerRelativeFrame`, `Layout`, `Grid`.
- **Hierarchy:** important content goes top and leading. Group with space or containers. Use progressive disclosure.
- Keep key controls away from the very bottom edge, where Home-indicator swipes conflict.

## 4. Navigation and modality
- **Structure:**
  - Flat peer sections: `TabView`.
  - Hierarchy: `NavigationStack` (push).
  - Many sections or iPad: sidebar or the adaptable tab bar.
- **Push for drill-down.** Keep the tab bar visible on push.
- **Modal only for a scoped, short, self-contained task** (compose, add item, filter, sign in).
  - Always give an obvious dismiss.
  - Confirm before data loss. Title the task.
  - Never stack modals. Use `.sheet(item:)` so only one is shown at a time.
- **Sheet buttons:**
  - Cancel goes leading and Done trailing.
  - Never show Cancel, Done and Back together. Done always pairs with Cancel or Back.
- **Detents:** `.presentationDetents([.medium, .large])` for progressive disclosure. Compose-like sheets are full height only.
  - Show the grabber with `.presentationDragIndicator(.visible)`.
  - Support swipe-down dismiss. With unsaved changes, use `.interactiveDismissDisabled(hasChanges)` plus a confirmation dialog (Save / Discard / Cancel).
- **Full-screen cover** is for media viewers, the camera and long multi-step editing, not simple forms.
- **Swipe-back must keep working.**
  - `.navigationBarBackButtonHidden(true)` or a custom back button breaks the interactive pop gesture.
  - Keep the system back button, set clear titles (iOS 26 back buttons are unlabeled, so the title tells users where they are), and never add edge-swipe gestures that compete with it.
- **Titles:** large titles on top-level screens (`.navigationBarTitleDisplayMode(.large)`), inline on pushed details.
- **State:**
  - Use `NavigationStack(path:)` with `.navigationDestination(for:)` and typed, value-based routes. One source of truth for the path.
  - Restore the tab, path and scroll position on relaunch.
- **Zoom transition** (iOS 18+): `.matchedTransitionSource(id:in:)` on the source plus `.navigationTransition(.zoom(sourceID:in:))` on the destination. Works for push and sheets, with interactive dismiss.

## 5. Search
- **Placement on iPhone:**
  - Bottom toolbar search when there is room (Mail, Settings pattern). With more than 2 other items it starts as a button.
  - Top when the bottom is occupied.
  - A search tab for exploratory, content-rich apps.
  - Inline under the title to scope one list.
- Attach `.searchable` at the container level. Use `.searchToolbarBehavior(.minimize)` to collapse it into a button.
- The placeholder says what is searchable ("Dishes, restaurants").
- Search as the user types. Show suggestions (`.searchSuggestions`) that visually separate typed text from suggested text.
- Show recent searches on focus, with delete and clear-all.
- Default to a broad scope and narrow with `.searchScopes` or visible filter chips. Tokens alone are hard to discover.
- No results: `ContentUnavailableView.search(text:)`, never a blank screen.

## 6. Controls, menus, alerts
- **Hit targets:** at least 44x44 pt (the absolute floor is 28 pt; don't design to it). Use about 12 pt of padding around bezeled controls and about 24 pt around unbezeled ones.
  - Small visuals: `.frame(minWidth: 44, minHeight: 44).contentShape(.rect)`.
  - This also fixes glass buttons that only respond on the symbol.
- **Buttons:**
  - One or two prominent buttons per view. Show the preferred choice by style, not size.
  - Labels are verbs ("Add to Cart").
  - Show progress inside slow buttons ("Placing order…") and disable repeat taps.
  - Never give a destructive action the primary role.
  - Every custom button needs a visible pressed state.
- **Standard controls:**
  - `Toggle` for on/off.
  - Segmented `Picker` for about 5 or fewer same-kind options.
  - `Picker` / `Menu` for longer lists.
  - `Stepper` or large +/- buttons for quantity.
  - `SecureField` for passwords. Format numbers with a formatter.
- **Menus:** about 3 groups or fewer, verb labels in title case, one submenu level, destructive items last.
- **Context menus (long press):**
  - Keep them few and relevant.
  - Every action must also exist elsewhere in the UI.
  - Hide (don't dim) unavailable items. Use `role: .destructive` last.
  - Match the top actions to the item's swipe actions.
- **Swipe actions:**
  - Trailing edge for the primary or destructive action, leading for secondary.
  - Use filled symbols. Allow full swipe only for undoable actions.
  - Always offer an alternative (context menu, detail screen).
  - iOS 27 adds `swipeActionsContainer()` for swipe actions outside `List`.
- **Pull to refresh:** `.refreshable { await load() }`. Never a custom spinner.
- **Alerts:** only for critical, ideally actionable information. Never on launch, never for undoable actions, never for plain information.
  - The title is specific ("Couldn't place your order", not "Error"), two lines at most.
  - Up to three buttons, with verb labels ("Delete", not "OK"). Always include "Cancel" when there is a choice.
  - Use the `.destructive` role on the dangerous one.
- **Confirmation dialogs:** for choices tied to an intentional action ("Discard changes?" when closing an edited sheet). Anchor them to the source control. Destructive option on top; Cancel is added automatically.
- **Lists:** rows give selection feedback. Keep row text succinct. Use a disclosure chevron for drill-in. The info button is for extra info, not navigation.
- **Loading:** show something immediately (`.redacted(reason: .placeholder)` skeleton, `ProgressView`), let people keep doing other things, never block on a spinner.

## 7. Typography
- **Fonts:** the system font is SF Pro, with SF Rounded, New York (serif) and SF Mono as variants. Use `.system` and `Font.Design`; never embed system fonts.
- **Sizes and weights:** default 17 pt, minimum 11 pt. Avoid Ultralight, Thin and Light weights at small sizes.
- **Text styles at the default size** (size/leading in pt):

| Style | Size/leading | Default weight |
|---|---|---|
| Large Title | 34/41 | Regular (emphasized: Bold) |
| Title 1 | 28/34 | Regular |
| Title 2 | 22/28 | Regular |
| Title 3 | 20/25 | Regular |
| Headline | 17/22 | Semibold |
| Body | 17/22 | Regular |
| Callout | 16/21 | Regular |
| Subheadline | 15/20 | Regular |
| Footnote | 13/18 | Regular |
| Caption 1 | 12/16 | Regular |
| Caption 2 | 11/13 | Regular |

- **Dynamic Type** runs xSmall … xxxLarge, then AX1–AX5. At AX5, Body is 53 pt (about 310%).
  - Support at least 200%. Apple's Accessibility Nutrition Label "Larger Text" requires it.
- **Rules:**
  - Use `.font(.body)` and the other semantic styles. `.system(size:)` does not scale, so never use it for content.
  - Custom fonts: `.custom("Name", size: 17, relativeTo: .body)`. They must respond to Bold Text too.
  - Use `@ScaledMetric(relativeTo: .body)` for icon sizes, padding and row heights tied to text.
  - Remove `.lineLimit(1)` from essential text. Use `minimumScaleFactor` only on non-essential text, because it defeats Dynamic Type.
  - At accessibility sizes, change the layout: swap `HStack` for `VStack` via `dynamicTypeSize.isAccessibilitySize` or `ViewThatFits`, and reduce columns. Keep primary content on top.
  - Cap only tiny fixed chrome with `.dynamicTypeSize(...DynamicTypeSize.accessibility3)`. Never cap body content.
  - Don't set manual tracking; the system applies optical sizing.
- **Case:** sentence case for body text, title case for buttons and menu items (Apple style).

## 8. Color and dark mode
- **Semantic colors:**
  - Backgrounds: `systemBackground` / `secondary…` / `tertiary…`, and the grouped variants for grouped lists.
  - Text: `label`, `secondaryLabel`, `tertiaryLabel`, `placeholderText`. Also `separator` and `link`.
  - Never redefine their meanings or hard-code their values.
- **Custom colors:** use an asset-catalog Color Set with Light, Dark and High Contrast variants (Display P3, sRGB fallback).
- **Dark mode:**
  - Follow the system appearance. Don't add an in-app light/dark toggle (HIG). A permanently dark UI is OK only for immersive media.
  - The system uses elevated backgrounds for sheets and popovers, and custom backgrounds can break this.
  - Soften pure-white images in dark mode.
- **Contrast:** at least 4.5:1 for text (aim for 7:1 for small text) and 3:1 for 18 pt+ or bold text. Check dark mode, Increase Contrast and Reduce Transparency, separately and combined.
- **Tint:** set one tint / AccentColor. Use it for actions, selection and status, not decoration. One color means one thing.
- **Bars:** keep tab bars and toolbars monochrome over colorful content. Color the glass background of the primary action (`.glassProminent`, `.borderedProminent`), not its label.
- **Hierarchy:** use `.foregroundStyle(.secondary/.tertiary)`. Avoid `quaternaryLabel` on thin materials.

## 9. SF Symbols
- Prefer SF Symbols (7,000+) over custom icons. They match text in weight, scale and localization.
- **Rendering modes:**
  - Monochrome.
  - Hierarchical (one color, layered opacity).
  - Palette (two or more colors).
  - Multicolor (intrinsic colors).
  - Check details at small sizes.
- **Weight and scale:** match the weight to adjacent text (`.fontWeight`). Use `imageScale` (small/medium/large) for emphasis.
- **Variants:** outline in toolbars and lists, fill in tab bars, swipe actions and selection, slash for unavailable. Prefer `.symbolVariant` over editing the name string.
- **Effects:**
  - Bounce to confirm.
  - Pulse/breathe for ongoing activity.
  - Variable color for progress.
  - Replace for state swaps: `.contentTransition(.symbolEffect(.replace))`.
  - Wiggle to point at a missed call to action.
  - Never loop forever for decoration. Respect Reduce Motion.
- **Meaning:** use standard symbols for standard actions (share is `square.and.arrow.up`, trash means delete). Don't repurpose them.
- Use `Label("Share", systemImage: "square.and.arrow.up")` so VoiceOver reads the text. Give custom symbols an accessibility description.

## 10. Motion and haptics
- **Principles (HIG):**
  - Motion is purposeful and brief, and it follows the gesture.
  - It is never the only carrier of information.
  - No motion on very frequent interactions.
  - Never make people wait for an animation; keep it interruptible.
- **Springs:** the SwiftUI default since iOS 17 is a spring.
  - `.smooth` has no bounce and fits most UI.
  - `.snappy` has a small bounce.
  - `.bouncy` is for playful moments only.
  - Custom: `.spring(duration:bounce:)`.
  - Changing numbers: `.contentTransition(.numericText())`.
- **Reduce Motion** (`@Environment(\.accessibilityReduceMotion)`):
  - Replace slides and zooms with fades and remove bounce.
  - Avoid z-depth, parallax and animating blur.
  - Zoom and matched-geometry transitions fall back to a cross-fade.
- **Widgets and Live Activities:** animations are capped at 2 s.
- **Haptics (HIG):**
  - Use system patterns only for their documented meaning.
  - Keep them short and discrete, matched to the visual change, and rare.
  - Standard controls already play haptics, so don't double them.
  - Some users turn haptics off, so haptics are never the only feedback.
- **SwiftUI** `.sensoryFeedback(_:trigger:)` (iOS 17+):
  - `.success` (order placed), `.warning`, `.error` (validation failed).
  - `.selection` (picker or segment change), `.increase` / `.decrease` (stepper).
  - `.impact(weight:intensity:)` (snaps, drops), `.start` / `.stop`.
- **UIKit:**
  - `UINotificationFeedbackGenerator` for success, warning or error.
  - `UIImpactFeedbackGenerator` (`.light`, `.medium`, `.heavy`, `.soft`, `.rigid`).
  - `UISelectionFeedbackGenerator`.
  - Core Haptics only for custom patterns, mostly in games.

## 11. iOS accessibility APIs
See `accessibility.md` for the cross-platform rules. iOS specifics:
- **Labels and traits:**
  - `.accessibilityLabel("Delete")` without the word "button".
  - `.accessibilityValue` for state. `.accessibilityHint` only when the result is not obvious.
  - `.accessibilityAddTraits(.isHeader / .isButton / .isSelected)`.
- **Grouping and hiding:**
  - `.accessibilityElement(children: .combine)` for rows. `.contain` for containers. `.accessibilitySortPriority` to fix reading order.
  - `.accessibilityHidden(true)` for decorative images.
- **Actions and rotors:**
  - `.accessibilityAction(named: "Delete") { … }` so swipe and long-press actions work with VoiceOver, Switch Control and Voice Control.
  - `.accessibilityRotor` for custom rotors.
- **Announcements:** `AccessibilityNotification.Announcement("Added to cart").post()`. Screen and layout changes post `.ScreenChanged` / `.LayoutChanged`.
- **Environment values:** `\.dynamicTypeSize`, `\.accessibilityReduceMotion`, `\.accessibilityReduceTransparency` (glass needs a solid fallback for custom effects), `\.colorSchemeContrast`, `\.legibilityWeight` (Bold Text), `\.accessibilityDifferentiateWithoutColor`.
- **Screen titles:** every screen has a unique, concise title, the first thing VoiceOver announces.
- **Voice Control:** the accessible name matches the visible label.
- **Switch Control / Full Keyboard Access:** every action is reachable without gestures.
- **Accessibility Nutrition Labels** (App Store Connect, voluntary for now): declare a feature only if all common tasks work with it (first launch, login, purchase, settings). "Larger Text" means at least 200%.
- **Tools:** Accessibility Inspector, Xcode previews with Dynamic Type variants, real-device VoiceOver.

## 12. System integration
- **Widgets (WidgetKit):**
  - Glanceable and single-purpose. Supported families: small, medium, large, plus Lock Screen accessories.
  - Support the accented/clear look (`widgetAccentable`, `containerBackground(for: .widget)`).
  - Updates are budgeted, so use `Text(date, style: .timer/.relative)` for live times.
  - Interactive Button and Toggle via App Intents.
- **Live Activities (ActivityKit):** for events with a start and an end, up to about 8 hours (delivery tracking, rides, timers).
  - Support compact, minimal, expanded and Lock Screen presentations.
  - The Dynamic Island background is black. Use heavier weights and large text.
  - No ads. Hide sensitive details.
  - A limited-width mode (iOS 27, e.g. landscape) fits a 28 pt circle.
- **App Intents** is the single integration layer for Siri (including iOS 27 "Siri AI"), Spotlight, Shortcuts and the Action button.
  - App Shortcuts work at install. Use short phrases that include the app name, with one parameter at most.
  - Describe on-screen content with app entities.
- **Control Center / Action button controls (ControlWidget):** a button or a toggle with on and off symbols. Redact sensitive values when locked.
- **Share:** `ShareLink` and the system share sheet. Never a custom share UI.
- **Sign in with Apple:**
  - Use the system button, no smaller than other sign-in buttons.
  - Defer sign-in until it is needed.
  - Don't ask for a password or a personal email afterwards.
  - Revoke tokens on account deletion.
- **Passkeys:** if you don't use Sign in with Apple, prefer passkeys. Name the method on the button ("Sign In with Face ID"). No in-app biometric toggle.
- **Apple Pay:**
  - Use it for physical goods and services (digital goods use In-App Purchase).
  - Make it the primary option when a card exists. Use the system button only, and don't hide or disable it.
  - Collect options before the button. Defer account creation until after payment.
  - Show an order confirmation.
- **Notifications:**
  - Request in context (`UNUserNotificationCenter.requestAuthorization`).
  - Copy is concise, specific and sentence case, without the app name.
  - Up to 4 actions; no "Open app" action. Badges show only unread counts.
  - Interruption levels: Passive, Active (default), Time Sensitive (relevant within about an hour; breaks through Focus), Critical (health and safety only; needs an entitlement). Never inflate urgency.
  - Push can't be required to use the app, or used for promotions without opt-in (App Review 4.5.4).

## 13. Permissions and privacy
- **When to ask:** request at the moment a feature needs it. Avoid launch-time requests unless the app cannot work without them. Ask for the narrowest scope.
- **Purpose strings** (`NS…UsageDescription`): one specific, active sentence.
  - Good: "Your location is used to show restaurants that deliver to you."
  - Bad: "for a better experience".
- **Priming screens** before the system alert are allowed with limits:
  - One button, and it must lead to the system alert. Don't label it "Allow".
  - No cancel that skips the alert. Never imitate the system alert.
  - For tracking, never incentivize or annotate the alert.
- **Prefer out-of-process pickers over blanket access:** `PhotosPicker`, `LocationButton` (one-time location), the contacts picker, the document picker.
- **Denial:** provide an alternative (manual address entry), don't nag, and keep core features independent of notifications, location and tracking.
- **App Tracking Transparency:** required before any cross-app tracking. Never gate paid features on consent.
- **Privacy manifest:** `PrivacyInfo.xcprivacy` for the app and each SDK that needs one, with required-reason APIs declared. Privacy labels must match reality. Fingerprinting is never allowed.

## 14. SwiftUI defaults and test matrix

```swift
// Sticky bottom CTA that respects safe area, keyboard, Dynamic Type and haptics
struct CartScreen: View {
    @State private var placed = false
    @ScaledMetric(relativeTo: .body) private var rowImage: CGFloat = 56
    var body: some View {
        List { /* rows */ }
            .safeAreaInset(edge: .bottom) {
                Button {
                    Task { placed = await placeOrder() }   // disable while in flight; idempotent request
                } label: {
                    Text("Checkout · 84 000 so'm").frame(maxWidth: .infinity)
                }
                .primaryActionStyle()                      // §1 wrapper: glassProminent on iOS 26+, borderedProminent before
                .controlSize(.large)
                .padding()
            }
            .sensoryFeedback(.success, trigger: placed)
            .navigationTitle("Cart")
    }
}
```

- Prefer `List` (lazy, accessible) for large collections. In a custom `ScrollView`, use `LazyVStack`.
- Use `.task {}` for loading tied to the view's lifetime, and handle cancellation.
- Previews: light/dark, `.environment(\.dynamicTypeSize, .accessibility5)`, a long-text locale.
- **Test matrix:** smallest and largest iPhone, landscape, AX5 text, Bold Text, dark mode, Increase Contrast, Reduce Transparency, Reduce Motion, VoiceOver, RTL pseudo-language, both extremes of the iOS 27 glass slider, slow network (Network Link Conditioner), a real device.

### iOS anti-patterns
- Glass in the content layer, glass on glass, custom bar backgrounds, tinted bars.
- Fixed font sizes, fixed-height rows, clipped text at AX sizes, Light weights at small sizes.
- Targets under 44 pt. A broken swipe-back. Hidden or disabled tabs. Stacked or undismissable sheets.
- Alerts for info, on launch, or with "OK" on a destructive action.
- Permission prompts at first launch. A fake pre-prompt that imitates the system alert.
- Third-party login without an equivalent privacy-focused option (Guideline 4.8). No in-app account deletion.
- Custom share, navigation or controls replacing the system ones. An app-specific dark-mode toggle.
- Haptics on every tap. Infinite decorative loops. Ignoring Reduce Transparency or the iOS 27 slider.
- Ads or marketing in Live Activities, notifications or Siri responses.
