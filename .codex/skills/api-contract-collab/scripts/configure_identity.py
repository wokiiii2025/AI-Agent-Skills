#!/usr/bin/env python3
import argparse
import getpass
import json
import os
import sys
from pathlib import Path

SIDES = {"frontend", "backend"}
SKILL_DIR = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_DIR / ".local" / "config.json"


def mask(value):
    if not value:
        return ""
    if len(value) <= 10:
        return value[:2] + "***"
    return value[:6] + "***" + value[-4:]


def read_existing():
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}


def write_config(data):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def main():
    parser = argparse.ArgumentParser(description="Configure api-contract-collab local identity and shared API token")
    parser.add_argument("--side", choices=sorted(SIDES), help="agent identity: frontend or backend")
    parser.add_argument("--base-url", help="API collab server base URL, e.g. http://162.250.126.10:38970")
    parser.add_argument("--project", default=None, help="project name, default keeps existing or movie-app")
    parser.add_argument("--lang", choices=["zh-CN", "en"], help="Skill script output language")
    parser.add_argument("--token", help="shared API token; visible in shell history")
    parser.add_argument("--token-stdin", action="store_true", help="read shared API token from stdin")
    parser.add_argument("--token-prompt", action="store_true", help="prompt for shared API token without echo")
    parser.add_argument("--show", action="store_true", help="show current config with masked token")
    args = parser.parse_args()

    data = read_existing()
    if args.show:
        visible = dict(data)
        if "token" in visible:
            visible["token"] = mask(visible["token"])
        print(json.dumps(visible, ensure_ascii=False, indent=2))
        return

    if args.side:
        data["side"] = args.side
    if args.base_url:
        data["baseUrl"] = args.base_url.rstrip("/")
    if args.project:
        data["project"] = args.project
    if args.lang:
        data["lang"] = args.lang
    if "project" not in data:
        data["project"] = "movie-app"

    token = args.token
    if args.token_stdin:
        token = sys.stdin.read().strip()
    if args.token_prompt:
        token = getpass.getpass("API_COLLAB_TOKEN: ").strip()
    if token:
        data["token"] = token

    missing = [key for key in ["side", "baseUrl", "token"] if not data.get(key)]
    if missing:
        raise SystemExit(
            "Missing required config: " + ", ".join(missing) + "\n"
            "Example: python scripts/configure_identity.py --side frontend --base-url http://162.250.126.10:38970 --token-stdin"
        )

    write_config(data)
    print(f"Saved api-contract-collab config: {CONFIG_PATH}")
    print(f"side={data['side']} baseUrl={data['baseUrl']} project={data.get('project', 'movie-app')} token={mask(data['token'])}")


if __name__ == "__main__":
    main()
