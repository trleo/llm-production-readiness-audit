# LLM Production Readiness Auditor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a stdlib-only Python CLI that audits a project folder against 15 deterministic production-readiness checks and emits a scored Markdown + JSON report with a go / no-go verdict.

**Architecture:** Scanner collects file paths and text; pure check predicates run over the scan; a pure report module scores and renders; a thin CLI handles arguments, exit codes, and file output.

**Tech Stack:** Python 3.10+, standard library only, `unittest` only for tests.

**Spec:** `docs/superpowers/specs/2026-10-28-llm-production-readiness-auditor-design.md`

## Global Constraints

- Python 3.10+, standard library only.
- Tests use `unittest` only.
- Scanning is read-only; reports go only to `--out`.
- Text files larger than 200 KB and binary files are skipped for content matching.
- Ignored directories: `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build`.
- Exit codes: 0 = GO or CONDITIONAL GO, 1 = NO-GO, 2 = usage error.
- Failing sample expected: 0/15, 0.0%, NO-GO. Passing sample expected: 15/15, 100.0%, GO.

## Review Focus

- A scanned project that is empty or missing: CLI must exit 2 for a missing path, and report NO-GO (not crash) for an empty directory.
- A sample that accidentally contains a keyword (for example `threshold` in a failing-sample README): tests must assert the exact sample scores, so accidental keywords fail the suite.
- A hardcoded secret in the auditor's own tests or samples other than the failing sample: the passing sample must not trigger REL-03.
- Report files must agree: JSON and Markdown must carry the same score, verdict, and per-check status.
- Large or binary files in a scanned project must not crash scanning or change the score by being read as text.

---

### Task 1: Scanner

**Files:**
- Create: `readiness_audit/scanner.py`
- Test: `tests/test_scanner.py`

**Interfaces:**
- Consumes: a directory path.
- Produces: `ScanResult(files: list[str], texts: dict[str, str])` where `files` are relative POSIX paths and `texts` maps relative path to lowercased text for eligible text files; and `scan_project(path: str) -> ScanResult`.

- [ ] **Step 1: Write the failing test** — test that scanning a temp dir returns relative paths, lowercased text, skips `.git/` and `node_modules/`, and skips a binary file's content.
- [ ] **Step 2: Run test to verify it fails** — Run: `python -m unittest tests.test_scanner -v` — Expected: FAIL / ModuleNotFoundError.
- [ ] **Step 3: Implement `scan_project` in `readiness_audit/scanner.py`** — walk with the ignore list and 200 KB limit, skip files containing a null byte.
- [ ] **Step 4: Run test to verify it passes** — Run: `python -m unittest tests.test_scanner -v` — Expected: PASS.

### Task 2: Checks

**Files:**
- Create: `readiness_audit/checks.py`
- Test: `tests/test_checks.py`

**Interfaces:**
- Consumes: `ScanResult` from Task 1.
- Produces: `CHECK_IDS: list[str]` (15 ids in spec order), `run_checks(scan: ScanResult) -> list[CheckResult]` with fields `id, area, title, severity, status, evidence, remediation`, where `status` is `pass` or `fail` and `evidence` is a relative path or `""`.

- [ ] **Step 1: Write the failing test** — test each predicate on hand-built scans: EVAL-01 by path, GUARD-02 by `schema`+`valid`, REL-03 by hardcoded `api_key = "sk-..."`, and a scan with no evidence failing 14 checks and passing REL-03 vacuously (no secret found).
- [ ] **Step 2: Run test to verify it fails** — Run: `python -m unittest tests.test_checks -v` — Expected: FAIL / ModuleNotFoundError.
- [ ] **Step 3: Implement the 15 checks in `readiness_audit/checks.py`** — exactly the ids, areas, critical flags, and predicates in the spec.
- [ ] **Step 4: Run test to verify it passes** — Run: `python -m unittest tests.test_checks -v` — Expected: PASS.

### Task 3: Report and scoring

**Files:**
- Create: `readiness_audit/report.py`
- Test: `tests/test_report.py`

**Interfaces:**
- Consumes: `list[CheckResult]` from Task 2 and a scanned path string.
- Produces: `score_results(results) -> tuple[float, str, dict]` returning score, verdict (`GO`, `CONDITIONAL GO`, `NO-GO`), and per-area counts; `render_markdown(...) -> str`; `render_json(...) -> str` (valid JSON with the same score, verdict, and checks).

- [ ] **Step 1: Write the failing test** — test GO at 15/15, CONDITIONAL GO at a 60-79 score with criticals passing, and NO-GO when a critical fails even at a high score.
- [ ] **Step 2: Run test to verify it fails** — Run: `python -m unittest tests.test_report -v` — Expected: FAIL / ModuleNotFoundError.
- [ ] **Step 3: Implement scoring and both renderers in `readiness_audit/report.py`**.
- [ ] **Step 4: Run test to verify it passes** — Run: `python -m unittest tests.test_report -v` — Expected: PASS.

### Task 4: CLI, samples, README, ADR

**Files:**
- Create: `readiness_audit/cli.py`, `readiness_audit/__main__.py`, `readiness_audit/__init__.py`, `pyproject.toml`, `LICENSE`, `README.md`, `docs/adr/0001-deterministic-checks-first.md`
- Create: `samples/failing-demo/README.md`, `samples/failing-demo/app.py`, `samples/passing-reference/README.md`, `samples/passing-reference/app.py`, `samples/passing-reference/config.yaml`, `samples/passing-reference/prompts/v1.txt`, `samples/passing-reference/evals/dataset.jsonl`, `samples/passing-reference/eval/run_eval.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: Tasks 1-3.
- Produces: CLI contract from the spec, including `--list-checks`, `--path`, `--out`, and exit codes 0/1/2.

- [ ] **Step 1: Write the failing test** — test CLI on both samples (failing: exit 1, 0.0%, NO-GO; passing: exit 0, 100.0%, GO), test `--list-checks` lists 15 ids, and test a missing path exits 2.
- [ ] **Step 2: Run test to verify it fails** — Run: `python -m unittest tests.test_cli -v` — Expected: FAIL / ModuleNotFoundError.
- [ ] **Step 3: Implement the CLI and write the samples, README, and ADR** — passing sample must contain evidence for all 15 checks and no hardcoded secret; failing sample must contain evidence for none and one hardcoded test key.
- [ ] **Step 4: Run the full suite** — Run: `python -m unittest discover -s tests -v` — Expected: all PASS, 0 failures.

### Task 5: Verification and review

- [ ] Run the full suite fresh: `python -m unittest discover -s tests -v`
- [ ] Run the CLI end-to-end on both samples into a temp out dir and read both reports back.
- [ ] Review the diff/file list for secrets, accidental keywords in samples, and report agreement between JSON and Markdown.
- [ ] Fix any failure before claiming completion; do not claim zero bugs without this evidence.
