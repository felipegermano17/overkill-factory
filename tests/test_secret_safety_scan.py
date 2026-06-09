import importlib.util
from pathlib import Path
import unittest


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "secret_safety_scan.py"


def load_scanner():
    spec = importlib.util.spec_from_file_location("secret_safety_scan", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SecretSafetyScanTest(unittest.TestCase):
    def test_rust_token_namespace_is_not_a_secret_assignment(self):
        scanner = load_scanner()
        line = "quasar_svm::token::create_keyed_system_account(&operator, OPERATOR_LAMPORTS)"

        self.assertFalse(any(pattern.search(line) for pattern in scanner.SECRET_PATTERNS))
        self.assertIsNone(scanner.ASSIGNMENT_RE.search(line))

    def test_secret_assignment_still_matches(self):
        scanner = load_scanner()
        line = "tok" + "en: " + "abcdefghijklmnopqrstuvwxyz123456"

        self.assertTrue(any(pattern.search(line) for pattern in scanner.SECRET_PATTERNS))
        self.assertIsNotNone(scanner.ASSIGNMENT_RE.search(line))


if __name__ == "__main__":
    unittest.main()
