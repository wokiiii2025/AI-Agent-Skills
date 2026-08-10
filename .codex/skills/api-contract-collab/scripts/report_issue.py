#!/usr/bin/env python3
import argparse
from api_collab_client import make_issue_payload, request_json, PRIORITIES, SIDES

parser = argparse.ArgumentParser(description="Report API collaboration issue")
parser.add_argument("--title", required=True)
parser.add_argument("--endpoint", action="append", required=True, help="API endpoint; repeat for multiple endpoints")
parser.add_argument("--owner", required=True, choices=sorted(SIDES))
parser.add_argument("--priority", default="P1", choices=sorted(PRIORITIES))
parser.add_argument("--type", default="contract-mismatch")
parser.add_argument("--description", required=True)
parser.add_argument("--expected", required=True)
parser.add_argument("--actual", required=True)
parser.add_argument("--evidence", default="")
parser.add_argument("--evidence-file")
parser.add_argument("--impact", required=True)
parser.add_argument("--close-criteria", required=True)
args = parser.parse_args()

result = request_json("POST", "/api/issues", make_issue_payload(args))
print(result.get("url") or result)
