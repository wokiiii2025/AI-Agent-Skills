#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from api_collab_client import request_json

parser = argparse.ArgumentParser(description="Upload OpenAPI JSON snapshot")
parser.add_argument("--file", required=True)
parser.add_argument("--label", default="latest")
args = parser.parse_args()

content = json.loads(Path(args.file).read_text(encoding="utf-8"))
result = request_json("POST", "/api/openapi", {"label": args.label, "openapi": content})
print(result.get("url") or result)
