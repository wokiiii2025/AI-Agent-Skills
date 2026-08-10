---
name: api-contract-collab
description: Frontend-backend API contract collaboration for Swagger/OpenAPI driven development. Use when Codex needs to compare OpenAPI changes, report API integration issues, update TODO-like issue status, upload markdown/json reports through an HTTP API, or coordinate frontend/backend API handoff with side-specific write permissions.
---

# API Contract Collab

## Version

Current Skill version: `0.5.5`. Latest metadata: `http://162.250.126.10:38970/shared/api-contract-collab-latest.json`. Versioned package: `api-contract-collab-0.5.5.zip`.

## Release Metadata Rule

`VERSION.json` inside the Skill package records install-time metadata only and must not contain the ZIP file `sha256` or `bytes`; those fields belong only to the server latest metadata (`api-contract-collab-latest.json`). This avoids self-referential ZIP hashes and keeps macOS/Linux update verification stable. `scripts/check_update.py` verifies the downloaded ZIP against the server latest metadata before installing.

## Agent Installation

For cross-platform agent installation, read `references/agent-install-guide.md`. It contains the Skill download URL, install commands, identity/API key configuration, and required API development standards.

## Purpose

Use this skill for lightweight frontend-backend API collaboration. It standardizes how agents compare Swagger/OpenAPI contracts, report API integration issues, move a shared issue through frontend/backend handoff, and publish Markdown/JSON artifacts through HTTP API upload.

## Permission Model

- A single shared `API_COLLAB_TOKEN` authenticates both frontend and backend agents.
- Issues are shared entities stored by issue ID; frontend and backend append role-scoped events to the same issue.
- `API_COLLAB_SIDE=frontend` may create issues, add frontend evidence/comments, verify frontend-facing fixes, reopen failed verification, and close issues after verification.
- `API_COLLAB_SIDE=backend` may create issues, add backend analysis/comments, submit proposed fixes, mark backend work started/resolved, and update backend evidence.
- Both sides may read all shared issues, reports, OpenAPI snapshots, and exported Markdown.
- Do not edit the other side's implementation details in an issue. The reporting side describes observable behavior and acceptance criteria; the responsible side records its own proposal after inspection.
- Use HTTP API scripts only; do not SSH into the server or manually edit server files during normal issue workflow.

## Required Environment

Set these values before using scripts. Environment variables override Skill-local config:

```bash
API_COLLAB_BASE_URL="http://HOST:PORT"
API_COLLAB_TOKEN="SHARED_API_TOKEN"
API_COLLAB_SIDE="frontend" # or backend
```

Skill-local config is stored at `.local/config.json` inside this Skill folder. After the first identity confirmation, write identity and API key into the Skill:

```bash
python scripts/configure_identity.py --side frontend --base-url http://HOST:PORT --token-stdin
python scripts/configure_identity.py --side backend --base-url http://HOST:PORT --token-stdin
python scripts/configure_identity.py --show
```

Use `--token-stdin` or `--token-prompt` for the shared API key. `--token` also works, but it can remain in shell history.

Additional environment:

```bash
API_COLLAB_PROJECT="movie-app"
API_COLLAB_OPENAPI_URL="http://162.250.126.10:8080/v3/api-docs"
```


## First-Use Identity Confirmation

Before the first write operation in a thread or workspace, confirm which side this agent represents:

```text
Please confirm this agent identity for API collaboration: frontend or backend?
```

After confirmation, set:

```bash
API_COLLAB_SIDE="frontend" # for frontend agent
API_COLLAB_SIDE="backend"  # for backend agent
```

If `API_COLLAB_SIDE` and Skill-local `side` are both missing, scripts stop and instruct the agent to ask the user. After the user answers, run `scripts/configure_identity.py` so the Skill remembers the identity and shared API key for future calls. Do not guess the side.

## Core Workflow


### Ask the Skill for next actions

At the start of an API collaboration session, run:

```bash
python scripts/next_actions.py
```

The command returns the current side, issues that need this agent, the reason, and the exact next script command to run. This is the preferred entry point for AI agents continuing work from prior issues.

### Create a server SQLite backup

