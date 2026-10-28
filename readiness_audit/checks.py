"""The 15 deterministic production-readiness checks.

Each check is a pure predicate over a ScanResult. A check passes only
on explicit evidence: a matching path or a matching keyword pattern in
scanned text. The hardcoded-secret check is the exception that proves
the rule: it passes when no hardcoded secret pattern is found.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .scanner import ScanResult

SECRET_PATTERN = re.compile(
    r'(api_key|password)\s*=\s*["\'](sk-[^"\']+|[^"\']+)["\']'
)


@dataclass
class CheckResult:
    id: str
    area: str
    title: str
    severity: str
    status: str
    evidence: str
    remediation: str


def _all_text(scan: ScanResult) -> str:
    return "\n".join(scan.texts.values())


def _evidence_for(scan: ScanResult, needle: str) -> str:
    for path in sorted(scan.texts):
        if needle in scan.texts[path]:
            return path
    return ""


def _combined_evidence(scan: ScanResult, needles) -> str:
    """Evidence naming every file that together proves *needles*.

    Needles may live in different files, so a single first file would
    be misleading. Returns one file, or files joined with ' + ' in
    needle order, with duplicates removed.
    """
    seen = []
    for needle in needles:
        path = _evidence_for(scan, needle)
        if path and path not in seen:
            seen.append(path)
    return " + ".join(seen)


def _has(scan: ScanResult, *needles: str) -> tuple[bool, str]:
    text = _all_text(scan)
    if all(needle in text for needle in needles):
        return True, _combined_evidence(scan, needles)
    return False, ""


def _has_path(scan: ScanResult, predicate) -> tuple[bool, str]:
    for path in scan.files:
        if predicate(path):
            return True, path
    return False, ""


def _check_eval_01(scan: ScanResult) -> tuple[bool, str]:
    return _has_path(
        scan,
        lambda p: (
            p.startswith("evals/")
            or ("eval" in p and p.rsplit(".", 1)[-1] in ("json", "jsonl", "csv", "yaml", "yml"))
        ),
    )


def _check_eval_02(scan: ScanResult) -> tuple[bool, str]:
    return _has(scan, "threshold", "baseline")


def _check_eval_03(scan: ScanResult) -> tuple[bool, str]:
    by_path, evidence = _has_path(
        scan, lambda p: "eval" in p and p.rsplit(".", 1)[-1] in ("py", "js")
    )
    if by_path:
        return True, evidence
    return _has(scan, "run_eval")


def _check_guard_01(scan: ScanResult) -> tuple[bool, str]:
    text = _all_text(scan)
    for alt in ("redact", "anonym", "mask"):
        if "pii" in text and alt in text:
            return True, _combined_evidence(scan, ["pii", alt])
    return False, ""


def _check_guard_02(scan: ScanResult) -> tuple[bool, str]:
    return _has(scan, "schema", "valid")


def _check_guard_03(scan: ScanResult) -> tuple[bool, str]:
    text = _all_text(scan)
    for alt in ("sanitiz", "validat", "allowlist", "blocklist"):
        if "injection" in text and alt in text:
            return True, _combined_evidence(scan, ["injection", alt])
    return False, ""


def _check_obs_01(scan: ScanResult) -> tuple[bool, str]:
    text = _all_text(scan)
    trace = "trace_id" if "trace_id" in text else "correlation_id" if "correlation_id" in text else ""
    log = "logging" if "logging" in text else "logger" if "logger" in text else ""
    if trace and log:
        return True, _combined_evidence(scan, [trace, log])
    return False, ""


def _check_obs_02(scan: ScanResult) -> tuple[bool, str]:
    return _has(scan, "token", "cost") if "cost" in _all_text(scan) else _has(scan, "token", "usage")


def _check_obs_03(scan: ScanResult) -> tuple[bool, str]:
    text = _all_text(scan)
    if "timeout" in text and ("latency" in text or "budget" in text):
        return True, _evidence_for(scan, "timeout")
    return False, ""


def _check_gov_01(scan: ScanResult) -> tuple[bool, str]:
    by_path, evidence = _has_path(scan, lambda p: p.startswith("prompts/"))
    if by_path:
        return True, evidence
    return _has(scan, "prompt_version")


def _check_gov_02(scan: ScanResult) -> tuple[bool, str]:
    text = _all_text(scan)
    for needle in ("human review", "human_approval", "approval_queue"):
        if needle in text:
            return True, _evidence_for(scan, needle)
    return False, ""


def _check_gov_03(scan: ScanResult) -> tuple[bool, str]:
    text = _all_text(scan)
    for alt in ("days", "delete", "policy"):
        if "retention" in text and alt in text:
            return True, _combined_evidence(scan, ["retention", alt])
    return False, ""


def _check_rel_01(scan: ScanResult) -> tuple[bool, str]:
    return _has(scan, "retry", "fallback")


def _check_rel_02(scan: ScanResult) -> tuple[bool, str]:
    return _has(scan, "try", "except", "error")


def _check_rel_03(scan: ScanResult) -> tuple[bool, str]:
    for path in sorted(scan.texts):
        if SECRET_PATTERN.search(scan.texts[path]):
            return False, path
    return True, ""


# id, area, title, severity, predicate, remediation
_DEFINITIONS = [
    ("EVAL-01", "Evaluation", "Eval dataset exists", "critical", _check_eval_01,
     "Add an eval dataset under evals/ (JSON, JSONL, CSV, or YAML) with expected outputs."),
    ("EVAL-02", "Evaluation", "Baseline and threshold defined", "important", _check_eval_02,
     "Define a baseline and a pass threshold in config or an eval script, and fail the build below it."),
    ("EVAL-03", "Evaluation", "Eval runner exists", "important", _check_eval_03,
     "Add a runnable eval script (for example eval/run_eval.py) that scores the dataset."),
    ("GUARD-01", "Guardrails", "PII handling present", "critical", _check_guard_01,
     "Redact, anonymise, or mask PII before logging or sending text to a model."),
    ("GUARD-02", "Guardrails", "Output schema validation present", "critical", _check_guard_02,
     "Validate model output against a schema before using it, and handle invalid output explicitly."),
    ("GUARD-03", "Guardrails", "Input validation / prompt-injection handling", "important", _check_guard_03,
     "Sanitise or validate user input and check for prompt injection before it reaches the model."),
    ("OBS-01", "Observability & Cost", "Tracing and logging present", "critical", _check_obs_01,
     "Log every request with a trace_id / correlation_id so a failure can be traced end to end."),
    ("OBS-02", "Observability & Cost", "Token and cost tracking present", "important", _check_obs_02,
     "Record token usage and cost per request so spend can be budgeted and investigated."),
    ("OBS-03", "Observability & Cost", "Timeout and latency budget present", "important", _check_obs_03,
     "Set a timeout and a latency budget for model calls, and handle slow calls explicitly."),
    ("GOV-01", "Governance", "Prompt versioning present", "important", _check_gov_01,
     "Keep prompts in versioned files (for example prompts/v1.txt) and record prompt_version per run."),
    ("GOV-02", "Governance", "Human review for high-risk actions", "important", _check_gov_02,
     "Route high-risk or low-confidence actions to human review / an approval queue before acting."),
    ("GOV-03", "Governance", "Data retention defined", "important", _check_gov_03,
     "Define a retention policy (for example retention days) and how stored data is deleted."),
    ("REL-01", "Reliability", "Retry and fallback present", "important", _check_rel_01,
     "Add retry with a fallback path so a transient model failure does not fail the whole request."),
    ("REL-02", "Reliability", "Structured error handling present", "important", _check_rel_02,
     "Handle errors with try/except and return a structured error, not an unhandled exception."),
    ("REL-03", "Reliability", "No hardcoded secrets", "critical", _check_rel_03,
     "Remove hardcoded api_key / password values and load secrets from the environment."),
]

CHECK_IDS = [d[0] for d in _DEFINITIONS]
CRITICAL_IDS = {d[0] for d in _DEFINITIONS if d[3] == "critical"}


def run_checks(scan: ScanResult) -> list[CheckResult]:
    """Run all checks over *scan* and return results in spec order."""
    results = []
    for check_id, area, title, severity, predicate, remediation in _DEFINITIONS:
        passed, evidence = predicate(scan)
        results.append(
            CheckResult(
                id=check_id,
                area=area,
                title=title,
                severity=severity,
                status="pass" if passed else "fail",
                evidence=evidence,
                remediation=remediation,
            )
        )
    return results
