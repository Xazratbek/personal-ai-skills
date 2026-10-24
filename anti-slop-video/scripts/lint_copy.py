#!/usr/bin/env python3
"""Lint video script copy for AI-slop tells.

Input: one or more files. Each is either
  * JSON  {"<id>": {"lines": ["...", ...]}, ...}  (a batch), or
  * plain text, one script per file, one line per row.
Checks: banned hype/filler phrases, duplicate openers/endings across the batch, metronome line lengths,
missing specifics (digits/times/places), exclamation spam, near-duplicate lines between videos.
Exit code 1 if any FAIL, 0 otherwise. Usage: python lint_copy.py content.json [more files]
"""
import json, re, statistics, sys
from pathlib import Path

BANNED = [
    # ru
    r"революцион", r"уникальн", r"инновацион", r"лучш(ий|ая|ее|ие)\b", r"невероят", r"прорыв", r"экосистем",
    r"в современном мире", r"не имеет аналогов", r"абсолютно бесплатно",
    # en
    r"revolutionar", r"game[- ]chang", r"cutting[- ]edge", r"seamless", r"unlock", r"best[- ]in[- ]class",
    r"in today'?s fast[- ]paced", r"incredible", r"ecosystem", r"next[- ]level",
    # uz
    r"\bnoyob\b", r"\beng yaxshi\b", r"\bajoyib\b", r"\bbeqiyos\b",
]
BANNED_RE = re.compile("|".join(BANNED), re.I)
SPECIFIC_RE = re.compile(r"\d|[А-ЯA-Z][а-яa-z]{3,}.*(ар|ад|ов|ев|ск)|Чиланзар|Юнусабад|Мирабад|Ташкент|Toshkent", re.U)


def load(path: Path):
    t = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        d = json.loads(t)
        return {f"{path.stem}:{k}": v["lines"] for k, v in d.items()}
    return {path.stem: [l.strip() for l in t.splitlines() if l.strip()]}


def norm(s):
    return re.sub(r"[^\w]+", " ", s.lower().replace("ё", "е")).strip()


def main(paths):
    batch = {}
    for p in paths:
        batch.update(load(Path(p)))
    fails, warns = [], []
    for vid, lines in batch.items():
        for l in lines:
            m = BANNED_RE.search(l)
            if m: fails.append(f"{vid}: banned phrase «{m.group(0)}» in: {l}")
            if l.count("!") > 1: warns.append(f"{vid}: exclamation spam: {l}")
        counts = [len(l.split()) for l in lines]
        if len(counts) >= 4:
            cv = statistics.pstdev(counts) / max(statistics.mean(counts), 1)
            if cv < 0.28: warns.append(f"{vid}: metronome rhythm (words/line {counts}, variation {cv:.2f} < 0.28) — mix short fragments and longer lines")
        body = " ".join(lines)
        if not SPECIFIC_RE.search(body):
            warns.append(f"{vid}: no concrete specific (number, time, district/place) found")
    ends, starts = {}, {}
    for vid, lines in batch.items():
        if not lines: continue
        ends.setdefault(norm(lines[-1]), []).append(vid)
        starts.setdefault(" ".join(norm(lines[0]).split()[:2]), []).append(vid)
    for k, v in ends.items():
        if len(v) > 1: fails.append(f"identical closing line in {v}: «{k}»")
    for k, v in starts.items():
        if len(v) > 1: warns.append(f"same opener ({k}…) in {v}")
    seen = {}
    for vid, lines in batch.items():
        for l in lines:
            n = norm(l)
            if len(n.split()) >= 4:
                if n in seen and seen[n] != vid: warns.append(f"duplicate line in {seen[n]} and {vid}: {l}")
                seen.setdefault(n, vid)
    print(f"checked {len(batch)} script(s), {sum(len(v) for v in batch.values())} lines")
    for f in fails: print("FAIL", f)
    for w in warns: print("WARN", w)
    if not fails and not warns: print("clean")
    return 1 if fails else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sys.exit(main(sys.argv[1:]))
