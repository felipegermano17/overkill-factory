import unittest

from scripts import whimsical_mcp


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


if __name__ == "__main__":
    unittest.main()
