# Field-tested failures

From a real 11-video batch that was rejected four times before approval. Format: what the viewer/client said → actual cause → fix.

## Voice
1. **"Robotic, buzzy"** → lightweight 22 kHz vocoder (spectral flatness ≈0.06) → change engine; flatness >0.045 is audible buzz.
2. **"Slowed down, metallic"** → a well-meant rule: random ±3 % resample per line "for variety" plus pasted noise breaths → never resample/stretch generated speech for variety; never synthesise breaths; use constant room tone.
3. **"Intonation and pacing still synthetic"** on a clone that was perfect on every metric → per-line generation resets the melody every sentence; a *designed* reference voice brings an announcer delivery into every clone → metrics don't measure charm; switch to native licensed voices / human reads.
4. **"No difference from the previous one — you can't control the tempo"** after moving to a premium cloud voice → the pipeline still synthesised each line separately, trimmed, glued with punctuation gaps and ran a studio chain → the assembly, not the model, was the metronome. Fix: whole script in one request, take untouched, timing from alignment. Approved immediately.
5. **"The first word sounds like a woman's moan"** → an emotion tag ("tired") plus an ellipsis made a breathy sigh before the first word → no breathy/intimate tags; automatic onset check (sound >0.2 s before first word = reject). For a brand this is safety, not taste.
6. **First consonant smeared** ("T-yatnitsa" for "Pyatnitsa") → tag placed on the very first word → never tag the first word; check the chosen take's first word.
7. **Paid voices returned 402** on a free tier; free tier also had no commercial licence and blocked high-bitrate formats → check plan limits and licence before building; ask the client before paying.
8. **Transcript compare scored 0.05 for a correct take** → Python `difflib` autojunk on long strings → `autojunk=False`.
9. **ASR "errors" that aren't** → numbers written as digits, local place names spelled phonetically → treat as ASR noise, confirm by ear.

## Script
10. **"The text itself sounds AI-written — humanize it"** → formal address, symmetrical slogan lines, no reactions → spoken register, informal address for a young audience, run-ons, reactions, fragments.
11. **Narrator gender mismatch** → gendered verb forms in a female read addressed to everyone → gender-neutral constructions.
12. **Stickers popping at the wrong moment after a copy edit** → scene anchors keyed to words that no longer exist → update anchors with every wording change.

## Picture
13. **"Still AI slop in every part, not like a professional made it"** after voice and copy were fixed → stacked text layers (headline + kicker + sticker + caption), identical device entrance in every scene, no real people/places → one text layer per moment, varied transitions, real footage moments, fewer decorations.

## Ops
14. Jobs died when the session ended or was backgrounded → detached queues + detached delivery.
15. `pkill -f "<pattern>"` killed the calling shell; a `pgrep -f` watchdog matched itself forever → match process names.
16. A service stopped for rendering must come back → `trap` + detached guard.
17. Client reviewed an outdated cut → delete superseded files; send each new one with its path.

