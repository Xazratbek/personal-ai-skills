# Store rules, quality bars and UX process

What gets apps rejected, what gets them demoted, and how to know the UX works. Verified 2026-10-17. Policies change often, so check the live pages before a release:
- https://developer.apple.com/app-store/review/guidelines/
- https://developer.apple.com/news/upcoming-requirements/
- https://support.google.com/googleplay/android-developer (Policy Center)

## App Store review items that hit UX
- **2.1 Completeness:**
  - No crashes, placeholder text or dead links.
  - A working demo account in the review notes. Backend live during review.
- **2.3 Accurate metadata:** screenshots show the real app. Accessibility Nutrition Labels must be truthful.
- **4.0 / 4.2 Design and minimum functionality:** more than a wrapped website or a link collection. Native, useful, polished.
- **4.8 Login services:** if you offer third-party or social login for the primary account, also offer an equivalent privacy-focused option (name and email only, private email relay, no ad tracking). Sign in with Apple qualifies.
- **5.1.1(v) Account deletion:**
  - If accounts can be created in the app, deletion must start in the app (Settings > Account), not by email or phone.
  - Deactivation alone isn't enough. Re-authentication is allowed.
  - Revoke Sign in with Apple tokens.
  - Explain what happens to active subscriptions.
  - Don't require login for apps without significant account-based features.
- **5.1.1 Permissions:** purpose strings that fully describe the use. Alternatives when people decline. Prefer out-of-process pickers.
- **5.1.2:** core features must not depend on tracking, location or notifications.
- **4.5.4 Push:** not required to use the app. No promotions without opt-in.
- **3.1.1 / 3.1.2 In-App Purchase:**
  - Digital content and subscriptions use IAP. Physical goods and real-world services (food, rides) don't.
  - Subscriptions: describe what users get before the subscribe button, and offer restore.
- **1.5:** a working support URL and contact.
- **SDK:** build with Xcode 26 / the iOS 26 SDK or later. With the iOS 27 SDK, UIKit apps must use UIScene.

## Google Play items that hit UX
- **Target API 36** for new apps and updates (since 2026-08-31). Existing apps below API 35 lose visibility on newer devices.
- **Account deletion:** a prominent in-app deletion path plus a web link for deletion requests, declared in the Data safety form. Deletion removes associated data except legally required data, which must be disclosed.
- **Data safety:** required for every app, including data collected by SDKs and WebViews. Mismatches block updates or remove the app.
- **Permissions:**
  - `READ_MEDIA_IMAGES/VIDEO` only when the Photo Picker can't serve the core function, with a declaration.
  - From 2027-01, apps targeting 37+ need declarations for broad contacts or fine location where pickers or the location button would do (verify the date in Play's policy announcement).
  - Foreground service types must be declared.
- **16 KB page size:** native code must be 16 KB aligned, or updates are blocked from 2027-02-01.
- **Android vitals bad-behavior thresholds** (lower visibility plus a store warning):
  - User-perceived crash rate above 1.09%.
  - ANR rate above 0.47%.
  - Either one above 8% on any single phone model.

## Quality bars to hold yourself to
- **Stability:** at least 99.5% crash-free users and well under Play's thresholds. Checkout and payment paths get top priority, because 17% of shoppers abandon after an error or crash.
- **Startup:** a cold start shows meaningful content in under about 2 s on a mid-range device. Android's "excessive" cold start is 5 s or more. Track TTID/TTFD (Android) and launch time (Xcode Organizer / MetricKit).
- **Smoothness:** no frozen frames (over 700 ms). Keep slow frames rare on scroll-heavy screens. Measure release builds on a low-end device.
- **Size and data:** keep the download small (AAB, app thinning, no bloated assets). Respect metered data.
- **Accessibility:** pass the screen-reader script and the settings matrix (`accessibility.md`) on the main flows before release.

## Rating prompts
- **Apple `requestReview`:** the system shows it at most 3 times in 365 days, and it may not show at all. Never call it from a button tap ("Rate us" buttons should deep-link to the App Store write-review page instead).
- **Google Play In-App Review:**
  - Trigger it after the user has experienced value.
  - No pre-question ("Do you like the app?"), no custom button that triggers the API, no modifying the card.
  - The quota is undocumented, so a call may show nothing.
- **Good moments:** right after a successful order is delivered, after a positive in-app rating, after a repeat success.
- **Bad moments:** first session, mid-task, after an error, refund or complaint.
- **Route unhappy users to in-app feedback or support,** not to the store.

## Release safety
- Feature flags and remote config for risky UI changes. Staged rollouts (for example 1%, 10%, 50%, 100%) with a halt on crash or ANR regressions.
- A kill switch or forced-update path for critical bugs. Make the forced-update screen honest and minimal.
- Keep a changelog that users can read ("What's new"). Never use update prompts for marketing.

## UX research process
- **Test with 5 users per round** (NN/g): about 85% of problems surface. Run several small rounds (test, fix, test) rather than one big study. With distinct groups (customers, couriers, restaurant staff), test 3–4 people per group.
- **Test in realistic conditions:** real devices including a low-end Android phone, outdoors in sunlight, one-handed, on a slow network, with large text, in each supported language.
- **Analytics funnel:**
  - Instrument the main path (open, browse, item, add to cart, cart, address, payment, order placed, delivered, rated).
  - Segment by platform, device tier, network, language, and new versus returning users.
  - Track errors per step and time to first content.
- **Pair numbers with "why":** session recordings (privacy-safe), interviews, support tickets, store reviews.
- **Error patterns:** if the same validation error happens to many users, treat it as a design bug, not a user mistake.
- **Keep a UX debt list.** Re-audit critical flows (onboarding, checkout, tracking) every release with `review-checklist.md`.
