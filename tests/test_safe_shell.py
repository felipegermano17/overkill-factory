from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "safe_shell.py"
SPEC = importlib.util.spec_from_file_location("safe_shell", MODULE_PATH)
assert SPEC is not None
safe_shell = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["safe_shell"] = safe_shell
SPEC.loader.exec_module(safe_shell)


class SafeShellTest(unittest.TestCase):
    def test_run_command_accepts_argv_and_returns_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = safe_shell.run_command(
                [sys.executable, "--version"],
                cwd=Path(tmpdir),
                allowed_executables={Path(sys.executable).name},
            )

        self.assertEqual(result.status, "PASS")
        self.assertEqual(result.returncode, 0)

    def test_run_command_rejects_disallowed_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "not allowed"):
                safe_shell.run_command(
                    [sys.executable, "--version"],
                    cwd=Path(tmpdir),
                    allowed_executables={"not-python"},
                )


if __name__ == "__main__":
    unittest.main()
