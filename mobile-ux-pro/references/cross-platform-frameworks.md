# Flutter, React Native and Compose Multiplatform

The UX rules are the same as for native apps. Cross-platform apps fail in predictable places: text scaling, safe areas and insets, accessibility props, back behavior, and chrome that looks native on one platform and foreign on the other. Library APIs change quickly, so check the current docs (ctx7) before you pin versions.

## Decide the visual strategy first
- **Platform-adaptive (recommended for consumer apps).** One product and one brand, but navigation, back, dialogs, switches, pickers, typography and haptics follow each platform. Users get conventions they already know.
- **Single brand UI everywhere.** Acceptable for strongly branded apps, but platform behaviors must still be native: back gesture, text scaling, keyboard, share sheet, permissions, accessibility.
- Never ship Material-only UI to iPhone or Cupertino-only UI to Android without a deliberate reason.

## Flutter
- **Material 3** is the default theme. Build the `ColorScheme` with `ColorScheme.fromSeed(seedColor: brand)`, plus a dark scheme. Read colors from `Theme.of(context).colorScheme` and text from `textTheme`; no hard-coded colors.
- **Adaptive widgets:**
  - `Switch.adaptive`, `Slider.adaptive`, `CircularProgressIndicator.adaptive`, `Checkbox.adaptive`.
  - `showAdaptiveDialog` / `AlertDialog.adaptive`.
  - Cupertino widgets (`CupertinoNavigationBar`, `CupertinoActionSheet`, `CupertinoPicker`) for iOS chrome where it matters.
- **Back:**
  - `MaterialPageRoute` uses the Cupertino transition with swipe-back on iOS by default, so don't override it with a custom route that loses the swipe.
  - Use `PopScope` (replaces `WillPopScope`) for unsaved-changes guards.
  - Enable Android predictive back (`android:enableOnBackInvokedCallback="true"`, `PredictiveBackPageTransitionsBuilder`) (verify current API).
- **Safe areas and insets:**
  - `SafeArea`, `MediaQuery.paddingOf(context)`, `MediaQuery.viewInsetsOf(context)` for the keyboard.
  - `Scaffold(resizeToAvoidBottomInset: true)`.
  - Android 15+ is edge-to-edge, so test both nav modes.
- **Text scaling:**
  - Respect `MediaQuery.textScalerOf(context)` (`textScaleFactor` is deprecated).
  - Never wrap the app in a fixed `TextScaler.noScaling`.
  - Clamp only small chrome (e.g. `textScaler.clamp(maxScaleFactor: 2.0)` on a badge).
  - Avoid fixed-height containers around text.
- **Touch targets:** keep `MaterialTapTargetSize.padded` (48 dp, `kMinInteractiveDimension`). Give `IconButton`s a `tooltip`, which also becomes the semantics label.
- **Accessibility:**
  - `Semantics(label:, button: true, header: true)`, `MergeSemantics` for rows, `ExcludeSemantics` for decoration.
  - `SemanticsService.announce` for announcements (sparingly).
  - `CustomSemanticsAction` for swipe actions.
  - Debug with `SemanticsDebugger`. Widget tests can use `meetsGuideline(androidTapTargetGuideline)`, `iOSTapTargetGuideline`, `textContrastGuideline` and `labeledTapTargetGuideline`.
- **Settings to read:** `MediaQuery.disableAnimationsOf`, `boldTextOf`, `highContrastOf`, `platformBrightnessOf`. Shorten or skip animations when animations are disabled.
- **Haptics:** `HapticFeedback.selectionClick()`, `lightImpact()`, `mediumImpact()`, `heavyImpact()`. Map them to meaning (selection, success) and use them sparingly.
- **Forms:**
  - `keyboardType: TextInputType.phone / emailAddress / number`, `textInputAction: TextInputAction.next`.
  - `autofillHints: [AutofillHints.telephoneNumber, AutofillHints.oneTimeCode]` inside an `AutofillGroup`.
  - `InputDecoration(labelText:, errorText:)`.
