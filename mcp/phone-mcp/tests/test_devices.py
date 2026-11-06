"""Situations no phone on this desk can stage: a real phone, a refused prompt, a screen with no accessibility tree."""
import json

import pytest

import phone_mcp.devices as devices
from fake import FakeDriver, connected, serve, text_of
from phone_mcp import locate, ocr
from phone_mcp.devices import Hub
from phone_mcp.elements import Element
from phone_mcp.errors import PhoneError, Unsupported
from phone_mcp.proc import Completed

ADB_LISTING = """List of devices attached
R58M12ABC      device usb:1-1 product:a53 model:SM_A536E device:a53x transport_id:3
emulator-5554  device product:sdk_gphone64_arm64 model:sdk_gphone64_arm64 transport_id:1
FA79K0301      unauthorized usb:1-2 transport_id:4
emulator-5556  offline transport_id:5
"""
SIMS = {"devices": {
    "com.apple.CoreSimulator.SimRuntime.iOS-27-0": [
        {"udid": "AAAAAAAA-0000-0000-0000-000000000001", "name": "iPhone 18", "state": "Booted"},
        {"udid": "AAAAAAAA-0000-0000-0000-000000000002", "name": "iPhone 17", "state": "Shutdown"},
        {"udid": "AAAAAAAA-0000-0000-0000-000000000003", "name": "iPad Air", "state": "Shutdown"}],
    "com.apple.CoreSimulator.SimRuntime.iOS-26-0": [
        {"udid": "AAAAAAAA-0000-0000-0000-000000000004", "name": "iPhone 17", "state": "Shutdown"}],
    "com.apple.CoreSimulator.SimRuntime.watchOS-11-0": [
        {"udid": "AAAAAAAA-0000-0000-0000-000000000005", "name": "Apple Watch", "state": "Shutdown"}],
}}


@pytest.fixture
def machine(monkeypatch):
    def fake_run(argv, *, timeout=30, stdin=None, check=True):
        joined = " ".join(argv)
        if joined.endswith("devices -l"):
            return Completed(0, ADB_LISTING.encode(), b"")
        if "emu avd name" in joined:
            return Completed(0, b"my_avd\nOK\n", b"")
        if "simctl list" in joined:
            return Completed(0, json.dumps(SIMS).encode(), b"")
        if "-list-avds" in joined:
            return Completed(0, b"INFO | noisy line\nmy_avd\nspare_avd\n", b"")
        return Completed(0, b"", b"")
    monkeypatch.setattr(devices, "run", fake_run)
    monkeypatch.setattr(locate, "adb", lambda: "/sdk/adb")
    monkeypatch.setattr(locate, "emulator", lambda: "/sdk/emulator")
    monkeypatch.setattr(locate, "xcrun", lambda: "/usr/bin/xcrun")
    return Hub()


def test_running_lists_real_phones_emulators_and_simulators(machine):
    phones = {p.id: p for p in machine.running()}
    assert phones["R58M12ABC"].kind == "device" and phones["R58M12ABC"].name == "SM A536E"
    assert phones["emulator-5554"].kind == "emulator" and phones["emulator-5554"].name == "my_avd"
    assert phones["AAAAAAAA-0000-0000-0000-000000000001"].title == "iPhone 18 (iOS 27.0)"
    assert "FA79K0301" not in phones and "emulator-5556" not in phones
    assert any("USB debugging" in p for p in machine.problems)
    assert any("offline" in p for p in machine.problems)
    assert len(phones) == 3


def test_startable_skips_what_runs_and_other_platforms(machine):
    options = machine.startable()
    ids = [p.id for p in options]
    assert "avd:spare_avd" in ids and "avd:my_avd" not in ids, "a running AVD cannot be started again"
    assert "AAAAAAAA-0000-0000-0000-000000000001" not in ids
    assert "AAAAAAAA-0000-0000-0000-000000000005" not in ids, "a watch is not a phone"
    assert not any("noisy" in i for i in ids)
    older = next(p for p in options if p.id.endswith("000000000004"))
    assert older.newest is False


