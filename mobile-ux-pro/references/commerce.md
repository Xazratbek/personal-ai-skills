# Commerce, ordering, checkout and tracking

For apps that sell or book anything: food delivery, restaurants, retail, tickets, services. The examples use a food-ordering app; the rules generalize. Data: Baymard checkout research (2025), NN/g status-tracker guidelines, MeasuringU food-delivery benchmark, tipping studies.

## Why this matters
- Average cart abandonment is about 70%.
- Reasons people abandon checkout (Baymard, excluding "just browsing"):

| Reason | Share |
|---|---|
| Extra costs too high (delivery, fees, tax) | 40% |
| Delivery too slow | 20% |
| Didn't trust the app with card details | 19% |
| Account creation required | 18% |
| Checkout too long or complicated | 17% |
| Errors or crashes | 17% |
| Couldn't see the total up front | 12% |
| Card declined | 10% |
| Not enough payment methods | 9% |

- Checkout design changes alone can lift conversion by up to 35% on large sites (Baymard).

## Browse and decide
- **Availability first.**
  - Show open/closed status, delivery availability for the user's address, minimum order, delivery fee and ETA range on store cards before people browse deeply.
  - Unclear open/closed status was a top complaint in food-delivery usability benchmarks.
- **Menu or catalog structure:**
  - Sticky category chips or tabs synced with scroll position.
  - Search with typo tolerance and cross-script matching.
  - Filters as visible chips (dietary, price, rating, delivery time).
- **Item cards:**
  - A photo (consistent ratio, designed placeholder if missing), name, a short description, price, and a key badge (spicy, vegetarian, popular).
  - An "Add" button with its own 48 dp target.
  - Never truncate the price or allergens.
- **Item detail and customization:**
  - Required choices first and clearly marked ("Choose size, required").
  - Optional extras after them, with price deltas shown ("+5 000 so'm").
  - A running total on the CTA ("Add to cart · 52 000 so'm").
  - A special-instructions field ("No onions").
  - The quantity stepper has large +/- buttons.
- **Allergen and dietary info** is accessible and never hidden behind a tap that people won't make. Misinformation here is a safety issue.

## Cart
- **Persist the cart** across app restarts and, when signed in, across devices. Never lose it on a network error.
- **Show availability changes clearly:** "1 item is no longer available. Remove it or choose a replacement".
- **Adding from a second restaurant** (if orders are single-store): ask clearly ("Start a new order? Your cart from Rayhon will be cleared") with "Keep current cart" as the safe option.
- **Make the cart reachable from everywhere:** a persistent cart bar with item count and total at the bottom of store screens, or a badge on a tab or toolbar icon.
- **Edit in place:** quantity steppers, swipe-to-remove with Undo plus a visible remove button.
- **Upsell lightly:** one "Add a drink?" row or a few suggestions, never a modal interruption.

## Cost transparency (the biggest lever)
- **Show every cost before the last step:** item subtotal, delivery fee, service fee, small-order fee, taxes, discounts.
- **No new fees on the review screen.** Hidden or drip-priced fees are the number one abandonment reason and a dark pattern.
- **Put the total on the sticky CTA** at every step ("Checkout · 84 000 so'm").
- **Explain fees** with a short info row ("Service fee helps run the app"), not a buried policy.
- **Free-delivery thresholds:** show the progress ("Add 12 000 so'm more for free delivery"). Never fake it.

## Checkout
- **Guest checkout or lightweight identity.** Phone plus OTP at checkout beats forced registration. Keep the guest option prominent.
- **As few steps as possible.** Address, then time, then payment, then review on one scrolling screen with smart defaults is usually best for repeat users.
- **Address:**
  - GPS pin with map confirmation plus text search.
  - Fields for entrance, floor, apartment, intercom code and courier notes.
  - Saved, labeled addresses (Home, Work).
  - Confirm the address on the final step with a mini-map.
- **Delivery time:**
  - Show a concrete range ("18:40–18:55"), not "fast".
  - For scheduled orders, show slots with the nearest one preselected.
  - Show cutoffs as a countdown ("Order in the next 25 min for lunch delivery"). 83% of sites miss this.