- **Lists and images:** `ListView.builder` / `SliverList` (lazy), stable `Key`s, `cached_network_image` with placeholders.
- **Localization:** `flutter_localizations` plus `intl` with ARB files, `EdgeInsetsDirectional` / `AlignmentDirectional` for RTL.
- **iOS Liquid Glass:** Flutter draws its own widgets, so it doesn't inherit Liquid Glass automatically. Either accept a branded look, or use platform views / native shells for the tab bar and navigation where native feel matters (verify current Flutter support).

## React Native (and Expo)
- **Navigation:**
  - Native stacks (`@react-navigation/native-stack` or Expo Router stacks) use real `UINavigationController` / Fragments, so swipe-back and native headers come for free.
  - Avoid JS-only stacks for main flows.
  - Native bottom tabs inherit the platform tab bar where supported (verify current Expo Router / React Navigation native-tabs support for iOS 26 glass).
- **Safe areas:** use `react-native-safe-area-context` (`SafeAreaProvider`, `useSafeAreaInsets`) everywhere. The core `SafeAreaView` is limited or deprecated. Android 15+ is edge-to-edge, so pad with the insets.
- **Keyboard:** `KeyboardAvoidingView` (behavior `padding` on iOS) or `react-native-keyboard-controller`. Keep the CTA above the keyboard.
- **Text scaling:**
  - `allowFontScaling` defaults to true; keep it.
  - Never set `maxFontSizeMultiplier={1}` on content.
  - Use flexible layouts and test with `useWindowDimensions().fontScale` at the maximum size.
- **Touch:** use `Pressable` with `hitSlop` to reach 44/48 targets, and `android_ripple` for Android feedback.
- **Accessibility:**
  - `accessible`, `accessibilityLabel` (or `aria-label`), `accessibilityRole` / `role` ("button", "header", "switch"), `accessibilityState` ({ selected, checked, disabled }), `accessibilityHint` sparingly.
  - `accessibilityActions` with `onAccessibilityAction` for swipe alternatives.
  - `AccessibilityInfo.announceForAccessibility`, used sparingly.
- **Settings:** `AccessibilityInfo.isReduceMotionEnabled()`, Reanimated's `useReducedMotion()` / `ReduceMotion.System`, `useColorScheme()` for dark mode.
- **Animation:** Reanimated (UI thread) for gestures and transitions, Gesture Handler for native gestures. Keep JS-thread work out of scroll.
- **Haptics:** `expo-haptics` (`Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success)`, `selectionAsync()`, `impactAsync(Haptics.ImpactFeedbackStyle.Light)`).
- **Forms:**
  - `keyboardType="phone-pad" | "email-address" | "number-pad"`, `returnKeyType="next"`.
  - OTP: `textContentType="oneTimeCode"` on iOS, `autoComplete="sms-otp"` on Android. `autoCorrect={false}` and `autoCapitalize="none"` for emails and codes.
- **Lists and images:** `FlatList` or FlashList with `keyExtractor` and fixed item layouts where possible. `expo-image` with placeholders and caching.
- **Platform differences:** `Platform.select`, or `.ios.tsx` / `.android.tsx` files for chrome that should differ (dialogs, pickers, headers).
- **Localization:** i18next or similar with ICU plurals, `Intl` formatters, `I18nManager` for RTL, start/end styles.

## Compose Multiplatform / KMP
- Shared business logic (KMP) with native UI per platform gives the most native result.
- Compose Multiplatform UI on iOS doesn't automatically match iOS conventions. Check swipe-back, scrolling physics, text-field behavior, Dynamic Type mapping, VoiceOver semantics and the keyboard. Consider SwiftUI for top-level navigation and chrome, with shared screens embedded (verify current CMP iOS accessibility and Dynamic Type support).
- Keep the Android side fully Material 3 per `android.md`.

## Cross-platform review additions
- [ ] Back swipe works on iOS and predictive back works on Android in every flow.
- [ ] Text scales on both platforms at maximum settings without clipping.
- [ ] Safe areas and insets are correct on both, including the keyboard and Android gesture nav.
- [ ] Accessibility labels and roles are set on custom touchables. A screen reader was tested on both platforms.
- [ ] Platform-appropriate dialogs, pickers, switches and share sheet.
- [ ] Performance checked in release builds on a low-end Android device (JS thread, overdraw, image sizes).
