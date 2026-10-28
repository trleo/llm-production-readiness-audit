"""Scoring, verdict, and report rendering (pure functions)."""

from __future__ import annotations

import json

from .checks import CRITICAL_IDS


def score_results(results):
    """Return (score, verdict, per-area counts) for *results*."""
    total = len(results)
    if total == 0:
        return 0.0, "NO-GO", {}
    passed = sum(1 for r in results if r.status == "pass")
    score = round(100.0 * passed / total, 1)
    critical_failed = any(
        r.id in CRITICAL_IDS and r.status != "pass" for r in results
    )
    if critical_failed or score < 60:
        verdict = "NO-GO"
    elif score >= 80:
        verdict = "GO"
    else:
        verdict = "CONDITIONAL GO"

    areas = {}
    for r in results:
        bucket = areas.setdefault(r.area, {"passed": 0, "total": 0})
        bucket["total"] += 1
        if r.status == "pass":
            bucket["passed"] += 1
    return score, verdict, areas


def _check_dict(r) -> dict:
    return {
        "id": r.id,
        "area": r.area,
        "title": r.title,
        "severity": r.severity,
        "status": r.status,
        "evidence": r.evidence,
        "remediation": r.remediation,
    }


def render_json(path: str, results, score: float, verdict: str) -> str:
    """Render the report as JSON. Same score, verdict, and checks as Markdown."""
    _, _, areas = score_results(results)
    payload = {
        "project": path,
        "score": score,
        "verdict": verdict,
        "passed": sum(1 for r in results if r.status == "pass"),
        "total": len(results),
        "areas": areas,
        "checks": [_check_dict(r) for r in results],
    }
    return json.dumps(payload, indent=2) + "\n"


def render_markdown(path: str, results, score: float, verdict: str) -> str:
    """Render the report as Markdown. Same score, verdict, and checks as JSON."""
    passed = sum(1 for r in results if r.status == "pass")
    lines = [
        "# LLM Production Readiness Report",
        "",
        f"**Project:** `{path}`",
        f"**Score:** {score:.1f}% ({passed}/{len(results)} checks passed)",
        f"**Verdict:** {verdict}",
        "",
        "| Check | Area | Status | Evidence |",
        "|---|---|---|---|",
    ]
    for r in results:
        mark = "PASS" if r.status == "pass" else "FAIL"
        lines.append(f"| {r.id} — {r.title} | {r.area} | {mark} | {r.evidence or '—'} |")
    lines.append("")
    lines.append("## What to fix first")
    lines.append("")
    failed = [r for r in results if r.status == "fail"]
    if not failed:
        lines.append("No failing checks. Keep the practices above under test as the project changes.")
    else:
        for r in failed:
            lines.append(f"- **{r.id} ({r.title}):** {r.remediation}")
    lines.append("")
    return "\n".join(lines)
