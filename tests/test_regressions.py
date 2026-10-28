"""Regression tests for the independent review (2026-10-28).

Bug 1: a NUL byte after the first 8,192 bytes must still mark a file
as binary, so its content never contributes to a check.
Bug 2: a bad --out must exit 2 with a clean error, not a traceback.
Bug 3: multi-keyword evidence must name the files that together prove
the check, not just the first keyword's file.
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from readiness_audit.checks import run_checks
from readiness_audit.scanner import ScanResult, scan_project

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "readiness_audit", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )


class TestRegressions(unittest.TestCase):
    def test_nul_after_8192_bytes_is_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = b"A" * 9000 + b"\x00" + b"token cost threshold baseline pii redact"
            (root / "late.bin").write_bytes(payload)
            result = scan_project(tmp)
            self.assertIn("late.bin", result.files)
            self.assertNotIn("late.bin", result.texts)

    def test_bad_out_exits_2_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "blocker"
            blocker.write_text("not a directory", encoding="utf-8")
            proc = run_cli(
                "--path", str(ROOT / "samples" / "passing-reference"),
                "--out", str(blocker),
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("error:", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)

    def test_empty_out_exits_2_cleanly(self):
        proc = run_cli(
            "--path", str(ROOT / "samples" / "passing-reference"),
            "--out", "",
        )
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn("Traceback", proc.stderr)

    def test_multi_keyword_evidence_names_both_files(self):
        scan = ScanResult(
            files=["a.txt", "b.txt"],
            texts={"a.txt": "threshold: 0.8", "b.txt": "baseline: 0.7"},
        )
        results = {r.id: r for r in run_checks(scan)}
        self.assertEqual(results["EVAL-02"].status, "pass")
        self.assertEqual(results["EVAL-02"].evidence, "a.txt + b.txt")


if __name__ == "__main__":
    unittest.main()
