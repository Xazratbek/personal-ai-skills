---
name: anti-slop-voice
description: Make TTS / AI voiceover that does not sound like AI slop — for Reels/TikTok/Shorts, motion-graphics explainers, product promos, ads, app demos and any narrated video. Use it whenever you are about to generate, choose, post-process, mix or review a synthetic voice, pick a TTS engine, write a script that will be read by TTS, or when the user says the voice is "robotic", "AI-sounding", "slow", "metallic", "buzzy", "flat", "has no emotion", "sounds slowed down", or asks for a "professional voiceover". Also use it before batch-producing several narrated videos, because one bad pipeline default ruins the whole batch.
---

# Anti-slop voice

Listeners decide "this is AI" in the first second of a voiceover, and the decision is driven by a few specific artifacts, not by the abstract quality of the model. Most of them are *introduced by our own pipeline* (time-stretching, resampling, fake breaths, equal pauses), not by the model. Your job: choose an engine that speaks the language natively, generate at the right pace, never damage the signal afterwards, and mix it like a studio read.

## The tells and what actually causes them

| What the listener hears | Usual cause | Fix |
|---|---|---|
| "Slowed down", draggy, sleepy | Model reads at ~130 wpm; or audio was resampled/stretched to change speed; long TTS "thinking" pauses inside lines | Generate at the target pace (pick a reference/voice that is already brisk, or the engine's own speed control). Shorten internal pauses > 0.26 s to ~0.19 s with crossfades. Target 150–170 wpm for Reels, 140–155 for dense explainers. |
| Metallic / phasey / "underwater" | Time-stretch or pitch-shift of generated audio (incl. "±3 % random speed/pitch per line" tricks done by naive resampling), low-bitrate MP3 from cloud TTS, cheap resampler | Never resample to vary speed (it shifts pitch *and* smears the vocoder). If you must change tempo, ≤ 6 % with a formant-preserving stretcher (Rubber Band `formant=preserved:pitchq=quality`). Resample once with SoX/soxr high precision. Prefer lossless engine output. |
| Buzz, hiss, raspy "xirillash" | Old/lightweight vocoder (e.g. VITS-class, 22 kHz), noisy decoder | Switch engine. Measure: mean spectral flatness of voiced speech > ~0.045 means audible buzz/noise; a modern codec model is ~0.01–0.02. |
| Flat, monotone, "reading a list" | Narrow pitch band; every sentence the same contour | Engine with expressive prosody; voice/ref chosen for warmth and smile; script with mixed sentence lengths, questions, fragments. Measure F0 spread: < ~2.5 semitones SD is monotone; lively ad reads are ~4–6. |
| Metronome rhythm | Identical gap between every line | Gaps by punctuation and meaning: after a question ~0.4 s, sentence ~0.3 s, colon/comma ~0.16–0.2 s, plus small deterministic jitter (±40 ms). Let music/visual beats breathe, not the voice. |
| Fake breath | White/pink noise bursts pasted before lines | Don't synthesize breaths. Either the model produces natural ones, or use none. A constant, very low room tone (−40…−46 dB) under the whole VO removes the "digital silence" instead. |
| Wrong stress, mangled names/brands | No stress dictionary; foreign words | Phonetic spoken spellings for the TTS text only (captions keep the real spelling); stress marks (+ or U+0301) where the engine supports them; ASR round-trip every line and regenerate mismatches. |
| Foreign accent | Speaker preset trained on another language (e.g. English preset reading Russian) | Use a native-language voice: native preset, or design/clone a native reference and clone from it for every line (same timbre across the whole batch). |
| Over-clean, "in the computer" | No processing, or heavy limiting with no dynamics | Light studio chain (below) and real mixing against music and SFX. |

Details, sources and the extra tells are in `references/tells.md`.

## Workflow

1. **Write for the ear.** Short lines, one idea each, varied length, a question somewhere, numbers written as the voice should say them. No hype words. Mark hard words for phonetic spoken text. (See also the `anti-slop-video` skill for script rules.)
2. **Pick the engine by measurement, not by brand.** Generate the same 2-sentence test line on 3–5 candidates, run `scripts/voice_qc.py` on all of them, then listen (or ask the user to listen). Native language + low flatness + healthy F0 spread + correct ASR wins. Engine notes and CPU timings: `references/engines.md`.
3. **Lock one brand voice.** Create one reference per voice role (e.g. female / male / calm male), 10–15 s, brisk conversational read, and clone every line from it. Never let each line pick a random voice.
4. **Generate line by line with QC.** Per line: generate → ASR match ≥ 0.92 and speech-rate window (Russian ≈ 3.6–6.6 syllables/s) → otherwise new seed, keep the best of N (3 is enough).
5. **Post-process without damage** (one pass, deterministic, from the raw take): soxr resample → studio chain → trim → tighten internal pauses. No speed variation, no fake breaths. Chain: `references/mix-chain.md`.
6. **Assemble with natural gaps**, then build caption timing from ASR word timestamps aligned to the script words (not from character-count guesses), so karaoke captions land on the real syllables.
7. **Mix:** VO is king. Music bed ducked 10–15 dB under speech (fast attack ~50 ms, release ~400 ms), SFX on real on-screen events, constant low room tone, final −14 LUFS integrated, true peak ≤ −1 dBTP.
8. **QA gate** (`references/qa-checklist.md`) — run `scripts/voice_qc.py --text` on every final line and on the final mix; report pass/fail honestly. If you cannot listen, say so and ask the user for a 10-second listen of one line before batch-rendering everything.

## Hard rules
- Never time-stretch or resample generated speech to make it "vary" or to fit a timeline. Fit the timeline by editing the script or the visuals.
- Never add synthetic breath noise.
- Never mix a non-native speaker preset into a language-specific product video.
- Never ship a voice you only checked by numbers when a human listen is possible — numbers catch buzz, monotony and pace, not charm.
- Same voice, same chain across a batch; variety comes from the script and the read, not from random DSP.
