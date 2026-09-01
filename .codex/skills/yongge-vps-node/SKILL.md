---
name: yongge-vps-node
description: "Conversation-driven VPS operations for proxy nodes and AI web services on SSH servers. Use when Codex needs to add, inspect, repair, migrate, or maintain VPS proxy nodes through dialogue (sing-box-yg, Cloudflare fixed Tunnel, domain-only Clash/OpenClash subscriptions, SSH random 5-digit port rotation) or deploy/repair VPS-hosted AI web tools such as DeepSeek Harness/dsh Web, Hermes, and reverse-proxy/security-group issues."
---

# Yongge VPS Node

Operate sing-box-yg VPS proxy nodes and VPS-hosted AI web services through dialogue. Do not require a batch manifest. Process only the node(s) or service(s) mentioned in the current turn, while keeping local state for follow-up.

## Core model

- One Cloudflare zone/root domain can host many nodes, each as a separate subdomain.
- Each VPS gets its own node name, hostname, Cloudflare Tunnel, cloudflared systemd service, domain-only subscription path, and state entry.
- Prefer **fixed Cloudflare Tunnel + domain URL** over exposing host ports. OpenClash/Clash Party should consume `https://<node-domain>/<token>/clmi.yaml`.
- Use random 5-digit **local-only** subscription ports (127.0.0.1:<port>), never public 0.0.0.0:<port> for subscription.
- When the user asks to change SSH, rotate to a random 5-digit port with a two-phase dual-port workflow, verify a new private-key SSH session, then close port 22.
- Never print or persist Cloudflare API tokens in the skill folder or final answer. Use env vars/current process only.

## State

Use `scripts/node_state.py` to store non-secret node metadata at:

```text
%USERPROFILE%\.codex\state\yongge-vps-node\nodes.json
```

State is a convenience cache. Verify live VPS and Cloudflare state before claiming success.

## Dialogue workflow

1. **Classify intent**
   - Add/configure node: user gives VPS + subdomain.
   - Repair: tunnel down, subscription broken, OpenClash/Clash Party issue.
   - Inspect/test: status, URL, ports, DNS, WebSocket, subscription, latency.
   - Migrate/rename: hostname/IP changes.
   - SSH hardening: rotate sshd from 22 to a random 5-digit port and verify private-key reconnection.
   - All nodes: user asks to check/export/fix all known nodes.
   - AI web service: user asks to install, replace, expose, auto-update, or debug DeepSeek Harness/dsh Web, Hermes, OpenCode, reverse proxy, public port, browser UI, workspace picker, or API transport errors.

2. **Load known context**
   - Run `python scripts/node_state.py list` or `get <name>`.
   - Reuse known root domain, account/zone id, tunnel id/name, SSH defaults, vmess port/path, and subscription URL only after live verification.

3. **Collect minimal missing input**
   - Cloudflare: `CF_API_TOKEN`, account id, zone id/name. If token is pasted, put it in a process env var; do not echo it.
   - VPS: host/IP, SSH user, SSH port, auth method.
   - Node: node name and hostname. Default hostname: `<node>.<root-domain>`.

4. **Inspect VPS and clean before install**
   - Confirm SSH works.
   - Before any install, upload/run `scripts/detect_node_tools.sh`.
   - If other proxy/node tools or old cloudflared/argo/subscription services exist, clean only clearly related conflicts, then verify services/processes/ports are gone.
   - Detect sing-box-yg files: `/etc/s-box/sb.json`, `/etc/s-box/clmi.yaml`, `/etc/s-box/sbox.json`, `/etc/s-box/jhsub.txt`, `/usr/bin/sb`.
   - Detect VMess WS port/path from `/etc/s-box/sb.json`.

5. **Configure Cloudflare fixed Tunnel**
   - Use `scripts/cf_tunnel.py ensure --node NAME --hostname HOSTNAME --service http://localhost:VMESS_PORT`.
   - Reuse `yg-<node>` tunnel when present.
   - Ensure DNS is proxied CNAME to `<tunnel_id>.cfargotunnel.com`. Delete same-name A/AAAA records before creating CNAME.
   - If DNS list returns 403 but tunnel APIs work, recheck token permissions for Zone DNS read/edit; do not assume account tunnel permissions imply DNS permissions.
   - Retrieve connector token only for VPS setup, then remove temporary local/remote copies.

6. **Configure VPS fixed tunnel**
   - Run `scripts/remote_node_setup.sh` on the VPS with `NODE_NAME`, `CF_TUNNEL_TOKEN`, `HOSTNAME`, and `VMESS_PORT`.
   - Keep local VMess as plain WS (`tls.enabled=false`) because Cloudflare provides client-facing TLS on 443.
   - Create `argo-fixed-<node>.service`; stop legacy `argo`/temporary cloudflared only when they target this node.
   - Verify `systemctl is-active sing-box` and `systemctl is-active argo-fixed-<node>`.

