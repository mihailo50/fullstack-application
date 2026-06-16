# Application via CI

A small Python script (`apply.py`) builds a canonical, HMAC-SHA256-signed JSON
payload and POSTs it from a GitHub Actions run. `test_apply.py` verifies the
signing offline against a published test vector before any submission is made.

## Configure

Edit the three values under `env:` in `.github/workflows/submit.yml`:

- `APPLICANT_NAME`
- `APPLICANT_EMAIL`
- `RESUME_LINK` (a public URL: hosted CV/PDF, LinkedIn, or profile page)

`repository_link` and `action_run_link` are derived automatically from the
GitHub Actions environment, so they always point at the run that submitted.

## Run

Push to `main`, or trigger the workflow manually from the Actions tab. The job
prints the canonical body, signature, and the submission receipt in its logs.

## Verify locally (optional, offline)

```bash
python test_apply.py
```
