# Pre-release QA gate (run before every delivery; report as a ✓/✗ table)

Run `python scripts/lint_copy.py <scripts>` first. Then go through every item for **each** video; fix ✗ items, don't ship with them.

## A. Script
1. Hook archetype is named and differs from every other video in the batch.
2. ≥ 1 concrete specific from the real product/place/time (no invented stats, counts, testimonials).
3. No banned hype/filler phrases (linter clean).
4. Closing line unique in the batch; CTA info present (link in profile/description) and bot/brand name not spoken if forbidden.
5. Sentence lengths vary (linter: not metronomic); hard-to-read words have phonetic spoken spellings.

## B. Look
6. No purple/violet→blue gradient, glow blobs, glassmorphism, gradient text, emoji headline, centred-everything layout.
7. Palette/type are brand- or place-specific and differ per video inside one system; device/layout/angle differ from the previous video.
8. Real product UI (captured) and real people photography only; no generated faces/hands; no gibberish text.
9. Safe zones respected (organic 1080×1920: top ≈220 px, bottom ≈420 px; paid ads: top ≈270 px, bottom ≈670 px, sides ≈65 px).
9a. Devices are real maker frames (licence read; PNGs only in a private repo), shadows from the real silhouette, screens captured at device size; no personal data or phone numbers in captures.
9b. Batch ledger: no device, hook, colour or closing line repeated inside the batch.

## C. Motion (view stills AND frame-step; check frame differences if you cannot watch)
10. ≥ 4 distinct compositions, ≥ 1 deliberate camera move, camera signatures differ scene to scene.
11. Organic imperfection present (drift/jitter, weight, overshoot); grain on.
12. No flicker, jumps, morphing; no dead frame > 0.5 s (`motion_qa.py`); hold times ≥ reading time of on-screen text; fast text/scroll moves have smooth (tent-weighted) motion blur, not double-edged ghosts.
13. Shot lengths vary (≈1–8 s), moves land on audio accents.
13a. Text never overlaps a hero element or decorative object (automated per-frame box check); display type wraps only where designed.
13b. Full quality kept: resolution, fps, motion-blur sub-frames and encode settings never lowered to save render time without approval.

## D. Audio
14. Voice passes the `anti-slop-voice` QA gate (native voice, pace, no stretch/fake breaths, studio chain, room tone); ASR round-trip matches the script.
15. Foley synced to taps/transitions/notifications; music ducked under voice.
16. Integrated loudness ≈ −14 LUFS, true peak ≤ −1 dBTP.

## E. Honesty
17. Anything simulated/sample on screen is disclosed in the caption/description.
18. State what you could not verify (e.g. you cannot hear audio) and ask one outside viewer: "Does anything look fake or AI-made?"