7. **Patch node config and subscription**
   - Use `scripts/fix_clmi.py --hostname HOSTNAME --edge-server cloudflare-ech.com`.
   - VMess client fields should be: `server: cloudflare-ech.com`, `port: 443`, `tls: true`, `servername: HOSTNAME`, WS Host `HOSTNAME`.
   - This is the CDN preferred-address model: client connects to a Cloudflare edge/preferred domain, Host/SNI routes to the fixed tunnel hostname.
   - Do not add Hy2/TUIC `ports:` hopping ranges unless the service-side sing-box config is explicitly configured to listen on the same ranges. Default sing-box-yg installs normally listen on one UDP port per protocol, so subscription output should keep only `port: <actual_port>`.

8. **Rotate SSH port when requested**
   - Read `references/ssh-port-rotation.md` before changing SSH.
   - Upload/run scripts/rotate_ssh_port.sh on the VPS.
   - Stage first with old + new ports active; do not close port 22 yet.
   - Open a fresh SSH connection from Codex using the same private key and the new 5-digit port.
   - Finalize only after the new private-key login succeeds; then verify port 22 is closed and update ssh_port in state.

9. **Create domain-only subscription URL**
   - Run `scripts/setup_domain_subscription.sh` on the VPS. It picks an unused random 5-digit localhost port and serves `/etc/s-box/clmi.yaml`, `sbox.json`, and `jhsub.txt` under `/root/websbox/<token>/`.
   - The service must listen on `127.0.0.1:<random-5-digit-port>`, not public interfaces.
   - Update Cloudflare tunnel config with path-specific subscription routes before the generic VMess route:
     - `/<token>/clmi.yaml -> http://localhost:<sub_port>`
     - `/<token>/sbox.json -> http://localhost:<sub_port>`
     - `/<token>/jhsub.txt -> http://localhost:<sub_port>`
     - hostname fallback/generic route -> `http://localhost:<vmess_port>`
   - Use `scripts/cf_tunnel.py ... --subscription-service http://localhost:<sub_port> --sub-token <token>` for this combined config.
   - Report the Clash/OpenClash URL as `https://<hostname>/<token>/clmi.yaml`.

10. **DeepSeek Harness / dsh Web service on VPS**
   - Read `references/deepseek-harness-web.md` before installing or repairing dsh Web.
   - Prefer dsh bound to `127.0.0.1:3081` and expose through 1Panel/OpenResty or another reverse proxy; current dsh may reject `--host 0.0.0.0`.
   - If the user replaces OpenCode, disable `opencode-web.service` and remove it from shared auto-update timers.
   - For IP:port HTTP access, add the reverse-proxy `crypto.randomUUID` polyfill because browsers hide `crypto.randomUUID()` outside HTTPS/localhost secure contexts.
   - For `/api/* HTTP 403`, add dsh `--trusted-host <public-host>` and `--trusted-host <public-host>:<public-port>`, and preserve `Host` with `$http_host` in the proxy.
   - Validate public port reachability from outside and local service health from the VPS.

11. **Verify before reporting success**
   - Cloudflare tunnel status: healthy or connections present.
   - DNS record: proxied CNAME to tunnel target.
   - VPS services: `sing-box`, `argo-fixed-<node>`, and `sbox-sub-local.service` active when subscription is enabled.
   - Ports: subscription on `127.0.0.1:<sub_port>` only; VMess origin on configured port.
   - Subscription URL returns `HTTP/1.1 200 OK` and YAML body.
   - VMess WS path returns `HTTP/1.1 101 Switching Protocols` when probed with WebSocket upgrade headers. Plain `curl -I` may return 405; that is acceptable if WebSocket upgrade is 101.
   - Update state with verified `subscription_url`, `vmess_path`, ports, and status.

## Reference routing

- Cloudflare APIs, DNS CNAME replacement, path routing, and connector tokens: read `references/cloudflare-fixed-tunnel.md`.
- sing-box-yg internals, generated subscription formats, local-only subscription service, CDN preferred address: read `references/sing-box-yg-node.md`.
- Conversation patterns and state discipline: read `references/conversation-workflow.md`.
- Failure diagnosis: read `references/troubleshooting.md`.
- SSH random 5-digit port rotation: read `references/ssh-port-rotation.md`.
- DeepSeek Harness/dsh Web deployment, IP:port HTTP fixes, trusted-host 403 fixes, and daily AI service updater: read `references/deepseek-harness-web.md`.

## Important rules

- Do not expose subscription via public host port. Use domain-only HTTPS through Cloudflare Tunnel.
- Do not use fixed 8888 unless the user explicitly asks; choose a random unused 5-digit local port.
- Do not close SSH port 22 until a fresh private-key login to the new 5-digit port has succeeded; after finalization, verify port 22 is closed.
- Keep subscription URL path stable after creation unless the user rotates UUID/token.
- Do not confuse node URL with subscription URL: node URL is a VMess share link; subscription URL is `https://host/token/clmi.yaml` for OpenClash/Clash Party.
- Fixed Cloudflare Tunnel and local VMess TLS are mutually exclusive for this workflow.
- Use separate hostnames/tunnels per VPS, e.g. `hei5s1a.example.com`, `hei5s1b.example.com`.
- Avoid broad destructive cleanup. Stop/replace only services clearly owned by this workflow.
- Never claim a node works until live checks have run in the current turn.





