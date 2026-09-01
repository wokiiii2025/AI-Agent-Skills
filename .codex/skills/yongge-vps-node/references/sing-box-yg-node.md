# sing-box-yg node operations

## Files

| Path | Purpose |
|---|---|
| `/etc/s-box/sb.json` | sing-box server config |
| `/etc/s-box/clmi.yaml` | Clash/Mihomo subscription for OpenClash / Clash Party |
| `/etc/s-box/sbox.json` | Sing-box client config |
| `/etc/s-box/jhsub.txt` | Aggregate node share links |
| `/etc/s-box/cloudflared` | preferred cloudflared binary path |
| `/etc/systemd/system/argo-fixed-<node>.service` | fixed tunnel service |
| `/etc/systemd/system/sbox-sub-local.service` | local-only subscription service |
| `/root/websbox/<token>/` | local subscription web root |

## Mandatory pre-install cleanup

Before installing sing-box-yg on any VPS, detect existing node/proxy tools:

```bash
bash /tmp/detect_node_tools.sh
```

If it reports conflicts, clean them before continuing:

```bash
CLEAN_NODE_TOOLS=1 bash /tmp/detect_node_tools.sh
```

Treat these as conflicts: v2ray, xray, hysteria, trojan, naiveproxy, tuic, brook, shadowsocks, old sing-box outside `/etc/s-box`, old cloudflared/argo tunnel services, and old subscription web servers/nginx/openresty configs that bind planned ports.

## Detect vmess-ws port and path

```bash
python3 - <<'PY'
import json
cfg=json.load(open('/etc/s-box/sb.json'))
for inbound in cfg.get('inbounds', []):
    if inbound.get('type') == 'vmess':
        print(inbound.get('listen_port'))
        print((inbound.get('transport') or {}).get('path',''))
PY
```

## Fixed Tunnel requires local vmess TLS off

Cloudflared connects locally over HTTP/WebSocket:

```bash
jq '.inbounds |= map(if .type == "vmess" then .tls.enabled = false else . end)' /etc/s-box/sb.json > /etc/s-box/sb.json.tmp
mv /etc/s-box/sb.json.tmp /etc/s-box/sb.json
systemctl restart sing-box
```

Client subscription still uses TLS because the client connects to Cloudflare 443.

## Subscription URL versus node URL

- VMess share URL: a `vmess://...` node link for single-node import.
- Subscription URL: `https://<hostname>/<token>/clmi.yaml`, consumed by OpenClash/Clash Party.

The source `sb` script can create local IP subscription URLs such as `http://IP:PORT/<token>/clmi.yaml`, but for this skill prefer domain-only Cloudflare Tunnel URLs and do not expose `PORT` publicly.

## Domain-only subscription service

Run `scripts/setup_domain_subscription.sh` on the VPS. It:

- picks a random unused 5-digit port unless `SUB_PORT` is set;
- binds busybox httpd to `127.0.0.1:<port>` only;
- symlinks `/etc/s-box/clmi.yaml`, `sbox.json`, `jhsub.txt` under `/root/websbox/<token>/`;
- writes `/etc/s-box/subtoken.log` and `/etc/s-box/subport.log`;
- installs `sbox-sub-local.service`.

Verification:

```bash
systemctl is-active sbox-sub-local.service
ss -tlnp | grep ':<port>'       # must show 127.0.0.1:<port>
curl -I http://127.0.0.1:<port>/<token>/clmi.yaml
```

## Subscription patch

VMess node in `clmi.yaml` should use:

```yaml
server: cloudflare-ech.com
port: 443
tls: true
servername: node.example.com
ws-opts:
  headers:
    Host: node.example.com
```

Default multi-port ranges:

- Hysteria2: `50000-59999`
- TUIC: `60000-65535`

## CDN preferred address

The `sb` script option `3 -> 9` changes VMess client `server/add` to a Cloudflare preferred address. It is a configuration rewrite, not automatic latency selection. Common values:

- `cloudflare-ech.com`
- `www.visa.com.sg`
- `www.wto.org`
- `www.shopify.com`
- `yg1.ygkkk.dpdns.org` through `yg13.ygkkk.dpdns.org`

For fixed tunnel mode, keep Host/SNI as the node hostname and use the preferred address only as the client `server`.
