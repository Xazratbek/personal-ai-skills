---
name: anti-slop-video
description: Guard against generic "AI slop" when making or reviewing any video, Reels/TikTok/Shorts, motion graphics, product/app promo, ad, voiceover script, storyboard, captions or social marketing content. Use it BEFORE writing a script or design direction and again as a pre-release QA before delivering anything. Make sure to use this skill whenever the user asks for a video, reel, promo, ad, animation, motion design, launch film, voiceover, captions or "make it better/more professional/premium", whenever they mention "AI slop", "looks AI-made", "generic", "template-y", "robotic voice", or when you are about to produce several similar videos in a batch (batches are where slop creeps in), even if they never say the word slop.
---

# Anti-slop video

"AI slop" is content that could be about anything: a swappable script, a default purple-blue gradient, glass cards, silky weightless motion, a metronome TTS voice, the same hook and ending every time. Viewers (and ad platforms) read it in two seconds and scroll. Your job is to make work that is *specific to this product, city and audience*, and to prove it before delivering.

Why these rules exist: generators drift to the most common pattern in their training data. Every default you accept (palette, font, hook, easing, ending line) is the slop. Specificity, imperfection and variation are what read as made-by-a-person.

## Workflow

1. **Brief before building.** Write down (3–6 lines): who exactly watches, the one concrete situation, the hook archetype, the 2–3 specific details (place, time, number, real UI state), the look (palette + type + one distinctive visual idea), the unique closing line. If you cannot name a detail only *this* product/city has, you are not ready to write.
2. **Get the concept approved cheaply** (one-page brief/styleframes; contact sheet before the full render — see `pro-video-production` → Approval loop), then **build with the rules below.**
3. **Run the QA gate** (`references/qa-checklist.md`) and the copy linter (`scripts/lint_copy.py`). Fix every failure; do not deliver with known fails.
4. **Say honestly what you could not verify** (e.g. you cannot hear audio; stills are not motion). Ask for one outside viewer pass: "does anything feel fake or AI-made?"

## Rules (the why in one line each)

**Script & structure** — slop is modular.
- One hook *archetype* per video, varied across a batch: story/POV, countdown/time pressure, pain statement, myth-busting, mini-tutorial, sensory moment, challenge, empathy, question, how-to-count. Never the same opener twice in a batch.
- Every script has concrete specifics (district names, clock times, "7 of 10", route length) taken from the real product, not invented stats. No fake user counts, awards or testimonials.
- The closing line is different in every video of a batch (same CTA info, different words and rhythm). Identical endings are the loudest template tell.
- Banned hype/filler (any language): revolutionary, unique, innovative, best, incredible, game-changing, ecosystem, seamless, unlock, "in today's fast-paced world"; Russian: революционный, уникальный, инновационный, лучший, невероятный, прорыв, экосистема; Uzbek: noyob, ajoyib (as filler), eng yaxshi. State a checkable fact instead.
- Mix sentence lengths. Short fragments, a question, one long line. Equal-length lines = metronome.

**Visuals** — slop is the default aesthetic.
- No purple/violet→blue gradients, blurred glow blobs, cyan-on-dark, glassmorphism pills, gradient text, emoji in headlines, three-icon feature grids, everything centered. Use a brand-specific palette chosen for a reason (a city, a culture, the product), flat colour fields, bold geometric shapes, hard-offset shadows, film grain, asymmetric layouts.
- Fonts: pick for the language (Cyrillic/Latin-ext coverage) and character; avoid unconsidered defaults. One display face + one accent face is plenty. Real hierarchy: huge/small contrast, tight tracking on headlines.
- Show the real product (actual UI captured at device resolution, real route/map data) instead of redrawn rectangles; use real photography for people (licensed stock/own shoots). Never generate faces/hands. Avoid in-scene gibberish text.
- Each video of a batch gets its own dominant colour and layout (device position/angle, camera path) inside one consistent system.

