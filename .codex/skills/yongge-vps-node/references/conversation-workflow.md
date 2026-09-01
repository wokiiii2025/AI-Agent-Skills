# Conversation workflow

This skill is conversation-first. Users may provide information gradually:

- "把这台 1.2.3.4 配成 hei5b1.yuns.top"
- "再加一台 hei5b2"
- "检查 hei5b1"
- "所有节点导出订阅地址"
- "hei5b3 不通，修一下"

## Slot model

Collect and remember these slots when needed:

| Slot | Meaning | Discovery |
|---|---|---|
| node | short name, e.g. hei5b1 | from subdomain or ask |
| hostname | full DNS name | `<node>.<domain>` default |
| root_domain | Cloudflare zone name | user or state |
| cf_account_id | Cloudflare account id | env/state/user |
| cf_zone_id | Cloudflare zone id | env, API by zone name, or state |
| vps_host | IP or SSH host | user/state |
| ssh_user | SSH user | default root |
| ssh_port | SSH port | default 22 |
| vmess_port | local vmess-ws port | parse `/etc/s-box/sb.json` |
| vmess_path | ws path | parse `/etc/s-box/sb.json` |
| tunnel_name | Cloudflare tunnel | `yg-<node>` default |
| tunnel_id | Cloudflare tunnel uuid | API |

## Mandatory install preflight

When the user wants to install or reinstall a node on a VPS:

1. Upload or paste `scripts/detect_node_tools.sh` to the VPS as `/tmp/detect_node_tools.sh`.
2. Run detection first.
3. If conflicts exist, run cleanup and verify the result.
4. Continue with sing-box-yg install only after cleanup has been verified.

Do not skip this preflight just because the VPS is new; provider templates often include old scripts or leftover services.

## Turn behavior

- If the user gives one node, operate on one node.
- If the user gives several nodes in prose, process sequentially and summarize after each.
- If required credentials are missing, ask for the specific missing item.
- If the user gives a Cloudflare token, use it only for the current shell/process and avoid printing it.
- Persist non-secret state after successful verification.

## Reporting format

For each node, report:

```text
node | hostname | VPS sing-box | cloudflared service | Cloudflare DNS | Tunnel | subscription patch | next action
```

Include exact failed check output when something fails.
