import importlib.util
from pathlib import Path
import tempfile
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

    def test_disappeared_scan_path_does_not_crash(self):
        scanner = load_scanner()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            clean = root / "clean.txt"
            clean.write_text("public docs only\n", encoding="utf-8")
            vanished = root / "vanished.txt"

            original_root = scanner.ROOT
            original_iter_scan_paths = scanner.iter_scan_paths
            scanner.ROOT = root
            scanner.iter_scan_paths = lambda _root: iter([vanished, clean])
            try:
                findings = scanner.scan()
            finally:
                scanner.ROOT = original_root
                scanner.iter_scan_paths = original_iter_scan_paths

        self.assertEqual([], findings)

    def test_ignored_tmp_reference_repos_are_not_scanned(self):
        scanner = load_scanner()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ignored = root / ".tmp" / "reference-repos" / "sample.env"
            ignored.parent.mkdir(parents=True)
            ignored.write_text("tok" + "en: " + "abcdefghijklmnopqrstuvwxyz123456\n", encoding="utf-8")
            clean = root / "README.md"
            clean.write_text("public docs only\n", encoding="utf-8")

            original_root = scanner.ROOT
            scanner.ROOT = root
            try:
                findings = scanner.scan()
            finally:
                scanner.ROOT = original_root

        self.assertEqual([], findings)


if __name__ == "__main__":
    unittest.main()
