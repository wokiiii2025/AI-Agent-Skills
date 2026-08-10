#!/usr/bin/env python3
import argparse
import json
import hashlib
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
VERSION_PATH = SKILL_DIR / "VERSION.json"
DEFAULT_LATEST_URL = "http://162.250.126.10:38970/shared/api-contract-collab-latest.json"


def load_version():
    try:
        return json.loads(VERSION_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"version": "0.0.0"}


def parse_version(value):
    parts = []
    for part in str(value or "0").split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def fetch_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def download(url, out):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp, out.open("wb") as f:
        shutil.copyfileobj(resp, f)


def file_sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_download(zip_path, latest):
    expected_sha = str(latest.get("sha256") or "").strip().lower()
    expected_bytes = latest.get("bytes")
    actual_sha = file_sha256(zip_path)
    actual_bytes = Path(zip_path).stat().st_size
    print(f"downloadBytes={actual_bytes}")
    print(f"downloadSha256={actual_sha}")
    if expected_bytes is not None and int(expected_bytes) != actual_bytes:
        raise SystemExit(f"download size mismatch: expected {expected_bytes}, got {actual_bytes}")
    if expected_sha and expected_sha != actual_sha:
        raise SystemExit(f"download sha256 mismatch: expected {expected_sha}, got {actual_sha}")


def install_zip(zip_path):
    parent = SKILL_DIR.parent
    backup = parent / f"api-contract-collab.backup-{load_version().get('version','unknown')}"
    with zipfile.ZipFile(zip_path) as z:
        roots = {Path(name).parts[0] for name in z.namelist() if name.strip()}
        if "api-contract-collab" not in roots:
            raise SystemExit("Downloaded zip does not contain api-contract-collab/ root folder")
        if backup.exists():
            shutil.rmtree(backup)
        shutil.copytree(SKILL_DIR, backup, ignore=shutil.ignore_patterns(".local", "__pycache__", "*.pyc"))
        tmp = Path(tempfile.mkdtemp(prefix="api-collab-install-"))
        z.extractall(tmp)
        extracted = tmp / "api-contract-collab"
        for item in extracted.iterdir():
            if item.name == ".local":
                continue
            dest = SKILL_DIR / item.name
            if dest.exists():
                if dest.is_dir():
                    shutil.rmtree(dest)
                else:
                    dest.unlink()
            if item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
    return backup


def main():
    parser = argparse.ArgumentParser(description="Check or install latest api-contract-collab Skill version")
    parser.add_argument("--latest-url", default=os.environ.get("API_COLLAB_SKILL_LATEST_URL", DEFAULT_LATEST_URL))
    parser.add_argument("--install", action="store_true", help="download and install the latest version when newer")
    args = parser.parse_args()

    current = load_version()
    latest = fetch_json(args.latest_url)
    current_version = current.get("version", "0.0.0")
    latest_version = latest.get("version", "0.0.0")
    newer = parse_version(latest_version) > parse_version(current_version)
    print(f"current={current_version}")
    print(f"latest={latest_version}")
    print(f"latestUrl={args.latest_url}")
    print(f"downloadUrl={latest.get('downloadUrl')}")
    if not newer:
        print("status=up-to-date")
        return
    print("status=update-available")
    if args.install:
        url = latest.get("downloadUrl")
        if not url:
            raise SystemExit("latest metadata missing downloadUrl")
        tmp = Path(tempfile.mkdtemp(prefix="api-collab-update-")) / latest["zipFile"]
        download(url, tmp)
        verify_download(tmp, latest)
        backup = install_zip(tmp)
        print(f"installed={latest_version}")
        print(f"backup={backup}")
    else:
        print("hint=run with --install to update")


if __name__ == "__main__":
    main()
