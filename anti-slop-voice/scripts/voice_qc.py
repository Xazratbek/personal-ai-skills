#!/usr/bin/env python3
"""Objective voice-slop checks for TTS lines or a finished VO/mix.

Usage:
  python voice_qc.py a.wav b.mp3 ...                 # signal checks only
  python voice_qc.py line.wav --text "Script line"   # + speech rate and ASR round-trip
  python voice_qc.py --json lines.json               # [{"path":..., "text":...}, ...]
  options: --lang ru|en|uz  --no-asr  --mix (loudness/true-peak report for a final mix)

Needs: numpy, librosa, ffmpeg on PATH; faster-whisper for the ASR check (optional).
Prints one row per file plus PASS/WARN/FAIL reasons. Numbers catch buzz, monotony, pace,
clipping and mismatched text — they do not replace a human listen.
"""
import argparse, difflib, json, re, subprocess, sys
import numpy as np

VOWELS = {"ru": "аеёиоуыэюя", "uz": "aeiouоʻ", "en": "aeiouy"}
RATE = {"ru": (3.6, 6.6), "uz": (3.4, 6.4), "en": (3.0, 5.8)}   # syllables per second, voiced speech


def load(path, sr=24000):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(sr), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32), sr


def norm(s):
    return re.sub(r"[^\w]+", " ", s.lower().replace("ё", "е")).strip()


def syllables(text, lang):
    v = VOWELS.get(lang, VOWELS["en"])
    return len([c for c in text.lower() if c in v])


def longest_inner_pause(y, sr):
    n = int(0.02 * sr)
    env = 20 * np.log10(np.sqrt(np.convolve(y * y, np.ones(n) / n, "same") + 1e-12) + 1e-9)
    q = env < -45
    idx = np.where(~q)[0]
    if len(idx) == 0:
        return 0.0
    q = q[idx[0]:idx[-1]]
    best = cur = 0
    for v in q:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best / sr


def analyse(path, text, lang, use_asr, asr_model):
    import librosa
    y, sr = load(path)
    yt, _ = librosa.effects.trim(y, top_db=35)
    dur = len(yt) / sr
    res = {"file": path.split("/")[-1], "dur": round(dur, 2)}
    f0, _, _ = librosa.pyin(yt, fmin=65, fmax=420, sr=sr, frame_length=1024)
    f0 = f0[~np.isnan(f0)]
    res["f0_sd_st"] = round(float((12 * np.log2(f0 / np.median(f0))).std()), 2) if len(f0) > 20 else None
    rms = librosa.feature.rms(y=yt)[0]
    voiced = rms > np.percentile(rms, 40)
    flat = librosa.feature.spectral_flatness(y=yt)[0]
    res["flatness"] = round(float(flat[voiced[: len(flat)]].mean()), 4)
    res["clip_pct"] = round(float((np.abs(y) > 0.995).mean() * 100), 3)
    res["max_pause"] = round(longest_inner_pause(yt, sr), 2)
    reasons = []
    if res["flatness"] > 0.045: reasons.append("FAIL buzzy/noisy vocoder (flatness>0.045)")
    elif res["flatness"] > 0.03: reasons.append("WARN some noise/rasp (flatness>0.03)")
    if res["f0_sd_st"] is not None and res["f0_sd_st"] < 2.5: reasons.append("WARN monotone (F0 SD<2.5 st)")
    if res["clip_pct"] > 0.01: reasons.append("FAIL clipping")
    if res["max_pause"] > 0.45: reasons.append(f"WARN draggy inner pause {res['max_pause']}s")
    if text:
        r = syllables(text, lang) / max(dur, 0.1)
        res["syl_s"] = round(r, 2)
        res["wpm"] = round(len(text.split()) / dur * 60)
        lo, hi = RATE.get(lang, RATE["en"])
        if r < lo: reasons.append(f"FAIL too slow ({r:.2f} syl/s < {lo})")
        if r > hi: reasons.append(f"WARN rushed ({r:.2f} syl/s > {hi})")
        if use_asr and asr_model is not None:
            y16, _ = load(path, 16000)
            seg, _ = asr_model.transcribe(y16, language=lang, beam_size=5)
            hyp = " ".join(s.text for s in seg)
            m = difflib.SequenceMatcher(None, norm(text), norm(hyp), autojunk=False).ratio()
            res["asr"] = round(m, 2)
            if m < 0.92: reasons.append(f"FAIL ASR mismatch {m:.2f}: {hyp.strip()!r}")
    res["verdict"] = "FAIL" if any(x.startswith("FAIL") for x in reasons) else ("WARN" if reasons else "PASS")
    res["why"] = reasons
    return res


def mix_report(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    tail = out[out.rfind("Summary:"):]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail); lra = re.search(r"LRA:\s+([\d.]+) LU", tail)
    tp = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    I, L, P = (float(i.group(1)) if i else None), (float(lra.group(1)) if lra else None), (float(tp.group(1)) if tp else None)
    why = []
    if I is not None and abs(I + 14) > 1: why.append(f"integrated {I} LUFS (target -14 ±1)")
    if P is not None and P > -1: why.append(f"true peak {P} dBTP (> -1)")
    return {"file": path, "LUFS": I, "LRA": L, "TP": P, "verdict": "FAIL" if why else "PASS", "why": why}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="*")
    ap.add_argument("--text"); ap.add_argument("--json"); ap.add_argument("--lang", default="ru")
    ap.add_argument("--no-asr", action="store_true"); ap.add_argument("--mix", action="store_true")
    a = ap.parse_args()
    if a.mix:
        for f in a.files:
            print(json.dumps(mix_report(f), ensure_ascii=False))
        return
    items = [{"path": f, "text": a.text} for f in a.files]
    if a.json:
        items += json.load(open(a.json))
    asr_model = None
    if not a.no_asr and any(it.get("text") for it in items):
        try:
            from faster_whisper import WhisperModel
            asr_model = WhisperModel("small", device="cpu", compute_type="int8")
        except Exception as e:  # ASR optional
            print("ASR skipped:", e, file=sys.stderr)
    bad = 0
    for it in items:
        r = analyse(it["path"], it.get("text"), a.lang, not a.no_asr, asr_model)
        bad += r["verdict"] == "FAIL"
        print(json.dumps(r, ensure_ascii=False))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
