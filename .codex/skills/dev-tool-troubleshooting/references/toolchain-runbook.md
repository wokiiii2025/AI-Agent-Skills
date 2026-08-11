# Toolchain Runbook

## Node, Package Managers, And Lockfiles

- Start with `package.json`: inspect `scripts`, `packageManager`, engines, and framework versions.
- Use the package manager implied by the lockfile:
  - `yarn.lock` -> Yarn, usually Yarn 1 in the user's current projects.
  - `package-lock.json` -> npm.
  - `pnpm-lock.yaml` -> pnpm.
- If a Yarn project has a new `package-lock.json`, treat it as drift. Remove it only if it was created by the current task or the user approves.
- Prefer local runtime paths when needed:
  - `/Users/macop/dev/node/bin/node`
  - `/Users/macop/dev/node/bin/npm`
  - `/Users/macop/dev/bin/yarn`
  - `/Users/macop/dev/bin/pnpm`
- For dependency errors, first try the project-approved install command. Avoid upgrading packages unless the task requires it.

## TypeScript, Lint, Test, And Build

- For TypeScript failures, run the narrowest project command first, commonly `npx tsc --noEmit`, `yarn typecheck`, or `npm run typecheck`.
- For Jest failures, prefer the failing test file before the whole suite when the output identifies one.
- For Next/Expo/RN builds, distinguish type/lint failures from bundler/runtime failures; they usually need different fixes.
- Do not declare success from a dev server starting if the requested verification was typecheck, test, Android run, or build.

## Ports And Long-Running Dev Servers

- Identify listeners before killing:
  - `lsof -nP -iTCP:<port> -sTCP:LISTEN`
  - `ps -p <pid> -o pid,ppid,command`
- Common ports:
  - `3000`: Next.js/web dev servers.
  - `5173`: Vite.
  - `8081`: Metro.
- Prefer stopping a known stale project server over killing unrelated processes.
- If a server is already usable, reuse it and report its URL instead of starting another copy.

## Expo, Metro, And React Native

- Web preview is not Android verification. For Android-targeted work, use Android build/run or device validation when required.
- `Unable to load script` usually points to Metro/device connection:
  - confirm Metro is running on `8081`;
  - confirm the dev client points at the current machine/port;
  - run `adb reverse tcp:8081 tcp:8081` for USB-connected Android devices;
  - restart stale Metro only after identifying it.
- Native dependency changes require a rebuild/reinstall such as `yarn android`; refreshing Metro cannot load new native modules.
- `Cannot find native module ...` usually means the native binary does not include the module or the dev client was not rebuilt.

## Android, ADB, Gradle, And Java

- Preferred local paths:
  - `JAVA_HOME=/Users/macop/dev/java/Contents/Home`
  - `ANDROID_HOME=/Users/macop/dev/android`
  - `ADB=/Users/macop/dev/android/platform-tools/adb`
- Start with:
  - `adb devices`
  - `adb reverse --list`
  - `java -version`
  - `./gradlew --version` from `android/` when present.
- If a device is offline or missing, fix device connectivity before editing code.
- If Gradle fails after dependency changes, inspect the first concrete Gradle error, not the final summary line.
- ABI, signing, permissions, and manifest changes must be verified with the project-required Android command.

## Native Media And UI Runtime Issues

- For image capture/export/save/share issues, check platform-specific services before modifying UI components.
- Add timeout protection around native promises that can hang.
- Use `adb logcat` with targeted filters when Android native errors are unclear. Useful filters from existing projects include `ReactNativeJS`, `ViewShot`, `MediaLibrary`, `ExpoImageManipulator`, `Cannot find native module`, and `Expected to run on UI thread`.
- Do not rely on edits inside `node_modules` as a permanent fix unless the project already uses a patch mechanism or the user explicitly accepts the risk.

## External Docs And APIs

- If the failure may be caused by a recently changed external API, dependency, framework, or CLI behavior, verify against official docs or the upstream source before implementing.
- Prefer official docs, changelogs, repository source, or package release notes over blog posts and issue comments.
- Record any confirmed breaking change in the project's docs when it affects future maintenance.
