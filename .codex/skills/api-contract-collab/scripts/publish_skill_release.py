#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from api_collab_client import base_url, request_json

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "VERSION.json"

parser = argparse.ArgumentParser(description="Publish Skill release metadata and notify Telegram channel")
parser.add_argument("--version")
parser.add_argument("--zip-file")
parser.add_argument("--download-url")
parser.add_argument("--latest-url")
parser.add_argument("--sha256")
parser.add_argument("--bytes", type=int)
parser.add_argument("--note", default="")
args = parser.parse_args()

meta = {}
if VERSION_FILE.exists():
    meta = json.loads(VERSION_FILE.read_text(encoding="utf-8"))
if args.version: meta["version"] = args.version
if args.zip_file: meta["zipFile"] = args.zip_file
if args.download_url: meta["downloadUrl"] = args.download_url
if args.latest_url: meta["latestUrl"] = args.latest_url
if args.sha256: meta["sha256"] = args.sha256
if args.bytes is not None: meta["bytes"] = args.bytes
if args.note: meta["note"] = args.note
if not meta.get("version"):
    raise SystemExit("version is required in VERSION.json or --version")
meta.setdefault("zipFile", f"api-contract-collab-{meta['version']}.zip")
meta.setdefault("downloadUrl", f"{base_url().rstrip('/')}/shared/{meta['zipFile']}")
meta.setdefault("latestUrl", f"{base_url().rstrip('/')}/shared/api-contract-collab-latest.json")
result = request_json("POST", "/api/skill-release", meta)
print(json.dumps(result, ensure_ascii=False, indent=2))