**Motion** — slop is mathematically smooth.
- Weight and imperfection: anticipation, overshoot, settle; organic hand-held drift from several incommensurate sine frequencies; varied stagger and easing; camera moves that differ scene to scene and are motivated by what appears on screen. Camera and elements do not move on the same beat everywhere.
- Rhythm: vary shot length (≈1–8 s), hold for emphasis, cut/move on audio accents, at least four distinct compositions and one deliberate camera move per video. Subtle grain over everything.
- Frame-check for flicker, morphing, jumps, dead frames (>0.5 s with nothing moving).

**Voice & sound** — slop is the "TTS plateau".
- **Use the `anti-slop-voice` skill for every voiceover.** Short version: native-language modern model, one locked brand voice cloned for every line, generated at the target pace (≈150–170 wpm for Reels). Never resample/time-stretch lines for "variation" and never paste synthetic noise breaths — both make the voice sound slowed-down and metallic. Light studio chain, punctuation-aware gaps, constant room tone, real foley (tap click, whoosh, notification chime) synced to on-screen events, music ducked under voice, −14 LUFS integrated.
- Hard-to-read words get phonetic spellings in the *spoken* text only (keep the caption spelling): e.g. IELTS → "айэлтс", speaking → "спикинг". Run every line through an ASR round-trip and re-synthesise lines that don't match.
- Never say the brand/bot name if the user said not to; point to "link in profile/description" instead.

**Transition sounds — no whoosh carpet.** A noise "shuu / shirr" on every cut or text entrance is one of the loudest template tells and, by the client's own words, gets on people's nerves. Rules:
- At most one or two noise whooshes per video, and only on a genuinely big physical move (a device flying in). Never on text, captions, screen changes or every scene start.
- Default transition sounds are **tonal and soft**: a mallet/marimba note in the music's key (pentatonic so anything fits), a muted wood tap, a low soft thump with no click, a small bell on a success moment, a note from the music itself, or simply silence on the cut. Keep them −20…−30 dB under the voice.
- Library sounds: audition before use; prefer soft organic UI sets (Kenney UI/Interface — CC0; Google Material Design sound resources — CC BY 4.0, credit them) over "cinematic whoosh" packs.

**Script humanizer (do this pass on every script, every language).** AI copy gives itself away with punchy fragment chains copied from English ad templates ("Zero. Not a cent." → "Har buyurtmadan foiz — nol. Bir so'm ham.") that a native speaker would never say. Before voicing:
- Each sentence is a complete thought in natural word order for the language (Uzbek/Turkic: verb at the end; Russian: no calques from English). No dangling dashes or one-word sentences unless a person would really say them.
- Say it the way the target viewer talks to a colleague: "Buyurtmalardan foiz olmaymiz — umuman." instead of "Foiz — nol. Bir so'm ham."; "Mijoz botdan buyurtma beradi" instead of "Buyurtma — botda."
- Read every line aloud; if it sounds like a slogan or a translation, rewrite it. Ask the person (native speaker) to read the script once before the voice is generated.
- Keep facts exact while simplifying wording (prices, tariffs, what is in which plan).

**Quality is non-negotiable.** Every video ships at full quality: native resolution (1080×1920 / 1920×1080 or higher), the agreed frame rate (60 fps if promised), full motion-blur sub-frames, high-quality encode (x264 `-preset slow -crf 17–19`, AAC 256k). Never lower sub-frames, resolution, fps, bitrate or effects to make a render finish sooner — if it is slow, parallelise, run it detached and wait, or ask the person first. A shortcut the person did not approve is a broken deliverable.

