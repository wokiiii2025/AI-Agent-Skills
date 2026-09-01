#!/usr/bin/env bash
# Configure sing-box-yg subscription files behind a local-only HTTP service for Cloudflare Tunnel path routing.
set -euo pipefail
SUB_TOKEN="${SUB_TOKEN:-}"
SUB_PORT="${SUB_PORT:-}"
SUB_ROOT="${SUB_ROOT:-/root/websbox}"
SERVICE_NAME="${SERVICE_NAME:-sbox-sub-local.service}"

if [ ! -f /etc/s-box/sb.json ]; then
  echo "missing /etc/s-box/sb.json" >&2
  exit 2
fi
if [ -z "$SUB_TOKEN" ]; then
  SUB_TOKEN="$(python3 - <<'PY'
import json
cfg=json.load(open('/etc/s-box/sb.json'))
for inbound in cfg.get('inbounds',[]):
    if inbound.get('type') in ('vmess','vless','hysteria2','tuic','anytls'):
        users=inbound.get('users') or []
        if users and users[0].get('uuid'):
            print(users[0]['uuid']); break
PY
)"
fi
if [ -z "$SUB_TOKEN" ]; then echo "cannot detect subscription token/uuid" >&2; exit 3; fi
if [ -z "$SUB_PORT" ]; then
  for _ in $(seq 1 100); do
    p=$(shuf -i 10000-65535 -n 1)
    if ! ss -tuln | awk '{print $5}' | grep -qE ":${p}$"; then SUB_PORT="$p"; break; fi
  done
fi
if [ -z "$SUB_PORT" ]; then echo "cannot pick an unused 5-digit local port" >&2; exit 4; fi

mkdir -p "$SUB_ROOT/$SUB_TOKEN"
ln -sf /etc/s-box/clmi.yaml "$SUB_ROOT/$SUB_TOKEN/clmi.yaml"
ln -sf /etc/s-box/sbox.json "$SUB_ROOT/$SUB_TOKEN/sbox.json"
ln -sf /etc/s-box/jhsub.txt "$SUB_ROOT/$SUB_TOKEN/jhsub.txt"
printf '%s\n' "$SUB_TOKEN" > /etc/s-box/subtoken.log
printf '%s\n' "$SUB_PORT" > /etc/s-box/subport.log

cat > "/etc/systemd/system/${SERVICE_NAME}" <<EOF
[Unit]
Description=Local-only sing-box subscription files for Cloudflare Tunnel
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/bin/busybox httpd -f -p 127.0.0.1:${SUB_PORT} -h ${SUB_ROOT}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME" >/dev/null
systemctl restart "$SERVICE_NAME"
sleep 1
systemctl is-active --quiet "$SERVICE_NAME"
curl -fsSI --max-time 5 "http://127.0.0.1:${SUB_PORT}/${SUB_TOKEN}/clmi.yaml" >/dev/null
printf '{"sub_token":"%s","sub_port":%s,"service":"%s","origin":"http://localhost:%s","clash_path":"/%s/clmi.yaml"}\n' "$SUB_TOKEN" "$SUB_PORT" "$SERVICE_NAME" "$SUB_PORT" "$SUB_TOKEN"
