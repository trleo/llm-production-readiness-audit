# Passing Reference

A small, intentionally complete reference project. It is not a real
product: it shows, in one place, the production practices the auditor
checks for — evaluation, guardrails, observability, governance, and
reliability.

Run the audit on this folder:

```
python -m readiness_audit --path samples/passing-reference --out /tmp/passing-report
```

Run its eval:

```
python samples/passing-reference/eval/run_eval.py
```
