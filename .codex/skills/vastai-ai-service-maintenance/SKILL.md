---
name: vastai-ai-service-maintenance
description: Maintain AI services on a Vast.ai server, including safe in-place ComfyUI backend/frontend upgrades and Ollama service/model management. Preserves Vast.ai startup files, startup parameters, GPU-to-port mapping, local workspace state, ComfyUI custom node compatibility, and user-configured Ollama ports. Usually runs on the target server itself; SSH is optional only for remote debugging.
---

# Vast.ai AI Service Maintenance

Use this workflow for Vast.ai instances that run ComfyUI and/or Ollama. It covers:

- Safe ComfyUI upgrades under `/workspace/ComfyUI` using `/venv/main`.
- Ollama install/update, user-selected port configuration, model import, service start/stop, logs, and optional autostart.

Default assumption: the script or commands run **on the Vast.ai server itself**. Do not require SSH unless the user explicitly wants remote control.

## Non-Negotiables

### ComfyUI

- Do not edit `/opt/supervisor-scripts/*`, supervisor configs, portal files, `/workspace/comfyui_gpus_start.sh`, or other Vast.ai system/startup files.
- Do not change startup arguments, environment variables, base ports, port increments, GPU mapping, supervisor behavior, or ComfyUI launch commands.
- Never hardcode a GPU count or ComfyUI GPU ports such as `40052-40055`. Derive them from the existing startup script and actual GPU count.
- Preserve dirty worktree state. Record or restore existing local modifications/deletions such as `D input/example.png`.
- Keep a rollback ref before updating: `git branch vastai-pre-upgrade-$(date +%Y%m%d-%H%M%S) HEAD`.
- Update only `/workspace/ComfyUI`, `/venv/main` packages, and narrowly scoped custom-node compatibility fixes.
- Install dependencies through Vast.ai’s existing environment: `. /venv/main/bin/activate` then `uv pip --no-cache-dir install -r requirements.txt`.

### Ollama

- Do not assume an Ollama default port. Use the user-configured port stored in `/workspace/ollama/manager_config.json` or a command-line `--port`.
- A suggested first-time port such as `40056` may be shown in prompts, but it must not be silently used as a default.
- Store Ollama state under `/workspace/ollama`: logs, models, GGUF files, and manager config.
- When starting Ollama, set `OLLAMA_HOST={host}:{port}` and `OLLAMA_MODELS=/workspace/ollama/models` from the saved user config.
- Do not reuse ComfyUI ports for Ollama unless the user explicitly chooses one and it is free.
- In non-interactive mode, fail clearly if no Ollama port is configured and no `--port` is supplied.

## ComfyUI Preflight

Before upgrade, verify these exist:

- `/workspace`
- `/workspace/ComfyUI`
- `/workspace/ComfyUI/.git`
- `/workspace/ComfyUI/main.py`
- `/workspace/ComfyUI/requirements.txt`
- `/venv/main/bin/activate`
- `/venv/main/bin/python`
- `/opt/supervisor-scripts/comfyui.sh`
- `/workspace/comfyui_gpus_start.sh`

Verify commands:

```bash
command -v git
command -v python3
command -v curl
command -v ss
command -v supervisorctl
command -v uv
```

Record startup file hashes before any stop/update/restart:

```bash
sha256sum /opt/supervisor-scripts/comfyui.sh /workspace/comfyui_gpus_start.sh \
  > /tmp/vast_comfyui_startup_hash_before.txt
```

## ComfyUI Port And GPU Rules

Derive ports from the existing startup files and current hardware. This protects machines with 1, 2, 4, 8, or any other GPU count, and preserves the original port mapping.

```bash
get_supervisor_port() {
  grep -E 'COMFYUI_ARGS=.*--port[ =]?[0-9]+' /opt/supervisor-scripts/comfyui.sh 2>/dev/null \
    | sed -E 's/.*--port[ =]?([0-9]+).*/\1/' \
    | tail -1
}

get_gpu_base_port() {
  grep -E '^BASE_PORT=' /workspace/comfyui_gpus_start.sh 2>/dev/null \
    | sed -E 's/.*BASE_PORT=([0-9]+).*/\1/' \
    | tail -1
}

get_gpu_count() {
  nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null | wc -l
}

list_expected_ports() {
  supervisor_port=$(get_supervisor_port)
  base_port=$(get_gpu_base_port)
  gpu_count=$(get_gpu_count)

  [ -n "${supervisor_port:-}" ] && echo "$supervisor_port"

  if [ -n "${base_port:-}" ] && [ "${gpu_count:-0}" -gt 0 ]; then
    i=0
    while [ "$i" -lt "$gpu_count" ]; do
      echo "$((base_port + i))"
      i=$((i + 1))
    done
  fi
}
```

