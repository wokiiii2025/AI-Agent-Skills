#!/usr/bin/env python3
import argparse
from api_collab_client import PRIORITIES, SIDES, STATUSES, read_text_file, request_json

parser = argparse.ArgumentParser(description="Edit a shared API collaboration issue")
parser.add_argument("--id", required=True)
parser.add_argument("--title")
parser.add_argument("--endpoint", action="append", help="API endpoint; repeat for multiple endpoints")
parser.add_argument("--owner", choices=sorted(SIDES))
parser.add_argument("--priority", choices=sorted(PRIORITIES))
parser.add_argument("--type")
parser.add_argument("--status", choices=sorted(STATUSES))
parser.add_argument("--description")
parser.add_argument("--expected")
parser.add_argument("--actual")
parser.add_argument("--evidence")
parser.add_argument("--evidence-file")
parser.add_argument("--impact")
parser.add_argument("--close-criteria")
parser.add_argument("--markdown-file", help="Replace issue markdown with this file")
parser.add_argument("--note", default="")
args = parser.parse_args()

payload = {}
for attr, key in [
    ("title", "title"),
    ("owner", "owner_side"),
    ("priority", "priority"),
    ("type", "type"),
    ("status", "status"),
    ("description", "description"),
    ("expected", "expected"),
    ("actual", "actual"),
    ("evidence", "evidence"),
    ("impact", "impact"),
    ("close_criteria", "closeCriteria"),
]:
    value = getattr(args, attr)
    if value is not None:
        payload[key] = value

if args.endpoint:
    payload["endpoints"] = args.endpoint
if args.evidence_file:
    payload["evidence"] = (payload.get("evidence") or "") + ("\n\n" if payload.get("evidence") else "") + read_text_file(args.evidence_file)
if args.markdown_file:
    payload["markdown"] = read_text_file(args.markdown_file)
if args.note:
    payload["note"] = args.note
if not payload:
    raise SystemExit("Nothing to edit. Provide at least one editable field.")

result = request_json("PUT", f"/api/issues/{args.id}", payload)
print(result.get("url") or result)
