import unittest

from scripts import public_safety_scan


class PublicSafetyScanTests(unittest.TestCase):
    def test_blocks_literal_whimsical_board_id_in_public_command(self):
        board_id = "XV" + "vfzk"
        line = f"python scripts/whimsical_mcp.py snapshot --board-id {board_id}"

        matched = any(pattern.search(line) for pattern in public_safety_scan.PATTERNS)

        self.assertTrue(matched)

    def test_allows_placeholder_whimsical_board_id(self):
        line = "python scripts/whimsical_mcp.py snapshot --board-id <private-board-id>"

        matched = any(pattern.search(line) for pattern in public_safety_scan.PATTERNS)

        self.assertFalse(matched)


if __name__ == "__main__":
    unittest.main()