Only kill GPU listeners on those derived GPU ports. Do not kill broad `python main.py` patterns.

```bash
kill_expected_gpu_listeners() {
  base_port=$(get_gpu_base_port)
  gpu_count=$(get_gpu_count)
  [ -z "${base_port:-}" ] && return 0
  [ "${gpu_count:-0}" -le 0 ] && return 0

  i=0
  while [ "$i" -lt "$gpu_count" ]; do
    port=$((base_port + i))
    pid=$(ss -tlnp | grep ":${port} " | sed -E 's/.*pid=([0-9]+).*/\1/' | head -1 || true)
    [ -n "${pid:-}" ] && kill "$pid" || true
    i=$((i + 1))
  done
}
```

## ComfyUI Upgrade Flow

Use a fast-forward update whenever possible:

```bash
set -euo pipefail
cd /workspace/ComfyUI

git fetch --prune origin master
backup_branch="vastai-pre-upgrade-$(date +%Y%m%d-%H%M%S)"
old_head=$(git rev-parse --short HEAD)
new_head=$(git rev-parse --short origin/master)
git branch "$backup_branch" HEAD

git diff --name-only --diff-filter=D > /tmp/comfyui_deleted_paths.txt
if [ -s /tmp/comfyui_deleted_paths.txt ]; then
  xargs -a /tmp/comfyui_deleted_paths.txt git stash push -m "vastai-upgrade-preserve-deletions-$old_head" --
fi

supervisorctl stop comfyui || true
kill_expected_gpu_listeners
sleep 5

git switch master
git merge --ff-only origin/master

if [ -s /tmp/comfyui_deleted_paths.txt ]; then
  while IFS= read -r f; do [ -n "$f" ] && rm -f -- "$f"; done < /tmp/comfyui_deleted_paths.txt
  git stash list | grep -q "vastai-upgrade-preserve-deletions-$old_head" && git stash drop stash@{0} || true
fi

. /venv/main/bin/activate
uv pip --no-cache-dir install -r requirements.txt
```

Before restarting GPU helpers, verify startup files did not change:

```bash
sha256sum /opt/supervisor-scripts/comfyui.sh /workspace/comfyui_gpus_start.sh \
  > /tmp/vast_comfyui_startup_hash_after.txt
cmp -s /tmp/vast_comfyui_startup_hash_before.txt /tmp/vast_comfyui_startup_hash_after.txt
```

Then restart using the original Vast.ai path:

```bash
supervisorctl start comfyui || supervisorctl restart comfyui || true
sleep 10
WORKSPACE=/workspace /workspace/comfyui_gpus_start.sh || true
```

## ComfyUI Custom Nodes

If a custom node breaks after the core upgrade:

- First check whether that node has upstream updates: `git -C custom_nodes/NODE fetch --prune origin`.
- If no upstream fix exists, patch only the custom node, not ComfyUI core or Vast.ai startup files.
- Record the custom-node diff in the final summary.

Known ComfyUI `0.21.1` compatibility issue:

`ComfyUI-LTXVideo-Registry_Mattabyte` may import `precompute_freqs_cis` from `comfy.ldm.lightricks.model`, while newer ComfyUI exposes it as `self._precompute_freqs_cis(...)` on `LTXVModel`.

Narrow patch:

```diff
-    precompute_freqs_cis,
-        pe = precompute_freqs_cis(
+        pe = self._precompute_freqs_cis(
```

After patching, restart with the same original flow: `supervisorctl restart comfyui`, kill only derived GPU listener ports, then run `/workspace/comfyui_gpus_start.sh`.

## ComfyUI Final Verification

Wait for every derived port, not a hardcoded list:

```bash
failed=0
ports=$(list_expected_ports | sort -n | uniq)
[ -z "$ports" ] && exit 40

for port in $ports; do
  ok=0
  for i in $(seq 1 24); do
    body=$(curl -fsS --max-time 5 "http://127.0.0.1:${port}/system_stats" 2>/dev/null || true)
    version=$(printf "%s" "$body" | sed -n 's/.*"comfyui_version": "\([^"]*\)".*/\1/p')
    if [ -n "$version" ]; then
      echo "$port comfyui_version=$version"
      ok=1
      break
    fi
    sleep 5
  done
  [ "$ok" -ne 1 ] && failed=1
done
```

Also verify:

```bash
cd /workspace/ComfyUI
git rev-parse --short HEAD
git status --short
. /venv/main/bin/activate
python - <<'PY'
import comfyui_version
print("comfyui_version", getattr(comfyui_version, "__version__", "unknown"))
PY
python -m pip show comfyui-frontend-package comfyui-workflow-templates comfyui-embedded-docs \
  | awk '/^(Name|Version):/ {print}'
supervisorctl status comfyui
sha256sum /opt/supervisor-scripts/comfyui.sh /workspace/comfyui_gpus_start.sh
tail -n 280 /workspace/comfyui_gpu0.log | grep -Ei 'IMPORT FAILED|precompute_freqs_cis|traceback|cannot import|error|failed' || true
```

