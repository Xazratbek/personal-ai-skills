---
name: pro-video-production
description: Universal end-to-end guide for making short-form and launch videos that look and sound made by a professional human, not AI slop — Reels/TikTok/Shorts, product promos, app demos, launch films, 9:16 and 16:9. Covers brief, spoken script, AI voiceover (one continuous take), music and SFX, look, motion, captions, rendering, QA and delivery, with field-tested failure modes. Use whenever you plan, script, voice, build, render, review or deliver any video, choose a TTS engine or voice, or when someone says a video or voice feels robotic, AI-made, slow, flat, cheap, template-like or "slop" — even if they can't say exactly why.
---

# Professional video production (anti-slop)

Viewers decide "this is AI" within two seconds, and the decision is triggered by a small set of specific tells — most of them introduced by *our own pipeline defaults*, not by the model. The person you work for often can't name the defect ("hard to put into words"); this skill turns those vague verdicts into concrete causes. It folds together `anti-slop-video` and `anti-slop-voice` plus lessons from a real batch that was rejected four times before it was approved.

## Workflow

1. **Brief before building** (3–6 lines): who watches, the one concrete situation, the hook archetype, 2–3 specifics only this product/place has (names, times, numbers, real UI states), the look, a unique closing line, and the format(s) (9:16, 16:9, 1:1). If you cannot name a specific detail, you are not ready to write.
2. **Write for the ear** — see Script rules. Lint: `python scripts/lint_copy.py script.json`.
3. **Decide on voice at all.** Launch films, logo stings and UI showcases often work better with music + precise SFX and on-screen type only. A voice is for explaining or storytelling; a bad voice costs more than no voice.
4. **Voice (if any)** — see Voice rules. Get one human listen on the first finished take of each new voice before batch-producing.
5. **Build the picture** — see Look and Motion rules; real product footage/UI first.
6. **Mix and render**; long jobs detached from your session (see Ops).
7. **QA gate** `references/qa-gate.md` as a ✓/✗ table; state plainly what you measured vs. what a human heard/saw.
8. **Deliver**: send the file with its absolute path, delete superseded versions so nobody reviews an old cut, commit/push sources.

## Script rules
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
8. Metrics are necessary, not sufficient: a clone with perfect flatness, pitch spread and ASR was still rejected for intonation. When the listener says "still AI", change the method (continuous take, better voice, human actor), not the EQ.

## Look rules
- No default AI aesthetics: purple/violet→blue gradients, glow blobs, cyan-on-dark, glassmorphism, gradient text, emoji headlines, three-icon grids, everything centred.
- A palette with a reason (place, culture, product), flat colour fields, bold geometry, hard-offset shadows, grain; one display face + one accent face chosen for the script's language coverage.
- Real product (captured UI at device resolution, real data) and real people/places (own or licensed footage). Never generated faces/hands, no gibberish text.
- **One text layer per moment.** Headline + kicker + sticker + karaoke caption at once is a template tell the viewer reads as "AI-made" even without naming it.
- Each video in a batch gets its own dominant colour, layout and device angle inside one system.
- 9:16 safe zones: keep key content out of the top ~220 px and bottom ~420 px of 1080×1920. 16:9 is not a stretched 9:16 — recompose for the wide frame (side-by-side UI, wider type, longer holds).

## Motion rules
- Weight and imperfection: anticipation, overshoot, settle; organic drift from incommensurate sines; easing and stagger varied; camera moves motivated by content and different scene to scene.
- Vary transitions (hard cut on a beat, match cut on a tap, whip, push) — the same entrance every scene is a tell.
- Shot lengths ≈1–8 s, cut on audio accents, ≥4 compositions, no dead frame >0.5 s, no flicker/morph/jump. Subtle grain over everything.

## Sound rules
- Music bed ducked 10–15 dB under voice; with no voice, music carries the edit — cut to its beats.
- Foley/SFX only on real on-screen events (tap click, whoosh on a move, chime on a notification, success on a confirmation); constant very low room tone removes digital silence.
- −14 LUFS integrated, true peak ≤ −1 dBTP for social delivery.

## Ops (long renders, limited sessions)
- Run render queues detached (`nohup setsid script &`) with a log; deliver results from a detached notifier (e.g. a bot that sends each finished file with its path) so work survives the session.
- Never `pkill -f <pattern>` from a command whose own text contains the pattern (it kills your shell); a watchdog that greps its own command line never exits. Match process names (`pgrep -x`).
- Don't edit a shell script while bash is running it.
- If you stop a system service to free CPU for a render, restore it with a `trap` *and* a detached guard.
- Ask before spending money (paid TTS tiers, stock) and before deleting.

## References
- `references/lessons.md` — field-tested failures: the viewer's words, the real cause, the fix.
- `references/voice.md` — engine selection, measured engine notes, continuous-take recipe (ElevenLabs example), tags, QC metrics.
- `references/qa-gate.md` — pre-delivery checklist.
- `references/tells.md` — research-backed list of AI-slop tells with sources.
- `scripts/lint_copy.py` — script linter (banned phrases, duplicate openers/endings, metronome lines, missing specifics).
- `scripts/voice_qc.py` — voice metrics: spectral flatness, F0 spread, wpm, max pause, ASR match.
