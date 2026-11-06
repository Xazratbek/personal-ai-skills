"""Android emulators and USB/Wi-Fi phones through adb."""
from __future__ import annotations

import base64
import json
import re
import shlex
import subprocess
import tempfile
import time
from importlib import resources
from pathlib import Path

from .. import locate
from ..elements import Element, parse_android
from ..errors import PhoneError, Unsupported
from ..proc import Completed, run
from .base import App, Driver

IME_PACKAGE = "com.phonemcp.ime"
IME_ID = f"{IME_PACKAGE}/.Ime"
REMOTE_RECORDING = "/sdcard/phone_mcp_recording.mp4"
LABEL_CACHE = Path.home() / "Library/Caches/phone-mcp/android-labels.json"
MAX_APK_FOR_LABEL = 150 * 1024 * 1024

KEYS = {"HOME": 3, "BACK": 4, "APP_SWITCHER": 187, "ENTER": 66}
KEY_DEL, KEY_MOVE_END, KEY_ENTER, KEY_TAB, KEY_CTRL_LEFT, KEY_A = 67, 123, 66, 61, 113, 29

APP_ALIASES = {
    "settings": "com.android.settings", "chrome": "com.android.chrome", "camera": "com.android.camera2",
    "phone": "com.google.android.dialer", "dialer": "com.google.android.dialer",
    "messages": "com.google.android.apps.messaging", "contacts": "com.google.android.contacts",
    "photos": "com.google.android.apps.photos", "gmail": "com.google.android.gm", "maps": "com.google.android.apps.maps",
    "youtube": "com.google.android.youtube", "play store": "com.android.vending", "calendar": "com.google.android.calendar",
    "clock": "com.google.android.deskclock", "files": "com.google.android.documentsui",
    "calculator": "com.google.android.calculator", "google": "com.google.android.googlequicksearchbox",
}
PERMISSIONS = {
    "camera": ["android.permission.CAMERA"],
    "microphone": ["android.permission.RECORD_AUDIO"],
    "location": ["android.permission.ACCESS_FINE_LOCATION", "android.permission.ACCESS_COARSE_LOCATION"],
    "contacts": ["android.permission.READ_CONTACTS", "android.permission.WRITE_CONTACTS"],
    "calendar": ["android.permission.READ_CALENDAR", "android.permission.WRITE_CALENDAR"],
    "photos": ["android.permission.READ_MEDIA_IMAGES", "android.permission.READ_MEDIA_VIDEO"],
    "notifications": ["android.permission.POST_NOTIFICATIONS"],
    "phone": ["android.permission.CALL_PHONE"],
    "sms": ["android.permission.SEND_SMS", "android.permission.READ_SMS"],
}


def input_text_chunks(text: str) -> list[str]:
    """`input text` reads %s as a space, so a literal "%s" has to be sent in two pieces."""
    pieces = re.split(r"(?<=%)(?=s)", text)
    chunks: list[str] = []
    for piece in pieces:
        for start in range(0, len(piece), 200):
            chunks.append(piece[start:start + 200].replace(" ", "%s"))
    return chunks


def is_keyboard_safe(text: str) -> bool:
    return all(32 <= ord(c) < 127 or c in "\n\t" for c in text)


