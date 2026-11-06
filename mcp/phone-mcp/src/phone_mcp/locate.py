"""Finds the CLIs by absolute path: an MCP client often starts us with a minimal PATH."""
from __future__ import annotations

import glob
import os
import shutil
from pathlib import Path

HOME = Path.home()


def sdk_roots() -> list[Path]:
    roots = [os.environ.get("ANDROID_HOME"), os.environ.get("ANDROID_SDK_ROOT"),
             HOME / "Library/Android/sdk",
             "/opt/homebrew/share/android-commandlinetools",
             "/usr/local/share/android-commandlinetools"]
    return [Path(r) for r in roots if r and Path(r).is_dir()]


def _in_sdk(relative: str) -> str | None:
    for root in sdk_roots():
        candidate = root / relative
        if candidate.is_file():
            return str(candidate)
    return None


def adb() -> str | None:
    return _in_sdk("platform-tools/adb") or shutil.which("adb")


def emulator() -> str | None:
    return _in_sdk("emulator/emulator") or shutil.which("emulator")


def build_tool(name: str) -> str | None:
    for root in sdk_roots():
        versions = sorted((root / "build-tools").glob("*"), key=lambda p: [int(x) if x.isdigit() else 0
                                                                           for x in p.name.split(".")])
        for version in reversed(versions):
            if (version / name).is_file():
                return str(version / name)
    return shutil.which(name)


def axe() -> str | None:
    explicit = os.environ.get("PHONE_MCP_AXE")
    if explicit and Path(explicit).is_file():
        return explicit
    found = shutil.which("axe")
    if found:
        return found
    for fixed in ("/opt/homebrew/bin/axe", "/usr/local/bin/axe"):
        if Path(fixed).is_file():
            return fixed
    bundled = glob.glob(str(HOME / ".npm/_npx/*/node_modules/xcodebuildmcp/bundled/axe"))
    return max(bundled, key=os.path.getmtime) if bundled else None


def xcrun() -> str | None:
    return shutil.which("xcrun") or ("/usr/bin/xcrun" if Path("/usr/bin/xcrun").is_file() else None)
