#!/usr/bin/env python3
"""ASR round-trip for a finished take: transcript, match against the script, and must-hear words (brand, domain, numbers).
Uses ElevenLabs Scribe (ELEVENLABS_API_KEY) and, if installed, faster-whisper for a second, literal opinion.

  python asr_check.py take.mp3 --text "full script" --lang uz --expect brandname --expect "uch yuz ming"

Scribe "normalises" spelling, whisper is literal and biased toward big languages: a word both hear is safe; a word only one
hears needs a human listen. Never grade an accent with this — only wrong or missing words."""
import argparse, difflib, json, os, re, subprocess, sys

ISO3 = {"uz": "uzb", "ru": "rus", "en": "eng", "kk": "kaz", "tg": "tgk"}


def norm(s):
    s = s.lower().replace("ʻ", "'").replace("’", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", re.sub(r"[^\w' ]+", " ", s)).strip()


def scribe(path, lang):
    out = subprocess.run(["curl", "-sS", "-X", "POST", "https://api.elevenlabs.io/v1/speech-to-text", "-H", "xi-api-key: " + os.environ["ELEVENLABS_API_KEY"],
                          "-F", "model_id=scribe_v1", "-F", f"language_code={ISO3.get(lang, lang)}", "-F", f"file=@{path}"], capture_output=True, text=True).stdout
    return json.loads(out).get("text", "")


def whisper(path, lang):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        return None
    m = WhisperModel(os.environ.get("WHISPER_MODEL", "large-v3-turbo"), device="cpu", compute_type="int8")
    seg, _ = m.transcribe(path, language=lang, beam_size=5, temperature=0.0, condition_on_previous_text=False)
    return " ".join(s.text for s in seg)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("audio"); ap.add_argument("--text", default=""); ap.add_argument("--lang", default="uz")
    ap.add_argument("--expect", action="append", default=[]); ap.add_argument("--no-whisper", action="store_true")
    a = ap.parse_args()
    res = {"file": os.path.basename(a.audio)}
    for name, fn in (("scribe", scribe), ("whisper", None if a.no_whisper else whisper)):
        if fn is None:
            continue
        hyp = fn(a.audio, a.lang)
        if hyp is None:
            continue
        r = {"text": hyp.strip()}
        if a.text:
            r["match"] = round(difflib.SequenceMatcher(None, norm(a.text), norm(hyp), autojunk=False).ratio(), 3)
        r["missing"] = [w for w in a.expect if norm(w) not in norm(hyp)]
        res[name] = r
    print(json.dumps(res, ensure_ascii=False, indent=1))
    sys.exit(1 if any(res.get(k, {}).get("missing") for k in ("scribe",)) else 0)
