"""Drives every tool on real phones through a real MCP client over stdio, checking each by reading the result back.

    uv run python tests/e2e/run_e2e.py --ios <udid> --android <serial> [--lifecycle]

It installs a small test app, so point it only at phones you do not mind changing. --lifecycle also shuts each phone
down and boots it again.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "tests/fixtures/build"
ADVERSARIAL = "a b&c|d;e'f\"g(h)i<j>k$l`m*?#~\\ -- ... %s 50% end"
UNICODE = "Salom дунё oʻzbek 日本語 🙂"
FIXTURE = "com.phonemcp.fixture"


class Check(Exception):
    pass


def expect(condition, detail=""):
    if not condition:
        raise Check(str(detail))


class Phone:
    def __init__(self, session: ClientSession, device: str, platform: str, out: Path):
        self.session, self.device, self.platform, self.out = session, device, platform, out
        self.ios = platform == "ios"
        self.called: set[str] = set()
        self.results: list[tuple[str, bool, str, float]] = []

    async def raw(self, tool: str, **args):
        self.called.add(tool)
        return await self.session.call_tool(tool, {"device": self.device, **args})

    async def call(self, tool: str, **args) -> str:
        result = await self.raw(tool, **args)
        text = "\n".join(c.text for c in result.content if getattr(c, "type", None) == "text")
        if result.is_error:
            raise Check(f"{tool} returned an error: {text[:400]}")
        return text

    async def error(self, tool: str, **args) -> str:
        result = await self.raw(tool, **args)
        text = "\n".join(c.text for c in result.content if getattr(c, "type", None) == "text")
        expect(result.is_error, f"{tool} should have failed, returned: {text[:200]}")
        return text

    async def elements(self, **args) -> list[dict]:
        return json.loads(await self.call("phone_list_elements_on_screen", format="json", **args))

    async def by_id(self, element_id: str) -> dict:
        for _ in range(10):
            for e in await self.elements():
                if e["id"] == element_id:
                    return e
            await asyncio.sleep(0.5)
        raise Check(f"no element with id {element_id}")

    async def status(self) -> str:
        return (await self.by_id("status"))["text"]

    async def status_is(self, wanted: str, seconds: float = 5) -> str:
        deadline = time.monotonic() + seconds
        last = ""
        while time.monotonic() < deadline:
            last = await self.status()
            if last == wanted or (wanted.endswith("*") and last.startswith(wanted[:-1])):
                return last
            await asyncio.sleep(0.3)
        raise Check(f"status is {last!r}, wanted {wanted!r}")

    async def field(self) -> str:
        return (await self.by_id("field")).get("value", "")

    async def fresh_app(self):
        await self.call("phone_launch_app", name=FIXTURE)
        await asyncio.sleep(0.8)

    async def step(self, name: str, fn):
        began = time.monotonic()
        try:
            detail = await fn()
            self.results.append((name, True, str(detail or ""), time.monotonic() - began))
            print(f"  PASS {name} ({time.monotonic() - began:.1f}s) {detail or ''}", flush=True)
        except Exception as e:
            self.results.append((name, False, f"{type(e).__name__}: {e}", time.monotonic() - began))
            print(f"  FAIL {name}: {type(e).__name__}: {e}", flush=True)
            shot = self.out / f"fail_{self.platform}_{re.sub(r'[^a-z0-9]+', '_', name.lower())}.png"
            await self.raw("phone_save_screenshot", save_to=str(shot))
            print(f"       screen at failure: {shot}", flush=True)


def host(*argv: str) -> str:
    return subprocess.run(argv, capture_output=True, text=True, timeout=60).stdout


async def run_all(p: Phone, args, adb_path: str | None):
    ios = p.ios
    app_file = BUILD / ("PhoneMcpFixture.app" if ios else "fixture.apk")
    size = {}

    async def setup():
        text = await p.call("phone_doctor")
        expect("MISSING" not in text, text)
        return text.splitlines()[0]
    await p.step("phone_doctor", setup)

    async def devices():
        text = await p.call("phone_list_available_devices")
        expect(p.device in text, text)
        expect("Phones you can start" in text, text)
    await p.step("phone_list_available_devices", devices)

    async def info():
        text = await p.call("phone_get_device_info")
        expect(f"platform: {p.platform}" in text and "screen:" in text, text)
        return " ".join(text.splitlines()[3:5])
    await p.step("phone_get_device_info", info)

    async def screen():
        text = await p.call("phone_get_screen_size")
        m = re.search(r"(\d+)x(\d+)", text)
        size.update(w=int(m.group(1)), h=int(m.group(2)))
        return f"{size['w']}x{size['h']}"
    await p.step("phone_get_screen_size", screen)

    async def install():
        text = await p.call("phone_install_app", path=str(app_file))
        expect(FIXTURE in text, text)
    await p.step("phone_install_app", install)

    async def apps():
        text = await p.call("phone_list_apps")
        expect(FIXTURE in text, text)
        system = await p.call("phone_list_apps", include_system=True)
        expect(("com.apple.Preferences" if ios else "com.android.settings") in system, system[:300])
    await p.step("phone_list_apps", apps)

    async def launch_by_label():
        await p.call("phone_terminate_app", name=FIXTURE)
        text = await p.call("phone_launch_app", name="MCP Fixture")
        expect(FIXTURE in text, text)
        await asyncio.sleep(1)
        front = await p.call("phone_get_foreground_app")
        expect(FIXTURE in front, front)
        return front
    await p.step("phone_launch_app by icon label + phone_get_foreground_app", launch_by_label)

    async def system_app_by_name():
        settings = "com.apple.Preferences" if ios else "com.android.settings"
        text = await p.call("phone_launch_app", name="Settings")
        expect(settings in text, text)
        await asyncio.sleep(1.5)
        front = await p.call("phone_get_foreground_app")
        expect(settings in front, front)
        others = {"Safari": "com.apple.mobilesafari", "Calendar": "com.apple.mobilecal"} if ios else \
            {"Chrome": "com.android.chrome", "Camera": "com.android.camera2"}
        for name, bundle in others.items():
            text = await p.call("phone_launch_app", name=name)
            expect(bundle in text, text)
            await asyncio.sleep(1)
            await p.call("phone_terminate_app", name=name)
    await p.step("phone_launch_app system apps by name", system_app_by_name)

    async def wrong_app():
        text = await p.error("phone_launch_app", name="zzz-no-such-app")
        expect("Candidates" in text, text)
    await p.step("phone_launch_app unknown name explains", wrong_app)

    await p.fresh_app()

    async def elements():
        els = await p.elements()
        ids = {e["id"] for e in els}
        missing = {"status", "field", "tap_btn", "icon_btn", "hold_btn", "double_btn", "toggle"} - ids
        expect(not missing, f"missing {missing}; have {sorted(ids)}")
        text = await p.call("phone_list_elements_on_screen")
        expect('"Tap me" at (' in text and "elements, top to bottom" in text, text[:400])
        only = await p.elements(interactive_only=True)
        expect(only and all(e["clickable"] for e in only) and len(only) < len(els))
        return f"{len(els)} elements, {len(only)} interactive"
    await p.step("phone_list_elements_on_screen", elements)

    async def screenshot():
        r = await p.raw("phone_take_screenshot")
        note, image = r.content
        expect(image.mime_type == "image/jpeg", image.mime_type)
        if ios:
            expect("coordinates match the screen" in note.text, note.text)
        else:
            expect("multiply" in note.text, note.text)
        r2 = await p.raw("phone_take_screenshot", annotate=True)
        import base64
        (p.out / f"{p.platform}_annotated.jpg").write_bytes(base64.b64decode(r2.content[1].data))
        expect("e1" in r2.content[0].text)
        return note.text
    await p.step("phone_take_screenshot + annotate", screenshot)

    async def save():
        magic = {".png": b"\x89PNG", ".jpg": b"\xff\xd8\xff", ".webp": b"RIFF"}
        for suffix, head in magic.items():
            target = p.out / f"{p.platform}_shot{suffix}"
            await p.call("phone_save_screenshot", save_to=str(target))
            expect(target.read_bytes()[:len(head)] == head, suffix)
        small = p.out / f"{p.platform}_small.jpg"
        await p.call("phone_save_screenshot", save_to=str(small), max_size=300)
        expect(small.stat().st_size < (p.out / f"{p.platform}_shot.jpg").stat().st_size)
    await p.step("phone_save_screenshot png/jpg/webp", save)

    async def tap_coordinates():
        e = await p.by_id("tap_btn")
        await p.call("phone_click_on_screen_at_coordinates", x=e["x"], y=e["y"])
        return await p.status_is("tap:*")
    await p.step("phone_click_on_screen_at_coordinates", tap_coordinates)

    async def tap_by_text():
        before = int((await p.status()).split(":")[1])
        text = await p.call("phone_tap_element", text="tap ME")
        expect("Tap me" in text, text)
        return await p.status_is(f"tap:{before + 1}")
    await p.step("phone_tap_element by partial text", tap_by_text)

    async def tap_icon():
        await p.call("phone_tap_element", id="icon_btn")
        return await p.status_is("icon")
    await p.step("phone_tap_element by id, unlabelled icon", tap_icon)

    async def tap_ref():
        text = await p.call("phone_list_elements_on_screen")
        ref = re.search(r'"Tap me" at .*\[(e\d+)', text).group(1)
        await p.call("phone_tap_element", ref=ref)
        return await p.status_is("tap:*")
    await p.step("phone_tap_element by ref", tap_ref)

    async def tap_missing():
        text = await p.error("phone_tap_element", text="nothing like this", id=None)
        expect("On screen" in text, text)
    await p.step("phone_tap_element miss says what is there", tap_missing)

    async def long_press():
        e = await p.by_id("hold_btn")
        await p.call("phone_long_press_on_screen_at_coordinates", x=e["x"], y=e["y"], duration=900)
        return await p.status_is("long")
    await p.step("phone_long_press_on_screen_at_coordinates", long_press)

    async def double():
        e = await p.by_id("double_btn")
        await p.call("phone_double_tap", x=e["x"], y=e["y"])
        return await p.status_is("double")
    await p.step("phone_double_tap", double)

    async def toggle():
        await p.call("phone_tap_element", type="switch")
        await p.status_is("switch:on")
        expect((await p.by_id("toggle")).get("checked") is True)
        await p.call("phone_tap_element", id="toggle")
        await p.status_is("switch:off")
        expect((await p.by_id("toggle")).get("checked") is False)
    await p.step("phone_tap_element toggles a switch on and off", toggle)

    async def drag():
        e = await p.by_id("drag_area")
        span = round(size["w"] * 0.4)
        x1 = round(size["w"] * 0.2)
        await p.call("phone_drag", x1=x1, y1=e["y"], x2=x1 + span, y2=e["y"])
        status = await p.status_is("drag:*")
        dx = int(status.split(":")[1].split(",")[0])
        expect(abs(dx - span) < span * 0.15, f"moved {dx}, wanted {span}")
        return status
    await p.step("phone_drag", drag)

    async def swipe():
        await p.fresh_app()
        visible = {e["text"] for e in await p.elements()}
        expect("Item 1" in visible, sorted(visible))
        text = await p.call("phone_swipe_on_screen", direction="up", y=size["h"] * 0.85, distance=size["h"] * 0.25)
        await asyncio.sleep(1)
        after = {e["text"] for e in await p.elements()}
        expect("Item 1" not in after, sorted(after))
        return text
    await p.step("phone_swipe_on_screen", swipe)

    async def scroll_to():
        text = await p.call("phone_scroll_to_element", text="Item 45", exact=True, y=size["h"] * 0.85)
        expect("Found" in text, text)
        expect(any(e["text"] == "Item 45" for e in await p.elements()))
        return text
    await p.step("phone_scroll_to_element", scroll_to)

    async def scroll_to_miss():
        text = await p.error("phone_scroll_to_element", text="Item 999", y=size["h"] * 0.85, max_swipes=30)
        expect("Reached the end" in text, text)
    await p.step("phone_scroll_to_element stops at the end", scroll_to_miss)

    async def focus_field():
        await p.call("phone_tap_element", id="field")
        await asyncio.sleep(0.8)

    async def type_ascii():
        await focus_field()
        await p.call("phone_type_keys", text=ADVERSARIAL, clear=True)
        await asyncio.sleep(0.6)
        got = await p.field()
        expect(got == ADVERSARIAL, f"got {got!r}")
    await p.step("phone_type_keys adversarial ASCII reads back exactly", type_ascii)

    async def type_unicode():
        await focus_field()
        await p.call("phone_type_keys", text=UNICODE, clear=True)
        await asyncio.sleep(0.6)
        got = await p.field()
        expect(got == UNICODE, f"got {got!r}")
        return got
    await p.step("phone_type_keys Unicode and emoji read back exactly", type_unicode)

    async def type_token():
        await focus_field()
        await p.call("phone_type_keys", text="me@x.uz-42", clear=True, method="keys")
        await asyncio.sleep(0.5)
        got = await p.field()
        expect(got == "me@x.uz-42", f"got {got!r}")
    await p.step("phone_type_keys method=keys", type_token)

    async def type_submit():
        await focus_field()
        text = await p.call("phone_type_keys", text="done", clear=True, submit=True)
        expect("pressed Enter" in text, text)
        return await p.status_is("submit:done")
    await p.step("phone_type_keys clear + submit", type_submit)

    async def enter_button():
        await focus_field()
        await p.call("phone_type_keys", text="viaenter", clear=True)
        await p.call("phone_press_button", button="ENTER")
        return await p.status_is("submit:viaenter")
    await p.step("phone_press_button ENTER", enter_button)

    async def wait_for():
        text = await p.call("phone_wait_for_element", text="Tap me")
        expect("Found" in text, text)
        text = await p.error("phone_wait_for_element", text="never shows up", timeout=1)
        expect("did not appear" in text, text)
        text = await p.call("phone_wait_for_element", text="never shows up", gone=True, timeout=1)
        expect("gone" in text, text)
        text = await p.error("phone_wait_for_element", text="Tap me", gone=True, timeout=1)
        expect("still there" in text, text)
    await p.step("phone_wait_for_element", wait_for)

    async def idle():
        text = await p.call("phone_wait_for_idle", timeout=6)
        expect("settled" in text, text)
        return text
    await p.step("phone_wait_for_idle", idle)

    async def open_url():
        url = "phonemcp://hello?x=1&y=a%20b"
        await p.call("phone_open_url", url=url)
        await asyncio.sleep(1)
        return await p.status_is(f"url:{url}", 8)
    await p.step("phone_open_url deep link with & in it", open_url)

    async def clipboard():
        await p.call("phone_set_clipboard", text="буфер ok")
        got = await p.call("phone_get_clipboard")
        expect(got == "буфер ok", repr(got))
    await p.step("phone_set_clipboard + phone_get_clipboard", clipboard)

    async def appearance():
        before = "dark" if "appearance: dark" in await p.call("phone_get_device_info") else "light"
        text = await p.call("phone_set_appearance", mode="dark")
        expect(f"it was {before}" in text, text)
        await asyncio.sleep(0.8)
        expect("appearance: dark" in await p.call("phone_get_device_info"))
        await p.call("phone_set_appearance", mode="light")
        await asyncio.sleep(0.8)
        expect("appearance: light" in await p.call("phone_get_device_info"))
    await p.step("phone_set_appearance", appearance)

    async def location():
        await p.call("phone_set_permission", app=FIXTURE, permission="location", action="grant")
        await p.fresh_app()
        await p.call("phone_tap_element", id="where_btn")
        await asyncio.sleep(1.5)
        await p.call("phone_set_location", latitude=41.3111, longitude=69.2797)
        return "the app itself reports " + await p.status_is("loc:41.31,69.28", 12)
    await p.step("phone_set_location", location)

    async def orientation():
        if ios:
            text = await p.error("phone_set_orientation", orientation="landscape")
            expect("Simulator.app" in text, text)
            return "says it cannot, by design"
        await p.call("phone_set_orientation", orientation="landscape")
        await asyncio.sleep(2)
        landscape = await p.call("phone_get_screen_size")
        expect(f"{size['h']}x{size['w']}" in landscape, landscape)
        await p.call("phone_set_orientation", orientation="portrait")
        await asyncio.sleep(2)
        portrait = await p.call("phone_get_screen_size")
        expect(f"{size['w']}x{size['h']}" in portrait, portrait)
        await p.call("phone_set_orientation", orientation="auto")
        return landscape.split(",")[0]
    await p.step("phone_set_orientation", orientation)

    async def permission():
        await p.call("phone_set_permission", app=FIXTURE, permission="camera", action="grant")
        if ios:
            db = Path.home() / f"Library/Developer/CoreSimulator/Devices/{p.device}/data/Library/TCC/TCC.db"
            query = f"select auth_value from access where service='kTCCServiceCamera' and client='{FIXTURE}'"
            read = lambda: host("sqlite3", str(db), query).strip()
            expect(read() == "2", f"after grant: {read()!r}")
            await p.call("phone_set_permission", app=FIXTURE, permission="camera", action="revoke")
            expect(read() == "0", f"after revoke: {read()!r}")
            await p.call("phone_set_permission", app=FIXTURE, permission="camera", action="reset")
            expect(read() == "", f"after reset: {read()!r}")
        else:
            read = lambda: "android.permission.CAMERA: granted=true" in host(
                adb_path, "-s", p.device, "shell", f"dumpsys package {FIXTURE}")
            expect(read(), "not granted")
            await p.call("phone_set_permission", app=FIXTURE, permission="camera", action="revoke")
            expect(not read(), "still granted")
        text = await p.error("phone_set_permission", app=FIXTURE, permission="nonsense")
        return text[:70]
    await p.step("phone_set_permission", permission)

    await p.fresh_app()

    async def logs():
        await p.call("phone_tap_element", id="tap_btn")
        await asyncio.sleep(2)
        out = await p.call("phone_get_logs", app=FIXTURE, seconds=120, grep="tap:", max_lines=5)
        expect("tap:" in out, out[:400])
        expect(len(out.splitlines()) <= 5)
        everything = await p.call("phone_get_logs", seconds=10, max_lines=3)
        expect(len(everything.splitlines()) <= 3)
        return out.splitlines()[-1][-60:]
    await p.step("phone_get_logs", logs)

    async def recording():
        target = p.out / f"{p.platform}_rec.mp4"
        await p.call("phone_start_recording", save_to=str(target))
        text = await p.error("phone_start_recording", save_to=str(target))
        expect("Already recording" in text, text)
        await p.call("phone_swipe_on_screen", direction="up", y=size["h"] * 0.85)
        await asyncio.sleep(3)
        await p.call("phone_swipe_on_screen", direction="down", y=size["h"] * 0.6)
        await asyncio.sleep(1)
        saved = await p.call("phone_stop_recording")
        expect(target.is_file() and target.stat().st_size > 1000, saved)
        probe = host("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(target))
        expect(float(probe.strip() or 0) > 1, f"duration {probe!r}")
        text = await p.error("phone_stop_recording")
        expect("Nothing is recording" in text, text)
        return f"{float(probe):.1f}s video, {saved}"
    await p.step("phone_start_recording + phone_stop_recording", recording)

    async def notification():
        await p.fresh_app()
        if ios:
            await p.call("phone_tap_element", id="notify_btn")
            await asyncio.sleep(1.5)
            await p.call("phone_tap_element", text="Allow", exact=True, timeout=5)
            await p.status_is("notify:true", 6)
            await p.call("phone_press_button", button="HOME")
            await asyncio.sleep(1)
            await p.call("phone_send_notification", title="Hello MCP", body="Body text", app=FIXTURE)
            found = await p.call("phone_wait_for_element", text="Hello MCP", timeout=6)
            return found
        await p.call("phone_send_notification", title="Hello MCP", body="Body дунё")
        await asyncio.sleep(1)
        out = host(adb_path, "-s", p.device, "shell", "dumpsys notification --noredact")
        expect("Hello MCP" in out, "not posted")
    await p.step("phone_send_notification", notification)

    async def media():
        image = p.out / "phone_mcp_media.jpg"
        shutil.copy(p.out / f"{p.platform}_shot.jpg", image)
        await p.call("phone_add_media", path=str(image))
        if ios:
            db = Path.home() / f"Library/Developer/CoreSimulator/Devices/{p.device}/data/Media/DCIM"
            found = list(db.rglob("*.JPG")) + list(db.rglob("*.jpg")) + list(db.rglob("*.HEIC"))
            expect(found, f"nothing in {db}")
            return f"{len(found)} in the library"
        await asyncio.sleep(1.5)
        out = host(adb_path, "-s", p.device, "shell",
                   "content query --uri content://media/external/images/media --projection _display_name")
        expect("phone_mcp_media" in out, out[:300])
    await p.step("phone_add_media", media)

    async def shell():
        if ios:
            out = await p.call("phone_shell", command="launchctl list")
            expect("com.apple" in out, out[:200])
            failed = await p.call("phone_shell", command="launchctl nonsense-subcommand")
            expect(failed, "no output")
        else:
            out = await p.call("phone_shell", command="getprop ro.build.version.sdk")
            expect(out.strip().isdigit(), out)
            failed = await p.call("phone_shell", command="exit 7")
            expect("exit code 7" in failed, failed)
        return out[:30].replace("\n", " ")
    await p.step("phone_shell", shell)

    async def home():
        await p.fresh_app()
        await p.call("phone_press_button", button="HOME")
        await asyncio.sleep(1.5)
        front = await p.call("phone_get_foreground_app")
        expect("home screen" in front, front)
    await p.step("phone_press_button HOME", home)

    async def back():
        await p.call("phone_terminate_app", name="Settings")
        await p.call("phone_launch_app", name="Settings")
        await asyncio.sleep(1.5)
        if ios:
            await p.call("phone_tap_element", text="General", exact=True, type="button", timeout=5)
            await p.call("phone_wait_for_element", text="About", timeout=5)
            text = await p.call("phone_press_button", button="BACK")
            await asyncio.sleep(1)
            await p.call("phone_wait_for_element", text="Accessibility", timeout=5)
            return text
        await p.call("phone_tap_element", text="Network", timeout=5)
        await p.call("phone_wait_for_element", text="Internet", timeout=8)
        await p.call("phone_press_button", button="BACK")
        await p.call("phone_wait_for_element", text="Battery", timeout=8)
    await p.step("phone_press_button BACK", back)

    async def switcher():
        await p.fresh_app()
        await p.call("phone_press_button", button="APP_SWITCHER")
        await asyncio.sleep(1.5)
        target = p.out / f"{p.platform}_switcher.png"
        await p.call("phone_save_screenshot", save_to=str(target))
        if not ios:
            focus = host(adb_path, "-s", p.device, "shell", "dumpsys window | grep mCurrentFocus")
            expect(FIXTURE not in focus, focus)
        await p.call("phone_press_button", button="HOME")
        await asyncio.sleep(1)
        return f"see {target.name}"
    await p.step("phone_press_button APP_SWITCHER", switcher)

    async def batch():
        await p.call("phone_launch_app", name=FIXTURE)
        await asyncio.sleep(1)
        text = await p.call("phone_batch", actions=[
            {"action": "tap_element", "id": "field"}, {"action": "sleep", "seconds": 0.6},
            {"action": "type", "text": "batched", "clear": True}, {"action": "press", "button": "ENTER"},
            {"action": "wait_for", "text": "submit:batched", "timeout": 5}])
        expect("5. wait_for: Found" in text, text)
        failed = await p.error("phone_batch", actions=[{"action": "tap_element", "text": "absent thing"},
                                                       {"action": "press", "button": "HOME"}])
        expect("1 actions did not run" in failed, failed)
        expect(FIXTURE in await p.call("phone_get_foreground_app"))
    await p.step("phone_batch", batch)

    async def ocr():
        els = await p.elements(source="ocr")
        tap = next((e for e in els if e["text"] == "Tap me"), None)
        expect(tap and tap["source"] == "pixels", [e["text"] for e in els][:20])
        true_center = await p.by_id("tap_btn")
        expect(abs(tap["x"] - true_center["x"]) < size["w"] * 0.05, f"{tap['x']} vs {true_center['x']}")
        expect(abs(tap["y"] - true_center["y"]) < size["h"] * 0.02, f"{tap['y']} vs {true_center['y']}")
        text = await p.call("phone_list_elements_on_screen", source="ocr")
        expect("misread" in text, text[-200:])
        return f"{len(els)} words; 'Tap me' within tolerance of its real center"
    await p.step("phone_list_elements_on_screen source=ocr", ocr)

    async def terminate():
        await p.call("phone_terminate_app", name=FIXTURE)
        await asyncio.sleep(1)
        if ios:
            out = await p.call("phone_shell", command="launchctl list")
        else:
            out = await p.call("phone_shell", command=f"pidof {FIXTURE} || echo gone")
        expect(FIXTURE not in out, out[:200])
    await p.step("phone_terminate_app", terminate)

    async def clear_data():
        await p.fresh_app()
        await p.call("phone_tap_element", id="tap_btn")
        await p.status_is("tap:*")
        await asyncio.sleep(1)
        await p.call("phone_clear_app_data", name=FIXTURE)
        await asyncio.sleep(1)
        await p.fresh_app()
        if ios:
            info = await p.by_id("info")
            expect("taps=0" in info["text"], info["text"])
        else:
            await p.status_is("ready taps=0*")
    await p.step("phone_clear_app_data", clear_data)

    async def uninstall():
        await p.call("phone_terminate_app", name=FIXTURE)
        await p.call("phone_uninstall_app", name=FIXTURE)
        expect(FIXTURE not in await p.call("phone_list_apps"))
        await p.error("phone_launch_app", name=FIXTURE)
    await p.step("phone_uninstall_app", uninstall)

    async def bad_device():
        result = await p.session.call_tool("phone_get_screen_size", {"device": "no-such-phone"})
        text = result.content[0].text
        expect(result.is_error and "not running" in text, text)
    await p.step("unknown device explains", bad_device)

    async def missing_file():
        text = await p.error("phone_install_app", path="/no/such/file")
        expect("No such file" in text, text)
    await p.step("phone_install_app missing file explains", missing_file)

    if args.lifecycle:
        async def lifecycle():
            name_text = await p.call("phone_list_available_devices")
            avd = re.search(rf"{re.escape(p.device)}: (\S+) \(android", name_text)
            await p.call("phone_stop_device")
            await asyncio.sleep(2)
            listed = (await p.session.call_tool("phone_list_available_devices", {})).content[0].text
            running = listed.split("Phones you can start")[0]
            expect(p.device not in running, running)
            result = await p.session.call_tool("phone_get_screen_size", {"device": p.device})
            expect(result.is_error and "not running" in result.content[0].text, result.content[0].text)
            target = p.device if ios else avd.group(1)
            began = time.monotonic()
            p.called.add("phone_start_device")
            started = await p.session.call_tool("phone_start_device", {"device_id": target, "headless": True})
            text = started.content[0].text
            expect(not started.is_error, text)
            new_id = re.search(r"as device (\S+)\.", text).group(1)
            p.device = new_id
            again = await p.session.call_tool("phone_start_device", {"device_id": new_id})
            expect("already running" in again.content[0].text, again.content[0].text)
            expect(new_id in await p.call("phone_list_available_devices"), name_text)
            return f"booted in {time.monotonic() - began:.0f}s as {new_id}"
        await p.step("phone_stop_device + phone_start_device", lifecycle)


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ios")
    parser.add_argument("--android")
    parser.add_argument("--lifecycle", action="store_true")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    out = Path(args.out or tempfile.mkdtemp(prefix="phone-mcp-e2e-"))
    out.mkdir(parents=True, exist_ok=True)
    adb_path = shutil.which("adb")
    params = StdioServerParameters(command="uv", args=["--directory", str(ROOT), "run", "--quiet", "phone-mcp"])
    code = 0
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            print(f"{len(tools)} tools over stdio; artifacts in {out}")
            phones = []
            if args.ios:
                phones.append(Phone(session, args.ios, "ios", out))
            if args.android:
                phones.append(Phone(session, args.android, "android", out))
            for phone in phones:
                print(f"\n=== {phone.platform} {phone.device}")
                await run_all(phone, args, adb_path)
            print()
            for phone in phones:
                passed = sum(1 for r in phone.results if r[1])
                print(f"{phone.platform}: {passed}/{len(phone.results)} passed")
                for name, ok, detail, _t in phone.results:
                    if not ok:
                        print(f"  FAILED {name}: {detail[:300]}")
                        code = 1
                uncalled = sorted(tools - phone.called)
                if uncalled:
                    print(f"  tools not exercised: {uncalled}")
    return code


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
