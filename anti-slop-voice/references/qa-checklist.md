# Voice QA gate (per video; report as a ✓/✗ table)

Run `python scripts/voice_qc.py --json lines.json` on the final processed lines and `python scripts/voice_qc.py --mix final.mp4` on the delivered file first.

## A. Engine & voice
1. Native-language voice (no foreign-preset accent); one locked reference per role across the batch.
2. Every line: ASR match ≥ 0.92 (numbers/dates may legitimately differ — check those by ear or spelling).
3. Spectral flatness ≤ 0.03 on voiced speech (> 0.045 = audible buzz → change engine, don't EQ it away).
4. F0 spread ≥ 2.5 semitones SD (lively ad read ≈ 4–6).

## B. Pace & rhythm
5. Speech rate inside the window (Russian 3.6–6.6 syl/s; Reels target ≈ 150–170 wpm).
6. No inner pause > 0.45 s unless it is a deliberate dramatic beat written in the script.
7. Line gaps vary with punctuation/meaning; not one constant value.

## C. Signal integrity
8. No resample/time-stretch "variation"; any tempo change ≤ 6 % and formant-preserving.
9. No synthetic breath noise; constant room tone instead.
10. No clipping; single high-quality resample to delivery rate.

## D. Mix
11. Music ≥ 15 dB under the VO while words are spoken (measured), back up between sentences; every word intelligible on a phone speaker.
12. SFX on real on-screen events.
13. −14 LUFS integrated (±1), true peak ≤ −1 dBTP.

## D2. Words that must be heard
11a. Brand, domain, prices and numbers checked with `scripts/asr_check.py --expect …` *in the final take* (not in an isolated test line).
11b. Weak-ASR language: accent confirmed by a native listener on numbered samples, not by ASR metrics.

## E. Honesty
14. State what was measured vs. what was listened to. If nobody has listened yet, say so and ask for a 10-second listen before the batch render.
