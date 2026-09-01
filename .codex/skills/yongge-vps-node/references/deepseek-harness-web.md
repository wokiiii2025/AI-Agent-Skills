# DeepSeek Harness / dsh Web on VPS

Use this reference when the user asks to install, expose, repair, or maintain DeepSeek Harness (`dsh`) as a web service on a VPS, especially after replacing OpenCode or when the browser UI reports `crypto.randomUUID is not a function` or `/api/* HTTP 403`.

## Install and service pattern

- Install with npm in the server's active Node runtime path:
  - `npm view @deepseek-ai/dsh version bin --json`
  - `npm config set allow-scripts @deepseek-ai/dsh-subprocess-local,koffi,node-pty,@google/genai,protobufjs --location=global`
  - `npm install -g @deepseek-ai/dsh@latest --allow-scripts=@deepseek-ai/dsh-subprocess-local,koffi,node-pty,@google/genai,protobufjs`
- Verify: `dsh --version`.
- Do not assume `dsh web --host 0.0.0.0` works. Current dsh refuses public binds for safety. Bind local and put a reverse proxy in front:
  - dsh service: `127.0.0.1:3081`
  - public reverse proxy example: `0.0.0.0:4097 -> http://127.0.0.1:3081`
- Create `/usr/local/bin/dsh-web-service` and `/etc/systemd/system/dsh-web.service`; enable and start it.
- If replacing OpenCode, stop/disable `opencode-web.service` and remove it from any shared updater to avoid conflicting entry points.

Example wrapper:

```bash
#!/usr/bin/env bash
set -euo pipefail
export HOME=/root
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/root/.hermes/node/bin
exec /usr/local/bin/dsh web --port 3081 \
  --trusted-host PUBLIC_HOST \
  --trusted-host PUBLIC_HOST:PUBLIC_PORT \
  --trusted-host 127.0.0.1 \
  --trusted-host 127.0.0.1:3081 \
  --trusted-host localhost \
  --trusted-host localhost:3081
```

## 1Panel/OpenResty reverse proxy pattern

For 1Panel OpenResty, create a file under `/opt/1panel/www/conf.d/`, plus an htpasswd file under `/opt/1panel/www/auth/`. Keep dsh behind Basic Auth if using an IP/port entry.

Important reverse-proxy details:

- Preserve the external authority including port: `proxy_set_header Host $http_host;`
- Forward websocket upgrade headers.
- Use long read/send timeouts.
- Reload OpenResty through its container: `docker exec <1Panel-openresty-container> nginx -t && docker exec <container> nginx -s reload`.

Minimal server block:

```nginx
server {
    listen PUBLIC_PORT;
    server_name _;

    auth_basic "DeepSeek Harness";
    auth_basic_user_file /www/auth/dsh.htpasswd;

    location / {
        proxy_pass http://127.0.0.1:3081;
        proxy_http_version 1.1;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
        proxy_buffering off;
    }
}
```

## Fix `crypto.randomUUID is not a function`

Symptom: page loads over `http://IP:PORT`, but workspace picker, provider list, or RPC actions fail with:

```text
crypto.randomUUID is not a function
```

Cause: browser `crypto.randomUUID()` is exposed only in secure contexts (`https://...` or localhost). Plain `http://IP:PORT` is not a secure context. Prefer HTTPS with a domain when possible. If the user wants IP:port HTTP, inject a UUID v4 polyfill into the HTML at the reverse proxy.

OpenResty injection inside the `location /` block:

```nginx
sub_filter_once on;
sub_filter '<head>' '<head><script>(function(){try{if(!globalThis.crypto)globalThis.crypto={};if(!globalThis.crypto.randomUUID){globalThis.crypto.randomUUID=function(){var b=new Uint8Array(16);(globalThis.crypto.getRandomValues?globalThis.crypto.getRandomValues(b):b.forEach(function(_,i){b[i]=Math.random()*256|0;}));b[6]=b[6]&15|64;b[8]=b[8]&63|128;var h=Array.from(b,function(x){return x.toString(16).padStart(2,"0")});return h.slice(0,4).join("")+"-"+h.slice(4,6).join("")+"-"+h.slice(6,8).join("")+"-"+h.slice(8,10).join("")+"-"+h.slice(10,16).join("");};}}catch(e){}})();</script>';
```

Then test that the public page contains `crypto.randomUUID`, hard-refresh the browser, and clear the site cache if needed.

## Fix `/api/host.listDirectory: HTTP 403`

Symptom:

```text
transport failure for /api/host.listDirectory: HTTP 403
```

Cause: dsh's browser-trust fence rejects API calls when the browser's Host/Origin authority is not trusted, commonly after reverse proxying from `PUBLIC_HOST:PUBLIC_PORT` to `127.0.0.1:3081`.

Fix both sides:

1. Start dsh with `--trusted-host PUBLIC_HOST` and `--trusted-host PUBLIC_HOST:PUBLIC_PORT`.
2. In reverse proxy, use `proxy_set_header Host $http_host;` so dsh sees the same authority the browser uses.

Validate with a POST probe. A malformed body should return HTTP 200 with a JSON `bad-request`, not HTTP 403:

```bash
curl -i -u USER:PASSWORD \
  -H "Origin: http://PUBLIC_HOST:PUBLIC_PORT" \
  -H "Content-Type: application/json" \
  --data '{}' \
  http://PUBLIC_HOST:PUBLIC_PORT/api/host.listDirectory
```

Expected status: `HTTP/1.1 200 OK`.

## Ports and security-group checks

If the service works locally but not remotely, test from the operator machine:

- `Test-NetConnection HOST -Port PUBLIC_PORT` on Windows.
- `curl -u USER:PASSWORD --connect-timeout 5 http://HOST:PUBLIC_PORT/`.

On the server verify:

- `systemctl is-active dsh-web.service`
- `ss -lntup | grep -E ':(3081|PUBLIC_PORT)\\b'`
- `curl http://127.0.0.1:3081/`
- `curl -u USER:PASSWORD http://127.0.0.1:PUBLIC_PORT/`
- `iptables -S INPUT` or `nft list ruleset`

If local checks pass and remote port times out, the cloud security group/upstream firewall is blocking. Add inbound TCP `PUBLIC_PORT` from `0.0.0.0/0`, or use already-open `80/443` with an HTTPS/domain proxy.

## Daily auto-update pattern

Use one systemd timer for VPS AI web services. If the user replaced OpenCode with dsh, remove OpenCode from the updater.

Update sequence:

1. Update `@deepseek-ai/dsh@latest` with allowed npm scripts.
2. Restart `dsh-web.service`.
3. Update Hermes if installed, then restart `hermes.service`.
4. Health check local dsh (`3081`), public proxy port, and Hermes (`8787`) when applicable.
5. Log to `/var/log/codex-ai-services-update.log`.

Never print real passwords in final responses. Say the password was set as requested.
