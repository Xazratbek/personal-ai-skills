# Original music in code (numpy + scipy)

Use when stock/AI music licensing is unclear or the cut needs music that hits exact cue times. It will not beat a composer, but
arranged to the picture and ducked under a voice it reads as a deliberate bed. Reference implementation: RestoGo
`marketing/video/engine/music_gen.py`.

## Building blocks (48 kHz mono buses → stereo)
- **Plucked strings** — Karplus-Strong: a filtered noise burst through a delay line with feedback (`scipy.signal.lfilter([1], a)`
  with `a[N]=a[N+1]=-damp/2`); two slightly detuned strings read as a dutar/guitar. Cache one render per pitch.
- **Pad** — 3 detuned band-limited saws per chord tone (≈8 harmonics), 2-pole low-pass 900–1800 Hz, slow attack.
- **Sub bass** — sine + a little 2nd/3rd harmonic, short envelopes, `tanh` for warmth.
- **Drums** — kick: sine sweep 140→45 Hz with fast decay and a 3 ms click; clap: band-passed noise with 3 staggered bursts;
  hats: high-passed noise, 60 ms closed / 250 ms open.
- **Space** — one convolution reverb with an exponentially decaying noise IR (1.5–2 s), mostly on pads and plucks.

## Arranging to the cut
- Take the cue list from the renderer (scene starts, landings, drops) and lay the bar grid so a **downbeat lands on the biggest hit**
  (device landing, first logo). Re-grid after a drop instead of forcing one tempo through the whole piece.
- Sections follow the picture: sparse intro under the hook, groove under the demo, a cut to pad only for the "0 %"/price punch,
  groove back for the offer, a final chord (+ strum, + kick) on the logo that rings 2+ s under the end card.
- Different videos of a batch get different tempo, key and pattern (e.g. 96 BPM D minor groove vs. 118 BPM G minor four-on-the-floor
  for a paid ad).

## Mix checks
- Duck with an envelope follower keyed by the VO (attack ≈ 50 ms, release ≈ 400 ms) and **measure**: VO RMS − music RMS over voiced
  samples ≥ 15 dB. 17–21 dB of duck depth was needed under a busy groove.
- Analyse the bounce (RMS / low / high bands per 0.5 s) to confirm the sections are where you think they are.
- Master with two-pass linear loudnorm to −14 LUFS, TP −1.5 dBTP; no limiter pumping the voice.
