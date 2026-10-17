# Android: Material 3, M3 Expressive, Jetpack Compose

Verified 2026-10-17 against developer.android.com, androidx source and release notes, Maven metadata, and Material Components docs. Items marked "(verify)" came from secondary sources or memory. Check them in current docs before relying on them.

## Contents
1. Platform and library status
2. Material 3 Expressive: when and how
3. Edge-to-edge and insets
4. Predictive back and navigation
5. Adaptive layout
6. Navigation components
7. Touch and interaction
8. Typography
9. Color
10. Motion
11. Haptics
12. Compose accessibility APIs
13. Performance and quality
14. System integration
15. Compose defaults and test matrix

---

## 1. Platform and library status
- **Android versions:** Android 17 is API 37; Android 16 is API 36.
- **Play target API:**
  - New apps and updates must target API 36 since 2026-08-31.
  - Existing apps below API 35 lose visibility to new users on newer devices.
- **Compose versions:**
  - Compose BOM 2026.09.00 maps ui/foundation to 1.12.x and material3 to 1.4.0.
  - Compose 1.12 needs compileSdk 37 and AGP 9.1.1+.
- **Expressive components** are not in material3 1.4.0. 1.4.0 removed every `@ExperimentalMaterial3ExpressiveApi` API.
  - To use them, pin `androidx.compose.material3:material3:1.5.0-beta01` (or newer) explicitly, outside the BOM.
  - 1.5.0 stable is expected later in 2026.
- **Google is "Compose-first".** The Views toolkit is in maintenance mode, and Material Views 1.14 is the last big Views release. Build new UI in Compose.
- **Icons:** the Material Icons library is no longer recommended. Download Material Symbols as vector XML from fonts.google.com/icons. Don't depend on `material-icons-extended`; it bloats builds.
- **Other current versions** (verify before pinning): navigation-compose 2.10.x, navigation3 1.2.x, material3-adaptive 1.3.x, activity-compose 1.13.x, core-splashscreen 1.2.x, credentials 1.6.x, Coil 3.6.x.

### minSdk, compileSdk and API gating
- **Find the floor:** `minSdk`, `targetSdk` and `compileSdk` in `app/build.gradle(.kts)` or `gradle/libs.versions.toml`, plus the Compose BOM and any explicitly pinned material3 version.
  - Greenfield default: minSdk 26, with target and compile at the current API (check adoption).
  - State the choice.
- **Library floors are real too.**
  - Compose 1.12 needs compileSdk 37 and AGP 9.1.1+.
  - Expressive components need material3 1.5.x pinned outside the BOM.
  - Don't raise compileSdk/AGP or pin a beta silently. Propose it with the trade-off, or use only APIs the project's versions have.
- **API levels that need a check** (check exact levels in docs when unsure):

| API level | Feature | Fallback |
|---|---|---|
| 37 | Contact Picker (`ACTION_PICK_CONTACTS`) | system contacts intent / manual entry |
| 36 | `Notification.ProgressStyle` Live Updates | standard ongoing notification with progress |
| 34 | `UiModeManager.getContrast()`, `HapticFeedbackConstants.TOGGLE_ON/SEGMENT_TICK` | standard scheme; Compose `HapticFeedbackType` falls back automatically |
| 33 | `POST_NOTIFICATIONS` runtime permission, per-app language | no request needed below 33; AppCompat `setApplicationLocales` backports |
| 31 | Dynamic color, SplashScreen (platform) | brand color scheme; `core-splashscreen` compat |
| 30 | `HapticFeedbackConstants.CONFIRM/REJECT` | platform falls back to older constants |

- **Gating pattern:**

```kotlin
val scheme = when {
    dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S ->
        if (dark) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
    dark -> BrandDarkColors
    else -> BrandLightColors
}

@RequiresApi(Build.VERSION_CODES.TIRAMISU)
private fun requestNotificationPermission(launcher: ActivityResultLauncher<String>) =
    launcher.launch(Manifest.permission.POST_NOTIFICATIONS)
```

- **Prefer AndroidX APIs that backport for you:** `enableEdgeToEdge()` (activity), `PickVisualMedia` (photo picker, backported through Play services), `core-splashscreen`, `ViewCompat`/`WindowCompat`, `LocalHapticFeedback`, AppCompat per-app locales.
- Lint's `NewApi` check catches ungated calls. Run `./gradlew lint` (or at least compile) when possible, and say if you couldn't.

