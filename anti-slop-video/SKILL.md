---
name: anti-slop-video
description: Guard against generic "AI slop" when making or reviewing any video, Reels/TikTok/Shorts, motion graphics, product/app promo, ad, voiceover script, storyboard, captions or social marketing content. Use it BEFORE writing a script or design direction and again as a pre-release QA before delivering anything. Make sure to use this skill whenever the user asks for a video, reel, promo, ad, animation, motion design, launch film, voiceover, captions or "make it better/more professional/premium", whenever they mention "AI slop", "looks AI-made", "generic", "template-y", "robotic voice", or when you are about to produce several similar videos in a batch (batches are where slop creeps in), even if they never say the word slop.
---

# Anti-slop video

"AI slop" is content that could be about anything: a swappable script, a default purple-blue gradient, glass cards, silky weightless motion, a metronome TTS voice, the same hook and ending every time. Viewers (and ad platforms) read it in two seconds and scroll. Your job is to make work that is *specific to this product, city and audience*, and to prove it before delivering.

Why these rules exist: generators drift to the most common pattern in their training data. Every default you accept (palette, font, hook, easing, ending line) is the slop. Specificity, imperfection and variation are what read as made-by-a-person.

## Workflow

1. **Brief before building.** Write down (3–6 lines): who exactly watches, the one concrete situation, the hook archetype, the 2–3 specific details (place, time, number, real UI state), the look (palette + type + one distinctive visual idea), the unique closing line. If you cannot name a detail only *this* product/city has, you are not ready to write.
2. **Build with the rules below.**
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

**Captions** — readable, not template. Short phrases (≤ 2 lines), word-level highlight timed to speech, safe zones (platform UI covers roughly the top 220 px and bottom 420 px of 1080×1920), good contrast on busy backgrounds.

## Reference files
- `references/tells.md` — the research-backed list of slop tells with sources; read it when you need to explain a rule to the user or add a new one.
- `references/qa-checklist.md` — the pass/fail gate to run before every delivery (copy it into your reply as a table with ✓/✗ per item).
- `scripts/lint_copy.py` — run on script files (JSON `{id:{"lines":[...]}}` or plain text, one video per file): flags banned phrases, duplicate openers/endings across a batch, metronome line lengths, missing specifics, exclamation spam. Usage: `python scripts/lint_copy.py content.json [more files]`.
