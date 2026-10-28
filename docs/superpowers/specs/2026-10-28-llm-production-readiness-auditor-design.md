# LLM Production Readiness Auditor — Design

## Intent and why

Teams ship LLM demos that look good but cannot answer, with evidence,
whether the feature is evaluated, guarded, observable, governed, and
reliable. This tool gives a lead a deterministic, repeatable answer:
a scored audit with a go / no-go verdict, the exact file behind each
result, and what to fix first. It is a tool for shipping decisions,
not another chatbot.

## Goals

- Audit a project folder offline, with no API key, no network, and no
  model call, so the result is cheap, fast, and reproducible.
- Cover five areas a solution lead actually signs off on: Evaluation,
  Guardrails, Observability & Cost, Governance, Reliability.
- Produce two artifacts: a human-readable Markdown report and a
  machine-readable JSON report, with the same checks, score, and verdict.
- Be usable as a CI gate: exit 0 for GO / CONDITIONAL GO, 1 for NO-GO,
  2 for a usage error such as a missing path.
- Ship with a failing sample and a passing sample so a reviewer can
  run the tool in minutes and see the difference.

## Non-goals / anti-goals

- Not an LLM-as-judge. It does not grade answer quality, and it does
  not call a model. That keeps it deterministic and honest about what
  it proves: presence of production practices, not quality of answers.
- Not a security scanner. The hardcoded-secret check is one narrow,
  pattern-based signal, not a replacement for secret scanning.
- Not a prompt library, model wrapper, or demo chatbot.
- A passing audit is not a guarantee that a feature is safe. It is
  evidence that the checked practices are present.

## Constraints

- Python 3.10+, standard library only. No third-party dependencies,
  so `python -m readiness_audit` works after a plain checkout.
- Tests use the standard library `unittest` only, for the same reason.
- Scanning is read-only. The auditor never modifies the scanned project.
  Reports are written only to the `--out` directory.
- Text files larger than 200 KB are skipped for content matching, and
  binary files are skipped. Ignored directories: `.git`,
  `node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build`.
- A check passes only on explicit evidence: a matching file path or a
  matching keyword pattern in scanned text. Absence of evidence is a
  failure, not a warning, except where a check is defined otherwise.
  When a check's keywords live in different files, evidence lists
  every file that together proves it, joined with ` + `, never just
  the first keyword's file.

## The checks (15, 3 per area)

Critical checks are marked *. A verdict of GO requires all critical
checks to pass.

Evaluation:
- EVAL-01* eval dataset exists: a file under `evals/` or a file whose
  name contains `eval` with a `.json`, `.jsonl`, `.csv`, `.yaml`, or
  `.yml` extension.
- EVAL-02 baseline and threshold defined: scanned text contains both
  `threshold` and `baseline` (for example in a config or eval script).
- EVAL-03 eval runner exists: a file whose name contains `eval` with a
  `.py` or `.js` extension, or text containing `run_eval`.

Guardrails:
- GUARD-01* PII handling: text contains `pii` together with `redact`,
  `anonym`, or `mask`.
- GUARD-02* output schema validation: text contains both `schema` and
  `valid` (for example a validation function).
- GUARD-03 input validation / prompt-injection handling: text contains
  `injection` together with `sanitiz`, `validat`, `allowlist`, or
  `blocklist`.

Observability & Cost:
- OBS-01* tracing and logging: text contains `trace_id` or
  `correlation_id` together with `logging` or `logger`.
- OBS-02 token and cost tracking: text contains `token` together with
  `cost` or `usage`.
- OBS-03 timeout and latency budget: text contains `timeout` together
  with `latency` or `budget`.

Governance:
- GOV-01 prompt versioning: a path under `prompts/` or text containing
  `prompt_version`.
- GOV-02 human review for high-risk actions: text contains
  `human review`, `human_approval`, or `approval_queue`.
- GOV-03 data retention: text contains `retention` together with
  `days`, `delete`, or `policy`.

Reliability:
- REL-01 retry and fallback: text contains both `retry` and `fallback`.
- REL-02 structured error handling: text contains `try`, `except`,
  and `error` (for example an error response with a code).
- REL-03* no hardcoded secrets: passes only if no scanned text matches
  a hardcoded `api_key = "sk-..."` or `password = "..."` pattern.

## Scoring and verdict

- Score = 100 * passed / total checks, rounded to one decimal.
- GO: score >= 80 and all critical checks pass.
- CONDITIONAL GO: score >= 60 and all critical checks pass, but below GO.
- NO-GO: score < 60, or any critical check fails.

## Parts

- `readiness_audit/scanner.py`: walk a directory, collect relative
  file paths and text content, applying the ignore and size rules.
- `readiness_audit/checks.py`: the check definitions, their predicates,
  severity, and remediation text. Pure functions over a scan result.
- `readiness_audit/report.py`: scoring, verdict, and Markdown / JSON
  rendering. Pure functions over check results.
- `readiness_audit/cli.py`: argument parsing, exit codes, and writing
  `report.json` / `report.md` to `--out`.
- `readiness_audit/__main__.py`: `python -m readiness_audit` entry.
- `tests/`: unittest tests for scanner, checks, report, and CLI.
- `samples/failing-demo/`: intentionally minimal demo. Expected:
  0/15, 0.0%, NO-GO.
- `samples/passing-reference/`: intentionally complete reference.
  Expected: 15/15, 100.0%, GO.

## What the builder decides

- Exact wording of report tables and remediation strings, as long as
  every check id, area, status, evidence path, and remediation is
  present in both outputs.
- Internal helper names, as long as the public CLI contract below holds.

## CLI contract (pinned)

```
python -m readiness_audit --path <project-dir> [--out <dir>]
python -m readiness_audit --list-checks
```

- `--path` is required unless `--list-checks` is given.
- Default `--out` is `./readiness-report` in the working directory.
- Exit codes: 0 = GO or CONDITIONAL GO, 1 = NO-GO, 2 = usage error.
- `--out` must contain `report.json` and `report.md` on success.