**Layout: text never collides with anything.** Reserve a text zone (e.g. the top band below the platform's safe area) and keep heroes (device, cards, characters, decorative dots/balls) out of it while text is on screen; nothing passes over or under a caption, and a decorative element never sits on top of a word. Check it automatically: register every drawn element's bounding box per frame as "text" or "hero" and fail the render on any intersection (sample every 1/30 s). Display type: set explicit line breaks and a no-break space before a dash, so the layout never wraps a word or a lone dash onto a line you did not design.

**2.5D depth must be believable.** Don't thread a flat object through a ring/loop or fan several copies of the same device around it — fake depth sorting and interpenetrating copies read as broken. Shadows come from the object's real silhouette (alpha, blurred, offset with the lift), never from the image's bounding rectangle or a hard-edged offset quad (that shows up as a grey card behind a phone). An element lifted off a screen leaves its spot empty (screen background colour) so it reads as one object that moved, not a duplicate.

**When the person dislikes the execution, change the visual approach**, not only the bug they pointed at: if one idea produced several defects, rebuild the sequence with a different device (e.g. UI elements breaking out of the screen, colour-block wipes, kinetic type) and re-run the whole QA.

**Captions** — readable, not template. Short phrases (≤ 2 lines), word-level highlight timed to speech, safe zones (platform UI covers roughly the top 220 px and bottom 420 px of 1080×1920), good contrast on busy backgrounds.

**Batch ledger** — slop also lives *between* videos. Keep a table per batch: hook archetype, dominant colour, signature device/visual idea (receipt printer, odometer clock, chat thread, light line…), camera signature, closing line, music genre/tempo. A device reused in a second video of the same batch (e.g. the same "zero fee" stamp on a receipt in two videos) reads as a template even when every single video passes on its own.

**Devices and product proof**
- Never draw a phone, tablet or laptop by hand. Use the maker's real device frames (Apple Design Resources → Product Bezels for iPhone/iPad; read their licence — mock-ups only, no redistribution: a private project repo may hold the PNGs so anyone on the team can render, never a public repo — there, ship a download script) and composite the real screen *under* the bezel, aligned to the measured screen opening, with the bezel's own Dynamic Island.
- Capture screens at the device's own point size (iPhone 17 Pro: 402×874 pt @3x) with the platform chrome you would really see (status bar, Telegram web-app header), fixed clock/time zone and the right UI language.
- Real proof beats claims: crop the client's own pricing card, steps section or trial banner from their site and show it; verify every fact against the *current* source (code, live page) — old assets go stale (a social preview image still said "14 days free" when the product gave 30).
- Before any capture goes into a video, scan it for personal data and phone numbers (crop or re-frame) and say on screen that demo data is sample data.

**Captions that are part of the world** — instead of a template caption bar, let the product carry the words: chat bubbles whose words darken as they are spoken, kinetic type chunks of 2–4 words that replace each other, a receipt line that prints. One text layer per moment; the hook text is fully readable at frame 0 (no karaoke on the opening line).

**Paid ads (Reels/Stories ads)** differ from organic Reels:
- The message is already on frame 0 (call-out or offer), brand visible within 3 s, sound-off readable (burned-in word captions), one offer, one CTA that points at the platform's own button ("press the button below").
- Ad safe zones are stricter: keep key content out of the top ≈14 % (270 px) and bottom ≈35 % (670 px) of 1080×1920, and ≈6 % at the sides.
- 9:16, 12–20 s, a hard visual change every 2–4 s (flat colour fields, wipes), language variants composed per language (text length differs), not subtitled copies.

**Covers and frame 0** — never splice a different "poster" frame in as frame 0 (it flashes for one frame and the next frame looks different); make frame 0 a good cover, or deliver a separate cover image for upload.

**Ask, don't assume, what the ending says** — the domain/brand on the end card must be the one the client wants (an umbrella brand vs. a sub-product domain), and the CTA must match how sign-up really works (application vs. self sign-up).

## Reference files
- `references/tells.md` — the research-backed list of slop tells with sources; read it when you need to explain a rule to the user or add a new one.
- `references/qa-checklist.md` — the pass/fail gate to run before every delivery (copy it into your reply as a table with ✓/✗ per item).
- `../pro-video-production/scripts/motion_qa.py` — frame-difference check for dead frames (> 0.5 s) and jumps; run on every render.
- `scripts/lint_copy.py` — run on script files (JSON `{id:{"lines":[...]}}` or plain text, one video per file): flags banned phrases, duplicate openers/endings across a batch, metronome line lengths, missing specifics, exclamation spam. Usage: `python scripts/lint_copy.py content.json [more files]`.
