# Issue Schema

Each issue is a shared SQLite entity with generated Markdown export.

## Metadata

```json
{
  "id": "API-YYYYMMDD-NNN",
  "project": "movie-app",
  "reporter_side": "frontend",
  "owner_side": "backend",
  "status": "open",
  "priority": "P1",
  "type": "contract-mismatch",
  "endpoint": "GET /api/member/info",
  "endpoints": ["GET /api/member/info"],
  "endpointCount": 1,
  "title": "Short title",
  "createdAt": "YYYY-MM-DD HH:mm:ss",
  "updatedAt": "YYYY-MM-DD HH:mm:ss"
}
```

## Strict Structured Body

Issue creation is strict. `POST /api/issues` must include these body fields in `meta`; the server rejects the request when any field is empty:

```json
{
  "description": "Verified current behavior or product requirement.",
  "expected": "Observable expected outcome.",
  "actual": "Observed current behavior.",
  "evidence": "OpenAPI/real response/test/report evidence. Use a short text summary plus uploaded report links when needed.",
  "impact": "Affected frontend/backend workflow, screen, mapper, smoke path, or release risk.",
  "closeCriteria": "Black-box verification criteria required to close the issue."
}
```

Do not rely on generated Markdown sections, timeline notes, proposed notes, resolved notes, Telegram messages, or later comments to populate these fields. Timeline events are for lifecycle history only. The issue body is the source of truth for the problem statement.

## API Scope

Issues are only single-API or multi-API reports. Use `endpoints` for both cases:

- Single API: `endpoints` contains one item.
- Multi API: `endpoints` contains two or more related APIs.

Do not add unrelated environment/module categories to this Skill. For missing capabilities, reference the currently affected endpoint when one exists. Do not create a hypothetical endpoint name merely to describe a requirement.

## Time Format

All human-readable timestamps use the runtime local timezone format: `YYYY-MM-DD HH:mm:ss`. Docker deployment sets `TZ=Asia/Shanghai`. Do not emit ISO `T` / `Z` timestamps in issues or reports.

## Status

- `open`: newly reported.
- `backend_proposed` / `frontend_proposed`: responsible side inspected related code/OpenAPI and recorded a proposal; waiting for explicit user confirmation.
- `approved`: user confirmed the plan; implementation can start.
- `backend_doing` / `frontend_doing`: implementation in progress.
- `backend_resolved` / `frontend_resolved`: responsible side finished and attached deployment/test evidence.
- `frontend_verifying` / `backend_verifying`: verifying side is checking the result.
- `frontend_verified` / `backend_verified`: verifying side confirmed the result.
- `closed`: no more action.
- `blocked`: waiting for named external input.
- `reopened`: verification failed or scope needs another pass.

## Event Types

- `created`
- `commented`
- `proposed`
- `approved`
- `started`
- `resolved`
- `verified`
- `closed`
- `reopened`
- `blocked`
- `edited`

## Types

- `contract-mismatch`
- `swagger-outdated`
- `missing-endpoint`
- `missing-field`
- `wrong-status-code`
- `auth-token`
- `frontend-adaptation`
- `backend-bug`
- `test-data`
- `openapi-diff`
- `feature-request`
- `requirement`
- `suggestion`


## Frontend Data Structure Rule

When frontend reports an issue involving data structures, field meanings, enum values, pagination, resource card fields, CMS module shape, or DTO mapping, it must first document the backend current verified response structure and align the request to that structure whenever possible. The issue may describe UI requirements and observable gaps, but should not invent a replacement schema when the backend existing structure can express the requirement.

## Reporter Content Boundary

An issue created by the reporting side contains only:

- verified current behavior or contract evidence;
- the concrete user or product requirement;
- observable expected behavior;
- impact;
- black-box close criteria.

It excludes proposed paths, methods, parameter or field names, DTOs, payload examples, persistence/transaction design, code-level steps, batch limits, and other implementation choices. Those choices belong to the responsible side's later proposed event after code and OpenAPI inspection.

`Expected` states outcomes. `Close Criteria` states externally verifiable cases without dictating the implementation.

## Markdown Sections

Generated Markdown exports use these headings:

1. Summary
2. Related APIs
3. Description
4. Expected
5. Actual
6. Evidence
7. Impact
8. Close Criteria
9. Timeline
