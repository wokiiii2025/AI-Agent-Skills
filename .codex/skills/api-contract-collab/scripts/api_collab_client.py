#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
LOCAL_CONFIG_PATH = SKILL_DIR / ".local" / "config.json"

STATUSES = {
    "open", "triaged", "backend_proposed", "frontend_proposed", "approved",
    "backend_doing", "frontend_doing", "backend_resolved", "frontend_resolved",
    "frontend_verifying", "backend_verifying", "frontend_verified", "backend_verified",
    "closed", "blocked", "reopened",
}
PRIORITIES = {"P0", "P1", "P2", "P3"}
SIDES = {"frontend", "backend"}


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_local_config():
    try:
        return json.loads(LOCAL_CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        raise SystemExit(f"Invalid api-contract-collab local config: {LOCAL_CONFIG_PATH}: {error}")



def lang():
    value = os.environ.get("API_COLLAB_LANG") or load_local_config().get("lang") or "zh-CN"
    return "en" if str(value).lower().startswith("en") else "zh"

def text(key):
    zh = {
        "missing_side": "缺少 API_COLLAB_SIDE。请先确认当前 agent 身份是 frontend 还是 backend，然后运行 scripts/configure_identity.py 保存身份。",
        "missing_token": "缺少 API_COLLAB_TOKEN。请通过环境变量或 scripts/configure_identity.py 配置共享 API key。",
        "missing_base": "缺少 API_COLLAB_BASE_URL。请通过环境变量或 scripts/configure_identity.py 配置协作服务地址。",
        "missing_config": "缺少配置。请运行：python scripts/configure_identity.py --side frontend|backend --base-url http://HOST:PORT --token-stdin",
    }
    en = {
        "missing_side": "Missing API_COLLAB_SIDE. Confirm whether this agent is frontend or backend, then run scripts/configure_identity.py to save the identity.",
        "missing_token": "Missing API_COLLAB_TOKEN. Configure the shared API key through environment variables or scripts/configure_identity.py.",
        "missing_base": "Missing API_COLLAB_BASE_URL. Configure the collaboration server URL through environment variables or scripts/configure_identity.py.",
        "missing_config": "Missing config. Run: python scripts/configure_identity.py --side frontend|backend --base-url http://HOST:PORT --token-stdin",
    }
    return (en if lang() == "en" else zh).get(key, key)

def config_value(env_name, config_name=None, default=None, required=False):
    value = os.environ.get(env_name)
    if value:
        return value
    local = load_local_config()
    value = local.get(config_name or env_name)
    if value:
        return value
    if required:
        if env_name == 'API_COLLAB_BASE_URL':
            raise SystemExit(text('missing_base'))
        if env_name == 'API_COLLAB_TOKEN':
            raise SystemExit(text('missing_token'))
        raise SystemExit(text('missing_config'))
    return default


def base_url():
    return config_value("API_COLLAB_BASE_URL", "baseUrl", required=True).rstrip("/")


def token():
    return config_value("API_COLLAB_TOKEN", "token", required=True)


def side():
    value = config_value("API_COLLAB_SIDE", "side")
    if not value:
        raise SystemExit(text('missing_side'))
    if value not in SIDES:
        raise SystemExit(text('missing_side'))
    return value


def project():
    return config_value("API_COLLAB_PROJECT", "project", "movie-app")


def request_json(method, path, payload=None):
    data = None
    headers = {
        "Authorization": f"Bearer {token()}",
        "X-Api-Collab-Side": side(),
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    req = urllib.request.Request(base_url() + path, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {detail}")


def issue_action(issue_id, action, note="", extra=None):
    payload = {"note": note or ""}
    if extra:
        payload.update(extra)
    return request_json("POST", f"/api/issues/{issue_id}/{action}", payload)


def read_text_file(path):
    if not path:
        return ""
    return Path(path).read_text(encoding="utf-8")


def normalize_endpoints(values):
    endpoints = []
    for value in values or []:
        if not value:
            continue
        if isinstance(value, str):
            endpoints.append(value.strip())
        else:
            endpoints.append(str(value).strip())
    return [x for x in endpoints if x]


def format_endpoints_inline(endpoints):
    items = normalize_endpoints(endpoints)
    if not items:
        return "-"
    return ", ".join(f"`{item}`" for item in items)


def format_endpoints_block(endpoints):
    items = normalize_endpoints(endpoints)
    if not items:
        return "-"
    return "\n".join(f"- `{item}`" for item in items)


def render_issue_md(meta, description, expected, actual, evidence, impact, close_criteria):
    return f"""# {meta['id']} {meta['title']}

## Summary

- Project: {meta['project']}
- Reporter: {meta['reporter_side']}
- Status: {meta['status']}
- Owner: {meta['owner_side']}
- Priority: {meta['priority']}
- Type: {meta['type']}
- Endpoints: {format_endpoints_inline(meta.get('endpoints') or [meta.get('endpoint', '')])}
- CreatedAt: {meta['createdAt']}
- UpdatedAt: {meta['updatedAt']}

## Contract Source

OpenAPI / Swagger JSON and real integration evidence.

## Related APIs

{format_endpoints_block(meta.get('endpoints') or [meta.get('endpoint', '')])}

## Description

{description or '-'}

## Expected

{expected or '-'}

## Actual

{actual or '-'}

## Evidence

{evidence or '-'}

## Impact

{impact or '-'}

## Close Criteria

{close_criteria or '-'}

## Updates

- {meta['createdAt']} `{meta['reporter_side']}` created issue, status=`{meta['status']}`.
"""


def make_issue_payload(args):
    current_side = side()
    created = now_text()
    endpoints = normalize_endpoints(args.endpoint)
    if not endpoints:
        raise SystemExit("At least one --endpoint is required")
    meta = {
        "project": project(),
        "reporter_side": current_side,
        "status": "open",
        "owner_side": args.owner,
        "priority": args.priority,
        "type": args.type,
        "endpoint": endpoints[0],
        "endpoints": endpoints,
        "endpointCount": len(endpoints),
        "title": args.title,
        "createdAt": created,
        "updatedAt": created,
    }
    evidence = args.evidence or ""
    if args.evidence_file:
        evidence = evidence + ("\n\n" if evidence else "") + read_text_file(args.evidence_file)
    if not evidence.strip():
        raise SystemExit("--evidence or --evidence-file is required")
    meta.update({
        "description": args.description or "",
        "expected": args.expected or "",
        "actual": args.actual or "",
        "evidence": evidence or "",
        "impact": args.impact or "",
        "closeCriteria": args.close_criteria or "",
    })
    md = render_issue_md(
        {**meta, "id": "PENDING"},
        args.description,
        args.expected,
        args.actual,
        evidence,
        args.impact,
        args.close_criteria,
    )
    return {"meta": meta, "markdown": md}

