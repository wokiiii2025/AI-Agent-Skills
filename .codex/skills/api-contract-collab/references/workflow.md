# Workflow


## Agent Session Entry

At the start of a frontend/backend API collaboration session, run `python scripts/next_actions.py`. The output tells the agent which shared issue needs action, why, and the exact script command to run next. This avoids scanning every issue manually.

## Backup Rule

Before migrations, bulk deletes, imports, or dashboard storage changes, run `python scripts/backup_db.py`. Server backups are written under `data/backups/` and `latest.json` points to the newest backup.

## First-Use Identity Confirmation

Before creating issues, uploading reports, uploading OpenAPI snapshots, or updating a shared issue, confirm whether this agent is acting as `frontend` or `backend`. After the user answers, run `scripts/configure_identity.py` to write the identity and shared API key into Skill-local `.local/config.json`. If neither `API_COLLAB_SIDE` nor Skill-local `side` is set, stop and ask the user; do not infer it from repository name, current task, or issue owner.

## Non-Autonomous Execution Rule

This skill coordinates work; it does not authorize automatic code changes. Agents may collect evidence, inspect related code, compare OpenAPI, and upload reports without confirmation. Before changing backend or frontend code, the responsible agent must present a concise plan to the user and wait for explicit confirmation.

## Shared Issue Principle

One API problem has one shared issue ID. Frontend and backend append role-scoped events to that same issue. The dashboard, JSON API, and exported Markdown all show the same timeline.



## Identity-Specific Workflow Matrix

| Identity | Starts with | May create/report | Must inspect before proposal | Needs user confirmation before code change | Resolves/verifies | Special rule |
| --- | --- | --- | --- | --- | --- | --- |
| `frontend` | `python scripts/next_actions.py` | API problems, requirements, suggestions, frontend release summaries | Frontend API service, DTO/mapper/tests, Bruno, current OpenAPI/real response | Yes, for frontend-owned code changes | Verifies `backend_resolved`, closes after evidence | Data-structure reports must align to backend current verified response first. |
| `backend` | `python scripts/next_actions.py` | Backend-found API/Swagger issues and comments | Related backend code plus current OpenAPI output | Yes, after `propose_fix.py` and explicit approval | Resolves backend work with test/deploy/OpenAPI evidence | Proposed plan first; implementation second. |
| `user/owner` | Dashboard or issue detail | Comments, approval, block/reopen decisions | Proposal note and evidence | Gives approval | Confirms direction; final close still follows verification | Decision history remains on the same shared issue. |

## Requirement And Suggestion Reports

Use `--type requirement` for concrete API-scoped product requirements and `--type suggestion` for lower-priority API collaboration suggestions. Both still require affected endpoint(s), observable expected outcome, impact, and close criteria.

Frontend reports involving data structures must first align to the backend current verified response structure before describing gaps or requested outcomes.

## Release Summary Rule

After each frontend version release, the frontend agent uploads one API integration summary containing backend API total, integrated API count, problematic API count, version label, note, and update time.

## Frontend Agent

1. Run `python scripts/next_actions.py` first, then pull current OpenAPI JSON.
2. Compare against frontend API implementation, DTOs, tests, and Bruno requests.
3. For each actionable mismatch, create one shared issue with `reporter_side=frontend` and the correct `owner_side`.
4. Use `--owner backend` when backend/Swagger must change; use `--owner frontend` when frontend must adapt.
5. Keep the initial issue implementation-neutral: state verified behavior, requirement, evidence, impact, and black-box acceptance outcomes. Leave API shape and implementation planning to the responsible side.
6. If frontend-owned code changes are needed, inspect local code first, produce a plan, and ask the user to confirm before editing.
7. After backend marks `backend_resolved`, verify using typecheck/tests/smoke/manual evidence.
8. Run `scripts/verify_issue.py --result passed` after successful verification, then `scripts/close_issue.py` when no more action remains. Use `--result failed` to reopen when verification fails.

## Backend Agent Lightweight Flow

1. Run `python scripts/next_actions.py` first.
2. Read the shared issue and inspect only related backend code plus current OpenAPI output.
3. Run `scripts/propose_fix.py` to set `backend_proposed` with one concise note containing: finding, affected endpoint, planned change, validation command, and OpenAPI impact.
4. Ask the user for explicit confirmation before modifying backend code, database migrations, Swagger annotations, deployment config, or generated artifacts.
5. After confirmation, run `scripts/approve_issue.py` and `scripts/start_issue.py`, make backend-owned changes, and run checks related to the issue.
6. Upload a new OpenAPI snapshot only when the contract output changes: path, method, request parameter, response field, error code, auth rule, or Swagger annotation.
7. Run `scripts/resolve_issue.py` with deployment/version/test evidence.
8. If frontend adaptation is required, keep the same issue and set/leave `--owner frontend`; do not create a duplicate frontend-side issue for the same problem.

## Required Status Flow

```text
open -> backend_proposed -> approved -> backend_doing -> backend_resolved -> frontend_verifying -> frontend_verified -> closed
backend_resolved -> reopened
open -> blocked
blocked -> backend_proposed
```

Meaning:

- `backend_proposed` / `frontend_proposed`: related code/OpenAPI inspected; finding and fix plan recorded; waiting for user confirmation.
- `approved`: user confirmed the plan; implementation can start.
- `backend_doing` / `frontend_doing`: confirmed implementation is in progress.
- `backend_resolved` / `frontend_resolved`: responsible side finished and attached deployment/test evidence.
- `frontend_verified` / `backend_verified`: verifying side confirmed the result.
- `closed`: no more action.

## Closing Rule

The side that reported or is responsible for acceptance performs verification. The responsible side marks resolved; the verifying side marks verified and closes after evidence is recorded.

## Storage Rule

- SQLite is the source of truth: `data/api-collab.db`.
- Markdown files under `data/exports/issues/*.md` are generated read-only exports for humans and agents.
- Imported historical `frontend/*` and `backend/*` files are read-only traceability attachments; agents must create and update issues through the strict shared issue API.

