"""`phone-mcp`: stdio for a local client, `--port` for streamable HTTP on this computer only."""
from __future__ import annotations

import argparse
import atexit

from . import __version__
from .server import build_server


def main() -> None:
    parser = argparse.ArgumentParser(prog="phone-mcp", description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--port", type=int, help="Serve streamable HTTP at http://127.0.0.1:PORT/mcp instead of stdio. "
                        "It has no sign-in and can run commands on your phones, so it never binds another interface.")
    args = parser.parse_args()
    server = build_server()
    atexit.register(server.hub.shutdown)
    if args.port is None:
        server.run("stdio")
        return
    import uvicorn
    uvicorn.run(server.streamable_http_app(streamable_http_path="/mcp", json_response=True, host="127.0.0.1"),
                host="127.0.0.1", port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
