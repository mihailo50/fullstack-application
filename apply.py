#!/usr/bin/env python3
"""Submit a job application via a signed POST.

Designed to run inside CI (e.g. GitHub Actions). It builds a canonical,
HMAC-SHA256-signed JSON payload and POSTs it to the employer's endpoint,
then prints the returned receipt so it is visible in the CI run logs.

Applicant fields come from environment variables (set in the workflow):
    APPLICANT_NAME, APPLICANT_EMAIL, RESUME_LINK
The repository_link and action_run_link are derived from the standard
GitHub Actions variables (GITHUB_SERVER_URL, GITHUB_REPOSITORY, GITHUB_RUN_ID),
so they always point at the exact run that performed the submission.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.request

SUBMISSION_URL = "https://b12.io/apply/submission"
# Public per the application instructions, but handled as a signing key.
SIGNING_SECRET = b"hello-there-from-b12"

# CV committed alongside this script; RESUME_LINK="auto" links to its raw URL.
RESUME_FILENAME = "Mihailo_Cvetkovic_CV_2026.pdf"


def canonical_body(payload: dict) -> bytes:
    """Return the payload as compact, key-sorted JSON with non-ASCII escaped.
    """
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")


def signature(body: bytes) -> str:
    """Return 'sha256=<hex>' HMAC-SHA256 of the raw body using the signing secret."""
    digest = hmac.new(SIGNING_SECRET, body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def iso8601_now() -> str:
    """Current UTC time as an ISO 8601 timestamp with millisecond precision + 'Z'."""
    now = dt.datetime.now(dt.timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def build_payload() -> dict:
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repo = os.environ.get("GITHUB_REPOSITORY", "your/repository")
    run_id = os.environ.get("GITHUB_RUN_ID", "run_id")

    repository_link = os.environ.get("REPOSITORY_LINK") or f"{server}/{repo}"
    action_run_link = (
        os.environ.get("ACTION_RUN_LINK")
        or f"{server}/{repo}/actions/runs/{run_id}"
    )

    # Required applicant fields — fail loudly if missing so we never submit blanks.
    try:
        name = os.environ["APPLICANT_NAME"]
        email = os.environ["APPLICANT_EMAIL"]
    except KeyError as missing:
        raise SystemExit(f"Missing required environment variable: {missing}")

    # resume_link: an explicit URL, or "auto" to link the CV committed in this repo.
    resume_link = (os.environ.get("RESUME_LINK") or "auto").strip()
    if resume_link.lower() == "auto":
        branch = os.environ.get("GITHUB_REF_NAME", "main")
        if server.endswith("github.com"):
            resume_link = f"https://raw.githubusercontent.com/{repo}/{branch}/{RESUME_FILENAME}"
        else:
            resume_link = f"{server}/{repo}/-/raw/{branch}/{RESUME_FILENAME}"

    return {
        "timestamp": iso8601_now(),
        "name": name,
        "email": email,
        "resume_link": resume_link,
        "repository_link": repository_link,
        "action_run_link": action_run_link,
    }


def submit(payload: dict) -> int:
    body = canonical_body(payload)
    sig = signature(body)
    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": sig,
    }

    print("Canonical body:", body.decode("utf-8"))
    print("X-Signature-256:", sig)

    request = urllib.request.Request(
        SUBMISSION_URL, data=body, headers=headers, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response.status
            text = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        print(f"Submission failed: HTTP {error.code}\n{detail}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"Submission failed: {error}", file=sys.stderr)
        return 1

    print(f"HTTP {status}")
    print("Response:", text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        print("Could not parse JSON response.", file=sys.stderr)
        return 1

    if status == 200 and data.get("success"):
        print(f"RECEIPT: {data.get('receipt')}")
        return 0

    print("Submission was not successful.", file=sys.stderr)
    return 1


def main() -> int:
    return submit(build_payload())


if __name__ == "__main__":
    sys.exit(main())
