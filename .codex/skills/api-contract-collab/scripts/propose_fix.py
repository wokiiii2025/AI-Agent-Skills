#!/usr/bin/env python3
import argparse
from api_collab_client import issue_action
parser = argparse.ArgumentParser(description="Submit a proposed fix for a shared API issue")
parser.add_argument("--id", required=True)
parser.add_argument("--note", required=True)
args = parser.parse_args()
result = issue_action(args.id, "propose", args.note)
print(result.get("url") or result)
