# Voice slop tells — research notes and sources

Collected for a batch of Russian Instagram Reels (motion graphics + real app UI) whose first voice (Vosk-TTS + per-line resample "variation" + noise breaths) was rejected by the user as "slowed down, slightly buzzy, robotic". Every item below was either observed in that pipeline or reported by the sources.

## Listener-level tells
1. **Monotone pitch** — default TTS reads inside a narrow pitch band; every sentence has the same contour. ([Podcastle: 10 signs](https://podcastle.ai/blog/how-to-tell-if-audio-is-ai-generated), [Creatify](https://creatify.ai/blog/how-to-add-ai-voice-to-video), [Vidrush 2026](https://vidrush.ai/blog/why-your-ai-voiceover-sounds-robotic))
2. **Identical timing and pause length from start to finish** — pauses only at punctuation, always the same length. ([Async](https://async.com/blog/how-to-detect-ai-voices/))
3. **Breathing wrong** — never breathes, or breaths that feel pasted in after the fact. ([Podcastle](https://podcastle.ai/blog/why-do-ai-voices-sound-weird))
4. **Flat emphasis / emotion mismatch** — key words don't stand out; a warm line comes out neutral.
5. **Too smooth** — no micro-variation; a UC study attributes part of the naturalness gap to missing jitter/shimmer micro-perturbations in TTS. ([eScholarship](https://escholarship.org/uc/item/8vr8s6h8))
6. **Metallic sound at changed speeds** — slowing a TTS voice (e.g. 0.7×) makes it metallic; even 0.99× sounds different, because speed is done by stretching/pitch-shifting the generated audio. Regenerate at the intended speed instead. ([OpenAI community](https://community.openai.com/t/getting-metallic-voice-at-slower-speeds-on-speech-api/478108))
7. **Digital distortion / metallic overtones** as a general AI-voice artifact. ([Sonarworks](https://www.sonarworks.com/blog/learn/understanding-ai-voice-artifacts-and-how-to-minimize-them))
8. **Old engine class** — the single largest naturalness jump is moving off an old voice to a modern neural one. ([VoxBooster](https://voxbooster.com/blog/robotic-text-to-speech))

## Pipeline-level causes we found in our own code
- `np.interp` resample by ±2.5 % per line "to fight the TTS plateau" → changes pitch and tempo together; a lowered line sounds slowed-down and phasey. Remove.
- Band-passed white noise "breaths" before lines → reads as hiss, not breath. Remove; use constant room tone instead.
- 22 kHz VITS-class vocoder upsampled to 48 kHz → buzz/rasp; spectral flatness ≈ 0.06 vs ≈ 0.013 for a modern codec model (measured).
- Constant 0.26 s gap between all lines → metronome.
- Caption timing from letter-count ratios → captions drift from the voice, which viewers read as "fake".

## Pacing references
- 150 wpm is the most cited default for explainers; 120 for complex technical content, 180 for quick overviews; others give 140–160. Whiteboard/motion pieces with on-screen text can run slower because people read while listening. ([Voicebros](https://voicebros.com/en/blog/explainer-video-voice-over-guide), [Bread n Beyond](https://breadnbeyond.com/how-many-words-does-a-60-seconds-explainer-video-needs/), [Stimme24](https://www.stimme24.com/en/voice-overs/explainer-video/))
- Fix pacing by simplifying an overloaded sentence and breaking it where a speaker would breathe, before touching clip speed. ([CapCut guide](https://www.capcut.com/create/ai-voiceover-editing-pronunciation-pacing-emphasis))

## Mix references
- HPF ≈ 80–100 Hz, cut boxiness 200–400 Hz, presence +1–3 dB at 3–6 kHz, 2:1–4:1 compression with 3–6 dB GR, de-ess 5–8 kHz by 3–6 dB (light, heavy de-essing lisps), limiter −1 dBTP. ([Violet Recording](https://violetrecording.com/how-to-mix-spoken-word-vocals/), [Ruah Creative](https://ruahcreativehouse.org/blog/podcast-audio-mixing/), [Amped Studio](https://ampedstudio.com/blog/vocal-chain/))
- Music beds 10–15 dB under speech, ducked under the voice. ([Violet Recording](https://violetrecording.com/how-to-mix-a-podcast/))
- Social video: −14 LUFS integrated, −1 dBTP, LRA ≈ 11 is the common practical target (not an official Instagram spec). ([vloggingpro](https://vloggingpro.com/tools/audio-loudness/), [video-use](https://instagit.com/browser-use/video-use/social-media-loudness-normalization-targets/))
