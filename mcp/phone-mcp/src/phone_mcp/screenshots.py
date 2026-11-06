"""Screenshots sized for a model, and how they map back to tap coordinates.

Where the screen's coordinate space fits inside `max_size`, the image is resized to exactly that
space, so a point seen in the image is the point to tap and no multiplication can go wrong.
"""
from __future__ import annotations

from io import BytesIO

from PIL import Image as PILImage
from PIL import ImageChops, ImageDraw, ImageFont, ImageStat

from .elements import Element

DEFAULT_MAX_SIZE = 1024
JPEG_QUALITY = 80
SAVE_FORMATS = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}
MIME = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}


def image_size(data: bytes) -> tuple[int, int]:
    with PILImage.open(BytesIO(data)) as im:
        return im.size


def target_size(image: tuple[int, int], screen: tuple[int, int] | None, max_size: int | None,
                scale: float | None) -> tuple[int, int]:
    w, h = image
    if scale and scale > 0:
        factor = min(float(scale), 1.0)
        return max(1, round(w * factor)), max(1, round(h * factor))
    if max_size and max_size > 0:
        if screen and max(screen) <= max_size and screen != image and max(screen) < max(image):
            return screen
        if max(w, h) > max_size:
            factor = max_size / max(w, h)
            return max(1, round(w * factor)), max(1, round(h * factor))
    return w, h


def encode(png: bytes, size: tuple[int, int], fmt: str = "JPEG",
           marks: list[Element] | None = None, screen: tuple[int, int] | None = None) -> bytes:
    fmt = fmt.upper()
    with PILImage.open(BytesIO(png)) as im:
        im.load()
        if im.size != size:
            im = im.resize(size, PILImage.LANCZOS)
        if fmt == "JPEG" and im.mode not in ("RGB", "L"):
            im = im.convert("RGB")
        if marks and screen:
            im = _annotate(im.convert("RGB"), marks, screen)
        out = BytesIO()
        if fmt == "JPEG":
            im.save(out, "JPEG", quality=JPEG_QUALITY, optimize=True)
        elif fmt == "WEBP":
            im.save(out, "WEBP", quality=JPEG_QUALITY)
        else:
            im.save(out, "PNG", optimize=True)
        return out.getvalue()


def _annotate(im: PILImage.Image, marks: list[Element], screen: tuple[int, int]) -> PILImage.Image:
    fx, fy = im.width / screen[0], im.height / screen[1]
    draw = ImageDraw.Draw(im)
    font = ImageFont.load_default(size=max(11, round(im.height / 75)))
    for e in marks:
        left, top = (e.x - e.w / 2) * fx, (e.y - e.h / 2) * fy
        right, bottom = (e.x + e.w / 2) * fx, (e.y + e.h / 2) * fy
        draw.rectangle((left, top, right, bottom), outline=(230, 30, 90), width=2)
        tag = e.ref
        box = draw.textbbox((0, 0), tag, font=font)
        tw, th = box[2] - box[0] + 6, box[3] - box[1] + 6
        if right - left > tw * 3 and bottom - top > th:
            # Inside a wide row's far end, since its text usually starts at the left and a tag above would cover the row before.
            tx, ty = min(right, im.width) - tw, max(top, 0)
        else:
            tx, ty = min(max(left, 0), im.width - tw), max(top - th, 0)
        draw.rectangle((tx, ty, tx + tw, ty + th), fill=(230, 30, 90))
        draw.text((tx + 3 - box[0], ty + 3 - box[1]), tag, fill=(255, 255, 255), font=font)
    return im


def describe_mapping(image: tuple[int, int], screen: tuple[int, int] | None) -> str:
    iw, ih = image
    if not screen or min(iw, ih, *screen) <= 0:
        return f"Screenshot is {iw}x{ih}."
    sw, sh = screen
    if (iw, ih) == (sw, sh):
        return f"Screenshot is {iw}x{ih} and its coordinates match the screen."
    return (f"Screenshot is {iw}x{ih}. Screen coordinates are {sw}x{sh}. To tap something you see in this "
            f"screenshot, multiply its x by {sw / iw:.4g} and y by {sh / ih:.4g}.")


def same_screen(a: bytes, b: bytes, tolerance: float = 0.6) -> bool:
    """True when two captures differ by less than `tolerance` grey levels, ignoring the status bar's clock."""
    def small(data: bytes) -> PILImage.Image:
        with PILImage.open(BytesIO(data)) as im:
            grey = im.convert("L")
            return grey.crop((0, round(grey.height * 0.08), grey.width, grey.height)).resize((64, 128))
    return ImageStat.Stat(ImageChops.difference(small(a), small(b))).mean[0] < tolerance
