"""What goes beyond upstream, and the parsers and escaping the live test cannot corner."""
import pytest

from fake import FakeDriver, connected, serve, text_of
from phone_mcp.drivers.android import input_text_chunks, is_keyboard_safe
from phone_mcp.drivers.ios import IosDriver, should_paste
from phone_mcp.elements import Element, find, parse_android, parse_ios

pytestmark_async = pytest.mark.anyio

ANDROID_XML = b"""<?xml version='1.0' encoding='UTF-8' standalone='yes' ?><hierarchy rotation="0">
<node text="" resource-id="" class="android.widget.FrameLayout" content-desc="" checkable="false" checked="false"
 clickable="true" enabled="true" focusable="false" focused="false" long-clickable="false" selected="false"
 bounds="[0,0][1080,2400]">
  <node text="Title &amp; more" resource-id="com.x:id/title" class="android.widget.TextView" content-desc=""
   checkable="false" checked="false" clickable="false" enabled="true" focused="false" long-clickable="false"
   selected="false" bounds="[0,100][1080,200]"/>
  <node text="" resource-id="com.x:id/row" class="android.widget.LinearLayout" content-desc="" checkable="false"
   checked="false" clickable="true" enabled="true" focused="false" long-clickable="false" selected="false"
   bounds="[0,300][1080,400]">
    <node text="Inside row" resource-id="" class="android.widget.TextView" content-desc="" checkable="false"
     checked="false" clickable="false" enabled="true" focused="false" long-clickable="false" selected="false"
     bounds="[50,320][400,380]"/>
  </node>
  <node text="" resource-id="com.x:id/fab" class="android.widget.ImageButton" content-desc="Add" checkable="false"
   checked="false" clickable="true" enabled="false" focused="false" long-clickable="false" selected="false"
   bounds="[900,2000][1000,2100]"/>
  <node text="" resource-id="com.x:id/bare" class="android.widget.ImageButton" content-desc="" checkable="false"
   checked="false" clickable="true" enabled="true" focused="false" long-clickable="false" selected="false"
   bounds="[10,2000][110,2100]"/>
  <node text="secret" resource-id="com.x:id/field" class="android.widget.EditText" content-desc="" checkable="false"
   checked="false" clickable="true" enabled="true" focused="true" long-clickable="true" selected="false"
   bounds="[0,500][1080,600]"/>
  <node text="Wifi" resource-id="com.x:id/sw" class="android.widget.Switch" content-desc="" checkable="true"
   checked="true" clickable="true" enabled="true" focused="false" long-clickable="false" selected="false"
   bounds="[0,700][1080,800]"/>
  <node text="Off screen" resource-id="" class="android.widget.TextView" content-desc="" checkable="false"
   checked="false" clickable="false" enabled="true" focused="false" long-clickable="false" selected="false"
   bounds="[0,3000][1080,3100]"/>
  <node text="Zero" resource-id="" class="android.widget.TextView" content-desc="" checkable="false" checked="false"
   clickable="false" enabled="true" focused="false" long-clickable="false" selected="false" bounds="[10,10][10,10]"/>
</node></hierarchy>
UI hierchary dumped to: /dev/tty"""


def test_android_tree():
    els = {e.text or e.id: e for e in parse_android(ANDROID_XML, (1080, 2400))}
    assert "Title & more" in els and els["Title & more"].y == 150 and not els["Title & more"].clickable
    assert els["Inside row"].clickable, "text inside a clickable row can be tapped"
    assert "row" not in els, "a clickable container with a label inside is not listed twice"
    assert els["Add"].id == "fab" and els["Add"].enabled is False
    assert els["bare"].text == "" and els["bare"].clickable, "an icon with no label still appears"
    assert els["secret"].value == "secret" and els["secret"].focused
    assert els["Wifi"].checked is True
    assert "Off screen" not in els and "Zero" not in els


def test_android_tree_without_a_screen_size_keeps_offscreen():
    assert any(e.text == "Off screen" for e in parse_android(ANDROID_XML))


def _ios(kind, label=None, uid=None, value=None, frame=(10, 10, 100, 40), children=(), **extra):
    x, y, w, h = frame
    return {"type": kind, "AXLabel": label, "AXUniqueId": uid, "AXValue": value,
            "frame": {"x": x, "y": y, "width": w, "height": h}, "children": list(children), **extra}


