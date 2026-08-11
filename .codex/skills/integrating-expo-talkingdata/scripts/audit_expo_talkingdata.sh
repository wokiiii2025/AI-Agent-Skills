#!/usr/bin/env bash

set -u

project_root="${1:-.}"
pass_count=0
warn_count=0
fail_count=0

pass() {
  pass_count=$((pass_count + 1))
  printf 'PASS  %s\n' "$1"
}

warn() {
  warn_count=$((warn_count + 1))
  printf 'WARN  %s\n' "$1"
}

fail() {
  fail_count=$((fail_count + 1))
  printf 'FAIL  %s\n' "$1"
}

if ! command -v rg >/dev/null 2>&1; then
  printf 'FAIL  rg is required for this audit.\n' >&2
  exit 2
fi

if [ ! -d "$project_root" ]; then
  printf 'FAIL  Project directory does not exist: %s\n' "$project_root" >&2
  exit 2
fi

project_root="$(cd "$project_root" && pwd -P)"
cd "$project_root" || exit 2

if [ -f package.json ] && rg -q '"expo"|"expo-router"' package.json; then
  pass "Expo project detected"
else
  fail "package.json does not identify an Expo project"
fi

if rg -q 'EXPO_PUBLIC_TALKINGDATA_APP_ID' app.config.* android/app/build.gradle* docker package.json scripts 2>/dev/null; then
  pass "TalkingData App ID environment key is wired into project/build files"
else
  fail "EXPO_PUBLIC_TALKINGDATA_APP_ID is not wired into project/build files"
fi

if rg -q 'TD_APP_ID|talkingDataAppId' android/app/src/main/AndroidManifest.xml android/app/build.gradle* 2>/dev/null; then
  pass "Android manifest App ID placeholder/configuration detected"
else
  fail "Android manifest App ID injection was not detected"
fi

if rg -q 'initSDK' android/app/src/main src plugins 2>/dev/null \
  && rg -q 'startA' android/app/src/main src plugins 2>/dev/null \
  && rg -q 'getDeviceID|getDeviceId' android/app/src/main src plugins 2>/dev/null; then
  pass "Native TalkingData initialization and device ID bridge detected"
else
  fail "Native initSDK/startA/device ID bridge is incomplete"
fi

if rg -q 'getInitialClipboardText|onWindowFocusChanged|ClipboardManager' android/app/src/main 2>/dev/null; then
  pass "Focus-safe Android initial clipboard bridge detected"
else
  warn "No focus-safe native initial clipboard bridge detected; Expo-only startup reads may race window focus"
fi

if rg -q 'channelSource' src app 2>/dev/null; then
  pass "channelSource promotion parameter detected"
else
  fail "channelSource promotion parameter was not detected"
fi

if rg -q 'waitForTalkingDataDeviceId|TalkingData.*设备标识' src 2>/dev/null; then
  pass "Explicit TalkingData device ID wait/gate detected"
else
  warn "No explicit TalkingData device ID wait/gate detected for Android guest creation"
fi

if rg -q 'td_channelid' src app docker 2>/dev/null; then
  warn "td_channelid exists; verify it is H5 SDK transport only, not a second inbound promotion contract"
else
  pass "No td_channelid runtime usage detected"
fi

hardcoded_files="$(rg -l --glob '!**/*.test.*' --glob '!**/__tests__/**' --glob '!**/docs/**' --glob '!**/build/**' --glob '!**/.env*' --glob '!**/node_modules/**' '[A-Fa-f0-9]{32}' app.config.* src android/app/src plugins docker scripts 2>/dev/null || true)"
if [ -n "$hardcoded_files" ]; then
  warn "32-character hex values exist in runtime/build source; inspect these files for hardcoded test App IDs:"
  while IFS= read -r file; do
    [ -n "$file" ] && printf '      %s\n' "$file"
  done <<< "$hardcoded_files"
else
  pass "No obvious 32-character App ID hardcoding found in runtime/build source"
fi

if rg -q 'getAndroidId|installation_device_id|install_storage' src 2>/dev/null; then
  warn "Android/installation ID helpers exist; verify Android new-guest flow cannot use them as fallback"
else
  pass "No obvious Android/installation ID fallback helpers detected"
fi

if rg -q 'TalkingData|talkingdata' __tests__ test tests 2>/dev/null; then
  pass "TalkingData-related tests detected"
else
  warn "No TalkingData-related tests detected"
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  env_changes="$(git status --short -- .env .env.* 2>/dev/null || true)"
  if [ -n "$env_changes" ]; then
    warn "Tracked or untracked .env changes exist; do not commit credentials/config secrets"
  else
    pass "No .env changes reported by git"
  fi
fi

printf '\nSummary: %d pass, %d warn, %d fail\n' "$pass_count" "$warn_count" "$fail_count"

if [ "$fail_count" -gt 0 ]; then
  exit 1
fi
