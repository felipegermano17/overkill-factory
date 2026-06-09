#!/usr/bin/env python3
"""Small Whimsical Desktop MCP wrapper for sessions without native MCP tools."""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import re
import urllib.parse
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_ENDPOINT = "http://localhost:21190/mcp"
ALLOWED_ENDPOINT_HOSTS = {"localhost", "127.0.0.1", "::1"}
REQUIRED_TOOLS = {"inspect_state", "board_read", "board_edit", "board_create"}

PRIVATE_PATTERNS = [
    (re.compile(r"https://whimsical\.com/[^\s\"<>]+", re.IGNORECASE), "<whimsical-url>"),
    (re.compile(r"C:[/\\]+Users[/\\]+[^\s\"<>]+", re.IGNORECASE), "<local-path>"),
    (re.compile(r"(?i)\b[a-z0-9._%+-]*" + "fel" + "ipe" + r"[a-z0-9._%+-]*\b"), "<user>"),
]


@dataclass(frozen=True)
class McpClient:
    endpoint: str = DEFAULT_ENDPOINT
    timeout: int = 20

    def request(self, method: str, params: dict[str, Any] | None = None, request_id: int = 1) -> dict[str, Any]:
        parsed = validate_endpoint(self.endpoint)
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": method,
                "params": params or {},
            }
        )
        path = parsed.path or "/mcp"
        if parsed.query:
            path = f"{path}?{parsed.query}"
        connection = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=self.timeout)
        try:
            connection.request(
                "POST",
                path,
                body=body.encode("utf-8"),
                headers={
                    "Accept": "application/json, text/event-stream",
                    "Content-Type": "application/json",
                },
            )
            response = connection.getresponse()
            payload = response.read().decode("utf-8", errors="replace")
        finally:
            connection.close()
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"Whimsical MCP returned HTTP {response.status}: {payload[:200]}")
        return parse_mcp_payload(payload)

    def initialize(self) -> dict[str, Any]:
        return self.request(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "overkill-factory", "version": "1.0"},
            },
            request_id=1,
        )

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None, request_id: int = 2) -> dict[str, Any]:
        return self.request(
            "tools/call",
            {"name": name, "arguments": arguments or {}},
            request_id=request_id,
        )


def parse_mcp_payload(payload: str) -> dict[str, Any]:
    text = payload.strip()
    if not text:
        raise ValueError("empty MCP response")
    if text.startswith("{"):
        return json.loads(text)
    data_lines = []
    for line in text.splitlines():
        if line.startswith("data:"):
            data_lines.append(line.split(":", 1)[1].strip())
    if not data_lines:
        raise ValueError("MCP response did not contain JSON or SSE data")
    return json.loads("\n".join(data_lines))


def validate_endpoint(endpoint: str) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "http" or parsed.hostname not in ALLOWED_ENDPOINT_HOSTS:
        raise ValueError("Whimsical MCP endpoint must be local http")
    return parsed


def redact(value: Any) -> Any:
    if isinstance(value, str):
        redacted = value
        for pattern, replacement in PRIVATE_PATTERNS:
            redacted = pattern.sub(replacement, redacted)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    return value


def list_tool_names(response: dict[str, Any]) -> set[str]:
    return {tool.get("name", "") for tool in response.get("result", {}).get("tools", [])}


def build_health(initialize_response: dict[str, Any], tools_response: dict[str, Any]) -> dict[str, Any]:
    result = initialize_response.get("result", {})
    server = result.get("serverInfo", {})
    tool_names = list_tool_names(tools_response)
    missing = sorted(REQUIRED_TOOLS - tool_names)
    return {
        "status": "PASS" if not missing else "FAIL",
        "server": {
            "name": server.get("name"),
            "version": server.get("version"),
        },
        "tool_count": len(tool_names),
        "required_tools": sorted(REQUIRED_TOOLS),
        "missing_required_tools": missing,
    }


def print_json(data: Any, *, should_redact: bool) -> None:
    safe = redact(data) if should_redact else data
    print(json.dumps(safe, indent=2, sort_keys=True, ensure_ascii=True))


def run_health(client: McpClient, should_redact: bool) -> int:
    initialize_response = client.initialize()
    tools_response = client.request("tools/list", {}, request_id=2)
    health = build_health(initialize_response, tools_response)
    print_json(health, should_redact=should_redact)
    return 0 if health["status"] == "PASS" else 1


