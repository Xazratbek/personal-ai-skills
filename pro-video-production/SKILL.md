---
name: pro-video-production
description: Universal end-to-end guide for making short-form and launch videos that look and sound made by a professional human, not AI slop — Reels/TikTok/Shorts, product promos, app demos, launch films, 9:16 and 16:9. Covers brief, spoken script, AI voiceover (one continuous take), music and SFX, look, motion, captions, rendering, QA and delivery, with field-tested failure modes. Use whenever you plan, script, voice, build, render, review or deliver any video, choose a TTS engine or voice, or when someone says a video or voice feels robotic, AI-made, slow, flat, cheap, template-like or "slop" — even if they can't say exactly why.
---

# Professional video production (anti-slop)

Viewers decide "this is AI" within two seconds, and the decision is triggered by a small set of specific tells — most of them introduced by *our own pipeline defaults*, not by the model. The person you work for often can't name the defect ("hard to put into words"); this skill turns those vague verdicts into concrete causes. It folds together `anti-slop-video` and `anti-slop-voice` plus lessons from a real batch that was rejected four times before it was approved.

## Quality bar (non-negotiable)
Every delivered video is full quality: native resolution, the agreed frame rate, full motion-blur sub-frames on fast moves, a high-quality encode (x264 `-preset slow -crf 17–19`, `yuv420p`, AAC 256k, `+faststart`). **Never trade quality for render time** — no fewer sub-frames, lower resolution/fps/bitrate, dropped effects or "draft" encodes in a deliverable — unless the person explicitly approves it. If a render is slow: parallelise (frame segments across cores), run it detached, schedule follow-ups, and say how long it will take.

## Workflow

1. **Brief before building** (3–6 lines): who watches, the one concrete situation, the hook archetype, 2–3 specifics only this product/place has (names, times, numbers, real UI states), the look, a unique closing line, and the format(s) (9:16, 16:9, 1:1). If you cannot name a specific detail, you are not ready to write. For a spec ad or anything with a client brief template, write it to a file (`brief/PROMPT.md`: concept, beat sheet with timings, script, voice, music, SFX plan, assets list with licences) — see `references/spec-ad.md`.
2. **Write for the ear** — see Script rules. Lint: `python scripts/lint_copy.py script.json`.
3. **Decide on voice at all.** Launch films, logo stings and UI showcases often work better with music + precise SFX and on-screen type only. A voice is for explaining or storytelling; a bad voice costs more than no voice.
4. **Voice (if any)** — see Voice rules. Get one human listen on the first finished take of each new voice before batch-producing.
5. **Build the picture from the voice** — every scene start, caption word and SFX cue is computed from the take's word alignment ("re-time the picture to the voice, never the voice to the picture"), so a voice swap is a re-run. Real product footage/UI first; see Look and Motion rules.
6. **Mix and render**; long jobs detached from your session (see Ops).
7. **QA gate** `references/qa-gate.md` as a ✓/✗ table; state plainly what you measured vs. what a human heard/saw.
8. **Deliver**: send the file with its absolute path, delete superseded versions so nobody reviews an old cut, commit/push sources.

## Script rules
- **Humanize every script** (see `anti-slop-video` → Script humanizer): complete natural sentences in the language's own word order; no English-ad fragment chains ("Foiz — nol. Bir so'm ham."); native read-through before voicing.
- **Spoken, not written.** Polished ad lines ("One tap. You're in.") read as AI copy even with a perfect voice. Write how the target viewer talks to a friend: informal address when the audience is young, run-on sentences, a reaction, a fragment, a question. Read it aloud; if nobody would say it, rewrite it.
- One hook archetype per video, different across a batch: story/POV, countdown, pain, myth-busting, mini-tutorial, sensory moment, challenge, empathy, question, how-to-count, keynote parody.
- Concrete, checkable specifics; never invented stats, user counts, awards or testimonials.
- Closing line different in every video of a batch (same CTA info, new words).
- Banned hype/filler in any language (revolutionary, unique, innovative, best, incredible, game-changing, seamless, unlock, ecosystem, "in today's fast-paced world" and local equivalents).
- Mix sentence lengths; equal lines = metronome.
- Gendered languages: use gender-neutral constructions when the narrator's gender and the viewer's may differ.
- Keep the scene plan anchored to *words* of the script, and update it whenever the wording changes.

