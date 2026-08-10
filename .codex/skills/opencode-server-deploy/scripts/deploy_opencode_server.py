#!/usr/bin/env python3
"""Deploy and maintain OpenCode web on a remote SSH server."""

from __future__ import annotations

import argparse
import base64
import shlex
import subprocess
import sys
import textwrap
import time
from pathlib import Path

paramiko = None


SKILL_DIR = Path(__file__).resolve().parents[1]


def ensure_paramiko(auto_install: bool) -> None:
    global paramiko
    try:
        import paramiko as imported_paramiko

        paramiko = imported_paramiko
        return
    except ImportError:
        if not auto_install:
            raise SystemExit(
                "Missing dependency: paramiko. Install it with: "
                f"{sys.executable} -m pip install paramiko"
            )

    print("Python dependency 'paramiko' is missing; installing with the active Python...")
    command = [sys.executable, "-m", "pip", "install", "paramiko"]
    result = subprocess.run(command, text=True)
    if result.returncode != 0:
        raise SystemExit(
            "Failed to install paramiko automatically. Run this manually and retry:\n"
            + " ".join(shlex.quote(part) for part in command)
        )
    try:
        import paramiko as imported_paramiko

        paramiko = imported_paramiko
    except ImportError as exc:
        raise SystemExit("paramiko installed but could not be imported; check the Python environment.") from exc


def parse_env(path: Path) -> dict[str, str]:
    if not path.exists():
        raise SystemExit(f"Env file not found: {path}")
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def require(env: dict[str, str], key: str) -> str:
    value = env.get(key, "").strip()
    if not value or value == "change-me":
        raise SystemExit(f"Missing required .env value: {key}")
    return value


def q(value: str) -> str:
    return shlex.quote(value)


def env_bool(env: dict[str, str], key: str, default: bool = False) -> bool:
    value = env.get(key)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def opencode_hostname(env: dict[str, str]) -> str:
    explicit = env.get("OPENCODE_HOSTNAME", "").strip()
    if explicit:
        return explicit
    return "0.0.0.0" if env_bool(env, "ALLOW_PUBLIC_ACCESS", True) else "127.0.0.1"


def ssh_connect(env: dict[str, str]) -> paramiko.SSHClient:
    if paramiko is None:
        raise RuntimeError("paramiko is not initialized")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(
        hostname=require(env, "SERVER_HOST"),
        port=int(env.get("SERVER_SSH_PORT", "22")),
        username=require(env, "SERVER_USER"),
        password=require(env, "SERVER_PASSWORD"),
        timeout=20,
        banner_timeout=20,
        auth_timeout=20,
        look_for_keys=False,
        allow_agent=False,
    )
    return ssh


def run(ssh: paramiko.SSHClient, command: str, timeout: int = 120) -> tuple[int, str, str]:
    stdin, stdout, stderr = ssh.exec_command(command, timeout=timeout)
    del stdin
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return stdout.channel.recv_exit_status(), out, err


def put_text(ssh: paramiko.SSHClient, path: str, content: str, mode: int | None = None) -> None:
    sftp = ssh.open_sftp()
    tmp = f"{path}.tmp-{int(time.time())}"
    with sftp.file(tmp, "w") as handle:
        handle.write(content)
    if mode is not None:
        sftp.chmod(tmp, mode)
    sftp.rename(tmp, path)
    sftp.close()


