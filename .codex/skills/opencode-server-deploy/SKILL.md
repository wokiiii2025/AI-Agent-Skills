---
name: opencode-server-deploy
description: Deploy and maintain OpenCode web on an SSH server from a skill-local .env file using a cross-platform Python runner. Use when Codex is asked to configure OpenCode web service on a remote Linux systemd server, enable boot startup, create systemd service/timer units, configure automatic OpenCode updates, restart after update, toggle public access, or verify OpenCode web health using SSH credentials and web login settings.
---

# OpenCode Server Deploy

## Overview

Use the bundled Python script from Windows, macOS, or Linux to configure a remote Linux server for OpenCode web:

- create or repair `/usr/local/bin/opencode-web-service`
- create `opencode-web.service` for boot startup
- create `opencode-web-update.service` and `opencode-web-update.timer` for scheduled updates
- run an optional update check and restart the service
- verify the configured web port with HTTP Basic auth
- switch OpenCode web between public binding and local-only binding

## Quick Start

1. Copy `.env.example` to `.env` in this skill directory or provide another file with `--env-file`.
2. Fill in SSH server settings and OpenCode web settings.
3. Run:

```bash
python scripts/deploy_opencode_server.py
```

Or use the platform launcher from the skill directory:

```bash
# Windows
scripts\deploy_opencode_server.cmd

# macOS/Linux
sh scripts/deploy_opencode_server.sh
```

The runner is cross-platform. The launchers auto-detect `py -3`, `python3`, or `python`. The Python script also auto-installs missing `paramiko` into the active Python environment when `AUTO_INSTALL_PYTHON_DEPS=true`.

The remote host must be Linux with systemd, bash, curl, and python3 because the deployed boot service and timer are systemd units.

## Configuration

The script reads these keys from `.env`:

```dotenv
SERVER_HOST=156.238.255.88
SERVER_SSH_PORT=60245
SERVER_USER=root
SERVER_PASSWORD=change-me

OPENCODE_WEB_PORT=4096
OPENCODE_WEB_USER=opencode
OPENCODE_WEB_PASSWORD=change-me
ALLOW_PUBLIC_ACCESS=true

UPDATE_ON_CALENDAR=*-*-* 04:00:00
UPDATE_RANDOMIZED_DELAY_SEC=30m
RUN_UPDATE_NOW=true
AUTO_INSTALL_PYTHON_DEPS=true
```

Optional keys:

```dotenv
OPENCODE_BIN=/root/.opencode/bin/opencode
OPENCODE_HOSTNAME=
HEALTHCHECK_TIMEOUT_SEC=10
```

Set `ALLOW_PUBLIC_ACCESS=true` to listen on `0.0.0.0` and expose the service on the server IP. Set `ALLOW_PUBLIC_ACCESS=false` to listen only on `127.0.0.1`; use SSH tunneling or a reverse proxy if remote access is needed. `OPENCODE_HOSTNAME` is an advanced override and should usually stay empty.

## Workflow

Run the script and report the concise result to the user: service enabled/active state, timer next run, OpenCode version, public access mode, listening host/port, and HTTP health result.

If deployment fails:

- inspect remote `systemctl status opencode-web.service`
- inspect `journalctl -u opencode-web.service -n 120 --no-pager`
- inspect `/root/.config/opencode/opencode-web/opencode-web.log`
- inspect `/root/.config/opencode/opencode-web/opencode-web-update.log`

Do not print real passwords in final answers.
