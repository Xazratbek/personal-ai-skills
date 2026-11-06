"""On-device text recognition with Apple Vision, for screens with no accessibility tree (games, canvas, Flutter)."""
from __future__ import annotations

import hashlib
import json
import tempfile
from importlib import resources
from pathlib import Path

from .elements import Element
from .errors import PhoneError
from .locate import xcrun
from .proc import run

CACHE = Path.home() / "Library/Caches/phone-mcp"


def _binary() -> Path:
    source = resources.files("phone_mcp").joinpath("assets/ocr.swift").read_bytes()
    target = CACHE / f"ocr-{hashlib.sha256(source).hexdigest()[:12]}"
    if target.is_file():
        return target
    tool = xcrun()
    if not tool:
        raise PhoneError("Text recognition needs Xcode's command line tools (`xcode-select --install`).")
    CACHE.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "ocr.swift"
        src.write_bytes(source)
        built = Path(tmp) / "ocr"
        run([tool, "swiftc", "-O", str(src), "-o", str(built)], timeout=180)
        built.replace(target)
    return target


def recognize(png: bytes, screen: tuple[int, int]) -> list[Element]:
    binary = _binary()
    with tempfile.NamedTemporaryFile(suffix=".png") as image:
        image.write(png)
        image.flush()
        found = json.loads(run([str(binary), image.name], timeout=60).out or b"[]")
    elements = []
    for item in found:
        text = str(item.get("text") or "").strip()
        if not text:
            continue
        x, y, w, h = (float(item[k]) for k in ("x", "y", "w", "h"))
        elements.append(Element(text=text, x=(x + w / 2) * screen[0], y=(y + h / 2) * screen[1],
                                w=w * screen[0], h=h * screen[1], type="Text", source="pixels"))
    return elements