def test_ios_tree():
    tree = [_ios("Application", " ", frame=(0, 0, 402, 874), pid=1, children=[
        _ios("Group", None, frame=(0, 0, 402, 874), children=[
            _ios("Button", "General", "settings.general", frame=(16, 380, 370, 52), children=[
                _ios("StaticText", "General", frame=(30, 392, 100, 28))]),
            _ios("Button", "Apple Account, Sign in", frame=(16, 100, 370, 90), children=[
                _ios("StaticText", "Apple Account", frame=(100, 110, 138, 24))]),
            _ios("Button", "Hidden page", "x", frame=(0, 0, 0, 0)),
            _ios("Slider", "Vertical scroll bar, 1 page", value="0%", frame=(390, 0, 10, 800)),
            _ios("CheckBox", "Toggle", "toggle", value="1", frame=(16, 332, 370, 28)),
            _ios("TextField", None, "field", value="typed", frame=(16, 138, 370, 34)),
            _ios("Button", "", "icon_btn", frame=(192, 213, 18, 16)),
            _ios("StaticText", "Below", frame=(10, 2000, 100, 20)),
            _ios("Group", None, "just.a.container", frame=(0, 0, 402, 400)),
        ])])]
    els = {e.text or e.id: e for e in parse_ios(tree, (402, 874))}
    assert els["General"].type == "Button" and els["General"].id == "settings.general"
    assert list(e.text for e in parse_ios(tree, (402, 874))).count("General") == 1, "a button's own text is not repeated"
    assert "Apple Account" not in els
    assert "Hidden page" not in els and "Below" not in els and "just.a.container" not in els
    assert not any("scroll bar" in k for k in els)
    assert els["Toggle"].checked is True and els["Toggle"].clickable
    assert els["field"].value == "typed"
    assert els["icon_btn"].text == "" and els["icon_btn"].clickable


def test_ios_toggle_is_tapped_at_its_control():
    driver = IosDriver.__new__(IosDriver)
    wide = Element("Toggle", 201, 346, 370, 28, type="CheckBox")
    assert driver.tap_point(wide) == (201 + 185 - 30, 346)
    button = Element("Go", 201, 346, 370, 28, type="Button")
    assert driver.tap_point(button) == (201, 346)


def test_find_ranks_exact_then_prefix_then_contains():
    els = [Element("Not General here", 0, 0, 1, 1), Element("General settings", 0, 1, 1, 1),
           Element("General", 0, 2, 1, 1, type="StaticText"),
           Element("General", 0, 3, 1, 1, type="Button", clickable=True)]
    assert [e.y for e in find(els, text="general")] == [3, 2, 1, 0]
    assert [e.y for e in find(els, text="General", exact=True)] == [3, 2]
    assert [e.y for e in find(els, text="general", type="button")] == [3]


def test_find_understands_the_other_platforms_type_names():
    field = Element("", 0, 0, 1, 1, type="EditText", id="email")
    switch = Element("", 0, 1, 1, 1, type="CheckBox", id="wifi")
    assert find([field, switch], type="textfield") == [field]
    assert find([field, switch], type="switch") == [switch]
    assert find([field, switch], id="email") == [field]


def test_find_needs_a_question():
    with pytest.raises(Exception, match="Say what to look for"):
        find([], text=None)


def test_input_text_escaping():
    assert input_text_chunks("a b") == ["a%sb"]
    assert input_text_chunks("100%sure") == ["100%", "sure"], "a literal %s must not become a space"
    assert input_text_chunks("50% off") == ["50%%soff"]
    assert all(len(c) <= 200 for c in input_text_chunks("x" * 450))
    assert "".join(input_text_chunks("x" * 450)) == "x" * 450


def test_android_keyboard_safety():
    assert is_keyboard_safe("plain text!\n")
    assert not is_keyboard_safe("дунё")
    assert not is_keyboard_safe("🙂")


def test_ios_paste_decision():
    assert not should_paste("me@example.uz")
    assert not should_paste("1234")
    assert should_paste("two words"), "HID typing autocorrects sentences"
    assert should_paste("it's"), "smart punctuation curls the quote"
    assert should_paste("a--b"), "smart punctuation joins the dashes"
    assert should_paste("wait..."), "smart punctuation makes an ellipsis"
    assert should_paste("дунё")


@pytest.mark.anyio
async def test_tap_element_by_text_ref_id_and_failure():
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        assert text_of(await s.call_tool("phone_tap_element", {"text": "contin"})) \
            == 'Tapped "Continue" (Button) at (195, 500).'
        assert 'Tapped "close_btn"' in text_of(await s.call_tool("phone_tap_element", {"id": "close_btn"}))
        listing = text_of(await s.call_tool("phone_list_elements_on_screen", {}))
        assert "e3, Button, id=continue_btn" in listing
        assert "(195, 500)" in text_of(await s.call_tool("phone_tap_element", {"ref": "e3"}))
        missing = await s.call_tool("phone_tap_element", {"text": "nothing like this"})
        assert missing.is_error and "Hello" in text_of(missing), "a miss says what is on screen"
        stale = await s.call_tool("phone_tap_element", {"ref": "e99"})
        assert stale.is_error
        out_of_range = await s.call_tool("phone_tap_element", {"text": "Hello", "index": 5})
        assert out_of_range.is_error and "out of range" in text_of(out_of_range)
    assert ("tap", 195, 500) in phone.calls and ("tap", 40, 60) in phone.calls


@pytest.mark.anyio
async def test_ref_warns_after_the_screen_may_have_changed():
    async with connected(serve(FakeDriver())) as s:
        await s.call_tool("phone_list_elements_on_screen", {})
        assert "may have changed" not in text_of(await s.call_tool("phone_tap_element", {"ref": "e1"}))
        assert "may have changed" in text_of(await s.call_tool("phone_tap_element", {"ref": "e1"}))


