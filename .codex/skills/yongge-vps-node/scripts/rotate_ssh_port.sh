#!/usr/bin/env bash
# Rotate sshd to a random or supplied 5-digit port with a two-phase safety workflow.
# Phase 1 (default): keep old port + new port active, then print new port for client verification.
# Phase 2 (--finalize PORT): keep only PORT after the operator has verified a new SSH session.
set -euo pipefail
MODE="stage"
PORT="${SSH_NEW_PORT:-}"
if [ "${1:-}" = "--finalize" ]; then
  MODE="finalize"
  PORT="${2:-${SSH_NEW_PORT:-}}"
fi
if [ -z "$PORT" ]; then
  for _ in $(seq 1 100); do
    p=$(shuf -i 10000-65535 -n 1)
    if ! ss -tuln | awk '{print $5}' | grep -qE ":${p}$"; then PORT="$p"; break; fi
  done
fi
if ! printf '%s' "$PORT" | grep -qE '^[1-9][0-9]{4}$'; then
  echo "SSH port must be a 5-digit integer: $PORT" >&2
  exit 2
fi
mkdir -p /etc/ssh/sshd_config.d
cp -a /etc/ssh/sshd_config "/etc/ssh/sshd_config.bak.$(date +%Y%m%d%H%M%S)"

if [ "$MODE" = "stage" ]; then
  cat > /etc/ssh/sshd_config.d/99-codex-temp-dual-port.conf <<EOF
Port 22
Port ${PORT}
EOF
  printf '%s\n' "$PORT" > /root/.codex_new_ssh_port
else
  python3 - <<'PY'
from pathlib import Path
files=[Path('/etc/ssh/sshd_config')]
d=Path('/etc/ssh/sshd_config.d')
if d.exists():
    files += [p for p in d.glob('*.conf') if p.name not in {'99-codex-ssh-port.conf'}]
for p in files:
    if not p.exists():
        continue
    lines=p.read_text(errors='replace').splitlines()
    out=[]; changed=False
    for line in lines:
        stripped=line.strip().lower()
        if stripped.startswith('port ') and not line.lstrip().startswith('#'):
            out.append('# codex-disabled-old-ssh-port ' + line)
            changed=True
        else:
            out.append(line)
    if changed:
        p.write_text('\n'.join(out)+'\n')
PY
  rm -f /etc/ssh/sshd_config.d/99-codex-temp-dual-port.conf
  cat > /etc/ssh/sshd_config.d/99-codex-ssh-port.conf <<EOF
Port ${PORT}
EOF
fi

sshd -t
systemctl restart ssh || systemctl restart sshd
sleep 2
systemctl is-active --quiet ssh || systemctl is-active --quiet sshd
printf '{"mode":"%s","ssh_port":%s,"status":"active"}\n' "$MODE" "$PORT"
ss -tlnp | grep -E ":(22|${PORT})" || true
