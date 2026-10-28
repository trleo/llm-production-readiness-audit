# LLM Production Readiness Auditor

**Is your LLM feature ready to ship? Run one command and get a scored, evidence-based answer — in under a minute, offline, with no API key.**

> **Short answer:** This tool audits an LLM project folder against 15 deterministic production-readiness checks — evaluation, guardrails, observability and cost, governance, and reliability — and returns a **GO**, **CONDITIONAL GO**, or **NO-GO** verdict, with the exact file behind every result and what to fix first.

No model call. No API key. No dependencies. Python 3.10+, standard library only.

## Contents

- [Quick answer](#quick-answer)
- [Quickstart](#quickstart)
- [What it checks: the 15 checks](#what-it-checks-the-15-checks)
- [How to read the score](#how-to-read-the-score)
- [Example: failing vs passing](#example-failing-vs-passing)
- [All options](#all-options)
- [What this does not prove](#what-this-does-not-prove)
- [Frequently asked questions](#frequently-asked-questions)
- [How it works](#how-it-works)
- [Development](#development)

## Quick answer

**What is the LLM Production Readiness Auditor?**
It is a command-line tool for AI solution leads, engineering teams, and reviewers who need to decide whether an LLM feature is safe to ship. It does not demo a chatbot. It checks whether the production practices are actually present in the code and config.

**What do I get?**
A scored report in two formats with the same results:

- `report.md` — human-readable, with a check table and a "what to fix first" list
- `report.json` — machine-readable, for CI, dashboards, and further tooling

**How long does it take?**
Seconds for a typical project folder. It reads files only; it never modifies the project it audits.

**Who is it for?**
- An **AI solution lead** signing off a release
- A **team** that wants a repeatable pre-release gate, not a one-off opinion
- A **reviewer** who wants evidence, not claims — every check names its evidence file

## Quickstart

**1. Check the tool works:**

```bash
python -m readiness_audit --list-checks
python -m readiness_audit --version
```

**2. Audit the passing reference project:**

```bash
python -m readiness_audit --path samples/passing-reference --out /tmp/passing-report
```

Expected output:

```
Score: 100.0% (15/15)
Verdict: GO
```

**3. Audit the failing demo project:**

```bash
python -m readiness_audit --path samples/failing-demo --out /tmp/failing-report
```

Expected output:

```
Score: 0.0% (0/15)
Verdict: NO-GO
```

**4. Audit your own project:**

```bash
python -m readiness_audit --path /path/to/your-project --out ./readiness-report
```

That's it. Open `./readiness-report/report.md` for the verdict and the fix list.

## What it checks: the 15 checks

A check passes only on explicit evidence — a matching file, or a matching pattern in scanned text. Absence of evidence is a failure. Critical checks are marked **\***; all of them must pass for a GO or CONDITIONAL GO verdict.

### Evaluation — can you prove it works?

| Check | What it looks for | Why it matters |
|---|---|---|
| EVAL-01 \* | An eval dataset, e.g. under `evals/` | Without a dataset, "it works" is an anecdote |
| EVAL-02 | A baseline and a pass threshold | Without a threshold, regressions are invisible |
| EVAL-03 | A runnable eval script, e.g. `eval/run_eval.py` | An eval nobody can re-run will not be re-run |

### Guardrails — can bad input or bad output hurt you?

| Check | What it looks for | Why it matters |
|---|---|---|
| GUARD-01 \* | PII handling: PII plus redact, anonymise, or mask | Prevents private data leaking into logs and model calls |
| GUARD-02 \* | Output schema validation: schema plus validation | Stops malformed model output breaking downstream code |
| GUARD-03 | Prompt-injection handling: injection plus sanitise, validate, allowlist, or blocklist | Reduces instruction-override attacks from user input |

### Observability and cost — can you trace and budget it?

| Check | What it looks for | Why it matters |
|---|---|---|
| OBS-01 \* | Tracing and logging: trace ID or correlation ID plus logging | Without a trace ID, a production failure cannot be investigated |
| OBS-02 | Token and cost tracking: token plus cost or usage | Without usage tracking, spend cannot be budgeted or explained |
| OBS-03 | Timeout and latency budget: timeout plus latency or budget | Without a budget, one slow model call can stall the whole request |

### Governance — can you reproduce and oversee it?

| Check | What it looks for | Why it matters |
|---|---|---|
| GOV-01 | Prompt versioning: a `prompts/` folder or `prompt_version` | Without versioned prompts, results cannot be reproduced |
| GOV-02 | Human review for high-risk actions: human review, approval, or approval queue | High-risk actions should not run on model output alone |
| GOV-03 | Data retention: retention plus days, delete, or policy | Stored data needs a defined lifetime and deletion path |

### Reliability — can it fail safely?

| Check | What it looks for | Why it matters |
|---|---|---|
| REL-01 | Retry and fallback: both retry and fallback present | Transient model failures should not fail the whole request |
| REL-02 | Structured error handling: try, except, and an error response | Unhandled exceptions are the worst failure mode for users |
| REL-03 \* | No hardcoded secrets: no `api_key = "sk-..."` or `password = "..."` | Hardcoded secrets in code are a direct security risk |

When a check's evidence lives in different files, the report lists every file that together proves it, joined with ` + ` — never just the first file.

## How to read the score

**Score formula:** `100 × passed checks ÷ 15`, rounded to one decimal place.

| Verdict | Rule | What it means |
|---|---|---|
| ✅ GO | Score ≥ 80% and all critical checks pass | Ready to ship, on the evidence checked |
| ⚠️ CONDITIONAL GO | Score ≥ 60% and all critical checks pass | Ship with the listed fixes tracked, not ignored |
| ❌ NO-GO | Score < 60%, or any critical check fails | Do not ship yet — fix the critical checks first |

**Exit codes, for CI:**

| Exit code | Meaning |
|---|---|
| `0` | GO or CONDITIONAL GO |
| `1` | NO-GO |
| `2` | Usage error, e.g. a missing path or an unwritable `--out` directory |

## Example: failing vs passing

| | Failing demo | Passing reference |
|---|---|---|
| Folder | `samples/failing-demo/` | `samples/passing-reference/` |
| Score | 0.0% (0/15) | 100.0% (15/15) |
| Verdict | ❌ NO-GO | ✅ GO |
| What it shows | A minimal demo with a hardcoded sample key and no evals, logging, guardrails, or fallback | The same kind of project, with evals, guardrails, tracing, cost tracking, versioned prompts, human review, and fallback — its model call is a stub, so it runs offline |

Run both examples from [Quickstart](#quickstart) to see the full reports, including the fix list for the failing demo.

## All options

| Option | What it does |
|---|---|
| `--path <dir>` | Project directory to audit (required, unless `--list-checks` is given) |
| `--out <dir>` | Where `report.json` and `report.md` are written (default: `./readiness-report`) |
| `--list-checks` | Print the 15 check IDs and exit |
| `--version` | Print the package version (currently `0.1.0`) and exit |
| `--exclude <pattern>` | Glob pattern to leave out of scanning; repeatable; matches a file's relative path or basename |

Example — skip generated files:

```bash
python -m readiness_audit --path ./my-project --exclude "node_modules/*" --exclude "*.min.js" --out ./readiness-report
```

## What this does not prove

A passing audit proves the checked practices are present. It does **not** prove:

- Answer quality — this tool does not grade answers and does not call a model
- Security against all attacks — the secret check is one narrow pattern, not a full security scan
- Safety in every context — a GO is a first gate for a release decision, not a final guarantee

See `docs/adr/0001-deterministic-checks-first.md` for why deterministic checks come first, and what an optional LLM-judge layer could add later without replacing them.

## Frequently asked questions

### Do I need an API key, a model account, or internet access to run it?

No. It runs fully offline, with the Python standard library only, and never calls a model.

### Does a GO verdict mean my LLM feature is safe?

No — not on its own. GO means all 15 checked practices are present, including all critical ones. Use it as a release gate, alongside answer evaluation, security review, and testing for your specific use case.

### Does it grade how good my model's answers are?

No. That is deliberately out of scope for version 1, so the result is deterministic and reproducible. Add answer evaluation on your eval dataset separately; EVAL-01 to EVAL-03 check that such an eval exists and can be re-run.

### Can I use it in CI?

Yes. Exit code `0` means GO or CONDITIONAL GO, `1` means NO-GO, and `2` means a usage error. The JSON report has the same score, verdict, and checks as the Markdown report, so CI can gate on it or publish it.

### My project is not Python. Can I still audit it?

Yes. The auditor scans text files in any language — code, config, prompts, and docs — for the same evidence patterns. It does not run your project.

### Can I exclude files from an audit?

Yes. Use `--exclude` with a glob pattern, repeatable, for example `--exclude "*.min.js"`.

### What happens if a project folder is empty?

It reports NO-GO, not a crash. An empty folder passes only REL-03 (no hardcoded secret was found) and fails the other 14 checks, for a score of 6.7%.

### Where are the design decisions documented?

- Design: `docs/superpowers/specs/2026-10-28-llm-production-readiness-auditor-design.md`
- Implementation plan: `docs/superpowers/plans/2026-10-28-llm-production-readiness-auditor-plan.md`
- Key trade-off: `docs/adr/0001-deterministic-checks-first.md`

## How it works

1. **Scan (read-only).** Walks the project folder, skipping `.git`, `node_modules`, `__pycache__`, virtual environments, `dist`, and `build`, plus binary files and text files over 200 KB.
2. **Check.** Runs 15 pure, deterministic predicates over the scan — no model, no network, no randomness.
3. **Score and report.** Applies the verdict rules in [How to read the score](#how-to-read-the-score), then writes the same results as Markdown and JSON to `--out`.

Scanning never modifies the project it audits. Reports are written only to `--out`.

## Development

```bash
python -m unittest discover -s tests -v
```

Tests use the standard library `unittest` only, and follow TDD: every feature started as a failing test. The current suite is 22 tests, covering the scanner, all 15 checks, scoring and verdicts, the CLI, and the two samples end to end.
