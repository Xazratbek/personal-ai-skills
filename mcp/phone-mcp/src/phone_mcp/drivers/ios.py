"""iOS simulators through simctl (system, apps) and AXe (touch, keyboard, accessibility tree)."""
from __future__ import annotations

import json
import plistlib
import re
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from .. import locate
from ..elements import IOS_TOGGLES, Element, parse_ios
from ..errors import PhoneError, Unsupported
from ..proc import Completed, run
from ..screenshots import image_size
from .base import App, Driver

KEY_ENTER, KEY_BACKSPACE, KEY_A, KEY_V, MOD_COMMAND = 40, 42, 4, 25, 227
TREE_RETRIES = 4
# Unlike a paste, HID typing goes through smart punctuation, autocorrect and auto-capitalisation.
PLAIN_TOKEN = re.compile(r"[A-Za-z0-9_@.+\-]+")
SMART_PUNCTUATION = re.compile(r"--|\.\.\.")
SERVICES = {"camera": "camera", "microphone": "microphone", "location": "location", "contacts": "contacts",
            "calendar": "calendar", "photos": "photos", "reminders": "reminders", "motion": "motion",
            "media": "media-library", "siri": "siri", "all": "all"}


def should_paste(text: str) -> bool:
    return not PLAIN_TOKEN.fullmatch(text) or bool(SMART_PUNCTUATION.search(text))