class AndroidDriver(Driver):
    platform = "android"

    def __init__(self, serial: str):
        super().__init__()
        self.id = serial
        self.kind = "emulator" if serial.startswith("emulator-") else "device"
        self.name = serial
        self._recorder: subprocess.Popen | None = None
        self._recording_path: Path | None = None

    # --- adb ----------------------------------------------------------------------------------------------------

    def _adb(self, *args: str, timeout: float = 30, check: bool = True) -> Completed:
        tool = locate.adb()
        if not tool:
            raise PhoneError("adb is not installed. phone_doctor shows how to fix it.")
        done = run([tool, "-s", self.id, *args], timeout=timeout, check=False)
        problem = done.errtext.lower()
        if done.rc != 0 and ("not found" in problem or "offline" in problem or "no devices" in problem):
            raise PhoneError(f"device {self.id} is not running: phone_list_available_devices shows what is running.")
        if check and done.rc != 0:
            detail = (done.errtext.strip() or done.text.strip())[-600:]
            raise PhoneError(f"adb {args[0]} failed on {self.id}: {detail}")
        return done

    def _sh(self, command: str, timeout: float = 30, check: bool = True) -> str:
        return self._adb("shell", command, timeout=timeout, check=check).text.replace("\r\n", "\n").strip()

    def _settings(self, namespace: str, key: str) -> str:
        return self._sh(f"settings get {namespace} {key}")

    # --- the screen -------------------------------------------------------------------------------------------------

    def capture(self) -> bytes:
        for _ in range(2):
            data = self._adb("exec-out", "screencap", "-p", timeout=20).out
            if data[:8] == b"\x89PNG\r\n\x1a\n":
                return data
            time.sleep(0.5)
        raise PhoneError("The phone returned no screenshot.")

    def screen_size(self) -> tuple[int, int]:
        out = self._sh("dumpsys window displays", timeout=15)
        match = re.search(r"\bcur=(\d+)x(\d+)", out)
        if match:
            return int(match.group(1)), int(match.group(2))
        match = re.search(r"(\d+)x(\d+)", self._sh("wm size"))
        if not match:
            raise PhoneError("The phone did not report its screen size.")
        return int(match.group(1)), int(match.group(2))

    def elements(self) -> list[Element]:
        screen = self.screen_size()
        last = ""
        for _ in range(4):
            done = self._adb("exec-out", "uiautomator", "dump", "/dev/tty", timeout=25, check=False)
            if b"</hierarchy>" in done.out:
                return parse_android(done.out, screen)
            last = (done.text or done.errtext).strip()[:200]
            time.sleep(0.7)
        raise PhoneError(f"The accessibility tree is unavailable ({last}). Screens that never stop animating cause "
                         "this. Use source=\"ocr\" or a screenshot.")

    # --- touch ------------------------------------------------------------------------------------------------------

    def tap(self, x: int, y: int) -> None:
        self._sh(f"input tap {x} {y}")

    def double_tap(self, x: int, y: int) -> None:
        # GestureDetector ignores a second tap sooner than 40 ms or later than 300 ms after the first.
        self._sh(f"cmd input tap {x} {y}; sleep 0.08; cmd input tap {x} {y}")

    def long_press(self, x: int, y: int, seconds: float) -> None:
        self._sh(f"input swipe {x} {y} {x} {y} {int(seconds * 1000)}", timeout=seconds + 15)

    def swipe(self, x1: int, y1: int, x2: int, y2: int, seconds: float = 0.3) -> None:
        self._sh(f"input swipe {x1} {y1} {x2} {y2} {int(seconds * 1000)}", timeout=seconds + 15)

    def drag(self, x1: int, y1: int, x2: int, y2: int, seconds: float = 0.8) -> None:
        self._sh(f"input swipe {x1} {y1} {x2} {y2} {int(seconds * 1000)}", timeout=seconds + 15)

    # --- keyboard ---------------------------------------------------------------------------------------------------

    def type_text(self, text: str, method: str = "auto") -> str:
        if not text:
            return "keys"
        safe = is_keyboard_safe(text)
        if method == "keys" and not safe:
            raise PhoneError("method=\"keys\" can only send plain ASCII on Android. Use method=\"auto\".")
        if method == "paste" or not safe:
            self._with_ime(lambda: self._ime_send("TEXT", text))
            return "helper keyboard"
        self._keys(text)
        return "keys"

    def _keys(self, text: str) -> None:
        for part in re.split(r"([\n\t])", text):
            if part == "\n":
                self._sh(f"input keyevent {KEY_ENTER}")
            elif part == "\t":
                self._sh(f"input keyevent {KEY_TAB}")
            else:
                for chunk in input_text_chunks(part):
                    self._sh(f"input text {shlex.quote(chunk)}")

    def clear_text(self) -> None:
        done = self._adb("shell", f"input keycombination {KEY_CTRL_LEFT} {KEY_A}", check=False)
        if done.rc == 0 and "Error" not in done.text and "Unknown" not in done.text:
            self._sh(f"input keyevent {KEY_DEL}")
            return
        self._sh(f"input keyevent {KEY_MOVE_END} " + " ".join([str(KEY_DEL)] * 250))

    def press_enter(self) -> None:
        self._sh(f"input keyevent {KEY_ENTER}")

    def press(self, button: str) -> str | None:
        self._sh(f"input keyevent {KEYS[button]}")
        return None

    # --- the helper keyboard: Unicode and clipboard, which adb shell cannot reach ------------------------------------

    def _ensure_ime(self) -> None:
        if IME_PACKAGE in self._sh(f"pm path {IME_PACKAGE}", check=False):
            return
        apk = resources.files("phone_mcp").joinpath("assets/phone_mcp_ime.apk")
        with resources.as_file(apk) as path:
            self._adb("install", "-r", "-t", str(path), timeout=120)

    def _with_ime(self, action):
        self._ensure_ime()
        previous = self._settings("secure", "default_input_method")
        self._sh(f"ime enable {IME_ID}")
        try:
            self._sh(f"ime set {IME_ID}")
            deadline = time.monotonic() + 5
            while self._settings("secure", "default_input_method") != IME_ID and time.monotonic() < deadline:
                time.sleep(0.1)
            return action()
        finally:
            if previous and previous != "null":
                self._sh(f"ime set {shlex.quote(previous)}", check=False)
            self._sh(f"ime disable {IME_ID}", check=False)

    def _ime_send(self, action: str, text: str | None = None, retry_for: float = 4.0) -> str:
        command = f"am broadcast -a {IME_PACKAGE}.{action}"
        if text is not None:
            command += " --es b64 " + base64.b64encode(text.encode()).decode()
        deadline = time.monotonic() + retry_for
        while True:
            out = self._sh(command, timeout=20)
            match = re.search(r"result=(-?\d+)(?:, data=\"([^\"]*)\")?", out)
            code = match.group(1) if match else ""
            if code == "1":
                return match.group(2) or ""
            if time.monotonic() >= deadline:
                if code == "2":
                    raise PhoneError("No text field is focused. Tap the field first, then type.")
                raise PhoneError("The helper keyboard did not answer. Tap the field and try again.")
            time.sleep(0.25)

    def clipboard_get(self) -> str:
        data = self._with_ime(lambda: self._ime_send("CLIP_GET"))
        return base64.b64decode(data).decode("utf-8", errors="replace")

    def clipboard_set(self, text: str) -> None:
        self._with_ime(lambda: self._ime_send("CLIP_SET", text))

    # --- apps -------------------------------------------------------------------------------------------------------

    def _launcher_packages(self) -> list[str]:
        out = self._sh("cmd package query-activities --brief -a android.intent.action.MAIN "
                       "-c android.intent.category.LAUNCHER", check=False)
        packages = []
        for line in out.splitlines():
            line = line.strip()
            if "/" in line and " " not in line and line.split("/")[0] not in packages:
                packages.append(line.split("/")[0])
        return packages

    def _packages(self, flag: str = "") -> list[str]:
        out = self._sh(f"pm list packages {flag}".strip())
        return sorted(line.split(":", 1)[1].strip() for line in out.splitlines() if line.startswith("package:"))

    def list_apps(self, include_system: bool = False) -> list[App]:
        user = [p for p in self._packages("-3") if p != IME_PACKAGE]
        labels = _load_labels()
        ids = sorted(set(user) | set(self._launcher_packages())) if include_system else user
        return [App(p, labels.get(p, "")) for p in ids]

    def _resolve(self, name: str) -> str:
        """A package id, an icon label, or part of either; several matches come back as a question."""
        wanted = name.strip()
        everything = set(self._packages())
        if wanted in everything:
            return wanted
        launchable = self._launcher_packages()
        folded = wanted.casefold()
        alias = APP_ALIASES.get(folded)
        if alias and alias in everything:
            return alias
        labels = _load_labels()
        by_label = [p for p in launchable if labels.get(p, "").casefold() == folded]
        if len(by_label) == 1:
            return by_label[0]
        token = re.sub(r"[^a-z0-9]", "", folded)
        by_tail = [p for p in launchable if p.rsplit(".", 1)[-1].casefold() == token]
        if len(by_tail) == 1:
            return by_tail[0]
        partial = [p for p in launchable if token and token in re.sub(r"[^a-z0-9]", "", p.casefold())]
        if len(partial) == 1:
            return partial[0]
        labels = self._learn_labels(self._packages("-3"))
        by_label = [p for p in launchable if folded in labels.get(p, "").casefold()]
        if len(by_label) == 1:
            return by_label[0]
        choices = partial or by_label or launchable
        raise PhoneError(f"No single app matches {name!r}. Candidates: {', '.join(choices[:40])}. "
                         "Pass the package id.")

    def _learn_labels(self, packages: list[str]) -> dict[str, str]:
        """Icon labels live only inside the APK, so they are read from user apps once and cached."""
        labels = _load_labels()
        aapt = locate.build_tool("aapt2")
        if not aapt:
            return labels
        changed = False
        for package in packages:
            if package in labels:
                continue
            match = re.search(r"package:(\S+)", self._sh(f"pm path {package}", check=False))
            if not match:
                continue
            with tempfile.TemporaryDirectory() as tmp:
                size = self._sh(f"stat -c %s {shlex.quote(match.group(1))}", check=False)
                if not size.isdigit() or int(size) > MAX_APK_FOR_LABEL:
                    continue
                local = Path(tmp) / "app.apk"
                self._adb("pull", match.group(1), str(local), timeout=120, check=False)
                if not local.is_file():
                    continue
                out = run([aapt, "dump", "badging", str(local)], timeout=30, check=False).text
                found = re.search(r"application-label:'([^']*)'", out)
                if found:
                    labels[package] = found.group(1)
                    changed = True
        if changed:
            LABEL_CACHE.parent.mkdir(parents=True, exist_ok=True)
            LABEL_CACHE.write_text(json.dumps(labels, ensure_ascii=False, indent=0))
        return labels

    def launch_app(self, name: str) -> str:
        package = self._resolve(name)
        out = self._sh(f"cmd package resolve-activity --brief -c android.intent.category.LAUNCHER "
                       f"-a android.intent.action.MAIN {package}", check=False)
        component = next((line.strip() for line in reversed(out.splitlines()) if "/" in line), None)
        if not component:
            raise PhoneError(f"{package} has no launcher screen to open.")
        result = self._sh(f"am start -n {shlex.quote(component)}")
        if "Error" in result:
            raise PhoneError(f"Could not open {package}: {result[-300:]}")
        return package

    def foreground_app(self) -> App | None:
        out = self._sh("dumpsys window", timeout=15)
        match = re.search(r"mCurrentFocus=Window\{\S+ \S+ ([\w.]+)/", out) or \
            re.search(r"mFocusedApp=\S+\{\S+ \S+ ([\w.]+)/", out)
        if not match:
            return None
        package = match.group(1)
        home = self._sh("cmd package resolve-activity --brief -c android.intent.category.HOME "
                        "-a android.intent.action.MAIN", check=False)
        if package in home:
            return None
        return App(package, _load_labels().get(package, ""))

    def terminate_app(self, name: str) -> str:
        package = self._resolve(name)
        self._sh(f"am force-stop {package}")
        return package

    def install_app(self, path: Path) -> str:
        if path.suffix.lower() != ".apk":
            raise PhoneError(f"Android installs an .apk; got {path.name}.")
        out = self._adb("install", "-r", "-t", str(path), timeout=240).text
        if "Success" not in out:
            raise PhoneError(f"Install failed: {out[-300:]}")
        aapt = locate.build_tool("aapt2")
        if aapt:
            name = run([aapt, "dump", "packagename", str(path)], timeout=30, check=False).text.strip()
            if name:
                return name
        return path.name

    def uninstall_app(self, name: str) -> str:
        package = self._resolve(name)
        out = self._adb("uninstall", package, timeout=60, check=False)
        if "Success" not in out.text:
            raise PhoneError(f"Could not uninstall {package}: {(out.text or out.errtext).strip()[-300:]}")
        return package

    def clear_app_data(self, name: str) -> str:
        package = self._resolve(name)
        out = self._sh(f"pm clear {package}", timeout=30)
        if "Success" not in out:
            raise PhoneError(f"Could not clear {package}: {out[-300:]}")
        return package

    def set_permission(self, app: str, permission: str, action: str) -> str:
        package = self._resolve(app)
        names = PERMISSIONS.get(permission.casefold()) or ([permission] if "." in permission else None)
        if not names:
            raise PhoneError(f"Unknown permission {permission!r}. Use one of {', '.join(sorted(PERMISSIONS))}, "
                             "or a full android.permission.* name.")
        verb = "grant" if action == "grant" else "revoke"
        problems = []
        for name in names:
            out = self._adb("shell", f"pm {verb} {package} {shlex.quote(name)}", check=False)
            if out.rc != 0:
                problems.append((out.errtext or out.text).strip().splitlines()[0][:200])
        if len(problems) == len(names):
            raise PhoneError(f"Could not {verb} {permission} for {package}: {problems[0]}")
        return package

    def open_url(self, url: str) -> None:
        out = self._sh(f"am start -a android.intent.action.VIEW -d {shlex.quote(url)}")
        if "Error" in out:
            raise PhoneError(f"Nothing on the phone opens {url}: {out[-300:]}")

    # --- system -----------------------------------------------------------------------------------------------------

    def info(self) -> dict:
        w, h = self.screen_size()
        battery = re.search(r"level: (\d+)", self._sh("dumpsys battery", check=False))
        return {
            "id": self.id, "platform": self.platform, "kind": self.kind,
            "model": self._sh("getprop ro.product.model"),
            "os_version": self._sh("getprop ro.build.version.release"),
            "api_level": self._sh("getprop ro.build.version.sdk"),
            "abi": self._sh("getprop ro.product.cpu.abi"),
            "locale": self._sh("getprop persist.sys.locale") or self._sh("getprop ro.product.locale"),
            "screen": f"{w}x{h}",
            "density": self._sh("wm density").rsplit(" ", 1)[-1],
            "battery": f"{battery.group(1)}%" if battery else None,
            "appearance": self.get_appearance(),
        }

    def get_appearance(self) -> str:
        return "dark" if "yes" in self._sh("cmd uimode night") else "light"

    def set_appearance(self, mode: str) -> None:
        self._sh(f"cmd uimode night {'yes' if mode == 'dark' else 'no'}")

    def set_location(self, latitude: float, longitude: float) -> None:
        if self.kind != "emulator":
            raise Unsupported("A real Android phone's location cannot be set from adb; only an emulator's can.")
        self._adb("emu", "geo", "fix", str(longitude), str(latitude))

    def set_orientation(self, orientation: str) -> None:
        if orientation == "auto":
            self._sh("settings put system accelerometer_rotation 1")
            return
        rotation = {"portrait": 0, "landscape": 1}[orientation]
        self._sh("settings put system accelerometer_rotation 0")
        self._sh(f"settings put system user_rotation {rotation}")

    def logs(self, app: str | None, seconds: int) -> str:
        since = self._sh(f"date -d @$(( $(date +%s) - {int(seconds)} )) '+%m-%d %H:%M:%S.000'")
        command = f"logcat -d -v threadtime -T {shlex.quote(since)}"
        if app:
            package = self._resolve(app)
            pid = self._sh(f"pidof {package}", check=False).split()
            if pid:
                command += f" --pid={pid[0]}"
            else:
                command += f" | grep -F {shlex.quote(package)}"
        return self._sh(command, timeout=30, check=False)

    def start_recording(self, path: Path) -> None:
        if self._recorder and self._recorder.poll() is None:
            raise PhoneError("Already recording. phone_stop_recording first.")
        self._sh(f"rm -f {REMOTE_RECORDING}", check=False)
        self._recorder = subprocess.Popen([locate.adb(), "-s", self.id, "shell", "screenrecord", "--time-limit", "180",
                                           REMOTE_RECORDING], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                          stderr=subprocess.DEVNULL)
        self._recording_path = path
        time.sleep(0.5)
        if self._recorder.poll() not in (None, 0):
            self._recorder = None
            raise PhoneError("This phone refused to record its screen.")

    def stop_recording(self) -> Path:
        if not self._recorder or not self._recording_path:
            raise PhoneError("Nothing is recording. phone_start_recording first.")
        self._sh("pkill -INT screenrecord", check=False)
        try:
            self._recorder.wait(timeout=15)
        except subprocess.TimeoutExpired:
            self._recorder.kill()
        path, self._recorder, self._recording_path = self._recording_path, None, None
        time.sleep(0.5)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._adb("pull", REMOTE_RECORDING, str(path), timeout=120)
        self._sh(f"rm -f {REMOTE_RECORDING}", check=False)
        return path

    def send_notification(self, title: str, body: str, app: str | None) -> None:
        tag = "phone_mcp"
        self._sh(f"cmd notification post -S bigtext -t {shlex.quote(title)} {tag} {shlex.quote(body)}")

    def shell(self, command: str, timeout: float) -> str:
        done = self._adb("shell", command, timeout=timeout, check=False)
        out = (done.text + done.errtext).replace("\r\n", "\n").strip()
        return out if done.rc == 0 else f"[exit code {done.rc}]\n{out}"

    def add_media(self, path: Path) -> str:
        remote = f"/sdcard/Pictures/{path.name}"
        self._adb("push", str(path), remote, timeout=120)
        self._sh("content call --method scan_volume --uri content://media --arg external_primary", check=False)
        return remote

    def close(self) -> None:
        if self._recorder and self._recorder.poll() is None:
            try:
                self.stop_recording()
            except PhoneError:
                self._recorder.kill()


def _load_labels() -> dict[str, str]:
    try:
        data = json.loads(LABEL_CACHE.read_text())
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}
