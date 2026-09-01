#!/usr/bin/env bash
set -euo pipefail

# Detect and optionally clean existing proxy/node tooling before installing sing-box-yg.
# Usage:
#   bash detect_node_tools.sh          # detect only, exit 10 if conflicts found
#   CLEAN_NODE_TOOLS=1 bash detect_node_tools.sh   # stop/disable/remove known conflicts

CLEAN="${CLEAN_NODE_TOOLS:-0}"

patterns='v2ray|xray|hysteria|trojan|naiveproxy|tuic|brook|shadowsocks|ssserver|ss-local|sing-box|cloudflared|argo'
services="$(systemctl list-units --type=service --all --no-legend 2>/dev/null | awk '{print $1}' | grep -Ei "$patterns" || true)"
processes="$(ps -eo pid=,args= 2>/dev/null | grep -Ei "$patterns" | grep -vE 'grep|detect_node_tools' || true)"
dirs=""
for d in /etc/s-box /etc/sing-box /etc/v2ray /etc/xray /etc/hysteria /etc/trojan /etc/tuic /usr/local/etc/v2ray /usr/local/etc/xray; do
  [ -e "$d" ] && dirs="${dirs}${d}"$'\n'
done
bins=""
for b in /usr/bin/sing-box /usr/local/bin/sing-box /usr/bin/v2ray /usr/local/bin/v2ray /usr/bin/xray /usr/local/bin/xray /usr/bin/hysteria /usr/local/bin/hysteria /usr/bin/cloudflared /usr/local/bin/cloudflared; do
  [ -e "$b" ] && bins="${bins}${b}"$'\n'
done
ports="$(ss -tulnp 2>/dev/null | grep -Ei "$patterns|:80 |:443 |:8888 " || true)"

echo "== existing proxy/node services =="
printf '%s\n' "${services:-none}"
echo "== existing proxy/node processes =="
printf '%s\n' "${processes:-none}"
echo "== existing proxy/node directories =="
printf '%s\n' "${dirs:-none}"
echo "== existing proxy/node binaries =="
printf '%s\n' "${bins:-none}"
echo "== relevant listening ports =="
printf '%s\n' "${ports:-none}"

if [ -z "$services$processes$dirs$bins" ]; then
  echo "preflight clean: no existing node tools detected"
  exit 0
fi

if [ "$CLEAN" != "1" ]; then
  echo "conflicts detected; rerun with CLEAN_NODE_TOOLS=1 after confirming cleanup is intended" >&2
  exit 10
fi

echo "== cleaning detected proxy/node tools =="
for svc in $services; do
  systemctl stop "$svc" 2>/dev/null || true
  systemctl disable "$svc" 2>/dev/null || true
done

pkill -f 'v2ray|xray|hysteria|trojan|naiveproxy|tuic|brook|ssserver|ss-local|cloudflared tunnel|argo' 2>/dev/null || true

rm -rf /etc/v2ray /etc/xray /etc/hysteria /etc/trojan /etc/tuic /usr/local/etc/v2ray /usr/local/etc/xray
rm -rf /etc/sing-box
rm -f /etc/systemd/system/v2ray.service /etc/systemd/system/xray.service /etc/systemd/system/hysteria*.service
rm -f /etc/systemd/system/trojan*.service /etc/systemd/system/tuic*.service /etc/systemd/system/argo.service
rm -f /usr/bin/v2ray /usr/local/bin/v2ray /usr/bin/xray /usr/local/bin/xray
rm -f /usr/bin/hysteria /usr/local/bin/hysteria /usr/bin/tuic /usr/local/bin/tuic
systemctl daemon-reload

echo "== verify after cleanup =="
remaining_services="$(systemctl list-units --type=service --all --no-legend 2>/dev/null | awk '{print $1}' | grep -Ei 'v2ray|xray|hysteria|trojan|naiveproxy|tuic|brook' || true)"
remaining_processes="$(ps -eo pid=,args= 2>/dev/null | grep -Ei 'v2ray|xray|hysteria|trojan|naiveproxy|tuic|brook|ssserver|ss-local' | grep -vE 'grep|detect_node_tools' || true)"
printf 'remaining_services=%s\n' "${remaining_services:-none}"
printf 'remaining_processes=%s\n' "${remaining_processes:-none}"

if [ -n "$remaining_services$remaining_processes" ]; then
  echo "cleanup incomplete; inspect manually before installing" >&2
  exit 11
fi

echo "cleanup complete"