Before risky cleanup, migration, or bulk edits, run:

```bash
python scripts/backup_db.py --note "before bulk issue cleanup"
```

### Report an API issue

1. Confirm the current OpenAPI JSON, real response, or frontend code mismatch.
2. Create a structured issue Markdown using `scripts/report_issue.py`.
3. The script uploads structured metadata to the shared issue database and exports a Markdown copy.
4. Include endpoint, priority, issue type, expected behavior, actual behavior, evidence, and close criteria.
5. Report only the verified problem or concrete product requirement. Describe observable current and expected behavior, impact, evidence, and black-box acceptance criteria. Do not prescribe the responsible side's route design, HTTP method, parameter names, DTO shape, database transaction, implementation steps, limits, or code changes in the issue body.
6. For a missing capability, set `--endpoint` to the currently affected API when known; do not invent a future endpoint. The responsible side proposes the implementation after inspection through the normal `proposed` status flow.
7. When the frontend issue mentions data structures, field semantics, enum values, paging shape, resource cards, CMS modules, or DTO mapping, it must first describe and align to the backend current verified response structure. Frontend may propose UI needs and observable gaps, but should not invent a replacement schema when an existing backend structure can express the requirement.

```bash
python scripts/report_issue.py \
  --title "GET /api/member/info response missing avatar" \
  --endpoint "GET /api/member/info" \
  --owner backend \
  --priority P1 \
  --type contract-mismatch \
  --description "Swagger says avatarUrl exists, real response is missing it." \
  --expected "avatarUrl returned as string or Swagger removes it." \
  --actual "avatarUrl absent in real response." \
  --evidence-file tmp/member-info-response.json \
  --impact "Member profile screen cannot render avatar consistently without a verified contract." \
  --close-criteria "OpenAPI and real response consistently include avatarUrl, or OpenAPI removes it and frontend mapper is updated."
```

`--description`, `--expected`, `--actual`, `--evidence` or `--evidence-file`, `--impact`, and `--close-criteria` are required so the issue body is persisted as structured data, not timeline notes.

For requirements or suggestions, use `--type requirement` or `--type suggestion`. Keep them API-scoped with one or more affected endpoints.

For multi-API reports, repeat `--endpoint`:

```bash
python scripts/report_issue.py \
  --title "登录态相关接口字段不一致" \
  --endpoint "POST /api/member/login" \
  --endpoint "POST /api/member/refresh" \
  --endpoint "GET /api/member/info" \
  --owner backend \
  --priority P1 \
  --type contract-mismatch \
  --description "这些接口的 token/会员信息契约需要一起对齐。" \
  --expected "登录、刷新和会员信息接口的 token/会员字段语义一致且可由前端黑盒验证。" \
  --actual "当前三个接口的 token/会员字段表现不一致，前端无法稳定映射。" \
  --evidence "OpenAPI 与真实联调响应字段语义不一致。" \
  --impact "登录态恢复、会员信息展示和 token refresh 队列可能出现错误映射。" \
  --close-criteria "三个接口的 OpenAPI、真实响应和前端 smoke/mapper 验证均一致。"
```

### Shared issue lifecycle

Use one shared issue ID from report to backend processing, frontend verification, and close.

```bash
python scripts/propose_fix.py --id API-20260722-001 --note "Backend inspected controller and OpenAPI output; proposed fix is ..."
python scripts/approve_issue.py --id API-20260722-001 --note "User confirmed the proposed plan."
python scripts/start_issue.py --id API-20260722-001 --note "Implementation started."
python scripts/resolve_issue.py --id API-20260722-001 --note "Swagger updated and endpoint redeployed."
python scripts/verify_issue.py --id API-20260722-001 --result passed --note "Frontend verified with real API response."
python scripts/close_issue.py --id API-20260722-001 --note "Closed after frontend verification."
```

Preferred statuses:

```text
open -> backend_proposed -> approved -> backend_doing -> backend_resolved -> frontend_verifying -> frontend_verified -> closed
backend_resolved -> reopened
open -> blocked
blocked -> backend_proposed
```

### Identity-specific execution workflow

#### Frontend identity (`API_COLLAB_SIDE=frontend`)

