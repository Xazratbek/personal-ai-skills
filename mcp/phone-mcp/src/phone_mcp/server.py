"""The MCP server: one tool per thing an agent does to a phone.

The first fifteen tools keep the names, parameters and meaning of Phone Harness MCP, which follow
mobile-mcp, so an agent that knows either already knows these. The rest are local extras.
"""
from __future__ import annotations

import functools
import json
import re
import time
from pathlib import Path
from typing import Literal

import anyio
from mcp.server.mcpserver import Context, MCPServer
from mcp.server.mcpserver.utilities.types import Image
from mcp.types import TextContent, ToolAnnotations

from . import __version__, ocr, screenshots
from .devices import AVD_PREFIX, READY_WAIT, Hub, doctor
from .drivers.base import Driver
from .elements import Element, find, number, render
from .errors import PhoneError

INSTRUCTIONS = """Drive phones on this computer, free: iOS simulators, Android emulators and Android phones over adb.

Start with phone_list_available_devices. If one phone is running, every tool uses it without being told; with several, pass its id as `device`. phone_start_device boots one that is not running.

To act on something, phone_tap_element by text or id is the shortest path. phone_list_elements_on_screen shows what is on screen with refs and tap-ready centers; a screenshot helps with layout, and annotate=true numbers the elements on it. Coordinates are screen coordinates: points on iOS, pixels on Android. After a tap or typing, read the screen again rather than assuming it worked."""

READ_ONLY = ToolAnnotations(read_only_hint=True)
TOUCH = ToolAnnotations(read_only_hint=False, destructive_hint=False)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True)

LONG_PRESS_MIN_MS, LONG_PRESS_MAX_MS = 100, 10000
SWIPE_SHARE = 0.4
MAX_OUTPUT_CHARS = 30000


def _point(value) -> int:
    return int(round(float(value)))


def plan_swipe(direction: str, w: float, h: float, x: float | None, y: float | None,
               distance: float | None) -> tuple[int, int, int, int]:
    """The finger's path. With no start named, the gesture is centred on the screen; both ends stay on it."""
    vertical = direction in ("up", "down")
    span = float(distance) if distance else SWIPE_SHARE * (h if vertical else w)
    dx = {"left": -1, "right": 1}.get(direction, 0) * span
    dy = {"up": -1, "down": 1}.get(direction, 0) * span
    x1 = float(x) if x is not None else w / 2 - (dx / 2 if y is None else 0)
    y1 = float(y) if y is not None else h / 2 - (dy / 2 if x is None else 0)

    def clamp(value, high):
        return min(max(value, 0.0), high - 1)
    return (_point(clamp(x1, w)), _point(clamp(y1, h)), _point(clamp(x1 + dx, w)), _point(clamp(y1 + dy, h)))


def describe_phone(phone, screen=None) -> str:
    bits = [f"{phone.id}: {phone.title} ({phone.platform}/{phone.kind})", "ready"]
    if screen:
        bits.append(f"screen {screen[0]}x{screen[1]}")
    return ", ".join(bits)


