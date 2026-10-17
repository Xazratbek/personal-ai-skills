# Mobile accessibility

Accessibility is part of "done". Roughly 1 in 4 adults has some disability, everyone is temporarily impaired sometimes (sunlight, one hand busy, a noisy street), and both stores now surface accessibility: Apple has Accessibility Nutrition Labels, and Google Play's core app quality includes accessibility checks. Platform-specific APIs are in `ios.md` §11 and `android.md` §12.

## Quick rules (apply to every screen)
1. **Targets.** At least 44 pt (iOS) / 48 dp (Android), about 8 dp apart. WCAG 2.5.8 AA is 24 px; aim for the platform number.
2. **Names.** Every interactive element has an accessible name that matches its visible label. Icon-only buttons get a label that names the action plus the object ("Add Plov to cart").
3. **Decorative images are hidden** from assistive tech. Meaningful images get a description of their meaning, not their pixels.
4. **Roles and states.** Buttons are announced as buttons, toggles as switches with their on/off state, selected tabs as selected, headings as headings. Prefer system components, which do this for free.
5. **Grouping.** A card or row reads as one sensible sentence ("Plov, Rayhon restaurant, 45 000 so'm, 4.8 stars"), not five fragments. Inner actions stay separately reachable.
6. **Text scales.** Support at least 200%; iOS goes to about 310% at AX5. Nothing clips or overlaps. Layouts reflow (horizontal becomes vertical, fewer columns) instead of truncating. Never fixed heights for text.
7. **Contrast.** 4.5:1 for normal text and 3:1 for large text (18 pt+, or 14 pt bold). 3:1 for icons, control borders and focus indicators (WCAG 1.4.3, 1.4.11). Check light, dark and high-contrast modes.
8. **Never color alone** (WCAG 1.4.1). Errors get an icon plus text. Status chips get a label. Charts get patterns or labels.
9. **Gesture alternatives.** Swipe, long-press, drag and multi-finger actions have a visible alternative and a custom accessibility action.
10. **Focus and order.** Reading and focus order follow the visual order. After navigation, focus lands on the new screen's title. After an error, focus moves to the first invalid field. Sticky bars never hide the focused element (WCAG 2.4.11).
11. **Announce changes** that happen without user focus: "Added to cart", "3 results", "Order status: on the way". Use them sparingly.
12. **Motion.** Honor Reduce Motion / Remove animations. No flashing more than 3 times per second. Autoplaying motion can be paused.
13. **Time.** No time limits without a way to extend them. Don't auto-dismiss messages that contain actions too fast. OTP resend timers are fine; session timeouts warn first.
14. **Authentication.** No cognitive tests. Allow paste, autofill and password managers (WCAG 3.3.8). Offer OTP autofill.
15. **Forms.** Persistent visible labels, specific errors tied to the field, no repeated entry (WCAG 3.3.7), and help in a consistent place (WCAG 3.2.6).

## The settings matrix (test each)

| Setting | iOS | Android | What breaks |
|---|---|---|---|
| Largest text | Larger Accessibility Sizes, AX5 | Font size max plus Display size max | Clipping, overlap, fixed heights, hidden buttons |
| Bold text | Bold Text | Bold text | Custom fonts that ignore it |
| Screen reader | VoiceOver | TalkBack | Unlabeled icons, bad grouping, swipe-only actions, focus traps |
| Switch / keyboard | Switch Control, Full Keyboard Access | Switch Access, keyboard / D-pad | Gesture-only actions, invisible focus |
| Voice control | Voice Control | Voice Access | Accessible names that differ from visible labels |
| Reduce motion | Reduce Motion | Remove animations | Parallax, zooms, bounce, loops without a fallback |
| Transparency | Reduce Transparency | n/a | Custom glass or blur that loses contrast |
| Contrast | Increase Contrast | Contrast level (Android 14+), High contrast text | Thin borders, light gray text |
| Color filters | Differentiate Without Color, Smart Invert | Color correction, inversion | Color-only meaning, inverted photos |
| Dark mode | Dark | Dark theme | Hard-coded colors, invisible icons |
| RTL | Right-to-left pseudolanguage | Force RTL layout (developer options) | left/right instead of start/end, unmirrored arrows |

## Screen reader script (5 minutes per screen)
1. Turn the reader on and land on the screen. Is the title announced first?
2. Swipe through every element. Does each have a name, a role and a state? Is anything read twice, or is junk read ("image", "button button")?
3. Activate the primary action by double-tap. Does the result get announced?
4. Trigger an error. Is it announced, and does focus move to the problem?
5. Try every swipe or long-press feature through the actions rotor/menu.
6. Open and close a sheet or dialog. Is focus trapped inside while it's open, and does it return to the trigger afterwards?

## Content and cognition
- Plain language, short sentences, one task per screen, chunked long forms with progress.
- Keep critical information on screen; don't rely on memory across steps.
- Consistent placement and naming of navigation and help across screens.
- Captions or transcripts for essential video and audio. Visual and haptic alternatives for sound cues.
- Older users (NN/g, 65+ research): larger targets and text, plain words, visible labels, fewer gestures. Test with them directly.
- Low literacy or second-language users: icons with labels, photos of items, numeric input where possible, no abbreviations.

## Automated and manual tools
- **iOS:** Accessibility Inspector audit, Xcode previews with Dynamic Type and contrast variants, VoiceOver on a device, XCUITest `performAccessibilityAudit()`.
- **Android:** Accessibility Scanner, TalkBack, Compose UI tests with semantics matchers (`onNodeWithContentDescription`, `assertHasClickAction`), Android lint accessibility checks, `ComposeTestRule` with large font scale.
- **Flutter:** `SemanticsDebugger`, `meetsGuideline(androidTapTargetGuideline / iOSTapTargetGuideline / textContrastGuideline / labeledTapTargetGuideline)` in widget tests.
- **React Native:** test props (`accessibilityLabel`, `role`) with Testing Library `getByRole` / `getByLabelText`; test with the real readers.

Automated checks catch only about 30–40% of issues (verify). Always do the manual screen-reader script on the main flows.
