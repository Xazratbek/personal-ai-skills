"""One model of what is on screen, from either platform's accessibility tree or from OCR."""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from .errors import PhoneError

IOS_INTERACTIVE = {"Button", "Link", "TextField", "SecureTextField", "SearchField", "TextArea", "TextView", "Switch",
                   "CheckBox", "RadioButton", "Slider", "PopUpButton", "ComboBox", "Cell", "Tab", "MenuItem",
                   "Incrementor", "DisclosureTriangle", "SegmentedControl", "Key"}
IOS_TOGGLES = {"Switch", "CheckBox"}
IOS_NOISE = re.compile(r"^(Vertical|Horizontal) scroll bar")
TYPE_ALIASES = {
    "textfield": {"textfield", "edittext", "searchfield", "securetextfield", "textarea", "autocompletetextview"},
    "switch": {"switch", "checkbox", "togglebutton", "switchcompat", "switchmaterial"},
    "button": {"button", "imagebutton", "materialbutton", "appcompatbutton", "floatingactionbutton"},
    "text": {"statictext", "textview", "heading", "text", "appcompattextview", "materialtextview"},
    "image": {"image", "imageview", "appcompatimageview"},
}


@dataclass
class Element:
    text: str
    x: float
    y: float
    w: float
    h: float
    type: str = ""
    id: str = ""
    value: str = ""
    enabled: bool = True
    clickable: bool = False
    checked: bool | None = None
    selected: bool = False
    focused: bool = False
    source: str = "accessibility"
    ref: str = ""

    def to_json(self) -> dict:
        data = {"ref": self.ref, "text": self.text, "x": _point(self.x), "y": _point(self.y),
                "w": _point(self.w), "h": _point(self.h), "type": self.type, "id": self.id, "value": self.value,
                "enabled": self.enabled, "clickable": self.clickable, "selected": self.selected,
                "focused": self.focused, "source": self.source}
        if self.checked is not None:
            data["checked"] = self.checked
        return data

    @property
    def label(self) -> str:
        return self.text or self.value or self.id or self.type


def _point(value) -> int:
    return int(round(float(value)))


def number(elements: list[Element]) -> list[Element]:
    """Reading order, with the refs phone_tap_element accepts."""
    elements.sort(key=lambda e: (round(e.y / 12), e.x))
    for i, element in enumerate(elements, 1):
        element.ref = f"e{i}"
    return elements


def render(elements: list[Element], screen: tuple[int, int] | None) -> str:
    if not elements:
        return "Nothing readable on screen. Take a screenshot to see what is there."
    head = f"Screen is {screen[0]}x{screen[1]}. " if screen else ""
    lines = [head + f"{len(elements)} elements, top to bottom; (x, y) is the center to tap:"]
    for e in elements:
        facts = [e.ref]
        if e.type:
            facts.append(e.type)
        if e.id:
            facts.append(f"id={e.id}")
        if e.value and e.value != e.text:
            facts.append(f"value={e.value!r}")
        if e.checked is not None:
            facts.append("on" if e.checked else "off")
        if not e.enabled:
            facts.append("disabled")
        if e.selected:
            facts.append("selected")
        if e.focused:
            facts.append("focused")
        name = f'"{e.text}"' if e.text else "(no label)"
        lines.append(f"- {name} at ({_point(e.x)}, {_point(e.y)}), {_point(e.w)}x{_point(e.h)} [{', '.join(facts)}]")
    if any(e.source == "pixels" for e in elements):
        lines.append("Positions come from reading the pixels, so a word may be misread.")
    return "\n".join(lines)


def _type_matches(actual: str, wanted: str) -> bool:
    actual, wanted = actual.lower(), wanted.lower()
    if wanted == actual or actual in TYPE_ALIASES.get(wanted, ()):
        return True
    # "text" would otherwise also match TextField.
    return wanted != "text" and wanted in actual


def find(elements: list[Element], *, text: str | None = None, id: str | None = None, type: str | None = None,
         exact: bool = False) -> list[Element]:
    """Matches, best first: exact text, then prefix, then contains; tappable ones ahead of plain ones."""
    if not (text or id or type):
        raise PhoneError("Say what to look for: `text`, `id` or `type`.")
    wanted = text.casefold() if text else None
    scored = []
    for position, e in enumerate(elements):
        if id and not (e.id == id or e.id.endswith(f"/{id}")):
            continue
        if type and not _type_matches(e.type, type):
            continue
        rank = 0
        if wanted is not None:
            rank = _text_rank(wanted, e, exact)
            if rank is None:
                continue
        scored.append((rank, not e.clickable, position, e))
    scored.sort(key=lambda item: item[:3])
    return [item[3] for item in scored]


def _text_rank(wanted: str, e: Element, exact: bool) -> int | None:
    best = None
    for candidate in (e.text, e.value):
        folded = candidate.casefold()
        if not folded:
            continue
        if folded == wanted:
            rank = 0
        elif exact:
            continue
        elif folded.startswith(wanted):
            rank = 1
        elif wanted in folded:
            rank = 2
        else:
            continue
        best = rank if best is None else min(best, rank)
    return best