class IosDriver(Driver):
    platform = "ios"
    kind = "simulator"

    def __init__(self, udid: str, name: str = ""):
        super().__init__()
        self.id = udid
        self.name = name or udid
        self._scale: float | None = None
        self._size: tuple[int, int] | None = None
        self._size_at = 0.0
        self._recorder: subprocess.Popen | None = None
        self._recording_path: Path | None = None
        self._root: dict = {}

    # --- CLIs -------------------------------------------------------------------------------------------------------

    def _simctl(self, *args: str, timeout: float = 30, stdin: bytes | None = None, check: bool = True) -> Completed:
        done = run([locate.xcrun() or "xcrun", "simctl", args[0], self.id, *args[1:]], timeout=timeout, stdin=stdin,
                   check=False)
        if check and done.rc != 0:
            self._raise(f"simctl {args[0]}", done)
        return done

    def _axe(self, *args: str, timeout: float = 30, stdin: bytes | None = None, check: bool = True) -> Completed:
        tool = locate.axe()
        if not tool:
            raise PhoneError("AXe is not installed. Run `brew install cameroncooke/axe/axe`; phone_doctor has details.")
        done = run([tool, *args, "--udid", self.id], timeout=timeout, stdin=stdin, check=False)
        if check and done.rc != 0:
            self._raise(f"axe {args[0]}", done)
        return done

    def _raise(self, what: str, done: Completed):
        detail = (done.errtext.strip() or done.text.strip())[-500:]
        lowered = detail.lower()
        if "current state: shutdown" in lowered or "not booted" in lowered or "invalid device" in lowered:
            raise PhoneError(f"device {self.id} is not running: phone_list_available_devices shows what is running.")
        raise PhoneError(f"{what} failed: {detail}")

    # --- the screen -------------------------------------------------------------------------------------------------

    def capture(self) -> bytes:
        # `simctl io screenshot -` writes nothing to stdout on this Xcode, so go through a file.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "screen.png"
            self._simctl("io", "screenshot", "--type=png", str(path), timeout=30)
            data = path.read_bytes()
        self._remember_size(data)
        return data

    def _remember_size(self, png: bytes) -> tuple[int, int]:
        w, h = image_size(png)
        scale = self._device_scale()
        self._size, self._size_at = (round(w / scale), round(h / scale)), time.monotonic()
        return self._size

    def _device_scale(self) -> float:
        if self._scale:
            return self._scale
        self._scale = 3.0
        try:
            listing = json.loads(run([locate.xcrun() or "xcrun", "simctl", "list", "-j", "devices", "devicetypes"],
                                     timeout=20).out)
            type_id = next(d.get("deviceTypeIdentifier") for group in listing["devices"].values() for d in group
                           if d.get("udid") == self.id)
            bundle = next(t["bundlePath"] for t in listing["devicetypes"] if t["identifier"] == type_id)
            with open(Path(bundle) / "Contents/Resources/capabilities.plist", "rb") as handle:
                caps = plistlib.load(handle)
            found = _find_key(caps, "main-screen-scale")
            if found:
                self._scale = float(found)
        except (StopIteration, KeyError, OSError, ValueError, plistlib.InvalidFileException):
            pass
        return self._scale

    def screen_size(self) -> tuple[int, int]:
        if self._size and time.monotonic() - self._size_at <= 20:
            return self._size
        return self._remember_size(self.capture())

    def _tree(self) -> list:
        last = ""
        for attempt in range(TREE_RETRIES):
            # Right after boot the automation session can take several tries to come up.
            done = self._axe("describe-ui", timeout=30, check=False)
            if done.rc == 0:
                try:
                    tree = json.loads(done.out)
                except ValueError:
                    last = "AXe returned something that is not JSON"
                else:
                    roots = tree if isinstance(tree, list) else [tree]
                    self._root = roots[0] if roots else {}
                    return roots
            else:
                last = done.errtext.strip()[-300:]
                if "shutdown" in last.lower() or "not booted" in last.lower():
                    self._raise("axe describe-ui", done)
            time.sleep(1.0 + attempt)
        raise PhoneError(f"The accessibility tree is unavailable: {last}. Use source=\"ocr\" or a screenshot.")

    def elements(self) -> list[Element]:
        return parse_ios(self._tree(), self.screen_size())

    def tap_point(self, element: Element) -> tuple[float, float]:
        # A SwiftUI Toggle's row spans the screen, but only the control at its trailing end responds.
        if element.type in IOS_TOGGLES and element.w > 80:
            return element.x + element.w / 2 - 30, element.y
        return element.x, element.y

    # --- touch ------------------------------------------------------------------------------------------------------

    def tap(self, x: int, y: int) -> None:
        # AXe's default tap misses toggles about half the time; a real touch down and up has not.
        self._axe("tap", "-x", str(x), "-y", str(y), "--tap-style", "physical")

    def double_tap(self, x: int, y: int) -> None:
        # Each `axe batch` step sets up its session again, about 0.7 s, which is past iOS's double-tap window.
        # Two processes set up side by side and land inside it, with the second one held back slightly.
        tool = locate.axe()
        if not tool:
            raise PhoneError("AXe is not installed. Run `brew install cameroncooke/axe/axe`; phone_doctor has details.")
        tap = [tool, "tap", "-x", str(x), "-y", str(y), "--tap-style", "simulator", "--udid", self.id]
        taps = [subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                for argv in (tap, [*tap, "--pre-delay", "0.12"])]
        problems = []
        for process in taps:
            try:
                _out, err = process.communicate(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill()
                problems.append("timed out")
                continue
            if process.returncode != 0:
                problems.append(err.decode(errors="replace").strip()[-200:])
        if problems:
            raise PhoneError(f"The double tap did not complete: {problems[0]}")

    def long_press(self, x: int, y: int, seconds: float) -> None:
        self._axe("touch", "-x", str(x), "-y", str(y), "--down", "--up", "--delay", f"{seconds:.3f}",
                  timeout=seconds + 20)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, seconds: float = 0.3) -> None:
        self._axe("swipe", "--start-x", str(x1), "--start-y", str(y1), "--end-x", str(x2), "--end-y", str(y2),
                  "--duration", f"{seconds:.3f}", timeout=seconds + 20)

    def drag(self, x1: int, y1: int, x2: int, y2: int, seconds: float = 0.8) -> None:
        self._axe("drag", "--start-x", str(x1), "--start-y", str(y1), "--end-x", str(x2), "--end-y", str(y2),
                  "--duration", f"{seconds:.3f}", timeout=seconds + 20)

    # --- keyboard ---------------------------------------------------------------------------------------------------

    def type_text(self, text: str, method: str = "auto") -> str:
        if not text:
            return "keys"
        if method == "keys" and not text.isascii():
            raise PhoneError("method=\"keys\" can only send US keyboard characters on iOS. Use method=\"auto\".")
        if method == "paste" or (method == "auto" and should_paste(text)):
            self._paste(text)
            return "paste"
        self._axe("type", "--stdin", stdin=text.encode(), timeout=30 + len(text) / 10)
        return "keys"

    def _paste(self, text: str) -> None:
        saved = self._simctl("pbpaste", timeout=10, check=False)
        self._simctl("pbcopy", stdin=text.encode(), timeout=10)
        self._axe("key-combo", "--modifiers", str(MOD_COMMAND), "--key", str(KEY_V))
        time.sleep(0.3)
        if saved.rc == 0:
            self._simctl("pbcopy", stdin=saved.out, timeout=10, check=False)

    def clear_text(self) -> None:
        self._axe("key-combo", "--modifiers", str(MOD_COMMAND), "--key", str(KEY_A))
        time.sleep(0.15)
        self._axe("key", str(KEY_BACKSPACE))

    def press_enter(self) -> None:
        self._axe("key", str(KEY_ENTER))

    def press(self, button: str) -> str | None:
        if button == "HOME":
            self._axe("button", "home")
        elif button == "ENTER":
            self.press_enter()
        elif button == "APP_SWITCHER":
            self._axe("batch", "--step", "button home", "--step", "sleep 0.15", "--step", "button home")
        elif button == "BACK":
            return self._back()
        return None

    def _back(self) -> str:
        """An iPhone has no Back button: use the app's own one, else the edge gesture every navigation stack honours."""
        for node in _walk(self._tree()):
            if node.get("AXUniqueId") == "BackButton":
                frame = node.get("frame") or {}
                if frame.get("width") and frame.get("height"):
                    self.tap(round(frame["x"] + frame["width"] / 2), round(frame["y"] + frame["height"] / 2))
                    return "tapped the app's back button"
        w, h = self.screen_size()
        self._axe("gesture", "swipe-from-left-edge", "--screen-width", str(w), "--screen-height", str(h))
        return "swiped in from the left edge"

    # --- apps -------------------------------------------------------------------------------------------------------

    def _installed(self) -> dict:
        raw = self._simctl("listapps", timeout=30).out
        converted = run(["/usr/bin/plutil", "-convert", "json", "-o", "-", "-"], stdin=raw, timeout=15).out
        return json.loads(converted)

    @staticmethod
    def _display(meta: dict) -> str:
        return meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or ""

    def list_apps(self, include_system: bool = False) -> list[App]:
        apps = [App(bundle, self._display(meta)) for bundle, meta in self._installed().items()
                if include_system or meta.get("ApplicationType") == "User"]
        return sorted(apps, key=lambda a: a.id)

    def _resolve(self, name: str) -> tuple[str, dict]:
        wanted = name.strip()
        installed = self._installed()
        if wanted in installed:
            return wanted, installed[wanted]
        folded = wanted.casefold()
        exact = [b for b, m in installed.items() if self._display(m).casefold() == folded]
        if len(exact) == 1:
            return exact[0], installed[exact[0]]
        partial = exact or [b for b, m in installed.items()
                            if folded in self._display(m).casefold() or folded in b.casefold()]
        if len(partial) == 1:
            return partial[0], installed[partial[0]]
        choices = [f"{b} ({self._display(installed[b])})" for b in partial] or \
            [f"{b} ({self._display(m)})" for b, m in installed.items() if m.get("ApplicationType") == "User"]
        raise PhoneError(f"No single app matches {name!r}. Candidates: {', '.join(choices[:30]) or 'none'}. "
                         "Pass the bundle id; phone_list_apps with include_system lists every app.")

    def launch_app(self, name: str) -> str:
        bundle, _meta = self._resolve(name)
        out = self._simctl("launch", bundle, timeout=60).text
        match = re.search(r":\s*(\d+)", out)
        if match:
            self._wait_front(int(match.group(1)))
        return bundle

    def _wait_front(self, pid: int, seconds: float = 4.0) -> None:
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                if self._tree()[0].get("pid") == pid:
                    return
            except (PhoneError, IndexError):
                return
            time.sleep(0.3)

    def _bundle_of_pid(self, pid) -> str | None:
        out = self._simctl("spawn", "launchctl", "list", timeout=15, check=False).text
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) == 3 and parts[0] == str(pid):
                match = re.search(r"UIKitApplication:([^\[]+)", parts[2])
                return match.group(1) if match else None
        return None

    def foreground_app(self) -> App | None:
        tree = self._tree()
        root = tree[0] if tree else {}
        label = (root.get("AXLabel") or "").strip()
        bundle = self._bundle_of_pid(root.get("pid"))
        if not label or bundle in (None, "com.apple.springboard"):
            return None
        return App(bundle, label)

    def terminate_app(self, name: str) -> str:
        bundle, _meta = self._resolve(name)
        done = self._simctl("terminate", bundle, timeout=20, check=False)
        if done.rc != 0 and "found nothing to terminate" not in done.errtext:
            self._raise("simctl terminate", done)
        return bundle

    def install_app(self, path: Path) -> str:
        if path.suffix.lower() != ".app" or not path.is_dir():
            raise PhoneError(f"The simulator installs a .app built for the simulator; got {path.name}.")
        self._simctl("install", str(path), timeout=240)
        with open(path / "Info.plist", "rb") as handle:
            return plistlib.load(handle).get("CFBundleIdentifier", path.name)

    def uninstall_app(self, name: str) -> str:
        bundle, _meta = self._resolve(name)
        self._simctl("uninstall", bundle, timeout=60)
        return bundle

    def clear_app_data(self, name: str) -> str:
        bundle, _meta = self._resolve(name)
        self._simctl("terminate", bundle, timeout=20, check=False)
        container = Path(self._simctl("get_app_container", bundle, "data", timeout=20).text.strip())
        if f"/Devices/{self.id}/data/Containers/Data/Application/" not in str(container):
            raise PhoneError(f"Refusing to clear an unexpected path: {container}")
        for child in container.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, ignore_errors=True)
                child.mkdir(exist_ok=True)
            else:
                child.unlink(missing_ok=True)
        return bundle

    def set_permission(self, app: str, permission: str, action: str) -> str:
        bundle, _meta = self._resolve(app)
        service = SERVICES.get(permission.casefold())
        if not service:
            raise Unsupported(f"The simulator cannot set {permission!r} from outside the app. It can set: "
                              f"{', '.join(sorted(SERVICES))}.")
        self._simctl("privacy", action, service, bundle, timeout=30)
        return bundle

    def open_url(self, url: str) -> None:
        self._simctl("openurl", url, timeout=30)
        if not url.lower().startswith(("http://", "https://")):
            self._accept_open_prompt()

    def _accept_open_prompt(self, seconds: float = 3.0) -> None:
        """iOS asks `Open in "App"?` before following a custom scheme from outside, which would block everything after."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            nodes = list(_walk(self._tree()))
            asking = any((n.get("AXLabel") or "").startswith("Open in ") for n in nodes)
            button = next((n for n in nodes if n.get("type") == "Button" and n.get("AXLabel") == "Open"), None)
            if asking and button:
                frame = button.get("frame") or {}
                self.tap(round(frame["x"] + frame["width"] / 2), round(frame["y"] + frame["height"] / 2))
                return
            time.sleep(0.3)

    # --- system -----------------------------------------------------------------------------------------------------

    def info(self) -> dict:
        listing = json.loads(run([locate.xcrun() or "xcrun", "simctl", "list", "-j", "devices"], timeout=20).out)
        runtime, entry = next(((r, d) for r, group in listing["devices"].items() for d in group
                               if d.get("udid") == self.id), ("", {}))
        w, h = self.screen_size()
        return {
            "id": self.id, "platform": self.platform, "kind": self.kind, "model": entry.get("name", ""),
            "os_version": runtime.rsplit(".", 1)[-1].replace("iOS-", "").replace("-", "."),
            "state": entry.get("state", ""), "screen": f"{w}x{h}", "scale": self._device_scale(),
            "appearance": self.get_appearance(),
        }

    def get_appearance(self) -> str:
        return self._simctl("ui", "appearance", timeout=15).text.strip()

    def set_appearance(self, mode: str) -> None:
        self._simctl("ui", "appearance", mode, timeout=15)

    def set_location(self, latitude: float, longitude: float) -> None:
        self._simctl("location", "set", f"{latitude},{longitude}", timeout=15)

    def set_orientation(self, orientation: str) -> None:
        raise Unsupported("simctl and AXe cannot rotate a simulator. Use Device > Rotate in Simulator.app.")

    def clipboard_get(self) -> str:
        return self._simctl("pbpaste", timeout=10).text

    def clipboard_set(self, text: str) -> None:
        self._simctl("pbcopy", stdin=text.encode(), timeout=10)

    def logs(self, app: str | None, seconds: int) -> str:
        args = ["spawn", "log", "show", "--last", f"{int(seconds)}s", "--style", "compact", "--info", "--debug"]
        if app:
            bundle, meta = self._resolve(app)
            executable = str(meta.get("CFBundleExecutable") or bundle).replace('"', "")
            args += ["--predicate", f'process == "{executable}" OR subsystem == "{bundle}"']
        out = self._simctl(*args, timeout=60).text
        return "\n".join(line for line in out.splitlines()
                         if not line.startswith(("getpwuid_r", "Timestamp ", "Filtering the log data")))

    def start_recording(self, path: Path) -> None:
        if self._recorder and self._recorder.poll() is None:
            raise PhoneError("Already recording. phone_stop_recording first.")
        path.parent.mkdir(parents=True, exist_ok=True)
        self._recorder = subprocess.Popen(
            [locate.xcrun() or "xcrun", "simctl", "io", self.id, "recordVideo", "--codec=h264", "--force", str(path)],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        self._recording_path = path
        time.sleep(0.8)
        if self._recorder.poll() is not None:
            detail = self._recorder.stderr.read().decode(errors="replace")[-300:] if self._recorder.stderr else ""
            self._recorder = None
            raise PhoneError(f"The simulator refused to record: {detail}")

    def stop_recording(self) -> Path:
        if not self._recorder or not self._recording_path:
            raise PhoneError("Nothing is recording. phone_start_recording first.")
        # The MP4 is only finalised on SIGINT.
        self._recorder.send_signal(signal.SIGINT)
        try:
            self._recorder.wait(timeout=20)
        except subprocess.TimeoutExpired:
            self._recorder.kill()
        path, self._recorder, self._recording_path = self._recording_path, None, None
        if not path.is_file():
            raise PhoneError("The recording produced no file.")
        return path

    def send_notification(self, title: str, body: str, app: str | None) -> None:
        if not app:
            foreground = self.foreground_app()
            if not foreground:
                raise PhoneError("Say which app the notification comes from: `app`.")
            bundle = foreground.id
        else:
            bundle, _meta = self._resolve(app)
        payload = json.dumps({"aps": {"alert": {"title": title, "body": body}, "sound": "default"}}).encode()
        done = self._simctl("push", bundle, "-", stdin=payload, timeout=20, check=False)
        message = (done.errtext + done.text).strip()
        if done.rc != 0 or "not authorized" in message.lower():
            raise PhoneError(f"{bundle} did not accept the notification ({message[-200:]}). The app must request "
                             "notification permission and the user must allow it first.")

    def shell(self, command: str, timeout: float) -> str:
        done = self._simctl("spawn", *shlex.split(command), timeout=timeout, check=False)
        out = (done.text + done.errtext).strip()
        return out if done.rc == 0 else f"[exit code {done.rc}]\n{out}"

    def add_media(self, path: Path) -> str:
        self._simctl("addmedia", str(path), timeout=120)
        return path.name

    def close(self) -> None:
        if self._recorder and self._recorder.poll() is None:
            try:
                self.stop_recording()
            except PhoneError:
                self._recorder.kill()


def _walk(nodes):
    for node in nodes:
        yield node
        yield from _walk(node.get("children") or [])


def _find_key(value, key):
    if isinstance(value, dict):
        if key in value:
            return value[key]
        value = list(value.values())
    if isinstance(value, list):
        for item in value:
            found = _find_key(item, key)
            if found is not None:
                return found
    return None