def wrapper_script(env: dict[str, str]) -> str:
    hostname = opencode_hostname(env)
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        set -euo pipefail

        APP_NAME="opencode-web"
        STATE_DIR="/root/.config/opencode/${{APP_NAME}}"
        PID_FILE="${{STATE_DIR}}/${{APP_NAME}}.pid"
        LOG_FILE="${{STATE_DIR}}/${{APP_NAME}}.log"

        OPENCODE_BIN="${{OPENCODE_BIN:-$(command -v opencode || true)}}"
        if [[ -z "${{OPENCODE_BIN}}" && -x {q(env.get("OPENCODE_BIN", "/root/.opencode/bin/opencode"))} ]]; then
          OPENCODE_BIN={q(env.get("OPENCODE_BIN", "/root/.opencode/bin/opencode"))}
        fi
        OPENCODE_SERVER_USERNAME={q(require(env, "OPENCODE_WEB_USER"))}
        OPENCODE_SERVER_PASSWORD={q(require(env, "OPENCODE_WEB_PASSWORD"))}
        OPENCODE_HOSTNAME={q(hostname)}
        OPENCODE_PORT={q(env.get("OPENCODE_WEB_PORT", "4096"))}

        mkdir -p "${{STATE_DIR}}"

        usage() {{
          cat <<'EOF'
        Usage: opencode-web-service {{start|stop|restart|status|update|logs}}
        EOF
        }}

        require_opencode() {{
          if [[ -z "${{OPENCODE_BIN}}" || ! -x "${{OPENCODE_BIN}}" ]]; then
            echo "Error: opencode command not found or not executable." >&2
            exit 1
          fi
        }}

        is_running() {{
          [[ -f "${{PID_FILE}}" ]] || return 1
          local pid
          pid="$(cat "${{PID_FILE}}")"
          [[ -n "${{pid}}" ]] || return 1
          kill -0 "${{pid}}" 2>/dev/null
        }}

        start_service() {{
          require_opencode
          if is_running; then
            echo "${{APP_NAME}} is already running (PID: $(cat "${{PID_FILE}}"))"
            return 0
          fi
          rm -f "${{PID_FILE}}"
          echo "Starting ${{APP_NAME}}..."
          nohup env \\
            OPENCODE_SERVER_USERNAME="${{OPENCODE_SERVER_USERNAME}}" \\
            OPENCODE_SERVER_PASSWORD="${{OPENCODE_SERVER_PASSWORD}}" \\
            "${{OPENCODE_BIN}}" web --hostname "${{OPENCODE_HOSTNAME}}" --port "${{OPENCODE_PORT}}" \\
            >>"${{LOG_FILE}}" 2>&1 &
          local pid=$!
          echo "${{pid}}" > "${{PID_FILE}}"
          sleep 2
          if kill -0 "${{pid}}" 2>/dev/null; then
            echo "${{APP_NAME}} started (PID: ${{pid}})"
            echo "Log file: ${{LOG_FILE}}"
          else
            echo "Failed to start ${{APP_NAME}}. Check logs: ${{LOG_FILE}}" >&2
            rm -f "${{PID_FILE}}"
            exit 1
          fi
        }}

        stop_service() {{
          if ! is_running; then
            echo "${{APP_NAME}} is not running"
            rm -f "${{PID_FILE}}"
            return 0
          fi
          local pid
          pid="$(cat "${{PID_FILE}}")"
          echo "Stopping ${{APP_NAME}} (PID: ${{pid}})..."
          kill "${{pid}}" 2>/dev/null || true
          for _ in {{1..15}}; do
            if kill -0 "${{pid}}" 2>/dev/null; then
              sleep 1
            else
              rm -f "${{PID_FILE}}"
              echo "${{APP_NAME}} stopped"
              return 0
            fi
          done
          echo "Process did not exit gracefully, forcing stop..."
          kill -9 "${{pid}}" 2>/dev/null || true
          rm -f "${{PID_FILE}}"
          echo "${{APP_NAME}} stopped"
        }}

        status_service() {{
          if is_running; then
            echo "${{APP_NAME}} is running (PID: $(cat "${{PID_FILE}}"))"
            echo "Log file: ${{LOG_FILE}}"
          else
            echo "${{APP_NAME}} is not running"
            [[ -f "${{LOG_FILE}}" ]] && echo "Log file: ${{LOG_FILE}}"
          fi
        }}

        update_service() {{
          require_opencode
          local was_running=0
          if is_running; then
            was_running=1
            stop_service
          fi
          echo "Updating opencode..."
          HOME=/root curl -fsSL https://opencode.ai/install | HOME=/root bash
          OPENCODE_BIN="${{OPENCODE_BIN:-$(command -v opencode || true)}}"
          require_opencode
          echo "Updated version: $("${{OPENCODE_BIN}}" --version)"
          if [[ "${{was_running}}" -eq 1 ]]; then
            start_service
          fi
        }}

        logs_service() {{
          touch "${{LOG_FILE}}"
          tail -f "${{LOG_FILE}}"
        }}

        case "${{1:-}}" in
          start) start_service ;;
          stop) stop_service ;;
          restart) stop_service; start_service ;;
          status) status_service ;;
          update) update_service ;;
          logs) logs_service ;;
          *) usage; exit 1 ;;
        esac
        """
    )


def update_script(env: dict[str, str]) -> str:
    opencode_bin = env.get("OPENCODE_BIN", "/root/.opencode/bin/opencode")
    return textwrap.dedent(
        f"""\
        #!/usr/bin/env bash
        set -euo pipefail

        export HOME=/root
        export OPENCODE_BIN={q(opencode_bin)}
        LOG_FILE=/root/.config/opencode/opencode-web/opencode-web-update.log
        mkdir -p "$(dirname "${{LOG_FILE}}")"

        was_running=0
        restart_if_needed() {{
          local exit_code=$?
          if [[ "${{was_running}}" -eq 1 ]] && ! systemctl is-active --quiet opencode-web.service; then
            echo "Ensuring opencode-web.service is running after update attempt..."
            systemctl start opencode-web.service || true
          fi
          echo "Auto update check finished with exit code ${{exit_code}}."
          exit "${{exit_code}}"
        }}
        trap restart_if_needed EXIT

        {{
          echo "===== $(date '+%F %T %Z') opencode auto update check ====="
          if systemctl is-active --quiet opencode-web.service; then
            was_running=1
            echo "opencode-web.service is active; stopping before update..."
            systemctl stop opencode-web.service
          elif /usr/local/bin/opencode-web-service status | grep -q 'is running'; then
            was_running=1
            echo "opencode-web process is running outside systemd; stopping before update..."
            /usr/local/bin/opencode-web-service stop
          else
            echo "opencode-web is not running before update."
          fi

          before="unknown"
          [[ -x "${{OPENCODE_BIN}}" ]] && before="$(${{OPENCODE_BIN}} --version 2>/dev/null || true)"
          echo "Current version: ${{before}}"
          echo "Running official installer/update script..."
          curl -fsSL https://opencode.ai/install | bash
          after="unknown"
          [[ -x "${{OPENCODE_BIN}}" ]] && after="$(${{OPENCODE_BIN}} --version 2>/dev/null || true)"
          echo "Version after check: ${{after}}"

          if [[ "${{was_running}}" -eq 1 ]]; then
            echo "Restarting opencode-web.service..."
            systemctl start opencode-web.service
          else
            echo "Service was not running before update; leaving it stopped."
          fi
        }} >>"${{LOG_FILE}}" 2>&1
        """
    )


def service_unit(env: dict[str, str]) -> str:
    opencode_bin = env.get("OPENCODE_BIN", "/root/.opencode/bin/opencode")
    return textwrap.dedent(
        f"""\
        [Unit]
        Description=OpenCode Web Service
        After=network-online.target
        Wants=network-online.target

        [Service]
        Type=forking
        Environment=OPENCODE_BIN={opencode_bin}
        PIDFile=/root/.config/opencode/opencode-web/opencode-web.pid
        ExecStart=/usr/local/bin/opencode-web-service start
        ExecStop=/usr/local/bin/opencode-web-service stop
        ExecReload=/usr/local/bin/opencode-web-service restart
        Restart=on-failure
        RestartSec=10
        TimeoutStartSec=30
        TimeoutStopSec=30

        [Install]
        WantedBy=multi-user.target
        """
    )


def updater_unit(env: dict[str, str]) -> str:
    opencode_bin = env.get("OPENCODE_BIN", "/root/.opencode/bin/opencode")
    return textwrap.dedent(
        f"""\
        [Unit]
        Description=Check and update OpenCode, then restart OpenCode Web if needed
        Wants=network-online.target
        After=network-online.target

        [Service]
        Type=oneshot
        Environment=HOME=/root
        Environment=OPENCODE_BIN={opencode_bin}
        ExecStart=/usr/local/bin/opencode-web-auto-update
        """
    )


def timer_unit(env: dict[str, str]) -> str:
    return textwrap.dedent(
        f"""\
        [Unit]
        Description=Daily OpenCode Web update check

        [Timer]
        OnCalendar={env.get("UPDATE_ON_CALENDAR", "*-*-* 04:00:00")}
        RandomizedDelaySec={env.get("UPDATE_RANDOMIZED_DELAY_SEC", "30m")}
        Persistent=true
        Unit=opencode-web-update.service

        [Install]
        WantedBy=timers.target
        """
    )


def deploy(env: dict[str, str], run_update_now: bool) -> None:
    host = require(env, "SERVER_HOST")
    web_port = env.get("OPENCODE_WEB_PORT", "4096")
    web_user = require(env, "OPENCODE_WEB_USER")
    web_password = require(env, "OPENCODE_WEB_PASSWORD")
    health_timeout = int(env.get("HEALTHCHECK_TIMEOUT_SEC", "10"))
    allow_public = env_bool(env, "ALLOW_PUBLIC_ACCESS", True)
    hostname = opencode_hostname(env)

    ssh = ssh_connect(env)
    try:
        preflight = textwrap.dedent(
            """\
            set -euo pipefail
            uname -s
            command -v systemctl >/dev/null
            test -d /run/systemd/system
            command -v bash >/dev/null
            command -v curl >/dev/null
            command -v python3 >/dev/null
            """
        )
        code, out, err = run(ssh, preflight, timeout=30)
        if code != 0 or "Linux" not in out:
            raise SystemExit(
                "Remote host must be a Linux server running systemd with bash, curl, and python3.\n"
                f"STDOUT:\n{out}\nSTDERR:\n{err}"
            )

        put_text(ssh, "/usr/local/bin/opencode-web-service", wrapper_script(env), 0o755)
        put_text(ssh, "/usr/local/bin/opencode-web-auto-update", update_script(env), 0o755)
        put_text(ssh, "/etc/systemd/system/opencode-web.service", service_unit(env))
        put_text(ssh, "/etc/systemd/system/opencode-web-update.service", updater_unit(env))
        put_text(ssh, "/etc/systemd/system/opencode-web-update.timer", timer_unit(env))

        bootstrap = textwrap.dedent(
            """\
            set -euo pipefail
            bash -n /usr/local/bin/opencode-web-service
            bash -n /usr/local/bin/opencode-web-auto-update
            systemctl daemon-reload
            systemctl enable opencode-web.service
            systemctl enable --now opencode-web-update.timer
            systemctl reset-failed opencode-web.service opencode-web-update.service || true
            systemctl restart opencode-web.service
            """
        )
        code, out, err = run(ssh, bootstrap, timeout=120)
        if code != 0:
            raise SystemExit(f"Remote bootstrap failed:\nSTDOUT:\n{out}\nSTDERR:\n{err}")

        if run_update_now:
            code, out, err = run(ssh, "systemctl start opencode-web-update.service", timeout=300)
            if code != 0:
                raise SystemExit(f"Remote update check failed:\nSTDOUT:\n{out}\nSTDERR:\n{err}")

        token = base64.b64encode(f"{web_user}:{web_password}".encode()).decode()
        health = textwrap.dedent(
            f"""\
            set -euo pipefail
            sleep 8
            printf 'SERVICE_ENABLED='; systemctl is-enabled opencode-web.service
            printf 'SERVICE_ACTIVE='; systemctl is-active opencode-web.service
            printf 'TIMER_ENABLED='; systemctl is-enabled opencode-web-update.timer
            printf 'TIMER_ACTIVE='; systemctl is-active opencode-web-update.timer
            printf 'VERSION='; {q(env.get("OPENCODE_BIN", "/root/.opencode/bin/opencode"))} --version
            printf 'PUBLIC_ACCESS={str(allow_public).lower()}\\n'
            printf 'LISTEN_HOST={hostname}\\n'
            printf 'PORTS\\n'; ss -lntp | grep {q(":" + web_port)} || true
            printf 'NEXT_TIMER\\n'; systemctl list-timers opencode-web-update.timer --no-pager
            python3 - <<'PY'
            import urllib.request
            req = urllib.request.Request('http://127.0.0.1:{web_port}/')
            req.add_header('Authorization', 'Basic {token}')
            with urllib.request.urlopen(req, timeout={health_timeout}) as response:
                print('HTTP_STATUS=' + str(response.status))
                print('HTTP_CONTENT_TYPE=' + str(response.headers.get('content-type')))
            PY
            """
        )
        code, out, err = run(ssh, health, timeout=90)
        print(out)
        if err:
            print(err, file=sys.stderr)
        if code != 0:
            raise SystemExit("Health check failed")
        if allow_public and hostname != "127.0.0.1":
            print(f"DEPLOYED_URL=http://{host}:{web_port}")
        else:
            print(f"DEPLOYED_URL=local-only http://127.0.0.1:{web_port}")
    finally:
        ssh.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", default=str(SKILL_DIR / ".env"))
    parser.add_argument("--no-update-now", action="store_true")
    parser.add_argument(
        "--install-deps",
        action="store_true",
        help="Install missing Python dependencies into the active Python environment.",
    )
    parser.add_argument(
        "--no-install-deps",
        action="store_true",
        help="Do not auto-install missing Python dependencies.",
    )
    args = parser.parse_args()

    env = parse_env(Path(args.env_file))
    auto_install_deps = env_bool(env, "AUTO_INSTALL_PYTHON_DEPS", True)
    if args.install_deps:
        auto_install_deps = True
    if args.no_install_deps:
        auto_install_deps = False
    ensure_paramiko(auto_install=auto_install_deps)
    run_update_now = env.get("RUN_UPDATE_NOW", "true").lower() in {"1", "true", "yes", "y"}
    if args.no_update_now:
        run_update_now = False
    deploy(env, run_update_now=run_update_now)


if __name__ == "__main__":
    main()
