"""Errors worded for the model: what went wrong and what to do next."""
from __future__ import annotations

from mcp.server.mcpserver.exceptions import ToolError


class PhoneError(ToolError):
    """Reaches the model as an `is_error` result instead of a generic failure."""


class Unsupported(PhoneError):
    """This phone cannot do that, and retrying will not help."""
