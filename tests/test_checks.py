import unittest

from readiness_audit.checks import CHECK_IDS, run_checks
from readiness_audit.scanner import ScanResult


def scan(files=None, texts=None):
    return ScanResult(files=files or [], texts=texts or {})


def status(results, check_id):
    for r in results:
        if r.id == check_id:
            return r.status
    raise AssertionError(f"missing check {check_id}")


class TestChecks(unittest.TestCase):
    def test_fifteen_checks_in_spec_order(self):
        self.assertEqual(len(CHECK_IDS), 15)
        self.assertEqual(
            CHECK_IDS,
            [
                "EVAL-01", "EVAL-02", "EVAL-03",
                "GUARD-01", "GUARD-02", "GUARD-03",
                "OBS-01", "OBS-02", "OBS-03",
                "GOV-01", "GOV-02", "GOV-03",
                "REL-01", "REL-02", "REL-03",
            ],
        )

    def test_empty_scan_fails_14_and_passes_no_secret_check(self):
        results = run_checks(scan())
        passed = [r.id for r in results if r.status == "pass"]
        # REL-03 passes vacuously: no hardcoded secret was found.
        self.assertEqual(passed, ["REL-03"])

    def test_each_evidence_check(self):
        cases = [
            ("EVAL-01", scan(files=["evals/dataset.json"])),
            ("EVAL-02", scan(texts={"config.yaml": "baseline: 0.7 threshold: 0.8"})),
            ("EVAL-03", scan(files=["eval/run_eval.py"])),
            ("GUARD-01", scan(texts={"app.py": "pii redact function"})),
            ("GUARD-02", scan(texts={"app.py": "schema validate output"})),
            ("GUARD-03", scan(texts={"app.py": "prompt injection sanitize input"})),
            ("OBS-01", scan(texts={"app.py": "trace_id logging logger"})),
            ("OBS-02", scan(texts={"app.py": "token usage cost tracking"})),
            ("OBS-03", scan(texts={"app.py": "timeout latency budget"})),
            ("GOV-01", scan(files=["prompts/v1.txt"])),
            ("GOV-02", scan(texts={"app.py": "human review required"})),
            ("GOV-03", scan(texts={"config.yaml": "retention days 30"})),
            ("REL-01", scan(texts={"app.py": "retry with fallback"})),
            ("REL-02", scan(texts={"app.py": "try: pass except Exception as e: error_code"})),
        ]
        for check_id, s in cases:
            with self.subTest(check=check_id):
                self.assertEqual(status(run_checks(s), check_id), "pass")

    def test_hardcoded_secret_fails_rel03_and_env_passes(self):
        # Built by concatenation so this test fixture itself is not a
        # literal secret pattern in the repository.
        bad_text = 'api_key = "sk-' + 'abc123"'
        bad = run_checks(scan(texts={"app.py": bad_text}))
        self.assertEqual(status(bad, "REL-03"), "fail")
        good = run_checks(scan(texts={"app.py": 'api_key = os.getenv("API_KEY")'}))
        self.assertEqual(status(good, "REL-03"), "pass")

    def test_check_result_fields(self):
        results = run_checks(scan())
        for r in results:
            self.assertTrue(r.id)
            self.assertTrue(r.area)
            self.assertTrue(r.title)
            self.assertIn(r.severity, ("critical", "important"))
            self.assertIn(r.status, ("pass", "fail"))
            self.assertTrue(r.remediation)


if __name__ == "__main__":
    unittest.main()
