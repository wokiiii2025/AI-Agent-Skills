# OpenAPI Diff Standard

This skill uses `oasdiff` as the mandatory OpenAPI comparison engine.

## Required commands

Every old/new OpenAPI comparison must generate all three reports:

```bash
oasdiff summary old.json new.json --format json
oasdiff diff old.json new.json
oasdiff breaking old.json new.json
```

`scripts/generate_diff_report.py` wraps these commands and uploads one Markdown report.

## Validation policy

Use the policy wrapper rather than invoking `oasdiff validate` as a hard gate directly:

```bash
python scripts/validate_openapi.py current.json
```

The wrapper preserves `oasdiff` findings and applies one project policy exception:

- A `spec-validation-error` that only says a Schema component identifier containing Chinese characters is outside the OpenAPI identifier charset is reported as a recorded validation warning.
- This exception does not create an API issue, block frontend alignment, increase the problematic endpoint count, or fail validation by itself.
- Invalid/unresolved `$ref`, malformed paths, invalid parameter/request/response schemas, and every other error-level finding remain blocking.
- Warning/info findings such as example quality remain visible and follow their native non-blocking severity unless they reveal a verified runtime contract mismatch.

## Failure rule

If `oasdiff` is missing, do not generate a hand-written substitute report. Install `oasdiff`, then rerun the workflow.

## Classification rule

- `oasdiff breaking` output means the issue priority is at least `P1` unless the user explicitly downgrades it.
- Removed paths, removed response fields, required-field changes, auth changes, enum narrowing, and response envelope changes must be recorded as contract issues.
- Endpoint-only scans are allowed only as coverage reports; they do not replace `oasdiff` old/new comparison.
