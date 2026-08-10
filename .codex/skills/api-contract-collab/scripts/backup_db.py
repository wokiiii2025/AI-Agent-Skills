#!/usr/bin/env python3
import argparse
from api_collab_client import request_json
parser = argparse.ArgumentParser(description="Create a SQLite backup on the API collaboration server")
parser.add_argument("--note", default="manual backup")
args = parser.parse_args()
result = request_json("POST", "/api/backup", {"note": args.note})
print(result.get("url") or result)
