"""What the tools need from a phone. One driver per connected phone; never used by two threads at once."""
from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from ..elements import Element


@dataclass
class App:
    id: str
    name: str = ""

    def __str__(self) -> str:
        return f"{self.id} ({self.name})" if self.name else self.id


class Driver(ABC):
    id: str
    platform: str
    kind: str
    name: str

    def __init__(self):
        self.lock = threading.RLock()

    # The screen
    @abstractmethod
    def capture(self) -> bytes: ...
    @abstractmethod
    def screen_size(self) -> tuple[int, int]: ...
    @abstractmethod
    def elements(self) -> list[Element]: ...

    def tap_point(self, element: Element) -> tuple[float, float]:
        return element.x, element.y

    # Touch
    @abstractmethod
    def tap(self, x: int, y: int) -> None: ...
    @abstractmethod
    def double_tap(self, x: int, y: int) -> None: ...
    @abstractmethod
    def long_press(self, x: int, y: int, seconds: float) -> None: ...
    @abstractmethod
    def swipe(self, x1: int, y1: int, x2: int, y2: int, seconds: float = 0.3) -> None: ...
    @abstractmethod
    def drag(self, x1: int, y1: int, x2: int, y2: int, seconds: float = 0.8) -> None: ...

    # Keyboard
    @abstractmethod
    def type_text(self, text: str, method: str = "auto") -> str:
        """Returns how the text went in."""
    @abstractmethod
    def clear_text(self) -> None: ...
    @abstractmethod
    def press_enter(self) -> None: ...
    @abstractmethod
    def press(self, button: str) -> str | None:
        """Returns a note when the press was emulated."""

    # Apps
    @abstractmethod
    def list_apps(self, include_system: bool = False) -> list[App]: ...
    @abstractmethod
    def launch_app(self, name: str) -> str: ...
    @abstractmethod
    def foreground_app(self) -> App | None:
        """None means the home screen."""
    @abstractmethod
    def terminate_app(self, name: str) -> str: ...
    @abstractmethod
    def install_app(self, path: Path) -> str: ...
    @abstractmethod
    def uninstall_app(self, name: str) -> str: ...
    @abstractmethod
    def clear_app_data(self, name: str) -> str: ...
    @abstractmethod
    def set_permission(self, app: str, permission: str, action: str) -> str: ...
    @abstractmethod
    def open_url(self, url: str) -> None: ...

    # System
    @abstractmethod
    def info(self) -> dict: ...
    @abstractmethod
    def get_appearance(self) -> str: ...
    @abstractmethod
    def set_appearance(self, mode: str) -> None: ...
    @abstractmethod
    def set_location(self, latitude: float, longitude: float) -> None: ...
    @abstractmethod
    def set_orientation(self, orientation: str) -> None: ...
    @abstractmethod
    def clipboard_get(self) -> str: ...
    @abstractmethod
    def clipboard_set(self, text: str) -> None: ...
    @abstractmethod
    def logs(self, app: str | None, seconds: int) -> str: ...
    @abstractmethod
    def start_recording(self, path: Path) -> None: ...
    @abstractmethod
    def stop_recording(self) -> Path: ...
    @abstractmethod
    def send_notification(self, title: str, body: str, app: str | None) -> None: ...
    @abstractmethod
    def shell(self, command: str, timeout: float) -> str: ...
    @abstractmethod
    def add_media(self, path: Path) -> str: ...

    def close(self) -> None:  # noqa: B027
        """Finish anything still running when the server exits."""
