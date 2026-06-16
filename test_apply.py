#!/usr/bin/env python3
"""Self-test: verify canonicalization + HMAC against the employer's published vector.

Runs offline (no network). The CI workflow runs this BEFORE the real submission,
so a broken signing implementation fails fast instead of POSTing bad data.
"""
import apply

# Example payload and expected outputs published in the application instructions.
EXAMPLE = {
    "timestamp": "2026-01-06T16:59:37.571Z",
    "name": "Your name",
    "email": "you@example.com",
    "resume_link": "https://pdf-or-html-or-linkedin.example.com",
    "repository_link": "https://link-to-github-or-other-forge.example.com/your/repository",
    "action_run_link": "https://link-to-github-or-another-forge.example.com/your/repository/actions/runs/run_id",
}

EXPECTED_CANONICAL = (
    '{"action_run_link":"https://link-to-github-or-another-forge.example.com/your/repository/actions/runs/run_id",'
    '"email":"you@example.com","name":"Your name",'
    '"repository_link":"https://link-to-github-or-other-forge.example.com/your/repository",'
    '"resume_link":"https://pdf-or-html-or-linkedin.example.com",'
    '"timestamp":"2026-01-06T16:59:37.571Z"}'
)

EXPECTED_SIGNATURE = (
    "sha256=c5db257a56e3c258ec1162459c9a295280871269f4cf70146d2c9f1b52671d45"
)


def test_canonical_body() -> None:
    actual = apply.canonical_body(EXAMPLE).decode("utf-8")
    assert actual == EXPECTED_CANONICAL, f"canonical mismatch:\n{actual}"


def test_signature() -> None:
    actual = apply.signature(apply.canonical_body(EXAMPLE))
    assert actual == EXPECTED_SIGNATURE, f"signature mismatch: {actual}"


if __name__ == "__main__":
    test_canonical_body()
    test_signature()
    print("OK: canonicalization and HMAC-SHA256 match the published test vector.")
