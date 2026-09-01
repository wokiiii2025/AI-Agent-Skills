#!/usr/bin/env python3
"""Multi-provider temporary email inbox CLI.

Commands print JSON. Dependencies: Python stdlib only.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import string
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "providers.json"
_CONFIG_CACHE: Optional[dict] = None

def load_config() -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE
    if CONFIG_PATH.exists():
        try:
            _CONFIG_CACHE = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            _CONFIG_CACHE = {}
    else:
        _CONFIG_CACHE = {}
    return _CONFIG_CACHE

def config_value(provider: str, key: str, env_name: Optional[str] = None) -> Optional[str]:
    if env_name and os.environ.get(env_name):
        return os.environ.get(env_name)
    section = load_config().get(provider, {})
    value = section.get(key) if isinstance(section, dict) else None
    return value if isinstance(value, str) and value else None

OTP_RE = re.compile(r"(?<!\d)(\d{4,8})(?!\d)")


def http_json(method: str, url: str, body: Optional[dict] = None, headers: Optional[dict] = None, timeout: int = 25) -> Any:
    data = None
    req_headers = {"Accept": "application/json", "User-Agent": "codex-temp-email-inbox/1.0"}
    if headers:
        req_headers.update(headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        req_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if not raw:
                return None
            text = raw.decode("utf-8", errors="replace")
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                return {"raw": text}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {e.code} {url}: {raw[:500]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Request failed {url}: {e}") from e


def rand_user(prefix: str = "codex") -> str:
    suffix = "".join(random.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    return f"{prefix}-{suffix}"


def normalize_message(m: dict) -> dict:
    mid = m.get("id") or m.get("_id") or m.get("msg_id") or m.get("message_id") or m.get("emailId") or m.get("email_id")
    return {
        "id": mid,
        "from": m.get("from") or m.get("from_email") or m.get("sender") or m.get("senderAddress"),
        "subject": m.get("subject"),
        "created_at": m.get("createdAt") or m.get("created_at") or m.get("ts") or m.get("date"),
        "preview": m.get("preview_text") or m.get("intro"),
        "raw": m,
    }


def extract_body(msg: Any) -> str:
    if isinstance(msg, str):
        return msg
    if not isinstance(msg, dict):
        return json.dumps(msg, ensure_ascii=False)
    parts: List[str] = []
    for key in ("text", "intro", "html", "body", "content"):
        val = msg.get(key)
        if isinstance(val, str):
            parts.append(val)
        elif isinstance(val, list):
            parts.extend(str(x) for x in val)
    return "\n".join(parts) or json.dumps(msg, ensure_ascii=False)


class Provider:
    name = "base"
    def create(self, args): raise NotImplementedError
    def inbox(self, args): raise NotImplementedError
    def read(self, args): raise NotImplementedError
    def delete(self, args): raise NotImplementedError



class XxpoCcCd(Provider):
    name = "xxpo"
    base_default = "https://xxpo.cc.cd/api"

    def _base(self) -> str:
        return (config_value("xxpo", "base_url", "XXPO_BASE_URL") or self.base_default).rstrip("/")

    def _auth_headers(self) -> dict:
        token = config_value("xxpo", "token", "XXPO_TOKEN")
        if not token:
            email = config_value("xxpo", "admin_email", "XXPO_ADMIN_EMAIL") or "admin@xxpo.cc.cd"
            password = config_value("xxpo", "password", "XXPO_PASSWORD")
            if not password:
                raise RuntimeError("xxpo needs XXPO_PASSWORD or config/providers.json xxpo.password")
            data = http_json("POST", f"{self._base()}/login", {"email": email, "password": password})
            if not isinstance(data, dict) or data.get("code") not in (200, "200"):
                raise RuntimeError(f"xxpo login failed: {data}")
            token = ((data.get("data") or {}).get("token"))
            if not token:
                raise RuntimeError(f"xxpo login response has no token: {data}")
        return {"Authorization": token, "Content-Type": "application/json"}

    def _api(self, method: str, path: str, body: Optional[dict] = None, timeout: int = 25):
        url = path if path.startswith("http") else f"{self._base()}{path}"
        last = None
        for attempt in range(3):
            data = http_json(method, url, body, headers=self._auth_headers(), timeout=timeout)
            last = data
            if not (isinstance(data, dict) and data.get("code") in (401, "401")):
                return data
            time.sleep(1 + attempt)
        return last

    def create(self, args):
        if args.address:
            address = args.address
        else:
            domain = config_value("xxpo", "domain", "XXPO_DOMAIN") or "xxpo.cc.cd"
            address = f"agent-{int(time.time())}-{''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(4))}@{domain}"
        data = self._api("POST", "/account/add", {"email": address})
        account = data.get("data") if isinstance(data, dict) else None
        return {"provider": self.name, "email": address, "account_id": (account or {}).get("account_id") or (account or {}).get("accountId"), "raw": data}

    def _messages_from_payload(self, data: Any) -> list:
        if isinstance(data, list):
            return data
        if not isinstance(data, dict):
            return []
        payload = data.get("data", data)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in ("list", "rows", "emails", "messages", "records", "data"):
                val = payload.get(key)
                if isinstance(val, list):
                    return val
            if payload.get("send_email") or payload.get("subject") or payload.get("content") or payload.get("text"):
                return [payload]
        return []

    def _norm(self, m: dict) -> dict:
        n = normalize_message(m)
        n["from"] = m.get("send_email") or m.get("sendEmail") or n.get("from")
        n["to"] = m.get("email") or m.get("receive_email") or m.get("account_email") or m.get("toEmail")
        n["subject"] = m.get("subject") or n.get("subject")
        n["code"] = (m.get("code") or None) or first_otp(m)
        n["content"] = m.get("text") or m.get("content") or m.get("html") or m.get("body")
        return n

    def inbox(self, args):
        headers = self._auth_headers()
        tried = []
        if getattr(args, "account_id", None):
            tried.append(f"{self._base()}/email/latest?" + urllib.parse.urlencode({"accountId": args.account_id}))
        else:
            tried.append(f"{self._base()}/email/latest")
        # Admin tokens on the current xxpo backend can create aliases but the user-scoped
        # /email/* endpoints return code 401. Fall back to the documented admin-global list.
        tried.append(f"{self._base()}/allEmail/list?page=1&size=50")
        raw_results=[]
        data=None
        msgs=[]
        for url in tried:
            data = self._api("GET", url)
            raw_results.append({"url": url, "code": data.get("code") if isinstance(data, dict) else None, "message": data.get("message") if isinstance(data, dict) else None})
            if isinstance(data, dict) and data.get("code") not in (200, "200", None):
                continue
            msgs = self._messages_from_payload(data)
            break
        if args.address:
            al = args.address.lower()
            filtered=[]
            for m in msgs:
                if not isinstance(m, dict):
                    continue
                targets = [str(m.get(k, '')).lower() for k in ("email", "receive_email", "account_email", "to", "accountEmail", "toEmail")]
                if not any(targets) or al in targets:
                    filtered.append(m)
            msgs = filtered
        return {"provider": self.name, "email": args.address, "account_id": getattr(args, "account_id", None), "count": len(msgs), "messages": [self._norm(m) for m in msgs if isinstance(m, dict)], "raw": data, "tried": raw_results}

    def read(self, args):
        latest = self.inbox(args)
        if args.id:
            for m in latest.get("messages", []):
                if str(m.get("id")) == str(args.id):
                    return {"provider": self.name, "email": args.address, "id": args.id, "message": m, "otp": (m.get("code") or None) or first_otp(m)}
        if latest.get("messages"):
            m = latest["messages"][0]
            return {"provider": self.name, "email": args.address, "id": m.get("id"), "message": m, "otp": (m.get("code") or None) or first_otp(m)}
        return {"provider": self.name, "email": args.address, "id": args.id, "message": None, "otp": None}

    def delete(self, args):
        if not args.id:
            raise RuntimeError("xxpo delete needs --id/emailId")
        # Frontend API uses DELETE /email/delete?emailIds=ID for mailbox messages;
        # /allEmail/delete?emailIds=ID also works for admin-global list items.
        q = urllib.parse.urlencode({"emailIds": args.id})
        data = self._api("DELETE", f"/email/delete?{q}")
        if isinstance(data, dict) and data.get("code") not in (200, "200", None):
            data = self._api("DELETE", f"/allEmail/delete?{q}")
        return {"provider": self.name, "email": args.address, "id": args.id, "deleted": isinstance(data, dict) and data.get("code") in (200, "200"), "raw": data}

class TempMailC(Provider):
    name = "tempmailc"
    base = "https://tempmailc.com/api/v1"
    def create(self, args):
        if args.address:
            return {"provider": self.name, "email": args.address}
        data = http_json("GET", f"{self.base}/new")
        return {"provider": self.name, "email": data.get("email"), "raw": data}
    def inbox(self, args):
        q = urllib.parse.urlencode({"email": args.address})
        data = http_json("GET", f"{self.base}/inbox?{q}")
        msgs = data.get("messages", []) if isinstance(data, dict) else []
        return {"provider": self.name, "email": args.address, "count": len(msgs), "messages": [normalize_message(m) for m in msgs], "raw": data}
    def read(self, args):
        q = urllib.parse.urlencode({"email": args.address, "msg_id": args.id})
        data = http_json("GET", f"{self.base}/message?{q}")
        return {"provider": self.name, "email": args.address, "id": args.id, "message": data, "otp": first_otp(data)}
    def delete(self, args):
        q = urllib.parse.urlencode({"email": args.address, "msg_id": args.id})
        data = http_json("DELETE", f"{self.base}/message?{q}")
        return {"provider": self.name, "email": args.address, "id": args.id, "deleted": True, "raw": data}


class Catchmail(Provider):
    name = "catchmail"
    base = "https://api.catchmail.io/api/v1"
    def create(self, args):
        return {"provider": self.name, "email": args.address or f"{rand_user()}@catchmail.io"}
    def inbox(self, args):
        q = urllib.parse.urlencode({"address": args.address})
        data = http_json("GET", f"{self.base}/mailbox?{q}")
        if isinstance(data, list):
            msgs = data
        elif isinstance(data, dict):
            msgs = data.get("messages") or data.get("data") or data.get("emails") or []
        else:
            msgs = []
        return {"provider": self.name, "email": args.address, "count": len(msgs), "messages": [normalize_message(m) for m in msgs], "raw": data}
    def read(self, args):
        q = urllib.parse.urlencode({"mailbox": args.address})
        data = http_json("GET", f"{self.base}/message/{urllib.parse.quote(args.id)}?{q}")
        return {"provider": self.name, "email": args.address, "id": args.id, "message": data, "otp": first_otp(data)}
    def delete(self, args):
        q = urllib.parse.urlencode({"mailbox": args.address})
        data = http_json("DELETE", f"{self.base}/message/{urllib.parse.quote(args.id)}?{q}")
        return {"provider": self.name, "email": args.address, "id": args.id, "deleted": True, "raw": data}


class MailTM(Provider):
    name = "mailtm"
    base = "https://api.mail.tm"
    def create(self, args):
        password = args.password or ("Codex-" + rand_user("pw") + "!9")
        if args.address:
            address = args.address
        else:
            domains = http_json("GET", f"{self.base}/domains")
            if isinstance(domains, list):
                member = domains
            elif isinstance(domains, dict):
                member = domains.get("hydra:member") or domains.get("domains") or []
            else:
                member = []
            domain = member[0]["domain"] if member else "emalupe.com"
            address = f"{rand_user()}@{domain}"
        account = http_json("POST", f"{self.base}/accounts", {"address": address, "password": password})
        token = http_json("POST", f"{self.base}/token", {"address": address, "password": password})
        return {"provider": self.name, "email": address, "password": password, "token": token.get("token"), "account": account}
    def _token(self, args):
        token = args.token or os.environ.get("MAILTM_TOKEN")
        if token:
            return token
        if args.address and args.password:
            data = http_json("POST", f"{self.base}/token", {"address": args.address, "password": args.password})
            return data.get("token")
        raise RuntimeError("mailtm needs --token or --password for this mailbox")
    def inbox(self, args):
        token = self._token(args)
        data = http_json("GET", f"{self.base}/messages", headers={"Authorization": f"Bearer {token}"})
        if isinstance(data, list):
            msgs = data
        elif isinstance(data, dict):
            msgs = data.get("hydra:member") or data.get("messages") or []
        else:
            msgs = []
        return {"provider": self.name, "email": args.address, "count": len(msgs), "messages": [normalize_message(m) for m in msgs], "raw": data}
    def read(self, args):
        token = self._token(args)
        data = http_json("GET", f"{self.base}/messages/{urllib.parse.quote(args.id)}", headers={"Authorization": f"Bearer {token}"})
        return {"provider": self.name, "email": args.address, "id": args.id, "message": data, "otp": first_otp(data)}
    def delete(self, args):
        token = self._token(args)
        data = http_json("DELETE", f"{self.base}/messages/{urllib.parse.quote(args.id)}", headers={"Authorization": f"Bearer {token}"})
        return {"provider": self.name, "email": args.address, "id": args.id, "deleted": True, "raw": data}


class MailCX(Provider):
    name = "mailcx"
    base = "https://api.mail.cx/v1"
    def _headers(self):
        token = config_value("mailcx", "token", "MAIL_CX_TOKEN")
        if not token:
            raise RuntimeError("mailcx needs MAIL_CX_TOKEN or config/providers.json mailcx.token")
        return {"x-api-token": token}
    def create(self, args):
        if args.address:
            address = args.address
        else:
            try:
                cfg = http_json("GET", f"{self.base}/config", headers=self._headers())
                domains = cfg.get("system_domains", []) if isinstance(cfg, dict) else []
                default = next((d.get("domain") for d in domains if d.get("default")), None)
                domain = default or (domains[0].get("domain") if domains else "9k3r.com")
            except Exception:
                domain = "9k3r.com"
            # mail.cx local_part_rules currently cap local-part length at 20.
            address = f"cx-{rand_user('')[1:13]}@{domain}"
        return {"provider": self.name, "email": address, "requires": "MAIL_CX_TOKEN for inbox/read"}
    def inbox(self, args):
        data = http_json("GET", f"{self.base}/inbox/{urllib.parse.quote(args.address)}", headers=self._headers(), timeout=30)
        if isinstance(data, list):
            msgs = data
        elif isinstance(data, dict):
            msgs = data.get("emails") or data.get("messages") or data.get("data") or []
        else:
            msgs = []
        return {"provider": self.name, "email": args.address, "count": len(msgs), "messages": [normalize_message(m) for m in msgs], "raw": data}
    def read(self, args):
        data = http_json("GET", f"{self.base}/email/{urllib.parse.quote(args.id)}", headers=self._headers())
        return {"provider": self.name, "email": args.address, "id": args.id, "message": data, "otp": first_otp(data)}
    def delete(self, args):
        data = http_json("DELETE", f"{self.base}/email/{urllib.parse.quote(args.id)}", headers=self._headers())
        return {"provider": self.name, "email": args.address, "id": args.id, "deleted": True, "raw": data}


PROVIDERS = {p.name: p for p in (XxpoCcCd(), TempMailC(), Catchmail(), MailTM(), MailCX())}


def first_otp(obj: Any) -> Optional[str]:
    m = OTP_RE.search(extract_body(obj))
    return m.group(1) if m else None




def read_then_delete(provider: Provider, args) -> dict:
    full = provider.read(args)
    if getattr(args, "keep", False):
        full["deleted"] = False
        full["delete_skipped"] = "--keep"
        return full
    try:
        deletion = provider.delete(args)
        full["deleted"] = True
        full["delete_result"] = deletion
    except Exception as exc:
        full["deleted"] = False
        full["delete_error"] = str(exc)
    return full

def cmd_wait(provider: Provider, args):
    deadline = time.time() + args.timeout
    last = None
    while time.time() <= deadline:
        last = provider.inbox(args)
        if last.get("messages"):
            if args.otp:
                for msg in last["messages"]:
                    mid = msg.get("id")
                    if not mid:
                        continue
                    rargs = argparse.Namespace(**vars(args))
                    rargs.id = mid
                    full = read_then_delete(provider, rargs)
                    otp = full.get("otp")
                    if otp:
                        full["matched_message"] = msg
                        return full
            first = last["messages"][0]
            mid = first.get("id")
            if mid:
                rargs = argparse.Namespace(**vars(args))
                rargs.id = mid
                full = read_then_delete(provider, rargs)
                full["matched_message"] = first
                return full
            return last
        time.sleep(args.interval)
    return {"provider": provider.name, "email": args.address, "timeout": args.timeout, "messages": [], "last": last}


def cmd_test(provider: Provider, args):
    created = provider.create(args)
    address = created.get("email")
    targs = argparse.Namespace(**vars(args))
    targs.address = address
    if isinstance(created, dict):
        if created.get("password") and not getattr(targs, "password", None):
            targs.password = created.get("password")
        if created.get("token") and not getattr(targs, "token", None):
            targs.token = created.get("token")
    inbox = provider.inbox(targs)
    return {"ok": bool(address) and "messages" in inbox, "provider": provider.name, "create": created, "inbox": inbox}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Temporary email inbox CLI")
    parser.add_argument("command", choices=["create", "inbox", "read", "delete", "wait", "test"])
    parser.add_argument("--provider", choices=sorted(PROVIDERS), default="xxpo")
    parser.add_argument("--address")
    parser.add_argument("--id")
    parser.add_argument("--password")
    parser.add_argument("--token")
    parser.add_argument("--account-id")
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--interval", type=float, default=5)
    parser.add_argument("--otp", action="store_true")
    parser.add_argument("--keep", action="store_true", help="Do not delete a message after read/wait. Default is read-then-delete.")
    args = parser.parse_args(argv)
    provider = PROVIDERS[args.provider]
    try:
        if args.command == "create":
            out = provider.create(args)
        elif args.command == "inbox":
            if not args.address: parser.error("--address is required")
            out = provider.inbox(args)
        elif args.command == "read":
            if not args.address: parser.error("--address is required")
            if not args.id: parser.error("--id is required")
            out = read_then_delete(provider, args)
        elif args.command == "delete":
            if not args.address: parser.error("--address is required")
            if not args.id: parser.error("--id is required")
            out = provider.delete(args)
        elif args.command == "wait":
            if not args.address: parser.error("--address is required")
            out = cmd_wait(provider, args)
        else:
            out = cmd_test(provider, args)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if not (isinstance(out, dict) and out.get("ok") is False) else 2
    except Exception as exc:
        print(json.dumps({"ok": False, "provider": args.provider, "error": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
