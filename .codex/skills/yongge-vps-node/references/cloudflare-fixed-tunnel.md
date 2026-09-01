# Cloudflare fixed Tunnel for per-VPS subdomains

Use one fixed Cloudflare Tunnel per VPS node. All nodes may share the same Cloudflare account and zone.

## Naming

- Tunnel name: `yg-<node>`
- Public hostname: `<node>.<root-domain>` unless user specifies otherwise
- VMess origin service: `http://localhost:<vmess_port>`
- Subscription origin service: `http://localhost:<random_5_digit_sub_port>`
- DNS target: `<tunnel_id>.cfargotunnel.com`

## Required token permissions

The Cloudflare API token needs both scopes:

- Account Cloudflare Tunnel read/edit
- Zone DNS read/edit for the target zone

A token may successfully list/create tunnels while DNS record APIs return 403. Verify `/zones/{zone_id}/dns_records` specifically before concluding DNS is writable.

## DNS record rule

Cloudflare does not allow a CNAME at a name that already has A/AAAA records. For a fixed tunnel hostname:

1. List all records at `hostname`.
2. Delete same-name A/AAAA records.
3. Patch existing CNAME or create a proxied CNAME to `<tunnel_id>.cfargotunnel.com`.

## Ingress config with domain-only subscription

Path-specific subscription routes must appear before the generic hostname route:

```json
{
  "config": {
    "ingress": [
      {"hostname": "node.example.com", "path": "/TOKEN/clmi.yaml", "service": "http://localhost:50177"},
      {"hostname": "node.example.com", "path": "/TOKEN/sbox.json", "service": "http://localhost:50177"},
      {"hostname": "node.example.com", "path": "/TOKEN/jhsub.txt", "service": "http://localhost:50177"},
      {"hostname": "node.example.com", "service": "http://localhost:2052"},
      {"service": "http_status:404"}
    ]
  }
}
```

Use `scripts/cf_tunnel.py`:

```bash
python scripts/cf_tunnel.py ensure \
  --node NODE \
  --hostname node.example.com \
  --service http://localhost:2052 \
  --subscription-service http://localhost:50177 \
  --sub-token TOKEN
```

## Verification

- DNS record is a proxied CNAME to the tunnel target.
- Tunnel config includes subscription path routes and the generic VMess route.
- Connector token fetch works before deploying cloudflared.
- Cloudflare tunnel status is healthy or has active connections.
- `https://hostname/TOKEN/clmi.yaml` returns 200.
- WebSocket upgrade to `https://hostname/VMESS_PATH` returns 101.
