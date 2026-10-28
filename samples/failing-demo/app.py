# Demo chatbot - intentionally minimal.
# This sample is meant to fail a production readiness audit.
# The key below is a fake sample value, not a real secret.

api_key = "sk-sample"


def call_model(question):
    return "Answer to: " + question


def ask(question):
    return call_model(question)


if __name__ == "__main__":
    print(ask("Hello"))