## Second batch (9 videos for a restaurant-ordering SaaS, RU + UZ)
18. **"Fix the Uzbek speaker's accent"** → the ASR "accent score" (o→a, q→k substitutions in a literal whisper transcript) flagged native Uzbek [ɒ] and [w] as errors, and Scribe normalised everything to ≈0.99 → numbers could not decide. Fix: proper orthography (ʻ U+02BB, numbers as words, `language_code`), numbered A/B samples to the native listener, build voice-independent work while waiting.
19. **Brand domain heard with a wrong final vowel** → vowel reduction in context; a respelling that fixed an isolated test line failed in the full take → test respellings inside the full script and keep the domain big on screen.
20. **Text ghosting on fast scrolls** ("double letters") → box-averaged sub-frames + ease-out-quint scroll (infinite start velocity) → tent-weighted sub-frames, ≥16 samples, sine in-out scroll.
21. **Kinetic chunks overlapping** → the outgoing chunk still animating out when the next word landed → exit finishes before the next word's landing time.
22. **One-frame flash at the start** → a different poster frame spliced in as frame 0 → make frame 0 the cover or deliver a separate cover image.
23. **Receipt + stamp used in two videos of one batch** → template feel across the batch → keep a batch ledger of signature devices.
24. **Wrong domain on the end card** → the sub-product domain was used while the client wanted the umbrella brand → confirm the ending (domain, CTA) before rendering.
25. **Stale facts in assets** → the site's social preview still said "14 days free" while the product gave 30 → verify every claim against current code/site, not old assets.
26. **A public phone number inside a captured landing section** → re-frame captures so no phone numbers or personal data appear.
27. **Hand-drawn phones** → the client asked for real device assets → maker bezels (Apple Product Bezels), screen under the bezel; licence: mock-ups only; PNGs only in a private repo (see 43).
28. **Music bed only 12 dB under the voice** in a code-made groove → measured VO−music RMS on voiced samples and deepened the duck to ≥15 dB.
29. **Dev servers gone after a container restart** → capture scripts failed with connection refused → check/restart servers before every capture session.
30. **"The glare over the phone isn't smooth, it stutters"** → the specular sweep picked one of 32 precomputed phases → compute continuous effects per frame (or interpolate), never step through a small table.
31. **"Tips of the letters below show under the line"** → word sprites cropped from a multi-line text render; the span box (≈1.2 em) is taller than the line height (1.04 em), so each crop caught the next line's ascenders/accents → render each word alone (others `visibility:hidden`, same layout) and crop from that.
32. **"Shuu-shirr" on every transition got on the client's nerves** → a noise whoosh on each title and cut → tonal, soft transition sounds in the music's key; 1–2 whooshes max on real big moves.
33. **A literally translated slogan chain ("Zero commission. Not a cent.") sounded illogical/AI-written** → English slogan fragments translated literally → humanizer pass: complete sentences as a native speaker says them, native read-through before voicing.

## Third round (re-work of two concept videos)
34. **"You lowered the quality to render faster?"** → sub-frames were cut 10→6 without asking → quality is fixed; parallelise and wait, or ask first.
35. **"What is that grey thing behind the phone?"** → the phone's shadow was a hard-edged quad of the whole bezel image → shadows from the device's real silhouette, soft and offset with the lift.
36. **"The phone inside the ring looks strange; the screens run into each other"** → a flat device threaded through a 3D ring with faked depth sorting, plus six copies of the phone fanned over it → no interpenetrating 2.5D objects, no fans of copies; one hero per moment.
37. **"The ball hides the words"** → a decorative dot travelled along a line of text → automated per-frame text/hero intersection check, decorative elements routed around text.
38. **Captions printed over machine parts in a camera-follow scene** → the camera kept the active part at frame centre, so earlier parts scrolled through the caption band → frame the action below the text zone and give the text zone its own solid band the scene passes under.
39. **Big intro type wrapped by itself** ("buyurtma — bu" on one line, a lone dash elsewhere) → explicit line breaks for display type and a no-break space before dashes.
40. **"The concept is fine but the execution isn't — use other animation"** → patching single defects would have kept the weak device → rebuilt the sequence: real UI elements lift out of the phone in 3D (soft alpha shadow, empty spot left on screen), colour-block and iris wipes between scenes, slot-style counter, stamped badge with confetti, annotation circles drawn on a real admin table, chat bubbles stacking.
41. **"A short loanword sounds foreign"** ("bot" inside Uzbek speech) → list loanwords/brand words and listen to each in the full take before locking the picture; re-voice re-times automatically when the picture is driven by alignment.
42. **TTS key stopped working mid-project** → found only when a re-voice was needed → check keys/credits with one cheap call at the start of each session and report at once.
43. **"I can't render it on my Mac — assets are missing"** → device frames and render inputs were kept out of git, paths were absolute, and `pip install` failed on a `user = true` config → private repo holds every input, relative paths, `pip install --isolated`, one render script per video.
44. **Several deliverables, hard to match files to descriptions** → each video's description file carries the video's own file name (`<video>.md` next to `<video>.mp4`), and the bundle is one zip.
