#!/usr/bin/env python3
import argparse
from api_collab_client import request_json, lang
parser = argparse.ArgumentParser(description="Show next API collaboration actions for the current agent side")
parser.add_argument("--limit", type=int, default=20)
args = parser.parse_args()
result = request_json("GET", "/api/next-actions")
if lang() == "en":
    print(f"side={result.get('side')} count={result.get('count')}")
else:
    print(f"身份={result.get('side')} 数量={result.get('count')}")
for item in (result.get("actions") or [])[:args.limit]:
    print(f"- {item.get('id')} [{item.get('status')}] owner={item.get('owner_side')} priority={item.get('priority')} {item.get('title')}")
    print(f"  {'reason' if lang()=='en' else '原因'}: {item.get('nextReason')}")
    print(f"  {'command' if lang()=='en' else '命令'}: {item.get('suggestedCommand')}")
