#!/usr/bin/env python3
"""Sync git-backed skills into .codex/skills from skills-sources.json.

Local-snapshot skills are intentionally left unchanged because no upstream repo
was detected. Run this script locally or through GitHub Actions.
"""
from __future__ import annotations
import json, shutil, subprocess, tempfile
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "skills-sources.json"
SKILLS_DIR = ROOT / ".codex" / "skills"

IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".local"}
IGNORE_FILES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "config.json",
    "providers.json",
    "credentials.json",
    "secrets.json",
}

def ignore_func(dirpath, names):
    ignored = []
    for n in names:
        low = n.lower()
        if n in IGNORE_DIRS or low in IGNORE_FILES or low.endswith((".pyc", ".pyo", ".key", ".pem")):
            ignored.append(n)
    return ignored

def run(cmd, cwd=None):
    print("+", " ".join(cmd))
    subprocess.run(cmd, cwd=cwd, check=True)

def sync_one(entry):
    if entry.get("source_type") != "git":
        return False
    skill = entry["skill"]
    repo = entry["source_repo"]
    ref = entry.get("source_ref") or "main"
    source_path = entry["source_path"].strip("/")
    with tempfile.TemporaryDirectory(prefix="skill-sync-") as td:
        td = Path(td)
        clone_dir = td / "src"
        run(["git", "clone", "--depth", "1", "--branch", ref, repo, str(clone_dir)])
        src = clone_dir / source_path
        if not src.exists():
            raise FileNotFoundError(f"{skill}: source path not found: {source_path}")
        dest = SKILLS_DIR / skill
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest, ignore=ignore_func)
        if entry.get("rewrite_name"):
            skill_md = dest / "SKILL.md"
            if skill_md.exists():
                text = skill_md.read_text(encoding="utf-8", errors="replace")
                text = re.sub(r"(?m)^name:\s*.*$", f"name: {skill}", text, count=1)
                frontmatter = re.match(r"(?s)^---\s*\n(.*?)\n---\s*\n?(.*)$", text)
                if frontmatter:
                    fm, body = frontmatter.group(1), frontmatter.group(2)
                    name_line = f"name: {skill}"
                    description_match = re.search(r"(?ms)^description:\s*(.*?)(?=\n[a-zA-Z_-]+:|\Z)", fm)
                    description = description_match.group(1).rstrip() if description_match else ""
                    if description:
                        text = f"---\n{name_line}\ndescription: {description}\n---\n{body}"
                    else:
                        text = f"---\n{name_line}\ndescription: Synced upstream skill from {repo}.\n---\n{body}"
                if entry.get("ascii_safe"):
                    text = (
                        text.replace("→", "->")
                        .replace("—", "-")
                        .replace("–", "-")
                        .replace("…", "...")
                        .replace("要求", "Requirements")
                    )
                    text = text.encode("ascii", errors="ignore").decode("ascii")
                skill_md.write_text(text, encoding="utf-8")
        print(f"synced {skill} <- {repo}@{ref}:{source_path}")
        return True

def main():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    count = 0
    for entry in data["skills"]:
        if sync_one(entry):
            count += 1
    print(f"Synced {count} git-backed skills.")

if __name__ == "__main__":
    main()