## 2. Material 3 Expressive: when and how
- **Evidence.** Google's research covered 46 studies and 18,000+ participants. People spotted key elements up to 4x faster, and the age gap for 45+ users largely disappeared. These are Google-run numbers.
- **The five levers:** color, shape, size, motion, containment. Examples: bigger primary actions, key actions just above the keyboard, content grouped in high-contrast containers.
- **When to use it.**
  - Go expressive (springs, big shapes, emphasized type) for hero moments, primary actions, onboarding and media.
  - Stay standard for dense, form-heavy, financial or safety-critical flows.
- **Limits.**
  - Never remove labels or contrast to look expressive. Removing text labels from actions hurt usability in Google's own study.
  - Keep familiar patterns, and test calmer variants.
- **Theming.**
  - `MaterialExpressiveTheme(colorScheme, motionScheme, shapes, typography)` defaults to `expressiveLightColorScheme()` and `MotionScheme.expressive()`. It is light only by default, so pass your dark scheme yourself.
  - Plain `MaterialTheme` uses `MotionScheme.standard()`. Read the active scheme with `MaterialTheme.motionScheme`.
- **Shape scale (dp):** XS 4, S 8, M 12, L 16, LargeIncreased 20, XL 28, XLIncreased 32, XXL 48.
  - Buttons morph between round and square on press and when checked.
  - `MaterialShapes` / `PolygonShape` are still experimental.
- **Emphasized type:** every type role has an `*Emphasized` variant (`titleMediumEmphasized`). Use it for a few key texts, not whole screens.
- **Component status in 1.5:**
  - Stable: `ButtonGroup`, `SplitButton`, toggle buttons, `FloatingActionButtonMenu`, `HorizontalFloatingToolbar`/`VerticalFloatingToolbar`, flexible top app bars, expressive `ListItem`, `WavyProgressIndicator`.
  - Still experimental: `LoadingIndicator`, `MaterialShapes`, `AppBarWithSearch`.
- **Sizes (dp):**
  - Buttons: XS 32, S 40, M 56, L 96, XL 136.
  - FAB: 40 / 56 / 80 / 96.
  - Navigation bar: 64.
  - Floating toolbar: 64.
  - Collapsed wide rail: 96.

## 3. Edge-to-edge and insets
- **Edge-to-edge is enforced** at target 35+ on Android 15+. At target 36 the opt-out is gone. Call `enableEdgeToEdge()` in `onCreate` before `setContent`.
- **System bars:**
  - Never use opaque system bars.
  - Keep the gesture nav bar transparent, with no background behind the handle.
  - Use a translucent status bar over scrolling content and a transparent one over hero images.
  - Set icon contrast with `isAppearanceLightStatusBars`.
- **Inset types:**
  - `safeDrawing` keeps content clear of system UI.
  - `safeGestures` keeps gestures clear of system gestures.
  - `safeContent` covers both.
  - Also `statusBars`, `navigationBars`, `ime`, `displayCutout`, `systemGestures`.
- **Modifiers:** `safeDrawingPadding()`, `windowInsetsPadding(...)`, `systemBarsPadding()`, `imePadding()`, `consumeWindowInsets(...)`.
- **Scaffold:**
  - `TopAppBar` and `NavigationBar` apply their own insets.
  - Always apply the content lambda's `innerPadding`.
  - For lazy lists, pass `contentPadding = innerPadding` so content scrolls under the bars and the last item stays reachable. Don't also add `statusBarsPadding()`, or you pad twice.
- **Keyboard:** use `windowSoftInputMode="adjustResize"` plus `imePadding()`.
  - The focused field and the primary button must stay visible.
  - Android 17 no longer restores IME visibility after rotation, so show it explicitly if needed.
- **Gestures near edges:** keep swipeable UI out of `safeGestures` zones. `Modifier.systemGestureExclusion()` opts out only a limited area, and `mandatorySystemGestures` can never be excluded.
- **Cutouts:** apps draw into display cutouts. Pad with `displayCutout` and check landscape.
- **Test matrix:** gesture nav and 3-button nav, light and dark bar icons, landscape with a cutout, API 29 and API 35+.

