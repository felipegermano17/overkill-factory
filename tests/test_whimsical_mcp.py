import unittest
from argparse import Namespace
from base64 import b64encode
from tempfile import TemporaryDirectory

from scripts import whimsical_mcp


class FakeSnapshotClient:
    def __init__(self):
        self.tool_args = None

    def initialize(self):
        return {}

    def call_tool(self, name, arguments, request_id=2):
        self.tool_args = (name, arguments, request_id)
        return {
            "result": {
                "content": [
                    {"type": "text", "text": "board_id: test\nsize: 1x1"},
                    {"type": "image", "data": b64encode(b"png-bytes").decode("ascii")},
                ]
            }
        }


class WhimsicalMcpTests(unittest.TestCase):
    def test_parse_sse_payload(self):
        payload = 'event: message\ndata: {"jsonrpc":"2.0","id":1,"result":{"ok":true}}\n'

        parsed = whimsical_mcp.parse_mcp_payload(payload)

        self.assertEqual(parsed["result"]["ok"], True)

    def test_health_reports_missing_required_tools(self):
        init = {"result": {"serverInfo": {"name": "whimsical-desktop", "version": "0.1.0"}}}
        tools = {"result": {"tools": [{"name": "inspect_state"}, {"name": "board_read"}]}}

        health = whimsical_mcp.build_health(init, tools)

        self.assertEqual(health["status"], "FAIL")
        self.assertIn("board_edit", health["missing_required_tools"])
        self.assertIn("board_create", health["missing_required_tools"])

    def test_redacts_private_workspace_data(self):
        value = {
            "url": "https://whimsical.com/private-board-abc123",
            "path": "C:/Users/example/project",
            "user": "example-" + "fel" + "ipe",
        }

        redacted = whimsical_mcp.redact(value)

        self.assertEqual(redacted["url"], "<whimsical-url>")
        self.assertEqual(redacted["path"], "<local-path>")
        self.assertEqual(redacted["user"], "<user>")

    def test_endpoint_must_be_local_http(self):
        with self.assertRaises(ValueError):
            whimsical_mcp.validate_endpoint("https://example.com/mcp")

        whimsical_mcp.validate_endpoint("http://localhost:21190/mcp")

    def test_snapshot_writes_png_without_dumping_image_payload(self):
        with TemporaryDirectory() as tmpdir:
            out = f"{tmpdir}/snapshot.png"
            client = FakeSnapshotClient()
            args = Namespace(
                board_id="board1",
                object_id=["flow1"],
                scale=2,
                transparent=False,
                no_expand=False,
                out=out,
            )

            status = whimsical_mcp.run_snapshot(args, client, should_redact=True)

            self.assertEqual(status, 0)
            self.assertEqual(client.tool_args[0], "board_snapshot")
            self.assertEqual(client.tool_args[1]["board_id"], "board1")
            self.assertEqual(client.tool_args[1]["object_ids"], ["flow1"])
            with open(out, "rb") as handle:
                self.assertEqual(handle.read(), b"png-bytes")


if __name__ == "__main__":
    unittest.main()
