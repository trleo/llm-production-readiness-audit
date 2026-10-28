import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "readiness_audit", *args],
        cwd=ROOT, capture_output=True, text=True, timeout=60,
    )


class TestCli(unittest.TestCase):
    def test_list_checks(self):
        proc = run_cli("--list-checks")
        self.assertEqual(proc.returncode, 0)
        for check_id in ["EVAL-01", "GUARD-02", "OBS-01", "REL-03"]:
            self.assertIn(check_id, proc.stdout)

    def test_failing_sample_is_no_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli("--path", str(ROOT / "samples" / "failing-demo"), "--out", tmp)
            self.assertEqual(proc.returncode, 1)
            data = json.loads((Path(tmp) / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(data["score"], 0.0)
            self.assertEqual(data["verdict"], "NO-GO")
            self.assertEqual(len(data["checks"]), 15)
            md = (Path(tmp) / "report.md").read_text(encoding="utf-8")
            self.assertIn("NO-GO", md)

    def test_passing_sample_is_go(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli("--path", str(ROOT / "samples" / "passing-reference"), "--out", tmp)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            data = json.loads((Path(tmp) / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(data["score"], 100.0)
            self.assertEqual(data["verdict"], "GO")

    def test_version_flag(self):
        proc = run_cli("--version")
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(proc.stdout.strip(), "0.1.0")

    def test_missing_path_exits_2(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = run_cli("--path", str(Path(tmp) / "nope"), "--out", tmp)
            self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
