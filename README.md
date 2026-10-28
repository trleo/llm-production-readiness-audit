# LLM Production Readiness Auditor

A CLI that answers, with evidence, whether an LLM feature is actually
safe to ship — evaluated, guarded, observable, governed, and reliable.

It does **not** call a model, need an API key, or grade answer quality.
It checks, deterministically and offline, whether the production
practices are present in a project folder, and produces a scored
report with a go / no-go verdict.

## Why this exists

Most AI projects demo well. Few can quickly prove they are evaluated
against a baseline, guarded against bad input and bad output, traced
and costed per request, versioned, and able to fail safely. A solution
lead signs off on those things, not on a good demo. This tool makes
that sign-off visible.

## Install / run

Python 3.10+, standard library only. No dependencies to install.

```bash
python -m readiness_audit --list-checks
python -m readiness_audit --path samples/passing-reference --out /tmp/passing-report
python -m readiness_audit --path samples/failing-demo --out /tmp/failing-report
```

Exit codes: `0` = GO or CONDITIONAL GO, `1` = NO-GO, `2` = usage error
(for example a missing path).

## What it checks (15 checks)

| Area | Checks |
|---|---|
| Evaluation | Eval dataset, baseline + threshold, eval runner |
| Guardrails | PII handling, output schema validation, prompt-injection handling |
| Observability & Cost | Tracing + logging, token + cost tracking, timeout + latency budget |
| Governance | Prompt versioning, human review, data retention |
| Reliability | Retry + fallback, structured errors, no hardcoded secrets |

Critical checks (eval dataset, PII handling, schema validation,
tracing, no hardcoded secrets) must all pass for a GO or CONDITIONAL GO.

Verdict rules:

- **GO:** score ≥ 80% and all critical checks pass
- **CONDITIONAL GO:** score ≥ 60% and all critical checks pass
- **NO-GO:** score < 60%, or any critical check fails

## Example output

Passing reference:

```
Score: 100.0% (15/15)
Verdict: GO
```

Failing demo:

```
Score: 0.0% (0/15)
Verdict: NO-GO
```

Each report is written to `--out` as `report.md` (human-readable, with
what to fix first) and `report.json` (machine-readable, same score,
verdict, and checks).

## Samples

- `samples/failing-demo/` — intentionally minimal demo. Expected:
  0/15, NO-GO.
- `samples/passing-reference/` — intentionally complete reference.
  Expected: 15/15, GO. Its model call is a stub, so it runs offline.

## What this does not prove

A passing audit proves the checked practices are present. It does not
prove answer quality, security against all attacks, or that a feature
is safe in every context. Use it as a first gate, not a final guarantee.
See `docs/adr/0001-deterministic-checks-first.md` for the trade-offs.

## Development

```bash
python -m unittest discover -s tests -v
```

Tests use the standard library `unittest` only, and follow TDD:
every feature started as a failing test.