1. Start every API collaboration session with `python scripts/next_actions.py`.
2. When reporting an API problem, requirement, or suggestion, verify the current OpenAPI JSON, real response, frontend DTO/mapper/test, or Bruno evidence first.
3. For data-structure, field, enum, paging, card, CMS module, or DTO mapping topics, describe the backend current verified response structure before describing the frontend gap or requested outcome.
4. Create one shared issue for a single API or one related multi-API group. Use `--owner backend` when backend/Swagger behavior must change, and `--owner frontend` when frontend adaptation is responsible.
5. Keep the initial report implementation-neutral: observable behavior, impact, evidence, expected outcome, and close criteria only.
6. For frontend-owned changes, inspect frontend code first, present a concise proposed plan to the user, wait for confirmation, then edit code and record progress on the same issue.
7. For `backend_resolved` issues, verify with real API evidence and relevant frontend checks. Run `verify_issue.py --result passed` then `close_issue.py`; run `verify_issue.py --result failed` with evidence when the issue reopens.
8. After each frontend release, run `report_summary.py` to update backend API total, integrated count, problematic count, version, note, and update time.

#### Backend identity (`API_COLLAB_SIDE=backend`)

1. Start every API collaboration session with `python scripts/next_actions.py`.
2. For backend-owned `open` or `reopened` issues, inspect the related backend code and current OpenAPI output first.
3. Submit exactly one concise proposed plan with `propose_fix.py`, including finding, affected endpoint(s), intended contract/behavior impact, validation command, and deployment/OpenAPI impact.
4. Wait for explicit user confirmation before editing backend controllers, services, DTOs, Swagger annotations, database migrations, generated OpenAPI output, deployment files, or configuration.
5. After confirmation, record `approve_issue.py` and `start_issue.py`, implement the confirmed backend change, run focused checks, and upload a new OpenAPI snapshot when the contract output changes.
6. Finish with `resolve_issue.py` and include deployment/version/test evidence. The frontend then verifies and closes the same shared issue.
7. If frontend adaptation is also required, keep the same issue and move or leave ownership to `frontend`; do not create a duplicate issue for the same problem.

#### User / owner confirmation role

1. Review `backend_proposed` or `frontend_proposed` notes.
2. Approve the plan before implementation begins, or add a comment/reopen/block note on the same issue when the plan needs adjustment.
3. Treat the dashboard issue timeline as the shared source for decision history.

### Edit and delete issues

Issue edit/delete APIs target the shared issue ID. Use delete only for cleanup/test records after a backup:

```bash
python scripts/edit_issue.py --id API-20260722-001 --title "Updated title" --endpoint "GET /api/member/info" --note "Clarified scope."
python scripts/delete_issue.py --id API-20260722-001 --yes
```

### Upload release API integration summary

After each frontend release, upload the current integration summary:

```bash
python scripts/report_summary.py \
  --backend-total 104 \
  --integrated 74 \
  --problematic 30 \
  --version "v1.2.3" \
  --note "Release API coverage summary"
```

The server records `updatedAt` and keeps `frontend/summary/latest.json` plus historical summary files.

### Upload OpenAPI snapshot

```bash
python scripts/upload_openapi.py --file tmp/openapi-current.json --label swagger-v3.9.2
```

### Generate and upload mandatory oasdiff OpenAPI diff

```bash
python scripts/generate_diff_report.py --old old.json --new new.json --upload
```


## Human Confirmation Gate

This skill is not a full-auto execution system. Backend and frontend agents may inspect code, compare specs, and upload findings automatically. Before changing code or deployment configuration, the agent must:

1. Inspect the relevant code and contract evidence.
2. Upload or present a concise proposed-fix note that includes the inspection result.
3. Ask the user for explicit confirmation.
4. Proceed only after confirmation, then record implementation evidence.

Backend-specific lightweight rule: backend agents inspect only related backend code and current OpenAPI output, submit one `backend_proposed` note with `scripts/propose_fix.py`, then confirm with the user before changing controllers, services, DTOs, Swagger annotations, database migrations, generated OpenAPI output, or deployment files.

## Issue Rules