## 4. Predictive back and navigation
- **Android 16 at target 36:**
  - Predictive back is on by default.
  - `onBackPressed()` and `KEYCODE_BACK` are no longer dispatched.
  - Temporary opt-out: `android:enableOnBackInvokedCallback="false"`.
- **APIs:**
  - `BackHandler(enabled) { … }` for plain interception.
  - `PredictiveBackHandler(enabled) { progress -> try { progress.collect { e -> /* e.progress 0..1 */ }; commit() } catch (e: CancellationException) { reset(); throw e } }` for animated back.
  - The newer `NavigationBackHandler` comes from `navigationevent-compose`.
- **Rules:**
  - Tie `enabled` to observable state (for example, `enabled = sheetOpen`).
  - Never intercept back at the root; it kills the back-to-home animation.
  - Never use back callbacks for logging or business logic.
  - No custom on-screen back arrow replacing system back. A top-app-bar Up arrow inside a hierarchy is fine.
  - In list-detail on small windows, back closes the detail pane first.
- **Components with built-in predictive back:** `SearchBar`, `ModalBottomSheet`, `ModalNavigationDrawer` (pass `drawerState`).
- **Navigation Compose:**
  - The default back transition is a crossfade. Customize with `popEnterTransition`/`popExitTransition`, for example `scaleOut(targetScale = 0.9f)`.
  - Keep the system "preview" feel: a slight scale plus a corner morph. Don't replace it with a plain fade.
- **Navigation 3** (stable 1.2): you own the back stack (a list) and render it with `NavDisplay(backStack, onBack, entryProvider, …)`.
  - Adaptive scenes: `ListDetailSceneStrategy`, `SupportingPaneSceneStrategy`.
  - Shared elements via `SharedTransitionLayout`.
- **Deep links:** use verified App Links (`android:autoVerify="true"` plus `assetlinks.json`). Each deep link must build a sensible back stack and work from cold start and when logged out.
- Restore exact state when the user returns from Recents.

## 5. Adaptive layout
- **Window size classes** (width; height in parentheses):
  - Compact: < 600 dp (< 480).
  - Medium: 600–839 (480–899).
  - Expanded: 840–1199 (≥ 900).
  - Large: 1200–1599.
  - Extra-large: ≥ 1600.
  - Large and extra-large are opt-in in `currentWindowAdaptiveInfo`; check the V2 API in current docs.
- **Rules:**
  - Decide by width first.
  - A phone in landscape has medium width but compact height, so two panes rarely fit.
  - Never write `isTablet()` logic. Size classes describe the window, which changes on rotation, split-screen and fold.
- **Large screens (sw600dp+)** ignore `screenOrientation`, `resizeableActivity` and aspect-ratio limits on Android 16 at target 36. Android 17 at target 37 removes the opt-out.
  - Never lock to portrait.
  - Save UI state, because recreation happens more often.
- **Canonical layouts:**
  - List-detail: side by side on expanded, one pane otherwise.
  - Supporting pane: 70/30 on expanded.
  - Feed: `LazyVerticalGrid(GridCells.Adaptive(minSize = 180.dp))`.
- **APIs:** `ListDetailPaneScaffold`, `SupportingPaneScaffold`, `NavigationSuiteScaffold`. Cap content width; never stretch text fields and buttons edge to edge on tablets.
- **Grid:** 8 dp baseline, 4 dp for small elements and type. 16 dp side margins on compact are standard. Keep lines to 45–75 characters.
- **Foldables:** use Jetpack WindowManager `FoldingFeature`. No critical UI across the hinge.

## 6. Navigation components
- **Navigation bar:**
  - 3–5 destinations, 64 dp tall, always with labels.
  - Preserve each tab's back stack and scroll position. Re-selecting a tab scrolls to top or pops to root.
- **`NavigationSuiteScaffold`** (`material3-adaptive-navigation-suite`) switches automatically: a bar on compact, a rail on medium and expanded. You can pick a drawer on expanded width via `layoutType`. Give every icon a `contentDescription` or a visible label.
- **Rail and drawer:** `NavigationRail` / `WideNavigationRail` (the expanded rail replaces the drawer). A modal drawer only for secondary destinations; never hide primary sections in a hamburger menu.
- **Top app bars:**
  - `TopAppBar`, `CenterAlignedTopAppBar`, `MediumFlexibleTopAppBar`, `LargeFlexibleTopAppBar`. The flexible Medium/Large bars replace the deprecated ones.
  - Scroll behaviors (`pinned`, `enterAlways`, `exitUntilCollapsed`) are wired with `Modifier.nestedScroll(scrollBehavior.nestedScrollConnection)`.