@pytest.mark.anyio
async def test_ref_without_a_list_explains_itself():
    async with connected(serve(FakeDriver())) as s:
        r = await s.call_tool("phone_tap_element", {"ref": "e1"})
    assert r.is_error and "phone_list_elements_on_screen" in text_of(r)


@pytest.mark.anyio
async def test_wait_for_element():
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        assert "Found" in text_of(await s.call_tool("phone_wait_for_element", {"text": "Hello"}))
        r = await s.call_tool("phone_wait_for_element", {"text": "absent", "timeout": 0.1})
        assert r.is_error and "did not appear" in text_of(r)
        assert "gone" in text_of(await s.call_tool("phone_wait_for_element", {"text": "absent", "gone": True}))
        r = await s.call_tool("phone_wait_for_element", {"text": "Hello", "gone": True, "timeout": 0.1})
        assert r.is_error and "still there" in text_of(r)


@pytest.mark.anyio
async def test_scroll_stops_when_the_screen_stops_changing():
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        assert "after 0 swipes" in text_of(await s.call_tool("phone_scroll_to_element", {"text": "Hello"}))
        r = await s.call_tool("phone_scroll_to_element", {"text": "absent", "max_swipes": 9})
    assert r.is_error and "Reached the end after 1 swipes" in text_of(r)
    assert len([c for c in phone.calls if c[0] == "swipe"]) == 1


@pytest.mark.anyio
async def test_annotated_screenshot_lists_refs():
    async with connected(serve(FakeDriver())) as s:
        r = await s.call_tool("phone_take_screenshot", {"annotate": True})
    assert "e3, Button" in r.content[0].text and r.content[1].type == "image"


@pytest.mark.anyio
async def test_several_phones_must_be_told_apart():
    a, b = FakeDriver("A-1", "First"), FakeDriver("B-2", "Second")
    async with connected(serve(a, b)) as s:
        r = await s.call_tool("phone_get_screen_size", {})
        assert r.is_error and "A-1" in text_of(r) and "B-2" in text_of(r)
        await s.call_tool("phone_click_on_screen_at_coordinates", {"device": "B-2", "x": 1, "y": 2})
        await s.call_tool("phone_click_on_screen_at_coordinates", {"device": "second", "x": 3, "y": 4})
    assert a.calls == [] and b.calls == [("tap", 1, 2), ("tap", 3, 4)]


@pytest.mark.anyio
async def test_batch_runs_in_order_and_stops_at_a_failure():
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        done = text_of(await s.call_tool("phone_batch", {"actions": [
            {"action": "tap", "x": 1, "y": 2}, {"action": "sleep", "seconds": 0.01},
            {"action": "type", "text": "hi"}, {"action": "press", "button": "ENTER"}]}))
        assert done.splitlines()[0] == "1. tap: Tapped (1, 2)." and "4. press" in done
        r = await s.call_tool("phone_batch", {"actions": [
            {"action": "tap_element", "text": "absent"}, {"action": "tap", "x": 9, "y": 9}]})
        assert r.is_error and "1 actions did not run" in text_of(r)
        kept_going = text_of(await s.call_tool("phone_batch", {"stop_on_error": False, "actions": [
            {"action": "fly"}, {"action": "tap", "x": 7, "y": 7}]}))
        assert "FAILED" in kept_going and "Tapped (7, 7)" in kept_going
        bad_args = await s.call_tool("phone_batch", {"actions": [{"action": "tap", "x": 1}]})
        assert bad_args.is_error
    assert ("tap", 7, 7) in phone.calls and ("tap", 9, 9) not in phone.calls


@pytest.mark.anyio
async def test_logs_filter_and_limit():
    async with connected(serve(FakeDriver())) as s:
        assert text_of(await s.call_tool("phone_get_logs", {"grep": "t(wo|hree)"})) == "b two\nc three"
        assert text_of(await s.call_tool("phone_get_logs", {"max_lines": 1})) == "c three"
        assert text_of(await s.call_tool("phone_get_logs", {"grep": "("})) == "No log lines matched."


@pytest.mark.anyio
async def test_small_tools_answer():
    async with connected(serve(FakeDriver())) as s:
        assert "Appearance is now dark; it was light." == text_of(await s.call_tool("phone_set_appearance", {"mode": "dark"}))
        assert "platform: ios" in text_of(await s.call_tool("phone_get_device_info", {}))
        assert "empty" in text_of(await s.call_tool("phone_get_clipboard", {}))
        assert "ran ls" == text_of(await s.call_tool("phone_shell", {"command": "ls"}))
        r = await s.call_tool("phone_install_app", {"path": "/no/such/file.apk"})
        assert r.is_error and "No such file" in text_of(r)
        r = await s.call_tool("phone_stop_recording", {})
        assert r.is_error and "Nothing is recording" in text_of(r)
