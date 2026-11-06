"""The contract kept from Phone Harness MCP: same tool names, parameters, defaults and meaning.

Where a test differs from upstream's own, the comment says why.
"""
import base64
import re

import pytest

from fake import CAPTURE_SIZE, FakeDriver, connected, serve, text_of
from phone_mcp.server import plan_swipe

pytestmark = pytest.mark.anyio

UPSTREAM_TOOLS = {
    "phone_list_available_devices", "phone_start_device", "phone_stop_device",
    "phone_get_screen_size", "phone_take_screenshot", "phone_save_screenshot",
    "phone_list_elements_on_screen", "phone_click_on_screen_at_coordinates",
    "phone_long_press_on_screen_at_coordinates", "phone_swipe_on_screen", "phone_type_keys",
    "phone_press_button", "phone_list_apps", "phone_launch_app", "phone_get_foreground_app",
}
UPSTREAM_PARAMS = {
    "phone_start_device": {"platform", "kind", "device_id", "minutes"},
    "phone_stop_device": {"device"},
    "phone_get_screen_size": {"device"},
    "phone_take_screenshot": {"device", "max_size", "scale"},
    "phone_save_screenshot": {"device", "save_to", "max_size", "scale"},
    "phone_list_elements_on_screen": {"device", "format"},
    "phone_click_on_screen_at_coordinates": {"device", "x", "y"},
    "phone_long_press_on_screen_at_coordinates": {"device", "x", "y", "duration"},
    "phone_swipe_on_screen": {"device", "direction", "x", "y", "distance"},
    "phone_type_keys": {"device", "text", "submit"},
    "phone_press_button": {"device", "button"},
    "phone_list_apps": {"device"},
    "phone_launch_app": {"device", "name"},
    "phone_get_foreground_app": {"device"},
}


async def test_every_upstream_tool_and_parameter_exists():
    async with connected(serve(FakeDriver())) as s:
        tools = {t.name: t for t in (await s.list_tools()).tools}
    assert UPSTREAM_TOOLS <= set(tools)
    assert all(name.startswith("phone_") for name in tools)
    for name, params in UPSTREAM_PARAMS.items():
        assert params <= set(tools[name].input_schema["properties"]), name
    assert tools["phone_take_screenshot"].annotations.read_only_hint is True
    assert tools["phone_stop_device"].annotations.destructive_hint is True


async def test_defaults_match_upstream():
    async with connected(serve(FakeDriver())) as s:
        tools = {t.name: t for t in (await s.list_tools()).tools}
    assert tools["phone_take_screenshot"].input_schema["properties"]["max_size"]["default"] == 1024
    assert tools["phone_long_press_on_screen_at_coordinates"].input_schema["properties"]["duration"]["default"] == 800
    assert tools["phone_type_keys"].input_schema["properties"]["submit"]["default"] is False
    assert tools["phone_list_elements_on_screen"].input_schema["properties"]["format"]["default"] == "text"


async def test_list_then_start_then_list():
    phone = FakeDriver()
    server = serve(phone)
    async with connected(server) as s:
        before = text_of(await s.call_tool("phone_list_available_devices", {}))
        assert "Running phones" in before and f"{phone.id}: Fake iPhone (ios/simulator), ready, screen 390x844" in before
        assert "device_id=avd:spare" in before
        assert "OLD-1" not in before and "1 simulators on older" in before
        assert "OLD-1" in text_of(await s.call_tool("phone_list_available_devices", {"all": True}))
        started = text_of(await s.call_tool("phone_start_device", {"platform": "ios", "kind": "device", "minutes": 5}))
        assert "Started Started as device STARTED-1." in started and "Screen 390x844" in started
        assert "It stops in 5 min" in started
    assert server.hub.started == [("ios", "device", None, False)]
    server.hub.shutdown()


async def test_no_phone_running_says_what_to_do():
    async with connected(serve()) as s:
        text = text_of(await s.call_tool("phone_list_available_devices", {}))
        assert "No phone is running. phone_start_device starts one." in text
        r = await s.call_tool("phone_get_screen_size", {})
    assert r.is_error and "phone_start_device" in text_of(r)


async def test_screenshot_is_jpeg_with_a_mapping():
    async with connected(serve(FakeDriver())) as s:
        # Upstream gives 473x1024 and asks the model to multiply. The coordinate space fits, so use it 1:1.
        r = await s.call_tool("phone_take_screenshot", {})
        note, image = r.content
        assert image.type == "image" and image.mime_type == "image/jpeg"
        assert base64.b64decode(image.data)[:3] == b"\xff\xd8\xff"
        assert note.text == "Screenshot is 390x844 and its coordinates match the screen."

        r = await s.call_tool("phone_take_screenshot", {"scale": 0.25})
        m = re.match(r"Screenshot is (\d+)x(\d+)\. Screen coordinates are 390x844\. To tap something you see in "
                     r"this screenshot, multiply its x by ([\d.]+) and y by ([\d.]+)\.", r.content[0].text)
        assert m and int(m.group(1)) == CAPTURE_SIZE[0] // 4
        assert abs(float(m.group(3)) - 2.0) < 0.01


async def test_large_screen_shrinks_to_max_size():
    phone = FakeDriver()
    phone.screen_size = lambda: (1080, 2400)
    async with connected(serve(phone)) as s:
        r = await s.call_tool("phone_take_screenshot", {})
    assert r.content[0].text.startswith("Screenshot is 473x1024.")