def _on_screen(left: float, top: float, right: float, bottom: float, screen: tuple[int, int] | None) -> bool:
    if right - left <= 0 or bottom - top <= 0:
        return False
    return screen is None or (right > 0 and bottom > 0 and left < screen[0] and top < screen[1])


# --- Android ---------------------------------------------------------------------------------------------------------

_BOUNDS = re.compile(r"\[(-?\d+),(-?\d+)\]\[(-?\d+),(-?\d+)\]")


def parse_android(xml_bytes: bytes, screen: tuple[int, int] | None = None) -> list[Element]:
    end = xml_bytes.rfind(b"</hierarchy>")
    if end < 0:
        raise PhoneError("The Android accessibility tree came back incomplete.")
    root = ET.fromstring(xml_bytes[:end + len(b"</hierarchy>")])
    screen_area = screen[0] * screen[1] if screen else None
    found: list[Element] = []

    def walk(node, tappable_parent: bool) -> bool:
        """Returns whether this subtree produced a labelled element."""
        match = _BOUNDS.fullmatch(node.get("bounds", ""))
        box = tuple(int(v) for v in match.groups()) if match else (0, 0, 0, 0)
        kind = node.get("class", "").rsplit(".", 1)[-1]
        editable = "EditText" in kind
        own_tap = any(node.get(a) == "true" for a in ("clickable", "long-clickable", "checkable")) or editable
        area = (box[2] - box[0]) * (box[3] - box[1])
        # A clickable container that fills the screen says nothing about its children.
        small = screen_area is None or area < screen_area * 0.5
        passes_tap = tappable_parent or (own_tap and small)
        has_label = False
        for child in node.findall("node"):
            has_label = walk(child, passes_tap) or has_label

        text = (node.get("text") or "").strip()
        desc = (node.get("content-desc") or "").strip()
        label = text or desc
        if not _on_screen(*box, screen):
            return has_label
        rid = node.get("resource-id", "")
        short_id = rid.split(":id/", 1)[1] if ":id/" in rid else rid
        keep = bool(label) or (own_tap and small and not has_label)
        if keep:
            found.append(Element(
                text=label, x=(box[0] + box[2]) / 2, y=(box[1] + box[3]) / 2, w=box[2] - box[0], h=box[3] - box[1],
                type=kind, id=short_id, value=text if editable else "",
                enabled=node.get("enabled") != "false", clickable=own_tap or tappable_parent,
                checked=(node.get("checked") == "true") if node.get("checkable") == "true" else None,
                selected=node.get("selected") == "true", focused=node.get("focused") == "true"))
        return has_label or bool(label)

    for top in root.findall("node"):
        walk(top, False)
    return found


# --- iOS -------------------------------------------------------------------------------------------------------------

def _frame(node: dict) -> tuple[float, float, float, float]:
    frame = node.get("frame") or {}
    return (float(frame.get("x") or 0), float(frame.get("y") or 0),
            float(frame.get("width") or 0), float(frame.get("height") or 0))


def parse_ios(tree: list | dict, screen: tuple[int, int] | None = None) -> list[Element]:
    roots = tree if isinstance(tree, list) else [tree]
    found: list[Element] = []
    seen: set[tuple] = set()

    def walk(node: dict, parent_label: str):
        kind = node.get("type") or ""
        label = (node.get("AXLabel") or node.get("title") or "").strip()
        interactive = kind in IOS_INTERACTIVE or bool(node.get("custom_actions"))
        if IOS_NOISE.match(label):
            return
        x, y, w, h = _frame(node)
        visible = _on_screen(x, y, x + w, y + h, screen)
        value = node.get("AXValue")
        value_text = "" if value is None else str(value).strip()
        uid = (node.get("AXUniqueId") or "").strip()
        # A control's own text repeats its label: Button "General" holds StaticText "General".
        echoes_parent = bool(parent_label) and bool(label) and not interactive and label in parent_label
        structural = kind in ("Application", "Window", "ScrollArea", "Group", "GenericElement", "Other", "")
        keep = visible and not echoes_parent and (
            interactive or (bool(label) and kind != "Application") or (bool(value_text) and not structural))
        if keep:
            key = (label, kind, round(x), round(y))
            if key not in seen:
                seen.add(key)
                checked = None
                if kind in IOS_TOGGLES:
                    checked = value_text in ("1", "true", "on", "On")
                found.append(Element(
                    text=label, x=x + w / 2, y=y + h / 2, w=w, h=h, type=kind, id=uid,
                    value="" if kind in IOS_TOGGLES else value_text, enabled=node.get("enabled") is not False,
                    clickable=interactive, checked=checked))
        inherited = label if interactive else parent_label
        for child in node.get("children") or []:
            walk(child, inherited)

    for root in roots:
        walk(root, "")
    return found