- **Payment methods:**
  - Offer what the market uses. Preselect the last-used or most common method.
  - Change the CTA label when the method redirects ("Continue to Payme").
  - 10% of shoppers abandon when their preferred method is missing.
  - Uzbekistan example (verify availability and SDKs before building): cash or card on delivery, Uzcard and Humo cards, Payme, Click, Uzum. Apple Pay / Google Pay availability varies by country.
- **Card entry:**
  - Number pad, auto-format in 4-digit groups, auto-detect brand, Luhn check, expiry formatted like the card.
  - Card scanning where available.
  - Tokenized saving with consent. Never store raw card data.
- **Trust cues:** recognizable payment logos, a "Secure payment" note, a visible cancellation/refund policy, a support contact.
- **Keep Pay visible.** The primary Pay / Place order button is visible without scrolling on the payment step.
- **Double-submit protection:** disable the button on tap, show progress inside it, and use an idempotency key on the server so retries never create duplicate orders or charges.
- **Payment failures:** a specific reason and next step ("Card declined by the bank. Try another card or pay with cash"). Keep all other entered data.
- **Promo codes:** a collapsed "Add promo code" row so people don't leave to hunt for codes. Show the discount immediately in the total.

## Tipping
- **No pre-selected high default.**
  - A 13M-ride taxi study found higher suggested tips raised the odds of zero tip by more than 50% (reactance).
  - Highlighted defaults raise tips but make users feel manipulated.
- **Options:** a few round or percentage choices, a clear "No tip" and "Custom".
- **Explain where the tip goes** ("100% goes to your courier").
- **Allow tipping after delivery,** when the experience is known. Make it part of the rating step.

## Confirmation and tracking
- **Confirmation screen:** order number, ETA range, itemized total, address and payment method, a "Track order" button, and help or contact. Send the same information by push or SMS with a deep link.
- **This is a peak moment:** a short success animation, a success haptic, a clear next step. Ask for notification permission here if you haven't ("Get live updates when your courier is on the way?").
- **Status tracker** (NN/g):
  - The latest status first, in plain language with a time: placed, restaurant confirmed, preparing, courier assigned, picked up, arriving, delivered.
  - A dated history below.
  - A live ETA that updates honestly (under-promise).
  - A courier map, name and call/chat once assigned.
  - Consistent across app, push and SMS.
- **Live tracking surfaces:** a Live Activity / Dynamic Island on iOS and a Live Update (`ProgressStyle`) notification on Android 16+ for the active order. A persistent "Active order" pill in the app (tab bar accessory on iOS).
- **Problems:** a clear "Something wrong with your order?" path with item-level reporting and photos. Resolve with refund or credit in a few taps, not a support maze.

## After the order
- **Rating:** quick and optional, right after delivery. Rate food and delivery separately. Ask for the app-store rating only after a positive in-app rating, never after a complaint.
- **Reorder:** one-tap reorder from history and from a home-screen shortcut or widget. Clearly name anything unavailable or repriced.
- **Favorites and recents** pinned on the home screen for repeat users.
- **Receipts:** downloadable and shareable, in the user's language.

## Loyalty, subscriptions and promotions
- Show the price, the renewal date and how to cancel before purchase. Cancel in as few steps as sign-up. Remind before renewal.
- Digital subscriptions sold in-app follow store billing rules (Apple In-App Purchase 3.1.x; Google Play Billing). Physical goods and food delivery do not use In-App Purchase.
- Points, credits and progress are visible and explained. Credits shouldn't silently expire.
- Promotions are honest: no fake countdowns or scarcity, no pre-checked add-ons, no confirmshaming ("No thanks, I like paying more").

## Review checklist (commerce)
- [ ] Store open/closed, ETA, fees and minimum are visible before browsing deeply.
- [ ] Price and allergens are never truncated. Required options are marked. Totals update live.
- [ ] The cart persists and is reachable from everywhere.
- [ ] All fees are visible before the final step. The total is on the sticky CTA.
- [ ] Guest or OTP checkout. Smart defaults for address, time and payment.
- [ ] Pay is visible without scrolling, double-submit is protected, and the request is idempotent.
- [ ] Payment errors are specific and keep data.
- [ ] Tip: no high default, "No tip" available, the option to tip after delivery.
- [ ] The confirmation has a number, ETA and tracking link. Tracking is plain-language, deep-linked, and shows live ETA and courier contact.
- [ ] Reorder in one tap. Rating prompts only after positive moments.