- **FAB:**
  - At most one per screen, for the primary action, 16 dp from the edges.
  - `ExtendedFloatingActionButton` (icon plus label) is clearer than an icon-only FAB.
  - `FloatingActionButtonMenu` for 2–6 related actions.
- **Bottom sheets:** `ModalBottomSheet` with a drag handle, for short transient choices. Back dismisses it. Don't hide critical actions in sheets, and don't stack them.
- **Choosing the feedback surface:**
  - `AlertDialog` for decisions and critical info.
  - `Snackbar` (through `SnackbarHostState` in `Scaffold`) for brief, non-blocking status with at most one action (Undo, Retry).
  - Avoid Toast for in-app feedback.
  - A full-screen dialog only for complex input on compact windows.
- **In-screen sections:** `PrimaryTabRow` / `SecondaryTabRow` (scrollable variants exist), or segmented buttons for 2–5 options.

## 7. Touch and interaction
- **Touch target:** at least 48x48 dp, and it may extend beyond the visual. Material components add it automatically when they have an action. For custom controls use `Modifier.minimumInteractiveComponentSize()` or `sizeIn(minWidth = 48.dp, minHeight = 48.dp)`.
- **Whole-row toggles:** `Modifier.toggleable(value, role = Role.Checkbox, onValueChange = …)` on the row, with `Checkbox(checked, onCheckedChange = null)`.
- **Clickables:** always `Modifier.clickable(onClickLabel = "Open details", role = Role.Button) { … }`. No clickable children inside a clickable parent.
- **Long press:** `combinedClickable(onLongClick = …, onLongClickLabel = …)`. Every long-press action needs a visible alternative.
- **`SwipeToDismissBox`:**
  - Never the only way to delete. Add a visible action plus a `CustomAccessibilityAction`.
  - Offer Undo through a snackbar.
- **Pull to refresh:** `PullToRefreshBox(isRefreshing, onRefresh) { … }`. Fire haptic `GestureThresholdActivate` at the threshold.
- **Overscroll:** keep the default stretch overscroll.
- **Focus:** show visible focus indicators for keyboard and D-pad users.

## 8. Typography
**M3 type scale** (size / line height in sp):

| Role | Large | Medium | Small |
|---|---|---|---|
| Display | 57/64 | 45/52 | 36/44 |
| Headline | 32/40 | 28/36 | 24/32 |
| Title | 22/28 | 16/24 (Medium weight) | 14/20 (Medium) |
| Body | 16/24 | 14/20 | 12/16 |
| Label | 14/20 (Medium) | 12/16 (Medium) | 11/16 (Medium) |

- **Units:** text sizes and line heights are always in sp, never dp or px. Don't use sp for padding.
- **Font scaling:** Android 14+ scales fonts nonlinearly up to 200%. Large text grows less than small text.
  - Never do math with `fontScale`. Use `TypedValue.applyDimension(COMPLEX_UNIT_SP, …)` when you must convert.
  - Test at 200% plus maximum display size.
- **Layout for large text:**
  - `heightIn(min = …)` instead of fixed heights.
  - `FlowRow` for chips.
  - `maxLines` with ellipsis only for non-essential text.
  - Check tabs, buttons and time pickers at 200%.
- **Minimums:** body text at least 12 sp, and prefer `bodyLarge` (16 sp) for reading text.
- **Fonts:** Roboto is the default. For a brand font, set `fontFamily` per style or use the `Typography` constructor that takes a default `FontFamily` (1.5). Check that the font has Cyrillic and other needed glyphs (see `localization.md`).

## 9. Color
- **Read colors only from `MaterialTheme.colorScheme` roles.** Never hard-code hex in composables.
  - Pair each role with its "on" role: `onPrimary` on `primary`, `onPrimaryContainer` on `primaryContainer`, `onSurface` / `onSurfaceVariant` on surfaces.
  - Surfaces: `surface`, `surfaceContainerLowest` … `surfaceContainerHighest`, `surfaceDim`, `surfaceBright`. Use containers for cards, sheets and panes instead of shadows.
  - Other roles: `outline` / `outlineVariant` for borders and dividers, `error` / `errorContainer` for errors, `inverseSurface` for snackbars.
