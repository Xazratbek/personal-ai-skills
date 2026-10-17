# Localization and international readiness

Build every app as if it will ship in three languages, because adding localization later means rewriting layouts and strings. Examples use Uzbekistan (Uzbek Latin, Uzbek Cyrillic, Russian), a demanding but common case. Items marked "(verify)" depend on CLDR data or the local market; check them.

## Strings
- **Every user-visible string lives in resources:** UI, errors, notifications, push payload templates (server-side), widget text, accessibility labels, App Store/Play listings.
  - iOS: String Catalogs (`.xcstrings`).
  - Android: `strings.xml` per locale.
  - Flutter: ARB with `intl`.
  - React Native: i18next or similar.
- **Never concatenate fragments** ("Delivered in " + n + " minutes"). Use full templates with placeholders, because word order and grammatical case change between languages.
- **Plurals through the platform:**
  - Android `plurals`, iOS String Catalog plural variants, ICU MessageFormat.
  - Russian needs one/few/many/other.
  - Uzbek uses the singular after numerals ("5 ta taom") (verify with CLDR).
- **Give translators context:** comments on every string (where it appears, maximum length, what the placeholders mean).
- **Native-speaker review is mandatory** for prices, allergens, legal text and error messages. A mistranslated allergen is a safety issue.

## Layout for text expansion
- **Plan for 30–40% growth** from English, and far more for short strings (a 4-letter English label can double).
  - English to Russian typically grows 20–30%.
- **Rules:**
  - No fixed-width buttons, tabs or chips.
  - Labels may wrap to two lines.
  - Use flexible layouts (`FlowRow` / `ViewThatFits`).
  - Test with pseudo-localization (Android `en-XA` for accents and expansion, `ar-XB` for RTL; iOS "Double-Length Pseudolanguage" and "Right-to-Left Pseudolanguage").
- **Combine tests:** the longest language plus the largest text size plus the smallest phone. That is where layouts break.

## Uzbekistan specifics (example)
- **Locales:** `uz-Latn-UZ` (Latin, the official modern script), `uz-Cyrl-UZ` (Cyrillic, still used, especially by older users), `ru-RU` / `ru-UZ`.
  - Android resource folders: `values-b+uz+Latn`, `values-b+uz+Cyrl`, `values-ru`.
  - iOS: `uz-Latn`, `uz-Cyrl`, `ru` in the String Catalog.
- **Language picker:** each language name in its own script ("Oʻzbekcha", "Ўзбекча", "Русский"), never flags. Default to the device locale and allow an in-app switch. On Android 13+, use the per-app language API so the system setting stays in sync.
- **Apostrophes:**
  - Uzbek Latin uses the modifier letter ʻ (U+02BB) in oʻ and gʻ, and ʼ (U+02BC) for the tutuq belgisi.
  - Users type ' ` ‘ ’ instead, so normalize all of them in search and input.
  - Make sure fonts render U+02BB properly.
- **Cross-script search:** a user typing "choyxona" should find "чойхона" and vice versa. Index names in both scripts or transliterate queries; Latin–Cyrillic transliteration is mostly mechanical, with exceptions to review.
- **Fonts** must cover Cyrillic plus the Uzbek letters Ў ў Қ қ Ғ ғ Ҳ ҳ and the Latin ʻ. Check that the fallback font doesn't change weight or metrics mid-word.
- **Formats** (use platform formatters, never hand-built strings):
  - Currency: UZS, written "so'm" (Latin) or "сўм" (Cyrillic), digits grouped with spaces ("84 000 so'm"). Prices usually have no decimals (verify against CLDR output).
  - Phone: +998 XX XXX XX XX.
  - Dates and times: dd.MM.yyyy, 24-hour time (verify with CLDR / `DateFormatter` output).
  - Addresses: districts (tuman), mahalla and landmarks are common in delivery directions. Give couriers a free-text "landmark / orientir" field.

## Formatting rules (all locales)
- Use the locale-aware formatters:
  - iOS: `.formatted()`, `FormatStyle`, `Measurement`.
  - Android: `NumberFormat`, `DateTimeFormatter`, `android.icu`.
  - Flutter: `intl`.
  - JavaScript: `Intl`.
- Dates, times and ETAs respect the user's time zone and 12/24-hour setting.
- Store money as integer minor units or decimals with an ISO currency code. Format at display time.
- Sorting and search use locale-aware collation.

## RTL readiness
Even if launch languages are left-to-right, make RTL possible:
- Use start/end, never left/right.
  - Android: `paddingStart`, and Compose `start`/`end`, which handle this automatically.
  - iOS: leading/trailing.
  - Flutter: `EdgeInsetsDirectional`.
  - React Native: `start`/`end` styles.
- Set `android:supportsRtl="true"`.
- Mirror directional icons (back, forward, progress, send). Don't mirror logos, media playback controls, clocks, or numerals' internal order.
- Test with the RTL pseudo-locale.

## Culture and content
- No text inside images. Avoid idioms and culture-specific jokes in core flows.
- Respect local holidays and business hours (Ramadan hours, Navruz) in availability logic and promotions.
- Provide support, legal and privacy text in every supported language.
- Localize store listings and screenshots. They are the first UI people see.