async def test_save_screenshot_formats(tmp_path):
    async with connected(serve(FakeDriver())) as s:
        png = tmp_path / "shots" / "home.png"
        assert f"Saved 780x1688 PNG to {png}" in text_of(await s.call_tool("phone_save_screenshot", {"save_to": str(png)}))
        assert png.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
        jpg = tmp_path / "a.jpg"
        assert "390x844 JPEG" in text_of(await s.call_tool("phone_save_screenshot", {"save_to": str(jpg), "scale": 0.5}))
        assert jpg.read_bytes()[:3] == b"\xff\xd8\xff"
        # Upstream writes JPEG bytes into any other extension.
        webp = tmp_path / "a.webp"
        assert "WEBP" in text_of(await s.call_tool("phone_save_screenshot", {"save_to": str(webp)}))
        assert webp.read_bytes()[8:12] == b"WEBP"
        r = await s.call_tool("phone_save_screenshot", {"save_to": str(tmp_path / "a.gif")})
        assert r.is_error and ".png" in text_of(r)


async def test_screen_size_and_elements():
    async with connected(serve(FakeDriver())) as s:
        assert text_of(await s.call_tool("phone_get_screen_size", {})).startswith("Screen is 390x844")
        text = text_of(await s.call_tool("phone_list_elements_on_screen", {}))
        assert text.splitlines()[0] == "Screen is 390x844. 3 elements, top to bottom; (x, y) is the center to tap:"
        assert '- "Hello" at (195, 200), 200x30' in text
        assert '- "Continue" at (195, 500), 160x44' in text
        # Upstream drops anything without text, so an icon button is invisible to it.
        assert "(no label) at (40, 60)" in text and "id=close_btn" in text
        as_json = text_of(await s.call_tool("phone_list_elements_on_screen", {"format": "json"}))
        assert '"text": "Continue"' in as_json and '"ref": "e' in as_json


async def test_touch_tools_send_the_right_calls():
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        assert text_of(await s.call_tool("phone_click_on_screen_at_coordinates", {"x": 100.4, "y": 200.6})) \
            == "Tapped (100, 201)."
        await s.call_tool("phone_long_press_on_screen_at_coordinates", {"x": 10, "y": 20, "duration": 1500})
        await s.call_tool("phone_long_press_on_screen_at_coordinates", {"x": 10, "y": 20, "duration": 99999})
        assert text_of(await s.call_tool("phone_swipe_on_screen", {"direction": "up"})) \
            == "Swiped up from (195, 591) to (195, 253)."
        assert text_of(await s.call_tool("phone_type_keys", {"text": "hello", "submit": True})) \
            == "Typed 5 characters and pressed Enter."
        assert text_of(await s.call_tool("phone_press_button", {"button": "HOME"})) == "Pressed HOME."
        await s.call_tool("phone_press_button", {"button": "APP_SWITCHER"})
    assert phone.calls == [
        ("tap", 100, 201),
        ("long_press", 10, 20, 1.5),
        ("long_press", 10, 20, 10.0),
        ("swipe", 195, 591, 195, 253, 0.3),
        ("type", "hello", "auto"),
        ("enter",),
        ("press", "HOME"),
        ("press", "APP_SWITCHER"),
    ]


def test_swipe_starts_where_it_says_and_stays_on_screen():
    # Upstream's docstring says the swipe starts at (x, y), but it centres the gesture there, so a swipe "from" the
    # left edge travels half the distance. With x, y and distance all given it also skips the upper bound and can
    # leave the screen: y=800 + 400 on an 844 screen sends y2=1000.
    assert plan_swipe("right", 390, 844, 0, 400, 200) == (0, 400, 200, 400)
    assert plan_swipe("down", 390, 844, 100, 800, 400) == (100, 800, 100, 843)
    assert plan_swipe("up", 390, 844, None, None, None) == (195, 591, 195, 253)
    assert plan_swipe("left", 390, 844, 300, 100, 1000) == (300, 100, 0, 100)
    assert plan_swipe("up", 390, 844, 100, None, None) == (100, 422, 100, 84)


async def test_apps():
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        assert text_of(await s.call_tool("phone_launch_app", {"name": "Notes"})) == "Launched com.example.mock."
        assert text_of(await s.call_tool("phone_get_foreground_app", {})) == "Foreground app: com.example.mock (Mock)"
        assert text_of(await s.call_tool("phone_list_apps", {})) == "com.example.mock (Mock)"
        phone.front = None
        assert "home screen" in text_of(await s.call_tool("phone_get_foreground_app", {}))
        phone.apps = []
        assert "No user apps" in text_of(await s.call_tool("phone_list_apps", {}))


async def test_unknown_device():
    async with connected(serve(FakeDriver())) as s:
        r = await s.call_tool("phone_click_on_screen_at_coordinates", {"device": "s_nope", "x": 1, "y": 2})
    assert r.is_error and "device s_nope is not running" in text_of(r)


async def test_stop():
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        assert text_of(await s.call_tool("phone_stop_device", {"device": phone.id})) == f"Stopped device {phone.id}."
        r = await s.call_tool("phone_click_on_screen_at_coordinates", {"device": phone.id, "x": 1, "y": 2})
    assert r.is_error and "not running" in text_of(r)
