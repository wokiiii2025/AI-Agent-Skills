#!/usr/bin/env python3
import argparse
from api_collab_client import now_text, request_json, side, project

parser = argparse.ArgumentParser(description="Upload frontend/backend API integration summary")
parser.add_argument("--backend-total", type=int, required=True, help="current backend API total from Swagger/OpenAPI")
parser.add_argument("--integrated", type=int, required=True, help="frontend integrated API count")
parser.add_argument("--problematic", type=int, required=True, help="API count currently having open/resolved-not-verified issues")
parser.add_argument("--version", default="", help="release/version label")
parser.add_argument("--note", default="", help="short release note")
args = parser.parse_args()

if args.backend_total < 0 or args.integrated < 0 or args.problematic < 0:
    raise SystemExit("counts must be >= 0")
if args.integrated > args.backend_total:
    raise SystemExit("--integrated cannot exceed --backend-total")

payload = {
    "project": project(),
    "side": side(),
    "backendTotal": args.backend_total,
    "integrated": args.integrated,
    "problematic": args.problematic,
    "version": args.version,
    "note": args.note,
    "updatedAt": now_text(),
}
result = request_json("POST", "/api/summary", payload)
print(result.get("url") or result)
