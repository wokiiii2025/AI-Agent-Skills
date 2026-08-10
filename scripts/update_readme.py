#!/usr/bin/env python3
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'skills-sources.json').read_text(encoding='utf-8'))
skills = sorted(data['skills'], key=lambda x: x['skill'].lower())

def esc(s):
    s = str(s or '').replace('\n',' ').replace('|','\\|')
    return re.sub(r'\s+', ' ', s).strip()
rows = []
for s in skills:
    repo_path = f"[`{esc(s['repo_path'])}`]({esc(s['repo_path'])})"
    src = s.get('source_repo') or 'Local snapshot / upstream not detected'
    if s.get('source_repo'):
        ref = s.get('source_ref') or 'main'
        path = s.get('source_path') or ''
        url = s['source_repo'].replace('github.com/', 'github.com/')
        if path:
            src = f"[{esc(s['source_repo'])}/tree/{esc(ref)}/{esc(path)}]({esc(s['source_repo'])}/tree/{esc(ref)}/{esc(path)})"
        else:
            src = f"[{esc(s['source_repo'])}]({esc(s['source_repo'])})"
    rows.append(f"| {repo_path} | {src} | {esc(s.get('description'))} |")

readme = f"""# AI Agent Skills\n\nA syncable collection of personal Codex / AI-agent skills. Skills are stored under `.codex/skills/` so agents can install or mirror them consistently.\n\n## Install\n\n### PowerShell\n\n```powershell\ngit clone https://github.com/wokiiii2025/AI-Agent-Skills.git\ncd AI-Agent-Skills\n./scripts/install.ps1\n```\n\n### Bash\n\n```bash\ngit clone https://github.com/wokiiii2025/AI-Agent-Skills.git\ncd AI-Agent-Skills\nbash scripts/install.sh\n```\n\n## Auto sync\n\n- Git-backed skills are listed in `skills-sources.json`.\n- Run `python scripts/sync_skills.py` to refresh them from upstream.\n- GitHub Actions workflow `.github/workflows/sync-skills.yml` runs daily and can also be triggered manually.\n- Local snapshot skills stay unchanged until manually updated because no upstream repository was detected in local metadata.\n\n## Skill catalog\n\n| 仓库路径 | 源开源仓库地址 | Skill 说明 |\n|---|---|---|\n""" + "\n".join(rows) + "\n\n"


dups = data.get('duplicates_skipped') or []
if dups:
    readme += "## Duplicate local skills skipped\n\n"
    readme += "| Skill | Kept from | Skipped from |\n|---|---|---|\n"
    for d in dups:
        readme += f"| `{esc(d['name'])}` | `{esc(d['kept_from'])}` | `{esc(d['skipped_from'])}` |\n"

readme += "\n## Notes\n\nSecrets and local environment files such as `.env`, `.key`, and `.pem` are intentionally excluded from snapshots.\n"
(ROOT / 'README.md').write_text(readme, encoding='utf-8')
