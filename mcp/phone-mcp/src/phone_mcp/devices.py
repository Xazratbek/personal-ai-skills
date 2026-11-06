"""Which phones exist, which are running, and starting and stopping them."""
from __future__ import annotations

import json
import re
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from . import locate
from .drivers.android import AndroidDriver
from .drivers.base import Driver
from .drivers.ios import IosDriver
from .elements import Element
from .errors import PhoneError, Unsupported
from .proc import run

READY_WAIT = 300
LOG_DIR = Path.home() / "Library/Logs/phone-mcp"
UDID = re.compile(r"^[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}$")
AVD_PREFIX = "avd:"
NOT_RUNNING = "device {} is not running: phone_list_available_devices shows what is running."


def _adb() -> str:
    return locate.adb() or "adb"


def _xcrun() -> str:
    return locate.xcrun() or "xcrun"


@dataclass
class Phone:
    id: str
    platform: str
    kind: str
    name: str
    os: str = ""
    newest: bool = True

    @property
    def title(self) -> str:
        return f"{self.name} ({self.os})" if self.os else self.name


class Starting:
    """A phone on its way up. `poll` is cheap and is called until it reports ready."""

    def __init__(self, phone: Phone, note: str = ""):
        self.phone = phone
        self.note = note
        self.id: str | None = phone.id if not phone.id.startswith(AVD_PREFIX) else None

    def poll(self) -> tuple[bool, str]:
        return True, "ready"

    def abort(self) -> None:
        """Give up on a phone that did not come up."""


class StartingSimulator(Starting):
    def poll(self) -> tuple[bool, str]:
        try:
            run([_xcrun(), "simctl", "bootstatus", self.phone.id, "-b"], timeout=4)
        except PhoneError as e:
            if "did not finish" in str(e):
                return False, "booting"
            raise
        tool = locate.axe()
        if tool:
            # The first automation session after a boot is slow; pay for it here, not on the first tool call.
            try:
                run([tool, "describe-ui", "--udid", self.phone.id], timeout=30, check=False)
            except PhoneError:
                pass
        return True, "ready"

    def abort(self) -> None:
        run([_xcrun(), "simctl", "shutdown", self.phone.id], timeout=30, check=False)


class StartingEmulator(Starting):
    def __init__(self, phone: Phone, process: subprocess.Popen, log: Path, hub: Hub, note: str = ""):
        super().__init__(phone, note)
        self.process = process
        self.log = log
        self.hub = hub

    def poll(self) -> tuple[bool, str]:
        avd = self.phone.id[len(AVD_PREFIX):]
        if self.id is None:
            self.id = self.hub.serial_of_avd(avd)
        if self.id is None:
            if self.process.poll() is not None:
                tail = self.log.read_text(errors="replace")[-500:] if self.log.is_file() else ""
                raise PhoneError(f"The emulator {avd} exited while starting: {tail}")
            return False, "starting the emulator"
        done = run([_adb(), "-s", self.id, "shell", "getprop", "sys.boot_completed"], timeout=15, check=False)
        if done.text.strip() != "1":
            return False, "booting Android"
        return True, "ready"

    def abort(self) -> None:
        if self.id:
            run([_adb(), "-s", self.id, "emu", "kill"], timeout=15, check=False)
        else:
            self.process.terminate()


