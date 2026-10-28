"""Eval runner for the passing reference sample.

Scores the eval dataset against a baseline and a threshold.
This is a teaching stub: the 'model' is the same stub logic as app.py.
"""

import json
from pathlib import Path

BASELINE = 0.7
THRESHOLD = 0.8


def run_eval():
    dataset = Path(__file__).parent.parent / "evals" / "dataset.jsonl"
    rows = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    correct = sum(1 for row in rows if row["expected"].startswith("Answer to: "))
    score = correct / len(rows) if rows else 0.0
    print(f"eval score: {score:.2f} (baseline {BASELINE}, threshold {THRESHOLD})")
    return score >= THRESHOLD


if __name__ == "__main__":
    raise SystemExit(0 if run_eval() else 1)
