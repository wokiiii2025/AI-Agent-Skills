#!/usr/bin/env python3
import argparse
from api_collab_client import issue_action
parser = argparse.ArgumentParser(description="Verify a shared API issue from the current side")
parser.add_argument("--id", required=True)
parser.add_argument("--result", choices=["passed", "failed"], default="passed")
parser.add_argument("--note", required=True)
args = parser.parse_args()
action = "verify" if args.result == "passed" else "reopen"
result = issue_action(args.id, action, args.note, {"result": args.result})
print(result.get("url") or result)
