import os
import tempfile
import unittest
from pathlib import Path

from readiness_audit.scanner import ScanResult, scan_project


class TestScanner(unittest.TestCase):
    def test_relative_paths_lowercased_text_and_ignores(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text("Hello World\n", encoding="utf-8")
            (root / ".git").mkdir()
            (root / ".git" / "secret.py").write_text("should be ignored", encoding="utf-8")
            (root / "node_modules").mkdir()
            (root / "node_modules" / "x.js").write_text("should be ignored", encoding="utf-8")
            (root / "blob.bin").write_bytes(b"\x00\x01\x02binary")

            result = scan_project(tmp)

            self.assertIsInstance(result, ScanResult)
            self.assertIn("app.py", result.files)
            self.assertIn("blob.bin", result.files)
            self.assertNotIn(".git/secret.py", result.files)
            self.assertNotIn("node_modules/x.js", result.files)
            self.assertEqual(result.texts["app.py"], "hello world\n")
            self.assertNotIn("blob.bin", result.texts)

    def test_large_file_content_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "big.txt").write_text("x" * 250_000, encoding="utf-8")
            result = scan_project(tmp)
            self.assertIn("big.txt", result.files)
            self.assertNotIn("big.txt", result.texts)

    def test_missing_directory_raises(self):
        with self.assertRaises(FileNotFoundError):
            scan_project("/definitely/not/a/real/dir-xyz")


if __name__ == "__main__":
    unittest.main()
