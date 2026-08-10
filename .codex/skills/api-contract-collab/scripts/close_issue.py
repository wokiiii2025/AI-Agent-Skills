#!/usr/bin/env python3
import argparse
from api_collab_client import issue_action
parser = argparse.ArgumentParser(description="Close a shared API issue")
parser.add_argument("--id", required=True)
parser.add_argument("--note", default="Issue closed.")
args = parser.parse_args()
result = issue_action(args.id, "close", args.note)
print(result.get("url") or result)