def run_inspect(client: McpClient, should_redact: bool) -> int:
    client.initialize()
    response = client.call_tool("inspect_state", request_id=2)
    print_json(response, should_redact=should_redact)
    return 0


def run_board_read(args: argparse.Namespace, client: McpClient, should_redact: bool) -> int:
    client.initialize()
    tool_args: dict[str, Any] = {}
    if args.board_id:
        tool_args["id"] = args.board_id
    if args.grep:
        tool_args["grep_text"] = args.grep
    if args.format:
        tool_args["format"] = args.format
    if args.limit:
        tool_args["limit"] = args.limit
    if args.depth:
        tool_args["depth"] = args.depth
    response = client.call_tool("board_read", tool_args, request_id=2)
    print_json(response, should_redact=should_redact)
    return 0


def run_tool_call(args: argparse.Namespace, client: McpClient, should_redact: bool) -> int:
    client.initialize()
    try:
        arguments = json.loads(args.args_json)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--args-json must be valid JSON: {exc}") from exc
    if not isinstance(arguments, dict):
        raise SystemExit("--args-json must decode to a JSON object")
    response = client.call_tool(args.name, arguments, request_id=2)
    print_json(response, should_redact=should_redact)
    return 0


def run_snapshot(args: argparse.Namespace, client: McpClient, should_redact: bool) -> int:
    client.initialize()
    tool_args: dict[str, Any] = {}
    if args.board_id:
        tool_args["board_id"] = args.board_id
    if args.object_id:
        tool_args["object_ids"] = args.object_id
    if args.scale:
        tool_args["scale"] = args.scale
    if args.transparent:
        tool_args["transparent"] = True
    if args.no_expand:
        tool_args["expand"] = False

    response = client.call_tool("board_snapshot", tool_args, request_id=2)
    content = response.get("result", {}).get("content", [])
    text_blocks = [item.get("text", "") for item in content if item.get("type") == "text"]
    image_data = next((item.get("data") for item in content if item.get("type") == "image"), None)
    if not image_data:
        raise RuntimeError("board_snapshot did not return image data")

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(base64.b64decode(image_data))

    print_json(
        {
            "status": "PASS",
            "metadata": text_blocks,
            "output": str(out_path),
            "bytes": out_path.stat().st_size,
        },
        should_redact=should_redact,
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate Whimsical Desktop MCP through local JSON-RPC.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--no-redact", action="store_true", help="Print raw Whimsical response data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("health", help="Verify the local Whimsical MCP and required tools.")
    subparsers.add_parser("inspect-state", help="Inspect the currently focused Whimsical item.")

    board_read = subparsers.add_parser("board-read", help="Read a Whimsical board.")
    board_read.add_argument("--board-id", help="Board id or URL. Omit to use the current board.")
    board_read.add_argument("--grep", action="append", help="Case-insensitive text filter. Can be repeated.")
    board_read.add_argument("--format", choices=["ednl", "simple"], default="simple")
    board_read.add_argument("--limit", type=int)
    board_read.add_argument("--depth")

    tool_call = subparsers.add_parser("tool-call", help="Call any Whimsical MCP tool by name.")
    tool_call.add_argument("--name", required=True)
    tool_call.add_argument("--args-json", default="{}")

    snapshot = subparsers.add_parser("snapshot", help="Capture a board or object snapshot as a PNG.")
    snapshot.add_argument("--out", required=True, help="PNG output path.")
    snapshot.add_argument("--board-id", help="Board id or URL. Omit to use the current board.")
    snapshot.add_argument("--object-id", action="append", help="Object id to capture. Can be repeated.")
    snapshot.add_argument("--scale", type=int, choices=[1, 2], default=1)
    snapshot.add_argument("--transparent", action="store_true")
    snapshot.add_argument("--no-expand", action="store_true")

    return parser


def main() -> int:
    args = build_parser().parse_args()
    client = McpClient(endpoint=args.endpoint, timeout=args.timeout)
    should_redact = not args.no_redact
    if args.command == "health":
        return run_health(client, should_redact)
    if args.command == "inspect-state":
        return run_inspect(client, should_redact)
    if args.command == "board-read":
        return run_board_read(args, client, should_redact)
    if args.command == "tool-call":
        return run_tool_call(args, client, should_redact)
    if args.command == "snapshot":
        return run_snapshot(args, client, should_redact)
    raise SystemExit(f"unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