If startup file hashes changed, any derived ComfyUI port fails to respond, or the fresh logs still show `IMPORT FAILED.*ComfyUI-LTXVideo-Registry` / `precompute_freqs_cis`, treat the upgrade as failed and report the exact reason.

## Ollama Layout

Use these paths:

```bash
WORK_DIR=/workspace/ollama
LOG_DIR=/workspace/ollama/logs
MODELS_DIR=/workspace/ollama/models
GGUF_DIR=/workspace/ollama/models/gguf
CONFIG_FILE=/workspace/ollama/manager_config.json
```

Config shape:

```json
{"port": "USER_SELECTED_PORT", "host": "0.0.0.0"}
```

If the config file is missing, treat the port as empty. Prompt interactively or require `--port`; do not auto-fill a default.

## Ollama Port Handling

Interactive configuration:

```python
def prompt_for_ollama_port(current=""):
    # Show a suggestion such as 40056 only as UI help.
    # If no current port exists, user must type a numeric port.
    # Validate 1 <= port <= 65535.
    ...
```

Non-interactive behavior:

```text
If no saved port exists and no --port was supplied, exit with a clear error.
```

Before starting Ollama on a selected port, check whether it is already healthy:

```bash
curl -fsS --max-time 2 "http://127.0.0.1:${PORT}/api/tags"
```

If another process is listening on the selected port and it is not the expected Ollama API, report the conflict instead of silently choosing a different port.

## Ollama Install And Start

Install/update:

```bash
if ! command -v ollama >/dev/null 2>&1; then
  curl -fsSL https://ollama.com/install.sh | sh
fi
```

Start with the user-configured port:

```bash
mkdir -p /workspace/ollama/logs /workspace/ollama/models
export OLLAMA_HOST="${HOST}:${PORT}"
export OLLAMA_MODELS="/workspace/ollama/models"
export OLLAMA_CONTEXT_LENGTH="16384"
nohup ollama serve >> /workspace/ollama/logs/ollama.log 2>&1 &
```

Verify:

```bash
curl -fsS --max-time 5 "http://127.0.0.1:${PORT}/api/tags"
OLLAMA_HOST="127.0.0.1:${PORT}" ollama list
```

Stop:

```bash
systemctl stop ollama.service 2>/dev/null || true
pkill -f 'ollama serve' || true
```

## Ollama Model Import

Only import after the configured Ollama port is healthy.

Example Qwen GGUF workflow:

```bash
mkdir -p /workspace/ollama/models/gguf
curl -L -o /workspace/ollama/models/gguf/MODEL.gguf MODEL_URL
cat > /tmp/Modelfile_qwen <<'EOF'
FROM /workspace/ollama/models/gguf/MODEL.gguf
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""
EOF
OLLAMA_HOST="127.0.0.1:${PORT}" ollama create MODEL_NAME -f /tmp/Modelfile_qwen
```

Before downloading or importing, check:

```bash
OLLAMA_HOST="127.0.0.1:${PORT}" ollama list
```

Skip import if the model already exists.

## Ollama Autostart

Prefer systemd only when available:

```ini
[Service]
Environment="OLLAMA_HOST=HOST:USER_SELECTED_PORT"
Environment="OLLAMA_MODELS=/workspace/ollama/models"
ExecStart=/path/to/ollama serve
Restart=always
```

If systemd is unavailable, use crontab with the manager script and the saved user port:

```bash
@reboot python3 /path/to/vastai_manager.py serve --port USER_SELECTED_PORT
```

Do not write `40056` or any other suggested value into autostart unless that is the saved user-selected port.

## Notes

- Multiple ComfyUI instances can log a database lock warning when sharing `/workspace/ComfyUI/user/comfyui.db`. If services respond, report this as residual risk. Fixing it properly usually requires distinct `--database-url` or user directories per instance, which changes startup arguments and needs explicit approval.
- Some Vast.ai containers have `python3` globally but not `python`; check `/venv/main/bin/python` for ComfyUI and use activated `/venv/main` for runtime commands.
- If bundling this workflow into scripts, shell can provide the menu and Python can implement the business logic. The scripts should be location-independent, but should assume Vast.ai’s target paths are fixed.
- A good script name is `vastai_manager.sh` plus `vastai_manager.py`; the shell menu can expose “Ollama service/model management”, “ComfyUI check”, and “ComfyUI upgrade”.