def _clip(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    return f"[first {len(text) - MAX_OUTPUT_CHARS} characters cut]\n" + text[-MAX_OUTPUT_CHARS:]


def _path(value: str) -> Path:
    return Path(value).expanduser()


def build_server(phones: Hub | None = None) -> MCPServer:
    hub = phones or Hub()
    server = MCPServer(name="phone", title="Phone", version=__version__, instructions=INSTRUCTIONS)
    server.hub = hub

    async def in_thread(fn, *args, **kwargs):
        return await anyio.to_thread.run_sync(functools.partial(fn, *args, **kwargs))

    async def driver_for(device: str | None) -> Driver:
        return await in_thread(hub.driver, device)

    async def on(driver: Driver, fn, *args, **kwargs):
        """One operation at a time per phone: adb and AXe both misbehave when they overlap."""
        def locked():
            with driver.lock:
                return fn(*args, **kwargs)
        return await in_thread(locked)

    def read_screen(driver: Driver, source: str = "auto", interactive_only: bool = False) -> list[Element]:
        elements: list[Element] = []
        tree_error = None
        if source != "ocr":
            try:
                elements = driver.elements()
            except PhoneError as e:
                if source == "accessibility":
                    raise
                tree_error = e
        if source == "ocr" or (source == "auto" and not any(e.text for e in elements)):
            try:
                png = driver.capture()
                elements = ocr.recognize(png, driver.screen_size()) + elements
            except PhoneError:
                if source == "ocr" or tree_error:
                    raise (tree_error or PhoneError("Text recognition is unavailable on this computer.")) from None
        if interactive_only:
            elements = [e for e in elements if e.clickable]
        number(elements)
        hub.remember(driver.id, elements)
        return elements

    # --- phones ------------------------------------------------------------------------------------------------------

    @server.tool(name="phone_list_available_devices", title="List phones", annotations=READ_ONLY)
    async def list_available_devices(ctx: Context, all: bool = False) -> str:
        """List the running phones, whose ids the other tools take as `device`, and the phones that can be started. Older iOS versions are summarised unless `all` is true."""
        running = await in_thread(hub.running)
        lines = []
        if running:
            lines.append("Running phones (pass the id as `device`):")
            for phone in running:
                screen = None
                try:
                    driver = await driver_for(phone.id)
                    screen = await on(driver, driver.screen_size)
                except PhoneError:
                    pass
                lines.append("- " + describe_phone(phone, screen))
        else:
            lines.append("No phone is running. phone_start_device starts one.")
        lines.extend(f"Note: {p}" for p in hub.problems)
        options = await in_thread(hub.startable)
        shown = [p for p in options if all or p.platform != "ios" or p.newest]
        if shown:
            lines.extend(["", "Phones you can start:"])
            lines.extend(f"- {p.title}: platform={p.platform}, kind={p.kind}, device_id={p.id}" for p in shown)
        hidden = len(options) - len(shown)
        if hidden:
            lines.append(f"{hidden} simulators on older iOS versions are not shown; all=true lists them.")
        return "\n".join(lines)

    @server.tool(name="phone_start_device", title="Start a phone",
                 annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=True))
    async def start_device(ctx: Context,
                           platform: Literal["android", "ios"] | None = None,
                           kind: Literal["emulator", "simulator", "device"] | None = None,
                           device_id: str | None = None,
                           minutes: int | None = None,
                           headless: bool = False) -> str:
        """Start a phone and wait until it is ready; returns its device id. With nothing named, an Android emulator starts, or a simulator if there is none. `device_id` comes from phone_list_available_devices, or is a model or AVD name such as "iPhone 17". It keeps running until phone_stop_device, unless `minutes` says when to stop it. `headless` runs it without a window. A phone that is already running is simply returned."""
        starting = await in_thread(hub.begin_start, platform, kind, device_id, headless)
        began = time.monotonic()
        shown = None
        while True:
            try:
                ready, phase = await in_thread(starting.poll)
            except PhoneError:
                await in_thread(starting.abort)
                raise
            if ready:
                break
            elapsed = time.monotonic() - began
            if elapsed >= READY_WAIT:
                await in_thread(starting.abort)
                raise PhoneError(f"Gave up after {READY_WAIT}s waiting for {starting.phone.title}, and stopped it.")
            if phase != shown:
                shown = phase
                try:
                    await ctx.report_progress(elapsed, READY_WAIT, phase)
                except Exception:   # a client without a progress token
                    pass
            await anyio.sleep(1.5)
        device = starting.id or starting.phone.id
        if device.startswith(AVD_PREFIX):
            raise PhoneError(f"{starting.phone.title} started but could not be identified.")
        driver = await driver_for(device)
        screen = await on(driver, driver.screen_size)
        ends = ""
        if minutes:
            await in_thread(hub.stop_after, device, max(1, int(minutes)))
            ends = f" It stops in {max(1, int(minutes))} min unless phone_stop_device is called first."
        return (f"Started {starting.phone.title} as device {device}. Screen {screen[0]}x{screen[1]}.{ends}"
                f"{starting.note} Pass device=\"{device}\" to the other tools.")

    @server.tool(name="phone_stop_device", title="Stop a phone",
                 annotations=ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True))
    async def stop_device(ctx: Context, device: str | None = None) -> str:
        """Shut down an emulator or simulator. What it saved stays for next time; anything unsaved is lost. A real phone is left on."""
        stopped = await in_thread(hub.stop, device)
        return f"Stopped device {stopped}."

    # --- the screen --------------------------------------------------------------------------------------------------

    @server.tool(name="phone_get_screen_size", title="Screen size", annotations=READ_ONLY)
    async def get_screen_size(ctx: Context, device: str | None = None) -> str:
        """The phone's screen size in the coordinate space the tap and swipe tools use."""
        driver = await driver_for(device)
        w, h = await on(driver, driver.screen_size)
        return f"Screen is {w}x{h}, origin top-left. Taps and swipes take these coordinates."

    @server.tool(name="phone_take_screenshot", title="Take a screenshot", annotations=READ_ONLY,
                 structured_output=False)
    async def take_screenshot(ctx: Context, device: str | None = None, max_size: int = screenshots.DEFAULT_MAX_SIZE,
                              scale: float | None = None, annotate: bool = False) -> list:
        """Take a screenshot. The image is usually smaller than the screen; the text before it says how to convert a point you see into screen coordinates. `annotate` draws a numbered box on each element, matching the refs phone_tap_element takes. Do not reuse an old screenshot: the screen changes."""
        driver = await driver_for(device)

        def shoot():
            png = driver.capture()
            screen = driver.screen_size()
            marks = read_screen(driver) if annotate else None
            size = screenshots.target_size(screenshots.image_size(png), screen, max_size, scale)
            return screenshots.encode(png, size, "JPEG", marks, screen), size, screen, marks
        data, size, screen, marks = await on(driver, shoot)
        note = screenshots.describe_mapping(size, screen)
        if marks:
            note += "\n" + render(marks, screen)
        return [TextContent(type="text", text=note), Image(data=data, format="jpeg").to_image_content()]

    @server.tool(name="phone_save_screenshot", title="Save a screenshot", annotations=TOUCH)
    async def save_screenshot(ctx: Context, save_to: str, device: str | None = None, max_size: int | None = None,
                              scale: float | None = None) -> str:
        """Save a screenshot to a file on this computer, as PNG, JPEG or WebP according to the file's extension. Full size unless `max_size` or `scale` says otherwise."""
        path = _path(save_to)
        fmt = screenshots.SAVE_FORMATS.get(path.suffix.lower())
        if not fmt:
            raise PhoneError(f"Name the file .png, .jpg or .webp; got {path.name!r}.")
        driver = await driver_for(device)
        png = await on(driver, driver.capture)
        full = screenshots.image_size(png)
        if fmt == "PNG" and not max_size and not scale:
            data, size = png, full
        else:
            size = screenshots.target_size(full, None, max_size, scale)
            data = await in_thread(screenshots.encode, png, size, fmt)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return f"Saved {size[0]}x{size[1]} {fmt} to {path}."

    @server.tool(name="phone_list_elements_on_screen", title="List what is on screen", annotations=READ_ONLY)
    async def list_elements_on_screen(ctx: Context, device: str | None = None,
                                      format: Literal["text", "json"] = "text", interactive_only: bool = False,
                                      source: Literal["auto", "accessibility", "ocr"] = "auto") -> str:
        """List what is on screen with the center of each element, ready to tap, and a ref for phone_tap_element. It comes from the accessibility tree, so controls with no visible text appear too. When a screen exposes no text, as games and some Flutter apps do, `auto` reads the pixels instead. Call it again after the screen changes."""
        driver = await driver_for(device)

        def read():
            return read_screen(driver, source, interactive_only), driver.screen_size()
        elements, screen = await on(driver, read)
        if format == "json":
            return json.dumps([e.to_json() for e in elements], ensure_ascii=False)
        return render(elements, screen)

    # --- touching it -------------------------------------------------------------------------------------------------

    @server.tool(name="phone_click_on_screen_at_coordinates", title="Tap", annotations=TOUCH)
    async def click_on_screen_at_coordinates(ctx: Context, x: float, y: float, device: str | None = None) -> str:
        """Tap the screen at (x, y) in screen coordinates, such as a center from phone_list_elements_on_screen."""
        driver = await driver_for(device)
        await on(driver, driver.tap, _point(x), _point(y))
        hub.touched(driver.id)
        return f"Tapped ({_point(x)}, {_point(y)})."

    @server.tool(name="phone_double_tap", title="Double tap", annotations=TOUCH)
    async def double_tap(ctx: Context, x: float, y: float, device: str | None = None) -> str:
        """Tap twice quickly at (x, y) in screen coordinates."""
        driver = await driver_for(device)
        await on(driver, driver.double_tap, _point(x), _point(y))
        hub.touched(driver.id)
        return f"Double-tapped ({_point(x)}, {_point(y)})."

    @server.tool(name="phone_long_press_on_screen_at_coordinates", title="Long press", annotations=TOUCH)
    async def long_press_on_screen_at_coordinates(ctx: Context, x: float, y: float, duration: int = 800,
                                                  device: str | None = None) -> str:
        """Press and hold at (x, y) in screen coordinates for `duration` milliseconds (default 800, limited to 100-10000)."""
        ms = max(LONG_PRESS_MIN_MS, min(int(duration), LONG_PRESS_MAX_MS))
        driver = await driver_for(device)
        await on(driver, driver.long_press, _point(x), _point(y), ms / 1000)
        hub.touched(driver.id)
        return f"Long-pressed ({_point(x)}, {_point(y)}) for {ms} ms."

    @server.tool(name="phone_swipe_on_screen", title="Swipe", annotations=TOUCH)
    async def swipe_on_screen(ctx: Context, direction: Literal["up", "down", "left", "right"],
                              x: float | None = None, y: float | None = None, distance: float | None = None,
                              duration: int = 300, device: str | None = None) -> str:
        """Swipe in a direction: the way the finger moves, so "up" reveals what is below. Starts at (x, y), or centred on the screen when neither is given, and travels `distance` (default 40% of the screen) in `duration` milliseconds."""
        driver = await driver_for(device)
        w, h = await on(driver, driver.screen_size)
        x1, y1, x2, y2 = plan_swipe(direction, w, h, x, y, distance)
        await on(driver, driver.swipe, x1, y1, x2, y2, max(50, int(duration)) / 1000)
        hub.touched(driver.id)
        return f"Swiped {direction} from ({x1}, {y1}) to ({x2}, {y2})."

    @server.tool(name="phone_drag", title="Drag", annotations=TOUCH)
    async def drag(ctx: Context, x1: float, y1: float, x2: float, y2: float, duration: int = 800,
                   device: str | None = None) -> str:
        """Drag slowly from (x1, y1) to (x2, y2) over `duration` milliseconds: for sliders, reordering and moving things, where a swipe would be too fast."""
        driver = await driver_for(device)
        await on(driver, driver.drag, _point(x1), _point(y1), _point(x2), _point(y2), max(100, int(duration)) / 1000)
        hub.touched(driver.id)
        return f"Dragged from ({_point(x1)}, {_point(y1)}) to ({_point(x2)}, {_point(y2)})."

    @server.tool(name="phone_type_keys", title="Type text", annotations=TOUCH)
    async def type_keys(ctx: Context, text: str, submit: bool = False, clear: bool = False,
                        method: Literal["auto", "keys", "paste"] = "auto", device: str | None = None) -> str:
        """Type text into the focused field. Tap the field first so it has focus. Any language works, emoji too. `clear` empties the field first; `submit` presses Enter afterwards. `method` is best left on auto: on iOS it pastes anything keystrokes would change through smart punctuation or autocorrect, and on Android it uses a helper keyboard for non-ASCII. `keys` forces real keystrokes, for PIN pads and games."""
        driver = await driver_for(device)

        def run_typing():
            if clear:
                driver.clear_text()
            driver.type_text(text, method)
            if submit:
                driver.press_enter()
        await on(driver, run_typing)
        hub.touched(driver.id)
        cleared = "Cleared the field and typed" if clear else "Typed"
        return f"{cleared} {len(text)} characters" + (" and pressed Enter." if submit else ".")

    @server.tool(name="phone_press_button", title="Press a button", annotations=TOUCH)
    async def press_button(ctx: Context, button: Literal["HOME", "BACK", "APP_SWITCHER", "ENTER"],
                           device: str | None = None) -> str:
        """Press a system button: HOME, BACK, APP_SWITCHER or ENTER. An iPhone has no Back button, so BACK there taps the app's own or swipes in from the left edge."""
        driver = await driver_for(device)
        note = await on(driver, driver.press, button)
        hub.touched(driver.id)
        return f"Pressed {button}" + (f": {note}." if note else ".")

    # --- finding and acting on elements ------------------------------------------------------------------------------

    def by_reading_pixels(driver: Driver, elements: list[Element], text: str | None, exact: bool) -> list[Element]:
        """Last resort for text the tree does not hold, such as web content and system alerts."""
        if not text:
            return []
        try:
            matches = find(read_screen(driver, "ocr"), text=text, exact=exact)
        except PhoneError:
            matches = []
        if not matches:
            hub.remember(driver.id, elements)
        return matches

    def locate_element(driver: Driver, text, id, type, exact, timeout) -> tuple[Element, list[Element]]:
        deadline = time.monotonic() + max(0.0, float(timeout))
        while True:
            elements = read_screen(driver)
            matches = find(elements, text=text, id=id, type=type, exact=exact)
            if matches:
                return matches[0], matches
            if time.monotonic() >= deadline:
                matches = by_reading_pixels(driver, elements, text, exact) if not (id or type) else []
                if matches:
                    return matches[0], matches
                seen = [e.text for e in elements if e.text][:20]
                wanted = " ".join(f"{k}={v!r}" for k, v in (("text", text), ("id", id), ("type", type)) if v)
                raise PhoneError(f"Nothing on screen matches {wanted}. On screen: {seen or 'no readable text'}.")
            time.sleep(0.4)

    @server.tool(name="phone_tap_element", title="Tap an element", annotations=TOUCH)
    async def tap_element(ctx: Context, ref: str | None = None, text: str | None = None, id: str | None = None,
                          type: str | None = None, exact: bool = False, index: int = 0, timeout: float = 0.0,
                          long_press: bool = False, device: str | None = None) -> str:
        """Tap an element without working out coordinates: by `ref` from phone_list_elements_on_screen, or by `text`, `id` (accessibility id or resource id) and `type` ("button", "textfield", "switch"). Text matches ignore case and may be partial unless `exact`; the best match wins, and `index` picks another. `timeout` waits that many seconds for it to appear. `long_press` holds instead of tapping."""
        driver = await driver_for(device)

        def act():
            note = ""
            count = 1
            if ref:
                elements, age, dirty = hub.recall(driver.id)
                element = next((e for e in elements if e.ref == ref), None)
                if element is None:
                    raise PhoneError(f"No element {ref} in the last list; list the elements again.")
                if dirty:
                    note = f" The screen may have changed in the {age:.0f}s since that list."
            else:
                _best, matches = locate_element(driver, text, id, type, exact, timeout)
                count = len(matches)
                if index >= count or index < 0:
                    raise PhoneError(f"index {index} is out of range: {count} elements match.")
                element = matches[index]
            x, y = driver.tap_point(element)
            if long_press:
                driver.long_press(_point(x), _point(y), 0.8)
            else:
                driver.tap(_point(x), _point(y))
            if count > 1:
                note += f" {count} elements matched; index selects another."
            return element, x, y, note
        element, x, y, note = await on(driver, act)
        hub.touched(driver.id)
        verb = "Long-pressed" if long_press else "Tapped"
        return f"{verb} \"{element.label}\" ({element.type}) at ({_point(x)}, {_point(y)}).{note}"

    @server.tool(name="phone_wait_for_element", title="Wait for an element", annotations=READ_ONLY)
    async def wait_for_element(ctx: Context, text: str | None = None, id: str | None = None, type: str | None = None,
                               exact: bool = False, gone: bool = False, timeout: float = 10.0,
                               device: str | None = None) -> str:
        """Wait until an element appears, or with `gone` until it disappears, for up to `timeout` seconds. Returns where it is."""
        driver = await driver_for(device)

        def check(out_of_time: bool) -> list[Element]:
            elements = read_screen(driver)
            found = find(elements, text=text, id=id, type=type, exact=exact)
            if not found and out_of_time and not (id or type):
                found = by_reading_pixels(driver, elements, text, exact)
            return found

        began = time.monotonic()
        while True:
            matches = await on(driver, check, time.monotonic() - began >= timeout)
            elapsed = time.monotonic() - began
            if gone and not matches:
                return f"It is gone, after {elapsed:.1f}s."
            if matches and not gone:
                e = matches[0]
                return f"Found \"{e.label}\" ({e.type}) at ({_point(e.x)}, {_point(e.y)}) [{e.ref}] after {elapsed:.1f}s."
            if elapsed >= timeout:
                state = "is still there" if gone else "did not appear"
                raise PhoneError(f"After {timeout:g}s it {state}. phone_list_elements_on_screen shows the screen now.")
            await anyio.sleep(0.4)

    @server.tool(name="phone_scroll_to_element", title="Scroll to an element", annotations=TOUCH)
    async def scroll_to_element(ctx: Context, text: str | None = None, id: str | None = None, type: str | None = None,
                                exact: bool = False, direction: Literal["up", "down", "left", "right"] = "up",
                                max_swipes: int = 12, x: float | None = None, y: float | None = None,
                                device: str | None = None) -> str:
        """Swipe until an element is on screen, then say where it is. `direction` is the way the finger moves, so "up" looks further down the page. `x` and `y` start the swipes inside a particular scrolling area. Stops early once the screen no longer changes."""
        driver = await driver_for(device)

        def search():
            w, h = driver.screen_size()
            previous = None
            for attempt in range(max(1, int(max_swipes)) + 1):
                elements = read_screen(driver)
                matches = find(elements, text=text, id=id, type=type, exact=exact)
                visible = [e for e in matches if h * 0.05 < e.y < h * 0.95]
                if visible:
                    return visible[0], attempt
                signature = [(e.text, _point(e.y)) for e in elements]
                if signature == previous:
                    raise PhoneError(f"Reached the end after {attempt} swipes without finding it.")
                previous = signature
                x1, y1, x2, y2 = plan_swipe(direction, w, h, x, y, None)
                driver.swipe(x1, y1, x2, y2, 0.4)
                time.sleep(0.6)
            raise PhoneError(f"Not found after {max_swipes} swipes.")
        element, swipes = await on(driver, search)
        return (f"Found \"{element.label}\" ({element.type}) at ({_point(element.x)}, {_point(element.y)}) "
                f"[{element.ref}] after {swipes} swipes.")

    @server.tool(name="phone_wait_for_idle", title="Wait for the screen to settle", annotations=READ_ONLY)
    async def wait_for_idle(ctx: Context, timeout: float = 8.0, device: str | None = None) -> str:
        """Wait until the screen stops changing: after a tap that starts a transition or a load, for up to `timeout` seconds."""
        driver = await driver_for(device)
        began = time.monotonic()
        previous = await on(driver, driver.capture)
        settled = 0
        while time.monotonic() - began < timeout:
            await anyio.sleep(0.3)
            current = await on(driver, driver.capture)
            settled = settled + 1 if await in_thread(screenshots.same_screen, previous, current) else 0
            previous = current
            if settled >= 2:
                return f"The screen settled after {time.monotonic() - began:.1f}s."
        return f"The screen was still changing after {timeout:g}s."

    # --- apps --------------------------------------------------------------------------------------------------------

    @server.tool(name="phone_list_apps", title="List apps", annotations=READ_ONLY)
    async def list_apps(ctx: Context, include_system: bool = False, device: str | None = None) -> str:
        """List the apps installed on the phone: package ids on Android, bundle ids on iOS. `include_system` adds the built-in ones. Any of them can be passed to phone_launch_app."""
        driver = await driver_for(device)
        apps = await on(driver, driver.list_apps, include_system)
        if apps:
            return "\n".join(str(a) for a in apps)
        return "No user apps are installed. include_system=true lists the built-in ones."

    @server.tool(name="phone_launch_app", title="Launch an app", annotations=TOUCH)
    async def launch_app(ctx: Context, name: str, device: str | None = None) -> str:
        """Open an app by the name on its icon ("Settings", "Notes", "Chrome") or by its package or bundle id."""
        driver = await driver_for(device)
        opened = await on(driver, driver.launch_app, name)
        hub.touched(driver.id)
        return f"Launched {opened}."

    @server.tool(name="phone_get_foreground_app", title="Foreground app", annotations=READ_ONLY)
    async def get_foreground_app(ctx: Context, device: str | None = None) -> str:
        """Which app is in front right now."""
        driver = await driver_for(device)
        current = await on(driver, driver.foreground_app)
        return f"Foreground app: {current}" if current else "No app is in the foreground; the phone is on its home screen."

    @server.tool(name="phone_terminate_app", title="Close an app", annotations=DESTRUCTIVE)
    async def terminate_app(ctx: Context, name: str, device: str | None = None) -> str:
        """Force-quit an app, for a fresh launch or to test restoring state."""
        driver = await driver_for(device)
        return f"Terminated {await on(driver, driver.terminate_app, name)}."

    @server.tool(name="phone_install_app", title="Install an app", annotations=TOUCH)
    async def install_app(ctx: Context, path: str, device: str | None = None) -> str:
        """Install from a file on this computer: an .apk on Android, a simulator-built .app on iOS."""
        target = _path(path)
        if not target.exists():
            raise PhoneError(f"No such file: {target}")
        driver = await driver_for(device)
        return f"Installed {await on(driver, driver.install_app, target)}."

    @server.tool(name="phone_uninstall_app", title="Uninstall an app", annotations=DESTRUCTIVE)
    async def uninstall_app(ctx: Context, name: str, device: str | None = None) -> str:
        """Remove an app and all its data from the phone."""
        driver = await driver_for(device)
        return f"Uninstalled {await on(driver, driver.uninstall_app, name)}."

    @server.tool(name="phone_clear_app_data", title="Clear an app's data", annotations=DESTRUCTIVE)
    async def clear_app_data(ctx: Context, name: str, device: str | None = None) -> str:
        """Erase an app's data and close it, back to a first launch: logins, settings and files are lost."""
        driver = await driver_for(device)
        return f"Cleared the data of {await on(driver, driver.clear_app_data, name)}."

    @server.tool(name="phone_set_permission", title="Set an app permission", annotations=TOUCH)
    async def set_permission(ctx: Context, app: str, permission: str,
                             action: Literal["grant", "revoke", "reset"] = "grant", device: str | None = None) -> str:
        """Grant or revoke a permission without the system prompt: camera, microphone, location, contacts, calendar or photos. Android also takes notifications, phone, sms or a full android.permission.* name. On Android, reset means revoke. Changing one can make the system restart the app."""
        driver = await driver_for(device)
        target = await on(driver, driver.set_permission, app, permission, action)
        return f"Did {action} {permission} for {target}."

    @server.tool(name="phone_open_url", title="Open a URL", annotations=TOUCH)
    async def open_url(ctx: Context, url: str, device: str | None = None) -> str:
        """Open a web page or a deep link (myapp://screen) as if tapped from outside the app. On iOS the system's "Open in app?" prompt is accepted."""
        driver = await driver_for(device)
        await on(driver, driver.open_url, url)
        hub.touched(driver.id)
        return f"Opened {url}."

    # --- system ------------------------------------------------------------------------------------------------------

    @server.tool(name="phone_doctor", title="Check the setup", annotations=READ_ONLY)
    async def phone_doctor(ctx: Context) -> str:
        """Check what this computer has for driving phones, and how to install what is missing."""
        return "\n".join(await in_thread(doctor))

    @server.tool(name="phone_get_device_info", title="Device info", annotations=READ_ONLY)
    async def get_device_info(ctx: Context, device: str | None = None) -> str:
        """Model, OS version, screen, appearance and, on Android, API level, locale and battery."""
        driver = await driver_for(device)
        data = await on(driver, driver.info)
        return "\n".join(f"{k}: {v}" for k, v in data.items() if v not in (None, ""))

    @server.tool(name="phone_set_appearance", title="Dark or light mode", annotations=TOUCH)
    async def set_appearance(ctx: Context, mode: Literal["dark", "light"], device: str | None = None) -> str:
        """Switch the phone between dark and light mode. Says what it was before, so it can be put back."""
        driver = await driver_for(device)

        def change():
            before = driver.get_appearance()
            driver.set_appearance(mode)
            return before
        before = await on(driver, change)
        hub.touched(driver.id)
        return f"Appearance is now {mode}; it was {before}."

    @server.tool(name="phone_set_location", title="Set GPS location", annotations=TOUCH)
    async def set_location(ctx: Context, latitude: float, longitude: float, device: str | None = None) -> str:
        """Set the location a simulator or emulator reports. A real phone cannot be spoofed from here."""
        driver = await driver_for(device)
        await on(driver, driver.set_location, latitude, longitude)
        return f"Location is now {latitude}, {longitude}."

    @server.tool(name="phone_set_orientation", title="Rotate the screen", annotations=TOUCH)
    async def set_orientation(ctx: Context, orientation: Literal["portrait", "landscape", "auto"],
                              device: str | None = None) -> str:
        """Rotate an Android phone: portrait, landscape, or auto to follow the sensor again. Simulators cannot be rotated from outside Simulator.app."""
        driver = await driver_for(device)
        await on(driver, driver.set_orientation, orientation)
        hub.touched(driver.id)
        return f"Orientation is now {orientation}."

    @server.tool(name="phone_get_clipboard", title="Read the clipboard", annotations=READ_ONLY)
    async def get_clipboard(ctx: Context, device: str | None = None) -> str:
        """Read the phone's clipboard as text."""
        driver = await driver_for(device)
        return await on(driver, driver.clipboard_get) or "The clipboard is empty."

    @server.tool(name="phone_set_clipboard", title="Set the clipboard", annotations=TOUCH)
    async def set_clipboard(ctx: Context, text: str, device: str | None = None) -> str:
        """Put text on the phone's clipboard, in any language."""
        driver = await driver_for(device)
        await on(driver, driver.clipboard_set, text)
        return f"The clipboard holds {len(text)} characters."

    @server.tool(name="phone_get_logs", title="Read logs", annotations=READ_ONLY)
    async def get_logs(ctx: Context, app: str | None = None, seconds: int = 60, grep: str | None = None,
                       max_lines: int = 200, device: str | None = None) -> str:
        """Read recent device logs (logcat on Android, the unified log on iOS): the last `seconds`, for one `app` if named, keeping lines that match the regular expression `grep`, and at most the newest `max_lines`."""
        driver = await driver_for(device)
        out = await on(driver, driver.logs, app, seconds)
        lines = out.splitlines()
        if grep:
            try:
                pattern = re.compile(grep)
            except re.error:
                pattern = re.compile(re.escape(grep))
            lines = [line for line in lines if pattern.search(line)]
        lines = lines[-max(1, int(max_lines)):]
        return _clip("\n".join(lines)) if lines else "No log lines matched."

    @server.tool(name="phone_start_recording", title="Start recording the screen", annotations=TOUCH)
    async def start_recording(ctx: Context, save_to: str | None = None, device: str | None = None) -> str:
        """Start recording the screen to an MP4 on this computer; phone_stop_recording finishes it. The default file is in ~/Movies/phone-mcp. Android stops by itself after 180 seconds."""
        driver = await driver_for(device)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        target = _path(save_to) if save_to else Path.home() / f"Movies/phone-mcp/{driver.id}-{stamp}.mp4"
        await on(driver, driver.start_recording, target)
        return f"Recording to {target}."

    @server.tool(name="phone_stop_recording", title="Stop recording the screen", annotations=TOUCH)
    async def stop_recording(ctx: Context, device: str | None = None) -> str:
        """Finish the recording and report where the MP4 is."""
        driver = await driver_for(device)
        path = await on(driver, driver.stop_recording)
        return f"Saved {path.stat().st_size / 1_000_000:.1f} MB to {path}."

    @server.tool(name="phone_send_notification", title="Send a notification", annotations=TOUCH)
    async def send_notification(ctx: Context, title: str, body: str, app: str | None = None,
                                device: str | None = None) -> str:
        """Show a notification. On iOS it is a simulated push to `app` (the foreground app by default), which must have notification permission. On Android it is posted by the shell."""
        driver = await driver_for(device)
        await on(driver, driver.send_notification, title, body, app)
        return f"Sent the notification {title!r}."

    @server.tool(name="phone_add_media", title="Add a photo or video", annotations=TOUCH)
    async def add_media(ctx: Context, path: str, device: str | None = None) -> str:
        """Copy a photo or video from this computer into the phone's gallery, for testing pickers and uploads."""
        target = _path(path)
        if not target.is_file():
            raise PhoneError(f"No such file: {target}")
        driver = await driver_for(device)
        return f"Added {await on(driver, driver.add_media, target)} to the gallery."

    @server.tool(name="phone_shell", title="Run a command on the phone", annotations=DESTRUCTIVE)
    async def phone_shell(ctx: Context, command: str, timeout: float = 30.0, device: str | None = None) -> str:
        """Run a command on the phone, for anything the other tools do not cover: `adb shell` on Android, `simctl spawn` on iOS. It runs with the phone's shell privileges and can change or delete data."""
        driver = await driver_for(device)
        return _clip(await on(driver, driver.shell, command, float(timeout))) or "(no output)"

    # --- several steps at once ---------------------------------------------------------------------------------------

    steps = {
        "tap": click_on_screen_at_coordinates, "double_tap": double_tap,
        "long_press": long_press_on_screen_at_coordinates, "swipe": swipe_on_screen, "drag": drag,
        "type": type_keys, "press": press_button, "tap_element": tap_element, "wait_for": wait_for_element,
        "scroll_to": scroll_to_element, "wait_idle": wait_for_idle, "launch": launch_app, "open_url": open_url,
        "terminate": terminate_app,
    }

    @server.tool(name="phone_batch", title="Run several actions", annotations=TOUCH)
    async def phone_batch(ctx: Context, actions: list[dict], stop_on_error: bool = True,
                          device: str | None = None) -> str:
        """Run several actions in order, saving a round trip per action. Each is {"action": name, ...the arguments of the matching tool}; the names are tap, double_tap, long_press, swipe, drag, type, press, tap_element, wait_for, scroll_to, wait_idle, launch, open_url, terminate, and sleep with `seconds`. For example [{"action":"tap_element","text":"Email"},{"action":"type","text":"me@x.uz"},{"action":"press","button":"ENTER"}]. Stops at the first failure unless `stop_on_error` is false."""
        driver = await driver_for(device)
        lines = []
        failed = False
        for number_, step in enumerate(actions, 1):
            params = dict(step)
            name = str(params.pop("action", ""))
            params.pop("device", None)
            try:
                if name == "sleep":
                    seconds = float(params.get("seconds", 1))
                    await anyio.sleep(seconds)
                    result = f"Slept {seconds:g}s."
                elif name in steps:
                    result = await steps[name](ctx, device=driver.id, **params)
                else:
                    raise PhoneError(f"Unknown action {name!r}. Known: sleep, {', '.join(steps)}.")
            except (PhoneError, TypeError) as e:
                failed = True
                lines.append(f"{number_}. {name}: FAILED: {e}")
                if stop_on_error:
                    raise PhoneError("\n".join(lines) + f"\nStopped; {len(actions) - number_} actions did not run.") from None
                continue
            lines.append(f"{number_}. {name}: {result}")
        if failed:
            lines.append("Some actions failed.")
        return "\n".join(lines)

    return server
