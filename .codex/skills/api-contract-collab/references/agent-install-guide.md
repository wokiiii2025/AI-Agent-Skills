# api-contract-collab Agent Install Guide

Current version: `0.5.5`
Latest metadata: `http://162.250.126.10:38970/shared/api-contract-collab-latest.json`
Versioned package: `http://162.250.126.10:38970/shared/api-contract-collab-0.5.5.zip`

Server-only upgrades do not send Telegram notifications; only Skill package releases notify Telegram.

This guide is for frontend and backend AI agents. Install this Skill before API integration work, then follow its workflow for every API development, contract comparison, issue report, release summary, and status update.

## Download

Skill package:

```text
http://162.250.126.10:38970/shared/api-contract-collab-0.5.5.zip
```

Dashboard:

```text
http://162.250.126.10:38970
```

The dashboard requires login with the shared API key. This install guide and the Skill zip are public so agents can install the Skill before they have a saved local identity.


## Version discovery and update

The server publishes latest Skill metadata at:

```text
http://162.250.126.10:38970/shared/api-contract-collab-latest.json
```

The current versioned package is:

```text
http://162.250.126.10:38970/shared/api-contract-collab-0.5.5.zip
```

After installation, agents can check and update themselves without touching project files:

```bash
python3 scripts/check_update.py
python3 scripts/check_update.py --install
```

`check_update.py --install` preserves `.local/config.json` so the saved side and API key remain available after update.

Always install from the versioned package listed in latest metadata so agents can detect and apply updates deterministically.

## Install location

Install into the Codex skills directory.

Linux / macOS:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
curl -fL "http://162.250.126.10:38970/shared/api-contract-collab-0.5.5.zip" -o /tmp/api-contract-collab.zip
python3 - <<'PY'
import os, zipfile, pathlib, shutil
home = pathlib.Path(os.environ.get("CODEX_HOME", pathlib.Path.home() / ".codex"))
skills = home / "skills"
target = skills / "api-contract-collab"
if target.exists():
    shutil.rmtree(target)
with zipfile.ZipFile("/tmp/api-contract-collab.zip") as z:
    z.extractall(skills)
print(target)
PY
```

Windows PowerShell:

```powershell
$skills = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "skills" } else { Join-Path $HOME ".codex\skills" }
New-Item -ItemType Directory -Force $skills | Out-Null
$zip = Join-Path $env:TEMP "api-contract-collab.zip"
Invoke-WebRequest -Uri "http://162.250.126.10:38970/shared/api-contract-collab-0.5.5.zip" -OutFile $zip
$target = Join-Path $skills "api-contract-collab"
if (Test-Path $target) { Remove-Item -Recurse -Force $target }
Expand-Archive -Path $zip -DestinationPath $skills -Force
Write-Output $target
```

## Configure identity and API key

The frontend and backend agents use the same shared API key. The side is stored in the Skill-local config, not in the project repository.

Ask the user to confirm the agent identity first:

```text
Please confirm this agent identity for API collaboration: frontend or backend?
```

Then configure the Skill.

Linux / macOS:

```bash
cd "${CODEX_HOME:-$HOME/.codex}/skills/api-contract-collab"
printf "%s" "<SHARED_API_KEY>" | python3 scripts/configure_identity.py \
  --side frontend \
  --base-url http://162.250.126.10:38970 \
  --project movie-app \
  --token-stdin
```

Use `--side backend` for the backend agent.

Windows PowerShell:

```powershell
cd "$skills\api-contract-collab"
$token = "<SHARED_API_KEY>"
$token | py -3 scripts\configure_identity.py `
  --side frontend `
  --base-url http://162.250.126.10:38970 `
  --project movie-app `
  --token-stdin
```

Use `--side backend` for the backend agent.

Show current config with masked token:

```bash
python3 scripts/configure_identity.py --show
```

On Windows:

```powershell
py -3 scripts\configure_identity.py --show
```

## Required execution standard


- Requirements and suggestions are supported with `--type requirement` and `--type suggestion`; keep them tied to affected endpoint(s).
- Frontend data-structure reports must first follow the backend current verified response structure, then describe gaps or UI-required outcomes.


