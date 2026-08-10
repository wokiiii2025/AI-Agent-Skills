#!/usr/bin/env python3
import argparse
from api_collab_client import issue_action
parser = argparse.ArgumentParser(description="Approve a proposed API issue plan after user confirmation")
parser.add_argument("--id", required=True)
parser.add_argument("--note", default="User approved proposed plan.")
args = parser.parse_args()
result = issue_action(args.id, "approve", args.note)
print(result.get("url") or result)
