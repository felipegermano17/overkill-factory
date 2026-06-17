#!/usr/bin/env python3
"""Serve the local status cockpit on loopback only."""

from __future__ import annotations

import argparse
import ipaddress
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UI_DIR = ROOT / "ui" / "local-status-cockpit"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8784


def is_loopback_host(host: str) -> bool:
    text = (host or "").strip().lower()
    if text == "localhost":
        return True
    try:
        return ipaddress.ip_address(text).is_loopback
    except ValueError:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Serve the read-only local status cockpit")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Loopback host only; public binds are rejected")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--directory", type=Path, default=UI_DIR)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not is_loopback_host(args.host):
        raise SystemExit("Refusing public/non-loopback binding for this read-only local cockpit")
    directory = args.directory.resolve()
    if not directory.exists():
        raise SystemExit(f"UI directory not found: {directory}")
    os.chdir(directory)
    server = ThreadingHTTPServer((args.host, args.port), SimpleHTTPRequestHandler)
    print(f"the local status cockpit local cockpit: http://{args.host}:{args.port}/")
    print("Read-only static server; stop with Ctrl-C.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