- **Dynamic color** (API 31+) needs a brand fallback, or users get baseline purple:
  ```kotlin
  val context = LocalContext.current
  val scheme = when {
      Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && dynamic ->
          if (dark) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
      dark -> BrandDarkColors      // generated with Material Theme Builder
      else -> BrandLightColors
  }
  ```
  - For a strong brand (restaurant, bank), consider brand colors by default with dynamic color as an option. Keep semantic colors (error, success) fixed either way.
- **Dark theme** is required. Use `isSystemInDarkTheme()`. Elevation is tonal (`Surface(tonalElevation = …)`).
- **Contrast:** 4.5:1 for text, 3:1 for large text and UI graphics. Android 14+ exposes a system contrast level (`UiModeManager.getContrast()`). Material Theme Builder exports medium and high contrast schemes.
- **Icon:** ship a monochrome adaptive-icon layer. Android 16 QPR2 auto-themes icons without one.

## 10. Motion
- **Duration tokens (ms):**
  - Short: 50 / 100 / 150 / 200.
  - Medium: 250 / 300 / 350 / 400.
  - Long: 450–600.
  - Extra long: 700–1000.
- **Easing:**
  - Emphasized: `(0.2, 0, 0, 1)`.
  - Emphasized decelerate (enter): `(0.05, 0.7, 0.1, 1)`.
  - Emphasized accelerate (exit): `(0.3, 0, 0.8, 0.15)`.
- **`MotionScheme` springs** (damping ratio / stiffness):

| Token | Standard | Expressive |
|---|---|---|
| fastSpatial | 0.9 / 1400 | 0.6 / 800 |
| defaultSpatial | 0.9 / 700 | 0.8 / 380 |
| slowSpatial | 0.9 / 300 | 0.8 / 200 |
| fast/default/slow Effects | 1.0 / 3800, 1600, 800 | same |

- **Spatial vs effects:** spatial springs move position, size and shape (only Expressive overshoots). Effects springs animate color and opacity with no bounce. Take specs from the theme (`MaterialTheme.motionScheme…`) so the whole app moves consistently.
- **Picking the API:**
  - `animate*AsState` for one value.
  - `updateTransition` for linked values.
  - `Animatable` for gestures.
  - `AnimatedVisibility` for appear and disappear.
  - `AnimatedContent` for content swaps.
  - `animateContentSize()` for size changes.
  - `Modifier.animateItem()` for list items.
- **Shared elements:** `SharedTransitionLayout` with `Modifier.sharedElement()` (same content) or `sharedBounds()` (container transform; better for text). Use data-class keys with item ids. Shared elements don't work with `Dialog` or `ModalBottomSheet`.
- **Reduce motion:** "Remove animations" sets the animator scale to 0, and Compose respects it through `MotionDurationScale`. `basicMarquee` ignores it, so handle that yourself. Never put essential information only in animation.
- **Splash:** animation at most 1000 ms, start delay at most 166 ms, skippable.

## 11. Haptics
- **Principles:**
  - Less is more. Prefer clear over rich over buzzy; if the choice is buzzy or nothing, choose nothing.
  - Make haptics subtle for frequent events and stronger for meaningful ones.
  - Stay consistent and in sync with visuals.
  - Never use `Vibrator.vibrate()` or `createOneShot` for UI feedback.
  - Respect the system haptics setting and never force haptics.
- **Compose:** `LocalHapticFeedback.current.performHapticFeedback(HapticFeedbackType.X)`. It needs no VIBRATE permission.
  - Successful submit or order placed: `Confirm`.
  - Failed validation or declined: `Reject`.
  - Switch on/off: `ToggleOn` / `ToggleOff`.
  - Slider steps or discrete picks: `SegmentTick`. Dense scrubbing: `SegmentFrequentTick`.
  - Pull-to-refresh threshold: `GestureThresholdActivate`.
  - Long press: `LongPress`. Context menu: `ContextClick`.
- **Views:** `HapticFeedbackConstants.CONFIRM` / `REJECT` (API 30+), `TOGGLE_ON` / `SEGMENT_TICK` (API 34+). The platform supplies fallbacks on older APIs.
- Haptics are never the only feedback.