After installation, all API development work must follow this Skill:

1. Use OpenAPI JSON as the contract source.
2. Use `oasdiff` for old/new OpenAPI comparison: `summary`, full `diff`, and `breaking`.
3. Report API integration issues through this Skill, not only in chat.
4. Submit only single-API or multi-API issues. Repeat `--endpoint` for multi-API issues.
5. Frontend and backend use the same API key and the same shared issue IDs; each side appends only its own role-scoped events.
6. Backend agents use the lightweight gate: inspect related backend code and current OpenAPI output, run `propose_fix.py`, wait for explicit user approval, then edit code.
7. Frontend agents upload an API integration summary after each frontend release.
8. Timestamps use runtime local timezone format `YYYY-MM-DD HH:mm:ss`; server runtime sets `TZ=Asia/Shanghai`.



## Identity-specific workflows

### Frontend agent workflow

1. Run `python3 scripts/next_actions.py` at the start of each API collaboration session.
2. Report API problems, requirements, or suggestions only after checking current OpenAPI JSON, real response evidence, frontend API service/DTO/mapper/test, or Bruno evidence.
3. For data structure, field, enum, paging, card, CMS module, or DTO mapping topics, document the backend current verified response structure first, then describe the frontend gap or desired observable outcome.
4. Use one shared issue for one single API or one related multi-API group. Set `--owner backend` for backend/Swagger action and `--owner frontend` for frontend adaptation.
5. For frontend-owned changes, inspect frontend code, present the proposed plan to the user, wait for confirmation, then edit and record status on the same issue.
6. When backend marks an issue resolved, verify through real API evidence and relevant frontend checks, then run `verify_issue.py --result passed` and `close_issue.py`. If verification fails, run `verify_issue.py --result failed` with evidence.
7. After each frontend release, run `report_summary.py`.

### Backend agent workflow

1. Run `python3 scripts/next_actions.py` at the start of each API collaboration session.
2. For backend-owned `open` or `reopened` issues, inspect related backend code and current OpenAPI output first.
3. Run `propose_fix.py` with finding, affected endpoint(s), intended behavior/contract impact, validation command, and OpenAPI/deployment impact.
4. Wait for explicit user confirmation before editing backend code, Swagger annotations, migrations, generated OpenAPI output, deployment files, or configuration.
5. After confirmation, run `approve_issue.py` and `start_issue.py`, implement the confirmed change, run checks, and upload a new OpenAPI snapshot when contract output changes.
6. Run `resolve_issue.py` with deployment/version/test evidence. Frontend verifies and closes the same shared issue.
7. If frontend adaptation is required, keep the same shared issue and move/leave ownership to `frontend` instead of creating a duplicate issue.

### User / owner workflow

1. Review `backend_proposed` or `frontend_proposed` notes in the dashboard.
2. Approve the proposed plan before implementation begins, or add comments/reopen/block notes on the same issue.
3. Use the shared timeline as the decision record.

## Shared Issue Lifecycle

A single API problem should stay on one issue ID from report to close:

```text
open -> backend_proposed -> approved -> backend_doing -> backend_resolved -> frontend_verified -> closed
```

Use `comment_issue.py` for extra frontend/backend notes. Use `verify_issue.py --result failed` to reopen a failed verification. The dashboard shows all events in one timeline and exports a Markdown copy under `/exports/issues/`.

## Common commands

### Continue existing work

```bash
python3 scripts/next_actions.py
```

### Web dashboard issue detail and quick actions

Use the dashboard action cards to find issues awaiting approval, backend handling, or frontend verification. Open `/issues/{id}` to review the full timeline and use quick Web actions for human review notes, approval, verification result, close, or reopen. Agents should still prefer the scripts below for normal workflow updates.

### Backup before risky operations

```bash
python3 scripts/backup_db.py --note "before cleanup"
```


Report a single-API issue:

