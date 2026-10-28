"""Passing reference: the practices a production LLM feature needs.

This is a teaching sample, not a real model client. The model call is
a stub, so the file runs offline with no API key.
"""

import logging
import os
import time
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("API_KEY")
PROMPT_VERSION = "v1"
TIMEOUT_SECONDS = 30
LATENCY_BUDGET_MS = 2000
RETENTION_DAYS = 30


def redact_pii(text):
    """Redact PII before logging or sending text anywhere."""
    # In a real system this would use a PII detector; here the point
    # is the practice: pii is redacted, never logged raw.
    return text.replace("user@example.com", "[redacted]")


def sanitize_input(text):
    """Validate input and guard against prompt injection."""
    # prompt injection check: reject instruction-like overrides
    lowered = text.lower()
    if "ignore previous instructions" in lowered:
        raise ValueError("prompt injection blocked")
    return text.strip()


def validate_output(output, schema):
    """Validate model output against a schema; return True if valid."""
    if not isinstance(output, dict):
        return False
    return all(key in output for key in schema)


def call_model_stub(question):
    return {"answer": "Answer to: " + question, "confidence": 0.9}


def call_with_retry(question):
    """Retry once, then use a fallback answer."""
    last_error = None
    for attempt in range(2):  # retry
        try:
            return call_model_stub(question)
        except Exception as exc:  # structured error handling below
            last_error = exc
    # fallback
    return {"answer": "Sorry, I could not answer that.", "confidence": 0.0, "fallback": True}


def ask(question):
    trace_id = str(uuid.uuid4())
    start = time.time()
    try:
        clean = sanitize_input(redact_pii(question))
        result = call_with_retry(clean)
        token_usage = 42
        cost = token_usage * 0.001
        latency_ms = (time.time() - start) * 1000
        logger.info(
            "trace_id=%s prompt_version=%s token_usage=%s cost=%s latency_ms=%s",
            trace_id, PROMPT_VERSION, token_usage, cost, latency_ms,
        )
        if latency_ms > LATENCY_BUDGET_MS:
            logger.warning("trace_id=%s latency over budget", trace_id)
        if result.get("confidence", 0) < 0.5:
            # human review for low-confidence answers
            return {"answer": result["answer"], "human review": True, "trace_id": trace_id}
        if not validate_output(result, ["answer", "confidence"]):
            return {"error": "invalid output schema", "error_code": "INVALID_OUTPUT", "trace_id": trace_id}
        return {**result, "trace_id": trace_id}
    except Exception as exc:
        logger.info("trace_id=%s error=%s", trace_id, exc)
        return {"error": str(exc), "error_code": "REQUEST_FAILED", "trace_id": trace_id}


if __name__ == "__main__":
    print(ask("Hello"))
