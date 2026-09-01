#!/usr/bin/env bash
set -euo pipefail
: "${NODE_NAME:?NODE_NAME required}"
: "${HOSTNAME:?HOSTNAME required}"
: "${CF_TUNNEL_TOKEN:?CF_TUNNEL_TOKEN required}"
VMESS_PORT="${VMESS_PORT:-}"
SERVICE_NAME="argo-fixed-${NODE_NAME}.service"
CLOUDFLARED="/etc/s-box/cloudflared"

if [ ! -f /etc/s-box/sb.json ]; then
  echo "missing /etc/s-box/sb.json; install sing-box-yg first" >&2
  exit 2
fi

if [ -z "$VMESS_PORT" ]; then
  VMESS_PORT="$(python3 - <<'PY'
import json
cfg=json.load(open('/etc/s-box/sb.json'))
for inbound in cfg.get('inbounds',[]):
    if inbound.get('type')=='vmess':
        print(inbound.get('listen_port',''))
        break
PY
)"
fi
if [ -z "$VMESS_PORT" ]; then echo "cannot detect vmess port" >&2; exit 3; fi

cp /etc/s-box/sb.json "/etc/s-box/sb.json.bak.$(date +%Y%m%d%H%M%S)"
if command -v jq >/dev/null 2>&1; then
  jq '.inbounds |= map(if .type == "vmess" then .tls.enabled = false else . end)' /etc/s-box/sb.json > /etc/s-box/sb.json.tmp
  mv /etc/s-box/sb.json.tmp /etc/s-box/sb.json
fi
systemctl restart sing-box
sleep 2
systemctl is-active --quiet sing-box

if [ ! -x "$CLOUDFLARED" ]; then
  arch="$(uname -m)"
  url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
  case "$arch" in
    aarch64|arm64) url="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64" ;;
  esac
  curl -L "$url" -o "$CLOUDFLARED"
  chmod +x "$CLOUDFLARED"
fi

install -m 600 /dev/null /root/.cf_tunnel_token_${NODE_NAME}
printf 'CF_TUNNEL_TOKEN=%q\n' "$CF_TUNNEL_TOKEN" > /root/.cf_tunnel_token_${NODE_NAME}

cat > "/etc/systemd/system/${SERVICE_NAME}" <<EOF
[Unit]
Description=Cloudflare fixed tunnel for ${NODE_NAME} (${HOSTNAME})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
EnvironmentFile=/root/.cf_tunnel_token_${NODE_NAME}
ExecStart=${CLOUDFLARED} tunnel --no-autoupdate --edge-ip-version auto --protocol http2 run --token \${CF_TUNNEL_TOKEN}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE_NAME"
sleep 3
systemctl is-active --quiet "$SERVICE_NAME"
echo "node=$NODE_NAME hostname=$HOSTNAME vmess_port=$VMESS_PORT service=$SERVICE_NAME active"