## 12. Compose accessibility APIs
See `accessibility.md` for the cross-platform rules. Compose specifics:
- **Content descriptions:**
  - `Icon`/`Image(contentDescription = stringResource(R.string.…))`, or `null` if decorative.
  - Icon buttons must have one.
- **Grouping:**
  - `Modifier.semantics(mergeDescendants = true) {}` on a row or card makes it one announcement.
  - Only the parent is interactive.
  - `clearAndSetSemantics { contentDescription = "…" }` replaces noisy children.
- **Structure:** headings with `semantics { heading() }`, screen and pane changes with `semantics { paneTitle = "…" }`.
- **State and roles:**
  - `stateDescription`, `Role.Button` / `Checkbox` / `Switch` / `Tab`.
  - `selectable` and `toggleable` for custom controls.
  - `collectionInfo` / `collectionItemInfo` for custom lists.
- **Action labels:** `onClickLabel` and `onLongClickLabel` turn "Double tap to activate" into "Double tap to add to cart".
- **Gesture alternatives:** `semantics { customActions = listOf(CustomAccessibilityAction("Delete") { delete(); true }) }`. This serves TalkBack, Switch Access and Voice Access.
- **Announcements:**
  - Android 16 deprecates `announceForAccessibility`.
  - Use a `liveRegion` (sparingly), `paneTitle`, or error semantics (`semantics { error("Enter a valid phone number") }`).
- **Traversal:** follow reading order; use `isTraversalGroup` / `traversalIndex` when visual order differs.
- **Tools:** TalkBack, Accessibility Scanner, Switch Access, Compose UI tests with semantics matchers, lint.

## 13. Performance and quality
- **Frame budget:** 16 ms at 60 Hz, 11 ms at 90 Hz, 8 ms at 120 Hz. A frame over 700 ms counts as frozen. An ANR is 5 s or more.
- **Android vitals "bad behavior" thresholds** cut Play visibility and add a store warning (28-day window):
  - User-perceived crash rate above 1.09% overall or 8% per phone model.
  - ANR rate above 0.47% overall or 8% per phone model.
  - Aim for 99.5%+ crash-free users.
- **Startup:**
  - SplashScreen API (`installSplashScreen()`); never a custom splash Activity.
  - Hold it only while truly loading (`setKeepOnScreenCondition`).
  - Show progress if loading takes more than 2 s.
  - Report `ReportDrawnWhen {}` for time to full display.
- **Baseline Profiles:** about 30% faster code paths from first launch. Generate with Macrobenchmark and the Baseline Profile Gradle plugin. Release builds use `isMinifyEnabled = true`.
- **Compose:**
  - `LazyColumn { items(list, key = { it.id }, contentType = { it.type }) { … } }`.
  - `remember` expensive work, and use `derivedStateOf` for fast-changing to slow-changing state.
  - Defer reads with lambda modifiers (`Modifier.offset { }`, `graphicsLayer { }`).
  - Never write state you just read during composition.
  - Prefer immutable or stable models. `collectAsStateWithLifecycle()`.
  - Judge performance on release builds only.
- **Images:** Coil 3 `AsyncImage`, sized to the display. Use vectors for icons, WebP or AVIF from the server, and placeholders or a crossfade.
- **Main thread:** no disk, network or heavy work on it. Use `StrictMode` in debug.
- **App size:** ship an AAB with R8 and resource shrinking. Native libraries need 16 KB page alignment, or Play blocks updates from 2027-02-01.
- **Low-end devices:** test on a 2–3 GB RAM phone with throttled network. Heavy blur, Lottie and huge images hurt most there.

## 14. System integration
- **Notifications:**
  - Android 13+ needs `POST_NOTIFICATIONS` at runtime. Never ask on first launch; ask after a user action that implies value ("Notify me when my order is on the way"), or around the 3rd–4th launch.
  - Check `areNotificationsEnabled()` before posting.
  - Use separate channels for transactional and promotional messages so users can mute promos without losing order updates.
  - No cross-promotion in notifications.
- **Live Updates (Android 16):** `Notification.ProgressStyle` for delivery, ride, navigation and workout tracking.
  - Requires the `POST_PROMOTED_NOTIFICATIONS` permission, `setRequestPromotedOngoing(true)`, ongoing, and no custom RemoteViews.
  - Never for ads, chat or package tracking.
