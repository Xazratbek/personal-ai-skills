# Voiceover: engines, the continuous-take recipe, QC

## Choosing an engine and voice
- Native speaker of the target language beats any accented "premium" preset.
- Prefer licensed library/actor voices or a human read for marketing; never clone a real person found online.
- Shortlist by use case (social media / advertisement) and real usage, then generate the same 2-sentence test on 3–5 voices, run `scripts/voice_qc.py`, and get a human listen.
- Measured engine notes (2-core CPU VM, Russian test line):

| Engine | Verdict |
|---|---|
| VITS-class local (e.g. Vosk 22 kHz) | Audible buzz (flatness ≈0.06) — rejected. |
| Silero v5 | Clean and very fast; some speakers monotone. OK fallback. |
| Edge cloud TTS | Native but 48 kbps MP3, recognisable "TikTok voice". |
| Qwen3-TTS local clone (0.6B, CPU RTF ≈17) | Cleanest metrics, still rejected for intonation when built line by line. |
| ElevenLabs `eleven_v4`, whole-script take, native library voice | Approved. |

## Continuous-take recipe (ElevenLabs example; same idea for any engine with alignment)
```
POST /v1/text-to-speech/{voice_id}/with-timestamps?output_format=mp3_44100_128
{"text": "<entire script, lines joined by spaces>", "model_id": "eleven_v4", "language_code": "<lang>", "seed": <per take>}
```
- Response: `audio_base64` + `alignment.characters / character_start_times_seconds / character_end_times_seconds`, one entry per input character (tags and combining marks included). Record each line's character span when you join the script; cut line and word times from the alignment.
- Keep caption text and spoken text separate: spoken = tags, stress marks (U+0301), phonetic spellings; captions = real spelling. Keep word counts equal so caption words map 1:1.
- Cache each take's response keyed on the exact text so re-runs cost nothing.
- 3 takes with different seeds; score = ASR match − pace penalty − onset penalty; then read the transcript's first words.
- Output: resample once (soxr) to the project rate. Nothing else.
- Plans: library voices via API and commercial use need a paid tier; high-bitrate/PCM formats may need a higher tier. Check `GET /v1/user/subscription` and `GET /v1/models` first.
- No SSML breaks in the newest models: pauses come from punctuation, ellipses and sentence structure.

## Tags
- Allowed, sparingly: curious, warmly, upbeat, excited, mischievously, conspiratorially (English words in brackets, before the phrase).
- Avoid for commercial content: sighs, tired, exhales, whispers, laughs, playfully — breathy sounds can read as intimate.
- Never on the first word of the take.

## QC metrics (`scripts/voice_qc.py`)
| Metric | Good | Bad means |
|---|---|---|
| Spectral flatness (voiced) | ≤0.03 | >0.045 audible buzz → change engine |
| F0 spread | ≥2.5 st SD (lively ad 4–6) | monotone |
| Pace | Reels 150–170 wpm (145–185 ok); RU 3.6–6.6 syl/s | draggy / swallowed |
| ASR match | ≥0.95 (`autojunk=False`) | wrong words, mispronunciation |
| Onset before first word | ≤0.2 s | breath/sigh at the start |
| Max inner pause | ≤0.45 s unless written | "thinking" pauses |
Numbers catch buzz, monotony and pace; they do not catch charm or wrong emotion. Always say which you checked.

## Line-by-line fallback (only if an engine can't take the whole script)
Pass previous/next text context if supported, vary gaps by punctuation (question ≈0.4 s, sentence ≈0.3 s, comma ≈0.16 s ± small jitter), and expect a less natural result.