## Voice rules (details: `references/voice.md`)
1. **Native speaker of the target language**, licensed (a paid library/actor voice) or a consenting human reference. Never clone a real person's voice from the internet.
2. **Generate the whole script as one continuous take.** Line-by-line synthesis glued with gaps sounds like an announcer metronome *regardless of model quality* — this exact mistake made a premium voice indistinguishable from a cheap local clone to the listener. Take word/line timing from the engine's alignment (character timestamps) or ASR word timestamps.
3. **Leave a good take untouched**: one high-quality resample, nothing else. No EQ/compressor chain on premium output, no pause tightening, no tempo change, no per-line resample "variation", no synthetic breaths (both make speech sound slowed-down and metallic).
4. **Use the newest expressive model** — query the provider's model list; last year's best is often superseded.
5. **Audio/emotion tags sparingly** (≤1 per line, never on the first word). **No breathy or intimate tags** (sighs, tired, exhales, whispers, playful laughs) unless the content is meant to be intimate: a sigh before the first word of an ad was heard as a sexual moan.
6. **Pick by numbers, confirm by ear**: 3 takes, keep the best by ASR match (`difflib` with `autojunk=False`) and pace (Reels ≈150–170 wpm; 145–185 acceptable); reject takes with audible sound >0.2 s before the first word; then check the first word yourself in the transcript.
7. Phonetic spellings and stress marks in the *spoken* text only; captions keep real spelling.
8. Weak-ASR languages (e.g. Uzbek): ASR can catch wrong words but not accent — a native listener picks between numbered samples; write the language in its proper orthography (Uzbek ʻ U+02BB), test brand/domain respellings inside the full take. Details: `anti-slop-voice`.
9. Metrics are necessary, not sufficient: a clone with perfect flatness, pitch spread and ASR was still rejected for intonation. When the listener says "still AI", change the method (continuous take, better voice, human actor), not the EQ.

## Look rules
- No default AI aesthetics: purple/violet→blue gradients, glow blobs, cyan-on-dark, glassmorphism, gradient text, emoji headlines, three-icon grids, everything centred.
- A palette with a reason (place, culture, product), flat colour fields, bold geometry, hard-offset shadows, grain; one display face + one accent face chosen for the script's language coverage.
- Real product (captured UI at device resolution, real data) and real people/places (own or licensed footage). Never generated faces/hands, no gibberish text.
- Real devices, never hand-drawn: the maker's device frames (Apple Product Bezels) with the screen composited under the bezel at the measured opening; respect the licence (mock-ups only, no redistribution: a *private* project repo may hold the PNGs so the team can render; a public repo gets a download script instead). Device shadows come from the device's real silhouette (alpha), not the PNG rectangle.
- Fonts: check the licence for video/ads (SF Pro is licensed only for Apple-platform mock-ups) — prefer the brand's own fonts or OFL faces with full coverage of the script's language (Uzbek ʻ, Cyrillic).
- **Zones, checked by code.** A reserved text zone that heroes never enter while text is visible; nothing (device, card, decorative ball) passes over or under a caption. Register every element's box per frame and fail on text/hero intersections (`qa` pass at 30 samples/s) — eyeballing a contact sheet misses fast overlaps.
- **Believable 2.5D:** no flat object threaded through a ring, no fans of overlapping device copies; lifted elements cast soft alpha shadows and leave their spot empty on the screen.
- Display type: explicit line breaks and a no-break space before dashes so nothing wraps into a lone word or dash.
- **One text layer per moment.** Headline + kicker + sticker + karaoke caption at once is a template tell the viewer reads as "AI-made" even without naming it.
- Each video in a batch gets its own dominant colour, layout and device angle inside one system.
- 9:16 safe zones: keep key content out of the top ~220 px and bottom ~420 px of 1080×1920. 16:9 is not a stretched 9:16 — recompose for the wide frame (side-by-side UI, wider type, longer holds).

## Motion rules
- Weight and imperfection: anticipation, overshoot, settle; organic drift from incommensurate sines; easing and stagger varied; camera moves motivated by content and different scene to scene.
- Vary transitions (hard cut on a beat, match cut on a tap, whip, push) — the same entrance every scene is a tell.
- Shot lengths ≈1–8 s, cut on audio accents, ≥4 compositions, no dead frame >0.5 s, no flicker/morph/jump (`scripts/motion_qa.py`). Subtle grain over everything.
- **Motion blur that doesn't ghost text:** average sub-frames with a *tent* (triangular) weight, not a box — box-averaged text leaves two hard-edged copies. Use ≥12–16 sub-frames on fast moves (measure px/frame: ≥40 px/frame needs them), shutter 180–300°. Ease scrolls in-out (sine/cubic), not quint-out: an infinite start velocity smears the first frames.
- **Kinetic type**: chunks of 2–4 words that replace each other; each word lands on its spoken time; the outgoing chunk must be fully gone before the next word lands, or two text layers overlap. Cut word sprites from a render of that word alone (others hidden), never from the multi-line render — tight line-height makes crops catch the neighbouring line's letters.
- Continuous effects (glare sweeps, glows, gradients) are computed per frame from a continuous parameter; a small table of precomputed phases reads as stutter.

