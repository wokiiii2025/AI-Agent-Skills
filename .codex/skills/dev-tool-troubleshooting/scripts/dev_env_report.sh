#!/usr/bin/env bash
set -u

section() {
  printf '\n== %s ==\n' "$1"
}

cmd_exists() {
  command -v "$1" >/dev/null 2>&1
}

show_cmd() {
  local label="$1"
  shift
  printf '%s: ' "$label"
  if "$@" >/tmp/dev-tool-report.out 2>/tmp/dev-tool-report.err; then
    tr '\n' ' ' </tmp/dev-tool-report.out | sed 's/[[:space:]]*$//'
    printf '\n'
  else
    printf 'not available'
    if [ -s /tmp/dev-tool-report.err ]; then
      printf ' ('
      head -n 1 /tmp/dev-tool-report.err | tr '\n' ' '
      printf ')'
    fi
    printf '\n'
  fi
}

section "Context"
printf 'cwd: %s\n' "$(pwd)"
printf 'shell: %s\n' "${SHELL:-unknown}"
printf 'date: %s\n' "$(date '+%Y-%m-%d %H:%M:%S %Z')"

section "Git"
if cmd_exists git; then
  show_cmd "git root" git rev-parse --show-toplevel
  show_cmd "git branch" git branch --show-current
  printf 'git status:\n'
  git status --short 2>/dev/null | sed 's/^/  /' || true
else
  printf 'git: not found\n'
fi

section "Project Files"
for file in AGENTS.md package.json yarn.lock package-lock.json pnpm-lock.yaml .node-version .nvmrc app.json eas.json android/gradle.properties; do
  if [ -e "$file" ]; then
    printf 'found: %s\n' "$file"
  fi
done

section "Node And Package Managers"
for bin in node npm yarn pnpm; do
  if cmd_exists "$bin"; then
    printf '%s path: %s\n' "$bin" "$(command -v "$bin")"
    show_cmd "$bin version" "$bin" --version
  else
    printf '%s: not found\n' "$bin"
  fi
done

section "User Local Tool Paths"
for path in \
  /Users/macop/dev/node/bin/node \
  /Users/macop/dev/node/bin/npm \
  /Users/macop/dev/bin/yarn \
  /Users/macop/dev/bin/pnpm \
  /Users/macop/dev/java/Contents/Home/bin/java \
  /Users/macop/dev/android/platform-tools/adb; do
  if [ -x "$path" ]; then
    printf 'executable: %s\n' "$path"
  elif [ -e "$path" ]; then
    printf 'exists non-executable: %s\n' "$path"
  else
    printf 'missing: %s\n' "$path"
  fi
done

section "Java And Android"
show_cmd "JAVA_HOME" sh -c 'printf "%s" "${JAVA_HOME:-unset}"'
if cmd_exists java; then
  printf 'java path: %s\n' "$(command -v java)"
  java -version 2>&1 | head -n 3 | sed 's/^/java version: /'
else
  printf 'java: not found\n'
fi
show_cmd "ANDROID_HOME" sh -c 'printf "%s" "${ANDROID_HOME:-unset}"'
if cmd_exists adb; then
  printf 'adb path: %s\n' "$(command -v adb)"
  adb devices 2>/dev/null | sed 's/^/adb devices: /'
else
  printf 'adb: not found on PATH\n'
fi
if [ -x /Users/macop/dev/android/platform-tools/adb ]; then
  /Users/macop/dev/android/platform-tools/adb devices 2>/dev/null | sed 's/^/local adb devices: /'
fi

section "Common Ports"
for port in 3000 5173 8081; do
  printf 'port %s:\n' "$port"
  if cmd_exists lsof; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null | sed 's/^/  /' || printf '  no listener\n'
  else
    printf '  lsof not found\n'
  fi
done

rm -f /tmp/dev-tool-report.out /tmp/dev-tool-report.err
