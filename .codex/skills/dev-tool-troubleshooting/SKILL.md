---
name: dev-tool-troubleshooting
description: Diagnose and fix local development toolchain failures. Use when Codex encounters failing dev commands, missing or wrong Node/Yarn/npm/pnpm versions, Metro or Expo startup issues, Android/ADB/Gradle/Java problems, port conflicts, native module errors, lockfile/package-manager drift, flaky build/test/lint/typecheck commands, or uncertainty about whether a failure is code-related versus environment-related.
---

# Dev Tool Troubleshooting

## Overview

Use this skill to separate toolchain/environment failures from product code failures, collect the smallest useful evidence, and apply the least risky fix. Prefer project-local instructions first; this skill supplies the reusable diagnostic workflow and common local runbooks.

## Core Workflow

1. Read the project `AGENTS.md` and relevant docs before changing commands, dependencies, or native configuration.
2. Check the worktree with `git status --short`; do not overwrite unrelated user or agent changes.
3. Capture the exact failing command, cwd, exit code, and first meaningful error. Avoid treating long warning blocks as root cause.
4. Classify the failure:
   - Tool missing or wrong version: inspect `which`, `--version`, project scripts, `.nvmrc`, `.node-version`, `packageManager`, lockfiles, Java/Android paths.
   - Port/process conflict: identify the listener before killing anything.
   - Dependency/install drift: compare package manager and lockfile; avoid switching package managers unless explicitly requested.
   - Native mobile failure: distinguish Metro reload issues from a required rebuild/reinstall.
   - Code failure: reproduce with the narrowest typecheck/test/build command and fix code in scope.
5. Prefer a no-write diagnostic pass before fixes. Run `scripts/dev_env_report.sh` from this skill when toolchain context is unclear.
6. Apply the smallest reversible fix, then rerun the original command or the closest project-approved verification command.
7. Report what failed, what changed, what passed, and what remains unverified.

## Local Tool Preferences

- Prefer project scripts over ad hoc commands: `yarn typecheck`, `npm test`, `pnpm test`, `yarn android`, etc.
- Prefer user-local runtime paths when projects reference them:
  - Node: `/Users/macop/dev/node/bin/node`
  - npm: `/Users/macop/dev/node/bin/npm`
  - Yarn: `/Users/macop/dev/bin/yarn`
  - pnpm: `/Users/macop/dev/bin/pnpm`
  - Java: `/Users/macop/dev/java/Contents/Home`
  - Android SDK: `/Users/macop/dev/android`
  - adb: `/Users/macop/dev/android/platform-tools/adb`
- Do not create or commit `package-lock.json` in Yarn projects.
- After adding or upgrading native Expo/React Native dependencies, rerun the native build path such as `yarn android`; Metro reload alone is not sufficient.
- For Expo/Metro `Unable to load script`, check Metro, port `8081`, dev-client URL, and `adb reverse` before editing app code.

## Diagnostic Script

Run this read-only report from any project root:

```bash
/Users/macop/.codex/skills/dev-tool-troubleshooting/scripts/dev_env_report.sh
```

Use the report to choose the next narrow command. Do not paste the full report into user-facing replies unless asked; summarize only the relevant lines.

## Common Runbooks

Load [references/toolchain-runbook.md](references/toolchain-runbook.md) when the failure involves Expo/Metro, Android/ADB/Gradle/Java, dependency manager drift, port conflicts, or native module errors.

## Safety Rules

- Do not run destructive cleanup commands such as `git reset --hard`, deleting lockfiles, wiping `node_modules`, clearing Gradle caches, or killing broad process groups unless the user explicitly asks or the project docs require it.
- Do not install global tools when a project-local or user-local runtime exists.
- Do not change package managers to make a command pass.
- Do not hide API/data-contract problems with local mock fallbacks or guessed defaults.
- When verification cannot cover the target platform, say exactly what was not run, for example `android device manually verified: not run`.
