#!/usr/bin/env python3
"""Validate OpenAPI while treating Chinese component identifiers as warnings."""

import argparse
import json
import re
import shutil
import subprocess
import sys


CHINESE_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")
IDENTIFIER_ERROR_RE = re.compile(
    r'^identifier "(?P<identifier>.+)" is not supported by OpenAPIv3 standard'
)


def is_ignored_chinese_identifier(finding: dict) -> bool:
    if finding.get("id") != "spec-validation-error":
        return False
    match = IDENTIFIER_ERROR_RE.match(str(finding.get("text", "")))
    return bool(match and CHINESE_RE.search(match.group("identifier")))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Policy-aware OpenAPI validation using oasdiff"
    )
    parser.add_argument("spec", help="OpenAPI JSON/YAML path or URL")
    args = parser.parse_args()

    executable = shutil.which("oasdiff")
    if not executable:
        print("oasdiff is required", file=sys.stderr)
        return 127

    process = subprocess.run(
        [executable, "validate", args.spec, "--format", "json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode == 102:
        print(process.stderr or process.stdout, file=sys.stderr)
        return process.returncode

    try:
        findings = json.loads(process.stdout or "[]")
    except json.JSONDecodeError:
        print(process.stderr or process.stdout, file=sys.stderr)
        return process.returncode or 2

    ignored = [item for item in findings if is_ignored_chinese_identifier(item)]
    active = [item for item in findings if not is_ignored_chinese_identifier(item)]
    blocking = [item for item in active if int(item.get("level", 0)) >= 3]

    result = {
        "valid": not blocking,
        "blockingCount": len(blocking),
        "ignoredChineseSchemaIdentifierCount": len(ignored),
        "activeFindings": active,
        "ignoredFindings": ignored,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if blocking else 0


if __name__ == "__main__":
    raise SystemExit(main())
