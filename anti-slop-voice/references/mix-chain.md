# Studio VO chain (ffmpeg) and mix targets

> Use this chain only for raw local/cheap engines. A premium continuous take (e.g. ElevenLabs `eleven_v4` whole-script request) gets **one soxr resample and nothing else** — EQ, compression and pause tightening on it were heard as "processed" and made no listener-visible improvement.

Apply once, from the raw generated take, in this order. Every step is gentle; if you can hear a step working, it is too strong.

```bash
ffmpeg -i raw.wav -af "\
aresample=48000:resampler=soxr:precision=28,\
highpass=f=75:p=2,\
equalizer=f=280:t=q:w=1.1:g=-2.5,\
equalizer=f=3400:t=q:w=0.9:g=2,\
deesser=i=0.35:m=0.5:f=0.5,\
acompressor=threshold=-21dB:ratio=2.5:attack=6:release=110:makeup=2" \
-ac 1 -sample_fmt s16 line.wav
```

| Step | Why |
|---|---|
| soxr resample, once | Cheap resamplers add aliasing/"fizz"; one high-quality conversion to the delivery rate. |
| HPF 75 Hz | Removes rumble/DC wobble that eats headroom; no voice content lives there. |
| −2.5 dB @ 280 Hz | TTS voices are often "boxy/muddy"; this clears them on phone speakers. |
| +2 dB @ 3.4 kHz | Presence/intelligibility on small speakers and under music. |
| De-esser (light) | Codec TTS often has sharp "s/ш/щ". Heavy de-essing = lisp. |
| 2.5:1 compressor, 2–4 dB GR | Evens word levels so the voice sits on top of music without pumping. |

Only if tempo really must change (and ≤ 6 %): prepend `rubberband=tempo=1.04:pitchq=quality:formant=preserved,`. Never use `atempo`/resampling to "vary" lines.

## After the chain (in code)
- **Trim** to −42 dB envelope with 30 ms head / 100 ms tail and 12 ms fades.
- **Tighten** silences inside a line: anything quieter than −45 dB for > 0.26 s → cut down to 0.19 s with a 15 ms crossfade. This removes the "TTS thinking" drag without touching the voice itself.
- **Gaps between lines** by punctuation: `? 0.40 s · ! 0.30 · . 0.30 · : 0.20 · , 0.16`, ±40 ms deterministic jitter.
- **Caption timing** from ASR word timestamps (faster-whisper `word_timestamps=True`) aligned to the script tokens with difflib; interpolate only the unmatched words.

## Mix targets (Reels/TikTok/Shorts)
- Voice peak-normalised in the stem; the master does loudness: −14 LUFS integrated, true peak ≤ −1 dBTP (−1.5 for safety through re-encodes).
- Music bed −9 dB pre-duck and a further duck keyed by the VO so the bed ends up **≥ 15 dB under the voice while words are spoken** (measure VO vs music RMS over voiced samples; 10–12 dB was not enough under a busy code-made groove) (attack ≈ 50 ms, release ≈ 400 ms); fade in 0.8 s, fade out 1.6 s.
- Room tone −40…−46 dB constant under everything — kills "digital silence" between lines.
- SFX (tap, whoosh, chime) on real on-screen events, whoosh starts ~250 ms before the cut, taps ~50 ms before the visual press.
- Check on a phone speaker: every word intelligible with music on.