Issues are single-API or multi-API reports only. Use one `--endpoint` for a single API and repeated `--endpoint` arguments for multiple related APIs.

Issue creation uses a strict structured schema. New issues must have non-empty `description`, `expected`, `actual`, `evidence`, `impact`, and `closeCriteria` in the issue body. Do not depend on generated Markdown, timeline notes, proposed/resolved/verified comments, Telegram notifications, or Web comments to fill these fields later. If any required body field is missing, the server rejects the issue.

Reporter/responsible-side boundary:

- The reporting side states the problem or requirement and supplies evidence plus outcome-based acceptance criteria.
- The reporting side does not include a proposed API path, method change, field/parameter name, request/response structure, database design, transaction strategy, code location, or implementation plan.
- `expected` describes user-visible or API-observable outcomes, not how to build them.
- `closeCriteria` must be verifiable from black-box behavior and must remain implementation-neutral.
- The responsible side inspects its code and OpenAPI, then records its own implementation proposal in a `proposed` update and waits for user confirmation.



Read `references/issue-schema.md` before creating or updating issue formats. Read `references/workflow.md` when executing a full frontend-backend handoff or closing issues.

Supported issue types include `contract-mismatch`, `swagger-outdated`, `missing-endpoint`, `missing-field`, `wrong-status-code`, `auth-token`, `frontend-adaptation`, `backend-bug`, `test-data`, `openapi-diff`, `feature-request`, `requirement`, and `suggestion`.

Minimum fields:

- `id`, `reporter_side`, `status`, `owner_side`, `priority`, `type`
- `endpoint`, `title`, `createdAt`, `updatedAt`
- `endpoints`, `endpointCount`, `description`, `expected`, `actual`, `evidence`, `impact`, `closeCriteria`

## OpenAPI Comparison Rules

Read `references/openapi-diff.md` before comparing old/new OpenAPI files.

- `oasdiff` is mandatory for old/new OpenAPI comparisons.
- Generate `summary`, full `diff`, and `breaking` output for every comparison.
- Run `scripts/validate_openapi.py SPEC` for policy-aware validation. Schema component identifiers containing Chinese characters are reported as validation warnings for this workflow: record their count, but do not create an issue, block alignment, or fail the task solely for those findings.
- Continue to treat invalid or unresolved `$ref`, malformed paths, invalid parameter/request/response schemas, and other non-ignored validation errors as actionable failures.
- If `oasdiff` is missing, stop and install it; do not produce a substitute hand-written diff.
- OpenAPI JSON is the contract source; do not use Swagger UI screenshots as the source of truth.
- If no historical snapshot exists, run coverage checks and upload a coverage report, then save the current OpenAPI as the next baseline.

## Script Directory

- `scripts/api_collab_client.py`: shared HTTP client and issue renderer.
- `scripts/configure_identity.py`: save first-use identity, base URL, project, and shared API key into Skill-local `.local/config.json`.
- `scripts/report_issue.py`: create and upload Markdown/JSON issue.
- `scripts/backup_db.py`: creates a server-side SQLite backup before risky migration or cleanup.
- `scripts/next_actions.py`: lists current-side issue actions with suggested next commands for AI agents.
- `scripts/check_update.py`: checks latest version metadata and can install a newer Skill package while preserving `.local` identity config.
- `scripts/publish_skill_release.py`: publishes Skill release metadata to the server and sends Telegram update notification.
- `scripts/propose_fix.py`: responsible side submits a proposed fix after code/contract inspection.
- `scripts/approve_issue.py`: records explicit user approval for the proposed plan.
- `scripts/start_issue.py`: records that the current side started implementation.
- `scripts/resolve_issue.py`: records that the current side completed implementation.
- `scripts/verify_issue.py`: records verification passed or reopens on failed verification.
- `scripts/close_issue.py`: closes the shared issue after verification.
- `scripts/comment_issue.py`: appends a role-scoped comment to the shared issue.
- `scripts/edit_issue.py`: edit shared issue metadata by issue ID and append a role-scoped note.
- `scripts/delete_issue.py`: physically delete a shared issue by issue ID for cleanup/test records after backup.
- `scripts/report_summary.py`: upload release API integration summary with backend total, integrated count, problematic count, version, note, and updated time.
- `scripts/upload_openapi.py`: upload OpenAPI JSON snapshot.
- `scripts/generate_diff_report.py`: run mandatory `oasdiff summary`, `oasdiff diff`, and `oasdiff breaking`, then upload the Markdown report.
- `scripts/validate_openapi.py`: run `oasdiff validate` while classifying Chinese Schema identifier findings as recorded validation warnings.