```bash
python3 scripts/report_issue.py \
  --title "会员信息字段不一致" \
  --endpoint "GET /api/member/info" \
  --owner backend \
  --priority P1 \
  --type contract-mismatch \
  --description "Swagger 与真实响应不一致" \
  --expected "会员信息字段在 OpenAPI 与真实响应中保持一致，前端可稳定映射。" \
  --actual "当前 Swagger 与真实响应字段不一致。" \
  --evidence "附真实响应脱敏片段或上传 tmp/member-info-response.json。" \
  --impact "会员资料页面和 session ViewModel 字段映射不稳定。" \
  --close-criteria "OpenAPI、真实响应、前端 mapper 和相关测试均验证一致。"
```

Report a multi-API issue:

```bash
python3 scripts/report_issue.py \
  --title "登录态相关接口契约不一致" \
  --endpoint "POST /api/member/login" \
  --endpoint "POST /api/member/refresh" \
  --endpoint "GET /api/member/info" \
  --owner backend \
  --priority P1 \
  --type contract-mismatch \
  --description "登录态相关接口契约不一致。" \
  --expected "登录、刷新和会员信息接口的 token 与会员字段语义一致。" \
  --actual "当前这些接口的字段或语义不一致，前端无法稳定对接。" \
  --evidence "附 OpenAPI 差异、真实响应脱敏片段或 smoke 报告链接。" \
  --impact "登录、刷新、会话恢复和会员资料展示可能出现错误状态。" \
  --close-criteria "相关接口 OpenAPI、真实响应和前端 smoke/mapper 验证一致。"
```

Update status:

```bash
python3 scripts/propose_fix.py --id API-YYYYMMDD-001 --note "已检查相关代码和 OpenAPI 输出，提交处理计划，等待用户确认。"
python3 scripts/approve_issue.py --id API-YYYYMMDD-001 --note "用户已确认处理计划。"
python3 scripts/start_issue.py --id API-YYYYMMDD-001 --note "开始处理。"
python3 scripts/resolve_issue.py --id API-YYYYMMDD-001 --note "已部署并附验证证据。"
python3 scripts/verify_issue.py --id API-YYYYMMDD-001 --result passed --note "前端已用真实接口验证通过。"
python3 scripts/close_issue.py --id API-YYYYMMDD-001 --note "验证通过后关闭。"
```

Edit issue:

```bash
python3 scripts/edit_issue.py \
  --id API-YYYYMMDD-001 \
  --title "更新后的问题标题" \
  --endpoint "GET /api/member/info" \
  --priority P1 \
  --note "补充接口范围和验收条件"
```

Physically delete issue:

```bash
python3 scripts/delete_issue.py --id API-YYYYMMDD-001 --yes
```


Upload OpenAPI snapshot:

```bash
python3 scripts/upload_openapi.py --file openapi.json --label swagger-v3.9.2
```

Generate mandatory oasdiff report:

```bash
python3 scripts/generate_diff_report.py --old old-openapi.json --new new-openapi.json --upload
```

Upload frontend release summary:

```bash
python3 scripts/report_summary.py \
  --backend-total 104 \
  --integrated 74 \
  --problematic 30 \
  --version "v1.2.3" \
  --note "本次发布后的接口对接汇总"
```

## Verification checklist

Before continuing API work, verify:

```bash
python3 scripts/configure_identity.py --show
python3 scripts/report_issue.py --help
python3 scripts/report_summary.py --help
python3 scripts/propose_fix.py --help
python3 scripts/verify_issue.py --help
python3 scripts/next_actions.py --help
python3 scripts/backup_db.py --help
python3 scripts/check_update.py --help
oasdiff --help
```

If `oasdiff` is missing, install it before OpenAPI old/new comparison. Do not create a handwritten substitute diff.




## Telegram channel notification

Server deployments may enable Telegram channel notification with `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Agents keep using the Skill scripts as usual; Telegram is only for timely awareness and user confirmation prompts. The Web dashboard remains the complete issue record.

## Skill script language

Use `API_COLLAB_LANG=zh-CN|en` or save it into Skill-local config:

```bash
python3 scripts/configure_identity.py --side frontend --base-url http://HOST:PORT --lang zh-CN --token-stdin
python3 scripts/configure_identity.py --side backend --base-url http://HOST:PORT --lang en --token-stdin
```

Agents should answer user-facing API collaboration prompts and status summaries in the configured language.
