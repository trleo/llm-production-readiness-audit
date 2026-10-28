import json
import unittest

from readiness_audit.checks import CHECK_IDS
from readiness_audit.report import render_json, render_markdown, score_results


CRITICAL = {"EVAL-01", "GUARD-01", "GUARD-02", "OBS-01", "REL-03"}


class FakeResult:
    def __init__(self, check_id, status, area="Evaluation"):
        self.id = check_id
        self.area = area
        self.title = f"Title {check_id}"
        self.severity = "critical" if check_id in CRITICAL else "important"
        self.status = status
        self.evidence = "app.py" if status == "pass" else ""
        self.remediation = "Fix it."


def make_results(pass_ids):
    areas = {
        "EVAL-01": "Evaluation", "EVAL-02": "Evaluation", "EVAL-03": "Evaluation",
        "GUARD-01": "Guardrails", "GUARD-02": "Guardrails", "GUARD-03": "Guardrails",
        "OBS-01": "Observability & Cost", "OBS-02": "Observability & Cost", "OBS-03": "Observability & Cost",
        "GOV-01": "Governance", "GOV-02": "Governance", "GOV-03": "Governance",
        "REL-01": "Reliability", "REL-02": "Reliability", "REL-03": "Reliability",
    }
    return [
        FakeResult(cid, "pass" if cid in pass_ids else "fail", areas[cid])
        for cid in CHECK_IDS
    ]


class TestReport(unittest.TestCase):
    def test_go_at_full_score(self):
        score, verdict, _ = score_results(make_results(set(CHECK_IDS)))
        self.assertEqual(score, 100.0)
        self.assertEqual(verdict, "GO")

    def test_conditional_go_at_66_with_criticals_passing(self):
        pass_ids = set(CHECK_IDS) - {"EVAL-02", "EVAL-03", "GUARD-03", "OBS-02", "OBS-03"}
        # 10/15 = 66.7, all criticals still pass
        self.assertTrue(CRITICAL.issubset(pass_ids))
        score, verdict, _ = score_results(make_results(pass_ids))
        self.assertEqual(score, 66.7)
        self.assertEqual(verdict, "CONDITIONAL GO")

    def test_no_go_when_critical_fails_even_at_high_score(self):
        pass_ids = set(CHECK_IDS) - {"REL-03"}
        score, verdict, _ = score_results(make_results(pass_ids))
        self.assertEqual(score, 93.3)
        self.assertEqual(verdict, "NO-GO")

    def test_json_and_markdown_agree(self):
        results = make_results(set(CHECK_IDS))
        score, verdict, _ = score_results(results)
        data = json.loads(render_json("proj", results, score, verdict))
        self.assertEqual(data["score"], score)
        self.assertEqual(data["verdict"], verdict)
        self.assertEqual(len(data["checks"]), 15)
        md = render_markdown("proj", results, score, verdict)
        self.assertIn("GO", md)
        self.assertIn("EVAL-01", md)
        self.assertIn("100.0", md)


if __name__ == "__main__":
    unittest.main()