class Hub:
    def __init__(self):
        self._drivers: dict[str, Driver] = {}
        self._snapshots: dict[str, tuple[list[Element], float]] = {}
        self._dirty: set[str] = set()
        self._timers: dict[str, threading.Timer] = {}
        self._known: tuple[float, set[str]] = (0.0, set())
        self._avd_names: dict[str, str] = {}
        self.problems: list[str] = []

    # --- listing -------------------------------------------------------------------------------------------------

    def _simulators(self) -> list[dict]:
        tool = locate.xcrun()
        if not tool:
            return []
        done = run([tool, "simctl", "list", "-j", "devices", "available"], timeout=20, check=False)
        if done.rc != 0:
            return []
        found = []
        for runtime, group in json.loads(done.out).get("devices", {}).items():
            match = re.search(r"\.iOS-([\d-]+)$", runtime)
            if not match:
                continue
            version = match.group(1).replace("-", ".")
            for entry in group:
                found.append({**entry, "os": f"iOS {version}",
                              "os_key": tuple(int(x) for x in version.split("."))})
        return found

    def _adb_devices(self) -> list[tuple[str, str, str]]:
        tool = locate.adb()
        if not tool:
            return []
        done = run([tool, "devices", "-l"], timeout=15, check=False)
        rows = []
        for line in done.text.splitlines()[1:]:
            parts = line.split()
            if len(parts) >= 2:
                model = next((p[6:] for p in parts[2:] if p.startswith("model:")), "")
                rows.append((parts[0], parts[1], model))
        return rows

    def _avd_of(self, serial: str) -> str:
        if serial not in self._avd_names:
            done = run([_adb(), "-s", serial, "emu", "avd", "name"], timeout=10, check=False)
            lines = [line.strip() for line in done.text.splitlines() if line.strip() and line.strip() != "OK"]
            if lines:
                self._avd_names[serial] = lines[0]
        return self._avd_names.get(serial, "")

    def serial_of_avd(self, avd: str) -> str | None:
        for serial, state, _model in self._adb_devices():
            if serial.startswith("emulator-") and state == "device" and self._avd_of(serial) == avd:
                return serial
        return None

    def running(self) -> list[Phone]:
        phones: list[Phone] = []
        self.problems = []
        for serial, state, model in self._adb_devices():
            if state == "device":
                if serial.startswith("emulator-"):
                    phones.append(Phone(serial, "android", "emulator", self._avd_of(serial) or "Android emulator"))
                else:
                    phones.append(Phone(serial, "android", "device", model.replace("_", " ") or "Android phone"))
            elif state == "unauthorized":
                self.problems.append(f"{serial}: accept the USB debugging prompt on the phone.")
            elif state == "offline":
                self.problems.append(f"{serial}: offline; it may still be starting.")
        for sim in self._simulators():
            if sim.get("state") == "Booted":
                phones.append(Phone(sim["udid"], "ios", "simulator", sim.get("name", "iPhone"), sim["os"]))
        self._known = (time.monotonic(), {p.id for p in phones})
        return phones

    def startable(self) -> list[Phone]:
        phones: list[Phone] = []
        tool = locate.emulator()
        if tool:
            done = run([tool, "-list-avds"], timeout=20, check=False)
            live = {self._avd_of(serial) for serial, state, _m in self._adb_devices() if serial.startswith("emulator-")}
            for line in done.text.splitlines():
                avd = line.strip()
                if avd and " " not in avd and "|" not in avd and avd not in live:
                    phones.append(Phone(f"{AVD_PREFIX}{avd}", "android", "emulator", avd))
        sims = self._simulators()
        newest = max((s["os_key"] for s in sims), default=())
        for sim in sorted(sims, key=lambda s: (s["os_key"], "iPhone" in s.get("name", "")), reverse=True):
            if sim.get("state") != "Booted":
                phones.append(Phone(sim["udid"], "ios", "simulator", sim.get("name", ""), sim["os"],
                                    newest=sim["os_key"] == newest))
        return phones

    # --- drivers -----------------------------------------------------------------------------------------------------

    def _make_driver(self, phone: Phone) -> Driver:
        if phone.platform == "ios":
            return IosDriver(phone.id, phone.name)
        driver = AndroidDriver(phone.id)
        driver.name = phone.name
        return driver

    def driver(self, device: str | None) -> Driver:
        checked_at, known = self._known
        if device and device in self._drivers and device in known and time.monotonic() - checked_at < 3:
            return self._drivers[device]
        phones = self.running()
        if device is None:
            if not phones:
                raise PhoneError("No phone is running. phone_start_device starts one.")
            if len(phones) > 1:
                listed = "; ".join(f"{p.id} ({p.title})" for p in phones)
                raise PhoneError(f"Several phones are running, so say which with `device`: {listed}.")
            phone = phones[0]
        else:
            wanted = device[len(AVD_PREFIX):] if device.startswith(AVD_PREFIX) else device
            phone = next((p for p in phones if p.id == device), None)
            if phone is None:
                named = [p for p in phones if p.name.casefold() == wanted.casefold()]
                if len(named) != 1:
                    raise PhoneError(NOT_RUNNING.format(device))
                phone = named[0]
        if phone.id not in self._drivers:
            self._drivers[phone.id] = self._make_driver(phone)
        return self._drivers[phone.id]

    # --- snapshots: what the refs from the last listing point at ----------------------------------------------------

    def remember(self, device: str, elements: list[Element]) -> None:
        self._snapshots[device] = (elements, time.monotonic())
        self._dirty.discard(device)

    def recall(self, device: str) -> tuple[list[Element], float, bool]:
        if device not in self._snapshots:
            raise PhoneError("No element list yet. Call phone_list_elements_on_screen, then use its refs.")
        elements, taken = self._snapshots[device]
        return elements, time.monotonic() - taken, device in self._dirty

    def touched(self, device: str) -> None:
        self._dirty.add(device)

    # --- starting and stopping --------------------------------------------------------------------------------------

    def begin_start(self, platform: str | None, kind: str | None, device_id: str | None, headless: bool) -> Starting:
        note = ""
        if kind == "device":
            if platform == "android":
                raise PhoneError("A real Android phone is not started from here: connect it with USB debugging on, "
                                 "and it appears in phone_list_available_devices.")
            if platform == "ios" or platform is None:
                platform = "ios"
                note = " Local iPhones are simulators: real iPhones cannot be driven without a paid signing setup."
        running = self.running()
        if device_id:
            live = next((p for p in running if p.id == device_id or p.name.casefold() == device_id.casefold()
                         or f"{AVD_PREFIX}{p.name}" == device_id), None)
            if live:
                done = Starting(live, " It was already running.")
                return done
        options = self.startable()
        if device_id:
            target = self._choose(options, device_id)
        else:
            target = self._default(options, platform, kind)
            if target is None:
                live = next((p for p in running if platform in (None, p.platform)), None)
                if live:
                    return Starting(live, " It was already running.")
                raise PhoneError(f"No {platform or 'local'} phone to start. phone_doctor shows what is missing.")
        if target.platform == "ios":
            return self._boot_simulator(target, headless, note)
        return self._boot_emulator(target, headless, note)

    @staticmethod
    def _choose(options: list[Phone], device_id: str) -> Phone:
        wanted = device_id[len(AVD_PREFIX):] if device_id.startswith(AVD_PREFIX) else device_id
        exact = next((p for p in options if p.id == device_id or p.id == f"{AVD_PREFIX}{wanted}"), None)
        if exact:
            return exact
        # Sorted newest OS first, so a bare model name means its newest simulator.
        named = next((p for p in options if p.name.casefold() == wanted.casefold()), None)
        if named:
            return named
        known = ", ".join(p.id for p in options[:25]) or "none"
        raise PhoneError(f"No phone with id {device_id!r}; ids are: {known}.")

    @staticmethod
    def _default(options: list[Phone], platform: str | None, kind: str | None) -> Phone | None:
        if kind == "simulator":
            platform = "ios"
        if kind == "emulator":
            platform = "android"
        for wanted in ([platform] if platform else ["android", "ios"]):
            for phone in options:
                if phone.platform == wanted and (wanted != "ios" or "iPhone" in phone.name):
                    return phone
        return None

    def _boot_simulator(self, phone: Phone, headless: bool, note: str) -> Starting:
        done = run([_xcrun(), "simctl", "boot", phone.id], timeout=60, check=False)
        if done.rc != 0 and "Booted" not in done.errtext:
            raise PhoneError(f"Could not boot {phone.title}: {done.errtext.strip()[-300:]}")
        if not headless:
            run(["/usr/bin/open", "-g", "-a", "Simulator", "--args", "-CurrentDeviceUDID", phone.id],
                timeout=20, check=False)
        self._known = (0.0, set())
        return StartingSimulator(phone, note)

    def _boot_emulator(self, phone: Phone, headless: bool, note: str) -> Starting:
        tool = locate.emulator()
        if not tool:
            raise PhoneError("The Android emulator is not installed. phone_doctor shows how to fix it.")
        avd = phone.id[len(AVD_PREFIX):]
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        log = LOG_DIR / f"{avd}.log"
        args = [tool, "-avd", avd, "-no-boot-anim"]
        if headless:
            args += ["-no-window", "-no-audio"]
        with open(log, "wb") as out:
            process = subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=out, stderr=out, start_new_session=True)
        self._known = (0.0, set())
        return StartingEmulator(phone, process, log, self, note)

    def stop(self, device: str | None) -> str:
        driver = self.driver(device)
        if driver.platform == "android" and driver.kind != "emulator":
            raise Unsupported("A real Android phone is not powered off from here; only emulators and simulators stop.")
        driver.close()
        if driver.platform == "ios":
            run([_xcrun(), "simctl", "shutdown", driver.id], timeout=60)
        else:
            run([_adb(), "-s", driver.id, "emu", "kill"], timeout=20)
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline and any(s == driver.id for s, _st, _m in self._adb_devices()):
                time.sleep(0.5)
        self._forget(driver.id)
        return driver.id

    def _forget(self, device_id: str) -> None:
        self._drivers.pop(device_id, None)
        self._snapshots.pop(device_id, None)
        self._dirty.discard(device_id)
        self._avd_names.pop(device_id, None)
        self._known = (0.0, set())
        timer = self._timers.pop(device_id, None)
        if timer:
            timer.cancel()

    def stop_after(self, device_id: str, minutes: int) -> None:
        old = self._timers.pop(device_id, None)
        if old:
            old.cancel()

        def fire():
            try:
                self.stop(device_id)
            except PhoneError:
                pass
        timer = threading.Timer(minutes * 60, fire)
        timer.daemon = True
        timer.start()
        self._timers[device_id] = timer

    def shutdown(self) -> None:
        for timer in self._timers.values():
            timer.cancel()
        for driver in self._drivers.values():
            try:
                driver.close()
            except Exception:
                pass


