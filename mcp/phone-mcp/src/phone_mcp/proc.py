"""Subprocesses with a deadline, so one stuck CLI can never hang a tool call."""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import PhoneError


@dataclass
class Completed:
    rc: int
    out: bytes
    err: bytes

    @property
    def text(self) -> str:
        return self.out.decode("utf-8", errors="replace")

    @property
    def errtext(self) -> str:
        return self.err.decode("utf-8", errors="replace")


def run(argv: list[str], *, timeout: float = 30, stdin: bytes | None = None, check: bool = True) -> Completed:
    label = " ".join(Path(argv[0]).name if i == 0 else a for i, a in enumerate(argv[:4]))
    try:
        done = subprocess.run(argv, input=stdin, capture_output=True, timeout=timeout,
                              stdin=None if stdin is not None else subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        raise PhoneError(f"`{label}` did not finish within {timeout:g}s.") from None
    except FileNotFoundError:
        raise PhoneError(f"{argv[0]} is not installed. phone_doctor shows what is missing.") from None
    result = Completed(done.returncode, done.stdout, done.stderr)
    if check and done.returncode != 0:
        detail = (result.errtext.strip() or result.text.strip() or f"exit code {done.returncode}")[-600:]
        raise PhoneError(f"`{label}` failed: {detail}")
    return result
