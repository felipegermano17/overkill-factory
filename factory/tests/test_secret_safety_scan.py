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

    def test_seed_phrase_assignment_matches(self):
        scanner = load_scanner()
        phrase = "abandon ability able about above absent absorb abstract absurd abuse access accident"
        line = "seed_" + "phrase: " + phrase

        self.assertTrue(any(pattern.search(line) for pattern in scanner.SECRET_PATTERNS))

    def test_solana_keypair_array_matches(self):
        scanner = load_scanner()
        key_bytes = ", ".join(str((index * 7) % 255) for index in range(64))
        line = "signing_" + "key: [" + key_bytes + "]"

        self.assertTrue(any(pattern.search(line) for pattern in scanner.SECRET_PATTERNS))

    def test_sensitive_key_assignment_matches_entropy_check(self):
        scanner = load_scanner()
        candidate = "Ab9/cD2+Ef3-Gh4_Ij5.Kl6/Mn7+Op8-Qr9_St0.Uv1/Wx2+Yz3"
        line = "custody_" + "key = " + candidate

        self.assertIsNotNone(scanner.ASSIGNMENT_RE.search(line))
        self.assertGreaterEqual(scanner.entropy(candidate), 4.2)

    def test_ignored_worktrees_are_not_scanned(self):
        scanner = load_scanner()

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            ignored = root / ".worktrees" / "task" / "sample.env"
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
