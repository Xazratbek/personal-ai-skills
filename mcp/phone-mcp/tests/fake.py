"""An in-memory phone and an MCP client wired to the server, so tests speak the protocol clients speak."""
from __future__ import annotations

from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path

import anyio
from mcp.client.session import ClientSession
from mcp.shared.memory import create_client_server_memory_streams
from PIL import Image

from phone_mcp.devices import Hub, Phone, Starting
from phone_mcp.drivers.base import App, Driver
from phone_mcp.elements import Element
from phone_mcp.errors import PhoneError
from phone_mcp.server import build_server

SCREEN = (390, 844)
CAPTURE_SIZE = (780, 1688)


def png_of(size) -> bytes:
    out = BytesIO()
    Image.new("RGB", size, (40, 90, 160)).save(out, "PNG")
    return out.getvalue()


class FakeDriver(Driver):
    platform = "ios"
    kind = "simulator"

    def __init__(self, id="FAKE-1", name="Fake iPhone"):
        super().__init__()
        self.id, self.name = id, name
        self.calls: list[tuple] = []
        self.screen = [
            Element("Hello", 195, 200, 200, 30, type="StaticText"),
            Element("Continue", 195, 500, 160, 44, type="Button", id="continue_btn", clickable=True),
            Element("", 40, 60, 44, 44, type="Button", id="close_btn", clickable=True),
        ]
        self.apps = [App("com.example.mock", "Mock")]
        self.front: App | None = App("com.example.mock", "Mock")

    def _log(self, *call):
        self.calls.append(call)

    def capture(self): return png_of(CAPTURE_SIZE)
    def screen_size(self): return SCREEN
    def elements(self): return [Element(**vars(e)) for e in self.screen]
    def tap(self, x, y): self._log("tap", x, y)
    def double_tap(self, x, y): self._log("double_tap", x, y)
    def long_press(self, x, y, seconds): self._log("long_press", x, y, seconds)
    def swipe(self, x1, y1, x2, y2, seconds=0.3): self._log("swipe", x1, y1, x2, y2, seconds)
    def drag(self, x1, y1, x2, y2, seconds=0.8): self._log("drag", x1, y1, x2, y2, seconds)
    def clear_text(self): self._log("clear")
    def press_enter(self): self._log("enter")

    def type_text(self, text, method="auto"):
        self._log("type", text, method)
        return "keys"

    def press(self, button):
        self._log("press", button)
        return None

    def list_apps(self, include_system=False):
        self._log("list_apps", include_system)
        return self.apps

    def launch_app(self, name):
        self._log("launch", name)
        return "com.example.mock"

    def foreground_app(self): return self.front
    def terminate_app(self, name): return name
    def install_app(self, path: Path): return path.name
    def uninstall_app(self, name): return name
    def clear_app_data(self, name): return name
    def set_permission(self, app, permission, action): return app
    def open_url(self, url): self._log("open_url", url)
    def info(self): return {"id": self.id, "platform": self.platform, "battery": None}
    def get_appearance(self): return "light"
    def set_appearance(self, mode): self._log("appearance", mode)
    def set_location(self, latitude, longitude): self._log("location", latitude, longitude)
    def set_orientation(self, orientation): self._log("orientation", orientation)
    def clipboard_get(self): return ""
    def clipboard_set(self, text): self._log("clipboard", text)
    def logs(self, app, seconds): return "a one\nb two\nc three"
    def start_recording(self, path): self._log("record", str(path))

    def stop_recording(self):
        raise PhoneError("Nothing is recording. phone_start_recording first.")

    def send_notification(self, title, body, app): self._log("notify", title, body, app)
    def shell(self, command, timeout): return f"ran {command}"
    def add_media(self, path): return path.name


class FakeHub(Hub):
    def __init__(self, *phones: FakeDriver):
        super().__init__()
        self.fakes = {d.id: d for d in phones}
        self.started: list[tuple] = []

    def running(self):
        return [Phone(d.id, d.platform, d.kind, d.name) for d in self.fakes.values()]

    def startable(self):
        return [Phone("avd:spare", "android", "emulator", "spare"),
                Phone("OLD-1", "ios", "simulator", "Old iPhone", "iOS 26.0", newest=False)]

    def _make_driver(self, phone):
        return self.fakes[phone.id]

    def begin_start(self, platform, kind, device_id, headless):
        self.started.append((platform, kind, device_id, headless))
        driver = FakeDriver("STARTED-1", "Started")
        self.fakes[driver.id] = driver
        return Starting(Phone(driver.id, driver.platform, driver.kind, driver.name))

    def stop(self, device):
        driver = self.driver(device)
        self._forget(driver.id)
        del self.fakes[driver.id]
        return driver.id


@asynccontextmanager
async def connected(server):
    async with create_client_server_memory_streams() as ((client_read, client_write), (server_read, server_write)):
        async with anyio.create_task_group() as tg:
            low = server._lowlevel_server
            tg.start_soon(low.run, server_read, server_write, low.create_initialization_options())
            async with ClientSession(client_read, client_write) as session:
                await session.initialize()
                yield session
            tg.cancel_scope.cancel()


def serve(*phones):
    return build_server(FakeHub(*phones))


def text_of(result) -> str:
    return "\n".join(c.text for c in result.content if getattr(c, "type", None) == "text")
