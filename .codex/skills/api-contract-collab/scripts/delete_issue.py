#!/usr/bin/env python3
import argparse
from api_collab_client import request_json

parser = argparse.ArgumentParser(description="Physically delete a shared API collaboration issue")
parser.add_argument("--id", required=True)
parser.add_argument("--yes", action="store_true", help="Confirm physical deletion")
args = parser.parse_args()

if not args.yes:
    raise SystemExit("Physical deletion requires --yes")

result = request_json("DELETE", f"/api/issues/{args.id}")
print(result)
