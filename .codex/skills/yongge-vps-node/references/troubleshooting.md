# Troubleshooting

## Cloudflare DNS API still returns 403

Tunnel APIs and DNS APIs use different permissions. Probe all of these:

- `/user/tokens/verify`
- `/zones?name=<zone>`
- `/zones/<zone_id>/dns_records?name=<hostname>`
- `/accounts/<account_id>/cfd_tunnel/<tunnel_id>`

If tunnel APIs succeed but DNS records fail, the token needs Zone DNS read/edit for the target zone.

## Hostname still returns 521 after tunnel creation

Likely the hostname still has a proxied A/AAAA record to the origin IP. Replace with proxied CNAME to `<tunnel_id>.cfargotunnel.com`. Delete same-name A/AAAA first.

## Subscription URL returns 404 or routes to VMess

Cloudflare ingress ordering is wrong. Put subscription path routes before the generic hostname VMess route:

1. `/<token>/clmi.yaml -> http://localhost:<sub_port>`
2. `/<token>/sbox.json -> http://localhost:<sub_port>`
3. `/<token>/jhsub.txt -> http://localhost:<sub_port>`
4. `hostname -> http://localhost:<vmess_port>`
5. fallback 404

## Subscription port is exposed publicly

Fix the systemd service to bind busybox to `127.0.0.1:<random_5_digit_port>`, not `0.0.0.0` and not the public IP. Use `scripts/setup_domain_subscription.sh`.

Check:

```bash
ss -tlnp | grep ':<sub_port>'
```

Expected:

```text
127.0.0.1:<sub_port>
```

## `handshake error: bad "Upgrade" header` in OpenClash / Clash Party

This usually means the VMess WebSocket endpoint was used as a subscription URL, or an HTTP client fetched the VMess path without WebSocket upgrade headers.

Use this for subscription import:

```text
https://HOST/TOKEN/clmi.yaml
```

Do not use this as a subscription URL:

```text
https://HOST/VMESS_PATH
```

The VMess path belongs inside the node config as `ws-opts.path`, not in OpenClash subscription management.
## VMess path returns 405/502 to plain curl

Plain `curl -I` is not a valid WebSocket client. Test WebSocket upgrade instead:

```bash
curl --http1.1 -k -i \
  -H 'Connection: Upgrade' \
  -H 'Upgrade: websocket' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  -H 'Sec-WebSocket-Version: 13' \
  https://HOST/VMESS_PATH
```

Expected success indicator: `HTTP/1.1 101 Switching Protocols`.

## OpenClash subscription update fails from router

Use the domain-only HTTPS URL:

```text
https://HOST/TOKEN/clmi.yaml
```

Do not use `http://IP:PORT/...` for this workflow. If OpenClash runs in a network that cannot reach Cloudflare reliably, test the URL from the router shell and compare with Clash Party from a desktop network.

## Fixed Tunnel / local VMess TLS conflict

For fixed Cloudflare Tunnel, local VMess must be WS over HTTP. If local VMess TLS is enabled, `cloudflared` origin `http://localhost:<vmess_port>` will mismatch. Disable local VMess TLS, restart sing-box, then re-test WebSocket upgrade.

## Tunnel healthy but client node slow

`cloudflare-ech.com` is only a preferred-address default. Try other preferred domains from `sing-box-yg-node.md`, while preserving Host/SNI as the node hostname. Record the chosen address in state or user notes.

