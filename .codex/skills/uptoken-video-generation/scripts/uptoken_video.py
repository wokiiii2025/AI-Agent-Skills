#!/usr/bin/env python3
"""Small UpToken video API helper: balance, asset upload, generation, polling, download."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path

BASE_URL = "https://uptoken.cc"


def api_key(args: argparse.Namespace) -> str:
    if getattr(args, "api_key", None):
        return args.api_key.strip()
    if getattr(args, "api_key_file", None):
        return Path(args.api_key_file).read_text(encoding="utf-8").strip()
    key = os.environ.get("UPTOKEN_API_KEY", "").strip()
    if key:
        return key
    raise SystemExit("Missing API key. Set UPTOKEN_API_KEY or pass --api-key-file.")


def request_json(method: str, path: str, key: str, body: dict | None = None) -> dict:
    data = None
    headers = {"Authorization": f"Bearer {key}", "User-Agent": "Codex-UpToken-Video/1.0"}
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {exc.reason}: {details}") from exc


def upload_multipart(path: Path, key: str) -> dict:
    boundary = f"----uptoken-{uuid.uuid4().hex}"
    ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    file_bytes = path.read_bytes()
    head = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode("utf-8")
    tail = f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/v1/assets",
        data=head + file_bytes + tail,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "User-Agent": "Codex-UpToken-Video/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {exc.reason}: {details}") from exc


def download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "Codex-UpToken-Video/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def add_csv_urls(body: dict, field: str, value: str | None) -> None:
    if value:
        body[field] = [item.strip() for item in value.split(",") if item.strip()]


def build_generation_body(args: argparse.Namespace) -> dict:
    if args.body_json:
        return json.loads(Path(args.body_json).read_text(encoding="utf-8"))
    body: dict = {
        "model": args.model,
        "duration": args.duration,
        "resolution": args.resolution,
        "ratio": args.ratio,
        "generate_audio": args.generate_audio,
    }
    if args.content_json:
        body["content"] = json.loads(Path(args.content_json).read_text(encoding="utf-8"))
    elif args.prompt:
        body["prompt"] = args.prompt
    else:
        raise SystemExit("Pass --prompt, --content-json, or --body-json.")
    add_csv_urls(body, "image_urls", args.image_urls)
    add_csv_urls(body, "video_urls", args.video_urls)
    add_csv_urls(body, "audio_urls", args.audio_urls)
    if args.first_frame_url:
        body["first_frame_url"] = args.first_frame_url
    if args.last_frame_url:
        body["last_frame_url"] = args.last_frame_url
    return body


def save_result(result: dict, output_dir: Path, label: str | None = None) -> tuple[Path, Path | None]:
    output_dir.mkdir(parents=True, exist_ok=True)
    task_id = result["id"]
    suffix = f".{label}" if label else ""
    json_path = output_dir / f"{task_id}{suffix}.result.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    video_path = None
    video_url = result.get("content", {}).get("video_url")
    if video_url:
        video_path = output_dir / f"{task_id}{suffix}.mp4"
        download(video_url, video_path)
    return json_path, video_path


def cmd_balance(args: argparse.Namespace) -> None:
    print(json.dumps(request_json("GET", "/v1/account/balance", api_key(args)), ensure_ascii=False, indent=2))


def cmd_upload_asset(args: argparse.Namespace) -> None:
    print(json.dumps(upload_multipart(Path(args.file), api_key(args)), ensure_ascii=False, indent=2))


def poll_task(key: str, task_id: str, interval: int, timeout: int, quiet: bool) -> dict:
    deadline = time.time() + timeout
    last_status = None
    while True:
        result = request_json("GET", f"/v1/video/generations/{urllib.parse.quote(task_id)}", key)
        status = result.get("status")
        if not quiet and status != last_status:
            print(f"[{time.strftime('%H:%M:%S')}] status={status}", file=sys.stderr)
            last_status = status
        if status in {"succeeded", "failed"}:
            return result
        if time.time() >= deadline:
            raise SystemExit(f"Timed out waiting for {task_id}")
        time.sleep(interval)


def cmd_generate(args: argparse.Namespace) -> None:
    key = api_key(args)
    task = request_json("POST", "/v1/video/generations", key, build_generation_body(args))
    task_id = task["id"]
    if args.no_poll:
        print(json.dumps(task, ensure_ascii=False, indent=2))
        return
    result = poll_task(key, task_id, args.interval, args.timeout, args.quiet)
    json_path, video_path = save_result(result, Path(args.output_dir), args.label)
    payload = {"result": result, "result_json": str(json_path), "video_path": str(video_path) if video_path else None}
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def cmd_poll(args: argparse.Namespace) -> None:
    result = poll_task(api_key(args), args.task_id, args.interval, args.timeout, args.quiet)
    if args.output_dir:
        json_path, video_path = save_result(result, Path(args.output_dir), args.label)
        print(json.dumps({"result": result, "result_json": str(json_path), "video_path": str(video_path) if video_path else None}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


def add_auth_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--api-key", help="API key value. Prefer UPTOKEN_API_KEY or --api-key-file.")
    parser.add_argument("--api-key-file", help="Path to a text file containing the API key.")


def main() -> None:
    parser = argparse.ArgumentParser(description="UpToken video generation helper")
    sub = parser.add_subparsers(dest="command", required=True)

    balance = sub.add_parser("balance")
    add_auth_flags(balance)
    balance.set_defaults(func=cmd_balance)

    upload = sub.add_parser("upload-asset")
    add_auth_flags(upload)
    upload.add_argument("--file", required=True)
    upload.set_defaults(func=cmd_upload_asset)

    generate = sub.add_parser("generate")
    add_auth_flags(generate)
    generate.add_argument("--prompt")
    generate.add_argument("--content-json", help="Path to a JSON file containing a content array.")
    generate.add_argument("--body-json", help="Path to a complete request body JSON file.")
    generate.add_argument("--model", default="seedance-2.0-fast")
    generate.add_argument("--duration", type=int, default=4)
    generate.add_argument("--resolution", default="480p")
    generate.add_argument("--ratio", default="16:9")
    generate.add_argument("--generate-audio", action="store_true")
    generate.add_argument("--image-urls", help="Comma-separated image URLs or asset:// IDs.")
    generate.add_argument("--video-urls", help="Comma-separated video URLs or asset:// IDs.")
    generate.add_argument("--audio-urls", help="Comma-separated audio URLs or asset:// IDs.")
    generate.add_argument("--first-frame-url")
    generate.add_argument("--last-frame-url")
    generate.add_argument("--output-dir", default="outputs")
    generate.add_argument("--label")
    generate.add_argument("--interval", type=int, default=5)
    generate.add_argument("--timeout", type=int, default=7200)
    generate.add_argument("--no-poll", action="store_true")
    generate.add_argument("--quiet", action="store_true")
    generate.set_defaults(func=cmd_generate)

    poll = sub.add_parser("poll")
    add_auth_flags(poll)
    poll.add_argument("--task-id", required=True)
    poll.add_argument("--output-dir")
    poll.add_argument("--label")
    poll.add_argument("--interval", type=int, default=5)
    poll.add_argument("--timeout", type=int, default=7200)
    poll.add_argument("--quiet", action="store_true")
    poll.set_defaults(func=cmd_poll)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
