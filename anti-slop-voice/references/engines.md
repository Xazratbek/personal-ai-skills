# Engine notes (measured, not marketing)

Measured 2026-10 on a 2-core ARM Neoverse-N1 VM (no GPU, no bf16 hardware), same Russian test line
("Вы уже дважды обновили ленту, а в чате друзей: «Может, завтра?». А в паре кварталов от вас прямо сейчас не хватает одного игрока."),
with `scripts/voice_qc.py`-style metrics. Lower flatness = cleaner; higher F0 SD = livelier.

| Engine / voice | wpm | F0 SD (st) | flatness | ASR | CPU speed | Notes |
|---|---|---|---|---|---|---|
| Vosk-TTS ru 0.9 multi (spk 2/3) | 151–173 | 3.1–3.8 | **0.058–0.060** | 1.00 | very fast | VITS-class 22 kHz: audible buzz/rasp — the user called it robotic. |
| Silero v5 ru (aidar/baya/kseniya/eugene/xenia) | 143–185 | 1.7–5.3 | 0.012–0.043 | 1.00 | very fast (RTF ≪ 1) | Clean for aidar; xenia/baya monotone. Good fast fallback. |
| Microsoft Edge ru-RU Svetlana/Dmitry (cloud, free) | 148–165 | 3.0 | 0.078–0.100 (48 kbps MP3) | 1.00 | network | Native Russian, but lossy low-bitrate stream and a very recognisable "TikTok voice". |
| Qwen3-TTS 0.6B CustomVoice (English preset "ryan") | 135 | 5.2 | **0.013** | 1.00 | RTF ≈ 17 (fp32) | Cleanest and liveliest, but the preset is not a native Russian speaker → design/clone a native voice instead. |
| Qwen3-TTS 1.7B VoiceDesign → 0.6B Base clone (ICL) | see project log | | | | design: slow on CPU without bf16; clone: RTF ≈ 15–20 | Chosen: native Russian voice designed once from a text description, cloned for every line. |

Notes
- Qwen3-TTS (Apache-2.0, `pip install qwen-tts`): models `Qwen/Qwen3-TTS-12Hz-{0.6B,1.7B}-{Base,CustomVoice,VoiceDesign}`, 24 kHz output, 10 languages incl. Russian. On CPU use fp32 for 0.6B; on CPUs without bf16 the 1.7B bf16 path falls back to slow BLAS — use it only for one-off reference design. CPU is 10–50× slower than GPU per the official FAQ.
- torch / torchaudio must be the same `+cpu` build (a CUDA torchaudio wheel on a CPU torch fails with `libcudart.so` errors).
- Hugging Face ZeroGPU Spaces run out of free quota quickly; don't build a batch pipeline on them.
- Cloud options worth comparing when budget allows: ElevenLabs, Cartesia, Azure (lossless formats). Always request lossless/24-bit or ≥ 128 kbps.
- Sources: [Qwen3-TTS FAQ](https://www.mintlify.com/QwenLM/Qwen3-TTS/resources/faq), [Silero v5 ru](https://huggingface.co/Dimitrius174/silero-v5-tts-ru), [open-source TTS guide 2026](https://tts.ai/blog/open-source-text-to-speech-guide-2026/), [quantized CPU TTS 2026](https://ocdevel.com/blog/20260711-quantized-cpu-tts).

## ElevenLabs `eleven_v4` (cloud), 2026-10, whole-script continuous takes
| Voice (library) | Lang | wpm | F0 SD (st) | flatness | Notes |
|---|---|---|---|---|---|
| Artem K | ru | 140–153 | 5.1–5.9 | 0.018–0.022 | Ad read; approved. |
| Vika Grib | ru | 133–140 | 4.2–4.5 | 0.010 | Calmer, slower. |
| Davronbek (journalist) | uz | 120–125 | 6.2–7.2 | 0.014–0.015 | Liveliest Uzbek library voice; brand words reduced ("restogo"→"restago"). |
| Asilbek, Mirzaev, Mirzabek, Shohjahon | uz | 107–116 | 4.2–6.9 | ≤ 0.015 | Slower; pick by native ear. |
- `POST /v1/text-to-speech/{id}/with-timestamps` returns per-character alignment (tags and combining marks included) — use it for word timing.
- Music API (`/v1/music`, composition plan): every section ≥ 3000 ms or HTTP 422; returns the plan's length ± 0.1 s; analyse energy before trusting the section map.
- Scribe STT (`/v1/speech-to-text`, `scribe_v1`, `language_code=uzb|rus`) is a good wrong-word check, a poor accent check.