def test_a_model_name_means_its_newest_simulator(machine):
    assert Hub._choose(machine.startable(), "iphone 17").id.endswith("000000000002")
    assert Hub._choose(machine.startable(), "spare_avd").id == "avd:spare_avd"
    with pytest.raises(PhoneError, match="ids are:"):
        Hub._choose(machine.startable(), "nothing")


def test_defaults_prefer_android_then_an_iphone(machine):
    options = machine.startable()
    assert Hub._default(options, None, None).id == "avd:spare_avd"
    assert "iPhone" in Hub._default(options, "ios", None).name
    assert Hub._default(options, None, "simulator").platform == "ios"
    assert Hub._default([], None, None) is None


def test_a_real_android_phone_is_not_started_or_stopped(machine):
    with pytest.raises(PhoneError, match="USB debugging"):
        machine.begin_start("android", "device", None, False)
    with pytest.raises(Unsupported, match="not powered off"):
        machine.stop("R58M12ABC")


def test_asking_for_an_ios_device_explains_it_is_a_simulator(machine, monkeypatch):
    monkeypatch.setattr(machine, "_boot_simulator", lambda phone, headless, note: (phone, note))
    phone, note = machine.begin_start("ios", "device", None, False)
    assert "iPhone" in phone.name and "simulators" in note


def test_a_running_phone_is_returned_not_restarted(machine):
    starting = machine.begin_start(None, None, "emulator-5554", False)
    assert starting.id == "emulator-5554" and "already running" in starting.note
    assert machine.begin_start(None, None, "avd:my_avd", False).id == "emulator-5554"


def test_missing_tools_are_not_a_crash(monkeypatch):
    monkeypatch.setattr(locate, "adb", lambda: None)
    monkeypatch.setattr(locate, "emulator", lambda: None)
    monkeypatch.setattr(locate, "xcrun", lambda: None)
    hub = Hub()
    assert hub.running() == [] and hub.startable() == []
    with pytest.raises(PhoneError, match="No phone is running"):
        hub.driver(None)


# --- reading the pixels when the tree has nothing ----------------------------------------------------------------------

class TreelessDriver(FakeDriver):
    """A game or canvas: no accessibility text at all."""

    def elements(self):
        return [Element("", 195, 700, 300, 60, type="Button", id="canvas", clickable=True)]


class BrokenTreeDriver(FakeDriver):
    def elements(self):
        raise PhoneError("The accessibility tree is unavailable (could not get idle state).")


@pytest.fixture
def pixels(monkeypatch):
    monkeypatch.setattr(ocr, "recognize", lambda png, screen: [Element("Play", 100, 300, 80, 30, type="Text", source="pixels")])


@pytest.mark.anyio
async def test_a_screen_with_no_text_is_read_from_its_pixels(pixels):
    phone = TreelessDriver()
    async with connected(serve(phone)) as s:
        text = text_of(await s.call_tool("phone_list_elements_on_screen", {}))
        assert '"Play" at (100, 300)' in text and "misread" in text
        assert "id=canvas" in text, "what the tree does know is kept"
        assert "Tapped" in text_of(await s.call_tool("phone_tap_element", {"text": "play"}))
    assert ("tap", 100, 300) in phone.calls


@pytest.mark.anyio
async def test_a_broken_tree_falls_back_to_pixels_unless_told_not_to(pixels):
    async with connected(serve(BrokenTreeDriver())) as s:
        assert '"Play"' in text_of(await s.call_tool("phone_list_elements_on_screen", {}))
        r = await s.call_tool("phone_list_elements_on_screen", {"source": "accessibility"})
        assert r.is_error and "idle state" in text_of(r)


@pytest.mark.anyio
async def test_text_the_tree_misses_is_found_in_the_pixels(pixels):
    phone = FakeDriver()
    async with connected(serve(phone)) as s:
        assert "Tapped" in text_of(await s.call_tool("phone_tap_element", {"text": "Play"}))
        r = await s.call_tool("phone_tap_element", {"id": "no_such_id"})
    assert r.is_error, "an id cannot be read from pixels"
    assert ("tap", 100, 300) in phone.calls