## Web Dashboard Issue Handling

The Web dashboard includes compact action cards for:

- awaiting user approval
- backend todo
- frontend verification
- total non-closed issues

Open `/issues/{id}` for the HTML detail page. It shows summary metadata, related APIs, issue body fields, timeline, Markdown/JSON links, and Web quick actions. Web quick actions are intended for lightweight owner/user decisions and review notes; agents should still use scripts for normal automated issue workflow.

## Backup And Google Drive

`scripts/backup_db.py` creates a server-side SQLite backup. Google Drive backup uses OAuth URL authorization from the protected Web dashboard page `/settings/google-drive`. Save OAuth Client ID/Secret and folder ID, click Connect Google Drive, approve in Google, and the server stores the refresh token under `/data/secrets`. Keep OAuth Client Secret and tokens out of the Skill package and source repo.

## Web Login And Language

The Web dashboard supports a remember-key login option backed by browser localStorage. Language is managed from the dashboard header and saved server-side/cookie. Skill scripts support `API_COLLAB_LANG=zh-CN|en` or Skill-local `lang` configured by `scripts/configure_identity.py --lang zh-CN|en`. Dashboard language selection is stored server-side/cookie. Skill scripts and agent-facing prompts support `API_COLLAB_LANG=zh-CN|en` or Skill-local `lang`; agents should answer user-facing API collaboration prompts, next-action summaries, confirmation prompts, and status explanations in that configured language.


## Server Upgrade Notification Rule

Standalone backend/service deployments must not send Telegram notifications. Telegram Skill update notifications are only for real Skill package releases that agents need to install. When deploying server-only changes, update the server and public package files directly; do not call `scripts/publish_skill_release.py` or `POST /api/skill-release` unless the Skill package version is intentionally released.

## Telegram Notification Channel

When the server is configured with `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, key issue lifecycle events are pushed to the Telegram channel. Treat Telegram as the timely notification layer and the Web dashboard/SQLite issue timeline as the source of truth.

Agents should still update issues through the HTTP API scripts. Do not replace issue evidence, OpenAPI snapshots, diff reports, or close criteria with Telegram messages only.

Notification-worthy events include issue creation, proposed plan, approval, start, resolve, verify, close, reopen, block, comments, frontend release summary, OpenAPI snapshot, report upload, and Skill release update.

Skill release updates should be announced with `scripts/publish_skill_release.py` after packaging/uploading a new version.

Telegram batching is enabled through `TELEGRAM_BATCH_WINDOW_SECONDS` and `TELEGRAM_BATCH_MAX_ITEMS`. Issue lifecycle events inside the batch window are merged into one summary message; `TELEGRAM_URGENT_IMMEDIATE=false` keeps reopened/blocked/failed verification events batched as well.

## Server Contract

The server exposes:

- `GET /` dashboard
- `GET /api/issues`
- `POST /api/backup`
- `POST /api/skill-release`
- `GET /api/next-actions`
- `GET /api/skill-release`
- `GET /api/issues/{id}`
- `POST /api/issues`
- `POST /api/issues/{id}/propose`
- `POST /api/issues/{id}/approve`
- `POST /api/issues/{id}/start`
- `POST /api/issues/{id}/resolve`
- `POST /api/issues/{id}/verify`
- `POST /api/issues/{id}/close`
- `POST /api/issues/{id}/reopen`
- `POST /api/issues/{id}/comments`
- `PUT/PATCH /api/issues/{id}`
- `DELETE /api/issues/{id}`
- `POST /api/openapi`
- `POST /api/reports`

Write requests must include:

```text
Authorization: Bearer <shared-api-token>
X-Api-Collab-Side: frontend|backend
Content-Type: application/json
```