## Launch films
- Build the film from the product's own design language and real sounds (its notification/success sounds), not a stock UI montage; one deadpan joke or metaphor carried through.
- Deliver narrated **and** music-only versions, each composed for 9:16 and 16:9; the music-only cut is edited to the beat with on-screen type carrying every claim.
- Ship with each file: post copy (caption, hashtags, alt text, demo-data disclosure) and a cover, in a description file named after the video.

## Sound rules
- Music sits ≥15 dB under the voice *while words are spoken* (measure VO vs music RMS on voiced samples) and comes back up between sentences; with no voice, music carries the edit — cut to its beats. Lay the music grid so a downbeat lands on the biggest visual hit; cut it for a "drop" and restart on a new downbeat.
- Original music can be written in code when licensing matters (`references/music-in-code.md`): plucked strings (Karplus-Strong), pads, sub bass, drums, reverb — arranged around the cue list, ending on a chord that rings under the end card.
- Motivated SFX, but **no whoosh carpet**: noise whooshes on every title/cut annoy listeners and read as template. Use tonal soft sounds instead (mallet notes in the music's key, wood taps, soft thumps, bells on success), at most 1–2 real whooshes per video on a big physical move.
- Foley/SFX only on real on-screen events (tap click, whoosh on a move, chime on a notification, success on a confirmation); constant very low room tone removes digital silence.
- −14 LUFS integrated, true peak ≤ −1 dBTP for social delivery.

## Ops (long renders, limited sessions)
- Run render queues detached (`nohup setsid script &`) with a log; deliver results from a detached notifier (e.g. a bot that sends each finished file with its path) so work survives the session.
- Never `pkill -f <pattern>` from a command whose own text contains the pattern (it kills your shell); a watchdog that greps its own command line never exits. Match process names (`pgrep -x`).
- Don't edit a shell script while bash is running it.
- If you stop a system service to free CPU for a render, restore it with a `trap` *and* a detached guard.
- Ask before spending money (paid TTS tiers, stock) and before deleting; estimate API credits (characters × takes) before generating.
- **Make the project portable**: relative paths only (no `/home/<user>/…`), every render input (sprites, screenshots, fonts, device frames, voice takes, mixes as FLAC, final videos) in the project's private repo, one script that renders on another machine (`python -m venv .venv` + `pip install --isolated …` — a user pip config with `user = true` otherwise breaks venv installs). Keep render outputs and segment folders out of git; keep the repo out of the app's Docker build context (`.dockerignore`).
- Check external API keys/credits with one cheap call before a step depends on them, and report a failure immediately.
- Containers restart: before a capture session check that the local app servers are still up; keep capture scripts re-runnable.
- Playwright captures: write HTML to a temp file and `goto file://` (inline `setContent` won't load local fonts/images); element screenshots with transparent backgrounds by clearing the surrounding backgrounds; fix clock and time zone; the app's UI language may come from the user profile, not the browser locale.

## References
- `references/lessons.md` — field-tested failures: the viewer's words, the real cause, the fix.
- `references/voice.md` — engine selection, measured engine notes, continuous-take recipe (ElevenLabs example), tags, QC metrics.
- `references/qa-gate.md` — pre-delivery checklist.
- `references/tells.md` — research-backed list of AI-slop tells with sources.
- `references/spec-ad.md` — spec-ad brief template and standing rules (60 fps, 16:9 + 9:16, real assets, code music, dense SFX, end card).
- `references/music-in-code.md` — recipe for original music in numpy/scipy, arranged to the cue list, with ducking checks.
- `scripts/lint_copy.py` — script linter (banned phrases, duplicate openers/endings, metronome lines, missing specifics).
- `scripts/voice_qc.py` — voice metrics: spectral flatness, F0 spread, wpm, max pause, ASR match.
- `scripts/asr_check.py` — ASR round-trip (Scribe + whisper) with must-hear words (brand, domain, prices).
- `scripts/motion_qa.py` — dead frames (> 0.5 s) and jumps from frame differences.