- **Widgets (Glance):**
  - `SizeMode.Responsive`. Accurate picker previews.
  - Targets at least 48 dp. Corner radius at most 28 dp.
  - Resizable.
- **App Shortcuts:** launchers show about 4 (static plus dynamic). Use them for top tasks ("Reorder last", "Track order").
- **Sharing:** always the system Sharesheet (`Intent.createChooser`). Add `FLAG_GRANT_READ_URI_PERMISSION` when sharing URIs (Android 18 will require it).
- **Sign-in:** Credential Manager (passkey plus password plus Sign in with Google in one request). Handle `NoCredentialException` by offering sign-up. Use the SMS Retriever / User Consent API for OTP; Android 17 delays OTP SMS for non-recipient apps.
- **Pickers instead of broad permissions:**
  - Photo Picker (`PickVisualMedia`) instead of `READ_MEDIA_*`.
  - The Contact Picker (Android 17) instead of `READ_CONTACTS`.
  - Coarse or one-time location where possible.
- **Runtime permissions:** check, explain, request, handle the result. Degrade gracefully and be specific about what is unavailable. A second denial is permanent, so don't burn the prompt. Use your own pre-screen only when `shouldShowRequestPermissionRationale` is true or the context needs it.
- **Foreground services:** declare `foregroundServiceType`. Prefer WorkManager or user-initiated data transfer jobs.

## 15. Compose defaults and test matrix

```kotlin
@Composable
fun CartScreen(state: CartUiState, onCheckout: () -> Unit, onBack: () -> Unit) {
    val haptics = LocalHapticFeedback.current
    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(stringResource(R.string.cart_title)) },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(painterResource(R.drawable.ic_arrow_back), contentDescription = stringResource(R.string.navigate_up))
                    }
                },
            )
        },
        bottomBar = {
            Surface(tonalElevation = 3.dp) {
                Button(
                    onClick = { haptics.performHapticFeedback(HapticFeedbackType.Confirm); onCheckout() },
                    enabled = !state.placingOrder && state.items.isNotEmpty(),
                    modifier = Modifier.fillMaxWidth().navigationBarsPadding().padding(16.dp).heightIn(min = 56.dp),
                ) { Text(stringResource(R.string.checkout_total, state.totalFormatted)) }
            }
        },
    ) { innerPadding ->
        LazyColumn(contentPadding = innerPadding) {
            items(state.items, key = { it.id }, contentType = { "cartItem" }) { item -> CartRow(item) }
        }
    }
}
```

- Keep state in a `ViewModel` exposing an immutable `UiState` (loading / content / empty / error) via `StateFlow`. Collect it with `collectAsStateWithLifecycle()`.
- Previews: light/dark, `fontScale = 2f`, a long-text locale, `widthDp = 360` and a tablet width.
- **Test matrix:** gesture and 3-button nav, small (360 dp) and large phones, foldable or tablet, 200% font plus max display size, dark mode, high contrast, Remove animations, TalkBack, Switch Access, RTL pseudo-locale, slow network, a low-end device, a release build.

### Android anti-patterns
- Expecting Expressive components from the BOM's material3 1.4.0. `MaterialExpressiveTheme` without a dark scheme.
- Ignoring `innerPadding`, or double-padding with `statusBarsPadding()`. Opaque or tinted system bars.
- A root-level always-enabled `BackHandler`. `onBackPressed()` overrides. Custom on-screen back buttons. Plain-fade back animations.
- Portrait lock, `isTablet()` checks, fixed-width layouts stretched on tablets.
- dp for text, fixed-height text boxes, math with `fontScale`.
- Hex colors in composables. Dynamic color without a brand fallback. No dark theme.
- `clickable` without `role`/label. Icon buttons without `contentDescription`. Swipe- or long-press-only actions.
- Targets under 48 dp. More than 5 bottom-nav items. Several FABs. Toasts for important feedback.
- Haptics on every tick. `createOneShot` buzzes.
- `POST_NOTIFICATIONS` or location requested on first launch. `READ_MEDIA_*` where the Photo Picker works.
- `LazyColumn` without keys. Judging performance on debug builds. No Baseline Profile.
