# Pre-delivery QA gate (report per video as a ✓/✗ table)

Run first: `scripts/lint_copy.py` on the script; `scripts/voice_qc.py --text "<script>" vo.wav` if there is a voice; `ffmpeg -i final.mp4 -af ebur128=peak=true -f null -`; a 6-frame contact sheet (`ffmpeg -ss T -frames:v 1` + `magick f*.png -resize x700 +append sheet.jpg`).

## A. Script
1. Spoken register; would a real person say it aloud?
2. ≥1 concrete specific; no invented stats/counts/testimonials.
3. Linter clean; hook archetype and closing line unique in the batch.
4. CTA present; brand name spoken only if allowed.

## B. Voice (if any)
5. Native licensed voice, same per role across the batch; a new voice has had a human listen.
6. One continuous take, unprocessed except one resample.
7. ASR ≥0.95, pace in window, onset ≤0.2 s, first word correct.
8. No breathy/intimate tags.

## C. Picture
9. No default AI aesthetics; palette/type with a reason.
10. Real product UI/footage; no generated faces/hands or gibberish.
11. One text layer per moment; captions match speech word-for-word (timed from the take's alignment); safe zones respected (paid ads: top ≈270 px, bottom ≈670 px); frame 0 is a usable cover.
11a. Devices are real maker frames (licence read; PNGs only in a private repo), shadows from the real silhouette; captures contain no personal data or phone numbers; facts checked against the current product/site.
11b. Batch ledger: hook, colour, signature device, music and closing line not repeated inside the batch.
12. ≥4 compositions; transitions vary; no dead frames, flicker or jumps (`scripts/motion_qa.py`); fast moves have tent-weighted motion blur with no double-edged text.
13. Each aspect ratio composed for itself (9:16 and 16:9 are separate layouts).
13a. Automated layout check passes: no text/hero box intersections at 30 samples/s; no decorative element over a word; no object threaded through another or fans of overlapping copies.
13b. Full quality: native resolution, agreed fps, full motion-blur sub-frames, x264 slow CRF 17–19 — nothing lowered for render time without explicit approval.

## D. Sound and file
14. Music ≥15 dB under the voice while words are spoken (measured), or cut to the beat if no voice; SFX on real events (dense but motivated); a final chord under the end card.
15. −14 LUFS ±1, true peak ≤ −1 dBTP; correct resolution/codec.

## E. Delivery and honesty
16. Sent with absolute path; superseded versions deleted; sources and every render input committed (portable: another machine can re-render); description file named after its video.
17. State what was measured vs. heard/seen; ask one outside viewer "does anything feel fake or AI-made?".
18. Any service stopped for rendering is running again.
