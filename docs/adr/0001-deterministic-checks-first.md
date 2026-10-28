# ADR 0001: Deterministic checks first, LLM-as-judge later

## Status

Accepted.

## Context

An auditor that grades with a model is expensive, slow, non-reproducible,
and can itself be wrong in ways that are hard to appeal. A lead who
needs a go / no-go decision in CI needs the same input to give the same
output, every time, with the file that proves it.

## Decision

Version 1 checks for the presence of production practices with
deterministic path and keyword evidence, offline, with no model call.
It explicitly does not grade answer quality.

## Consequences

- Good: fast, free, reproducible, usable as a CI gate, easy to review.
- Bad: a project can pass a check with a keyword and still be weak in
  practice (for example a `retry` that never actually retries well).
  Mitigation: checks require specific combinations (for example
  `schema` + `valid`, `trace_id` + `logging`), samples show good and
  bad examples, and the README states what a pass does not prove.
- Future: an optional, separate LLM-judge layer can score answer
  quality on the eval dataset, but it must never replace these
  deterministic checks or change their verdict silently.

## Alternatives considered

- LLM-as-judge only: rejected for v1 (cost, variance, no evidence file).
- Manual checklist only: rejected (not repeatable, not a CI gate).