def doctor() -> list[str]:
    lines = []

    def version(argv: list[str]) -> str:
        try:
            return run(argv, timeout=15, check=False).text.strip().splitlines()[0]
        except (PhoneError, IndexError):
            return "unknown version"

    xcrun = locate.xcrun()
    xcode = version(["/usr/bin/xcodebuild", "-version"]) if Path("/usr/bin/xcodebuild").exists() else ""
    lines.append(f"[{'ok' if xcrun and 'Xcode' in xcode else 'MISSING'}] Xcode: {xcode or 'install Xcode from the App Store'}")
    axe = locate.axe()
    lines.append(f"[ok] AXe {version([axe, '--version'])}: {axe}" if axe else
                 "[MISSING] AXe (iOS touch and accessibility): brew install cameroncooke/axe/axe")
    adb = locate.adb()
    lines.append(f"[ok] adb: {adb}" if adb else
                 "[MISSING] adb: brew install --cask android-platform-tools, or set ANDROID_HOME")
    emulator = locate.emulator()
    lines.append(f"[ok] emulator: {emulator}" if emulator else
                 "[MISSING] Android emulator: sdkmanager emulator, or install Android Studio")
    aapt = locate.build_tool("aapt2")
    lines.append(f"[ok] aapt2 (app labels): {aapt}" if aapt else
                 "[optional] aapt2 is missing, so Android apps open only by package id or a known name")
    return lines
