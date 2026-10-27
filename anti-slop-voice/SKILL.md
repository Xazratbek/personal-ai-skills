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

1. **Write for the ear, then humanize.** Run the script-humanizer pass from `anti-slop-video` (complete natural sentences, no English-template fragment chains like "Foiz — nol. Bir so'm ham.", native read-through) before spending any credits.
   **Write for the ear.** Short lines, one idea each, varied length, a question somewhere, numbers written as the voice should say them (spoken text) while captions keep digits. No hype words. Mark hard words for phonetic spoken text. (See also the `anti-slop-video` skill for script rules.)
2. **Estimate cost first.** Characters × takes (+ ASR minutes); read the remaining quota (`GET /v1/user/subscription` on ElevenLabs) and say the number before spending. Check which output formats and voices the plan allows (Starter: `mp3_44100_128`, library voices OK; 192 kbps/PCM need a higher tier).
3. **Pick the engine and voice by measurement, then by ear.** Same 2-sentence test on 3–5 *native* candidates → `scripts/voice_qc.py` → send the person **numbered samples** ("1_name.mp3 … 5_name.mp3") and ask for a number. While waiting, build everything that does not depend on the voice (see step 6), but do not run the final render.
4. **Generate the whole script as one continuous take** (one request; 2–3 seeds), with word/character alignment. Line-by-line synthesis resets the melody every sentence and makes a metronome even with a premium model. Line-by-line only as a fallback for engines without long-form input (then gaps by punctuation, below).
5. **Choose the take**: ASR match (`autojunk=False`), pace, onset ≤ 0.2 s, F0 spread, max inner pause; then check the brand/domain words and the first word specifically (`scripts/asr_check.py --expect`).
6. **Drive the picture from the take.** Word times from the engine alignment (or ASR word timestamps) feed every scene start, caption word and SFX cue, so swapping the voice later is a re-run, not a re-edit. Map spoken forms to caption forms explicitly (`"300 000" ↔ "uch yuz ming"`, `"30" ↔ "o'ttiz"`, `"brand.uz" ↔ "brand nuqta uz"`).
7. **Post-process only what needs it.** A premium continuous take: one soxr resample, nothing else — no EQ chain, no pause tightening. Raw local/cheap engines: the gentle studio chain in `references/mix-chain.md`. Never speed variation, never fake breaths.
8. **Mix:** VO is king. Music ducked so it sits **≥ 15 dB under the voice while words are spoken** (measure it: RMS of VO vs music over voiced samples), back up between sentences; SFX on real on-screen events — tonal and soft (mallet notes in key, wood taps, soft thumps), not a noise whoosh on every transition; constant low room tone; −14 LUFS integrated, true peak ≤ −1 dBTP (−1.5 for safety through AAC). Loudness normalisation must not squash the voice (two-pass linear loudnorm, no brick-wall limiter driving).
9. **QA gate** (`references/qa-checklist.md`) — report pass/fail honestly and name what nobody has listened to yet.

## Languages with weak ASR (Uzbek, Kazakh, Tajik, …)
Field notes from an Uzbek batch (ElevenLabs `eleven_v4`, native library voices):
- **ASR cannot grade an accent.** Whisper's literal transcript spells Uzbek with Turkic/Russian habits ("sawal", "kerek", "alasiz"), because Uzbek *o* is [ɒ] and *v* is often [w] — counting "o→a" substitutions flags native speech as accented. Scribe (`language_code=uzb`) "corrects" everything to ≈0.99 and hides real problems. Use ASR for *wrong words*, and the native listener for *accent*.
- **Write the language properly for the model:** Uzbek Latin with the modifier letter turned comma `ʻ` (U+02BB) in *oʻ / gʻ* (not ASCII `'`, which some models treat as a pause or quote), `language_code` set, numbers as words, no Cyrillic/Latin mixing in one script.
- **Brand and domain words get reduced vowels** in context (an *-o* ending heard as *-a*). Test respellings *inside the full sentence*, not in isolation (an isolated fix often fails in the continuous take): stress marks (`brandó`, `Brànd-gó`), hyphenation, splitting into words. If no spelling survives the continuous take, keep the most natural read and make the on-screen domain big and early — and tell the person.
- **Russian (and other Cyrillic-script languages):** write Latin brand names phonetically in Cyrillic in the spoken text (as they are said aloud), stress marks on ambiguous words, numbers and domains as words; captions keep the real spelling.
- **Short loanwords get a foreign vowel too** (an English-sounding "bot", "app", "chat" inside native speech is heard as an accent). List every loanword and brand word in the script, listen to each one in the full take, and respell or rephrase the ones that slip — before the picture is locked, because a re-voice re-times the edit.
- **Check the API key and credit balance before you plan a re-voice** (one cheap call); if the key fails, say so at once and carry on with voice-independent work instead of discovering it at the end.
- Library voices for smaller languages are few (Uzbek: male only, 107–123 wpm): accept a slower pace instead of time-stretching, and write shorter lines.

## When synthetic is not enough
Measured cleanliness is not naturalness. In a real batch, a clean local clone (Qwen3-TTS 0.6B on CPU, flatness 0.008, F0 SD 4.7, 142 wpm, ASR 1.0) was still rejected by the listener for **intonation and pacing**: per-line generation resets the melody every sentence, and a designed (synthetic) reference carries its own slow, announcer-like delivery into every clone. If the listener says it still sounds AI-made:
- Prefer a **human read**: hire a native voice actor (Kwork/Fiverr/Voice123) with a brief (lines, mood per video, pace, pronunciation, dry 48 kHz WAV, one file per line), then ingest, trim and time captions from ASR. This is the most reliable anti-slop voice.
- Or a **licensed premium voice** (e.g. ElevenLabs Voice Library — actors who consented and are paid).
- **Never** take or clone a real person's voice found online (YouTube, podcasts, open ASR datasets like Common Voice) for marketing: they did not consent to being cloned into ads.
- If staying synthetic: generate a whole video's script in one pass (continuous prosody) instead of line by line, and clone from a real consenting human reference rather than a designed voice.

## Hard rules
- **Get a human listen on one finished line before batch-rendering videos.** Wait for the answer; do not start the final render "in the meantime" (voice-independent work — captures, sprites, layouts, draft renders for motion QA — is fine and keeps the wait cheap).
- Never time-stretch or resample generated speech to make it "vary" or to fit a timeline. Fit the timeline by editing the script or the visuals.
- Never add synthetic breath noise.
- Never mix a non-native speaker preset into a language-specific product video.
- Never ship a voice you only checked by numbers when a human listen is possible — numbers catch buzz, monotony and pace, not charm.
- Same voice, same chain across a batch; variety comes from the script and the read, not from random DSP.
