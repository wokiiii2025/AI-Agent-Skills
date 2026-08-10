#!/usr/bin/env python3
import argparse
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from api_collab_client import request_json



def run_oasdiff(args):
    exe = shutil.which("oasdiff")
    if not exe:
        raise SystemExit(
            "oasdiff is required. Install it before running this script: "
            "curl -fsSL https://raw.githubusercontent.com/oasdiff/oasdiff/main/install.sh | sh"
        )
    proc = subprocess.run(
        [exe, *args],
        text=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    # oasdiff breaking may return non-zero when breaking changes exist. Keep output, fail only on tool/runtime errors with no useful report.
    output = (proc.stdout or "") + (("\n" + proc.stderr) if proc.stderr else "")
    if proc.returncode not in (0, 1) and not output.strip():
        raise SystemExit(f"oasdiff failed with exit code {proc.returncode}")
    return proc.returncode, output.strip()


def section(title, body):
    return f"## {title}\n\n```text\n{body.strip() or 'No output.'}\n```\n"


def main():
    parser = argparse.ArgumentParser(description="Generate mandatory oasdiff OpenAPI report")
    parser.add_argument("--old", required=True, help="base OpenAPI JSON/YAML")
    parser.add_argument("--new", required=True, help="revision OpenAPI JSON/YAML")
    parser.add_argument("--out", default="api-openapi-oasdiff-report.md")
    parser.add_argument("--upload", action="store_true")
    args = parser.parse_args()

    old = str(Path(args.old).resolve())
    new = str(Path(args.new).resolve())
    for file in [old, new]:
        if not Path(file).exists():
            raise SystemExit(f"OpenAPI file not found: {file}")

    # Keep summary structured, and use default human-readable output for diff/breaking.
    # The default renderer is the portable text output across oasdiff builds.
    summary_rc, summary = run_oasdiff(["summary", old, new, "--format", "json"])
    diff_rc, diff = run_oasdiff(["diff", old, new])
    breaking_rc, breaking = run_oasdiff(["breaking", old, new])

    normalized_breaking = breaking.strip()
    has_breaking = (
        bool(normalized_breaking)
        and "No breaking changes" not in normalized_breaking
        and "No changes detected" not in normalized_breaking
    )
    lines = [
        "# OpenAPI oasdiff Report",
        "",
        f"Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}",
        f"Base: `{old}`",
        f"Revision: `{new}`",
        f"Breaking changes: {'YES' if has_breaking else 'NO'}",
        "",
        section("oasdiff summary", summary),
        section("oasdiff diff", diff),
        section("oasdiff breaking", breaking),
    ]
    md = "\n".join(lines)
    Path(args.out).write_text(md, encoding="utf-8")
    print(args.out)
    if args.upload:
        result = request_json("POST", "/api/reports", {"kind": "oasdiff", "title": "OpenAPI oasdiff Report", "markdown": md})
        print(result.get("url") or result)


if __name__ == "__main__":
    main()
