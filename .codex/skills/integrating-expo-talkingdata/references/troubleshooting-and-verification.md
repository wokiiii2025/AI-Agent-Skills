# Troubleshooting and Verification

## Contents

1. Failure map
2. Lessons and traps
3. Test matrix
4. ADB recipes
5. Delivery checklist

## 1. Failure map

| Symptom | Likely cause | Evidence to collect |
|---|---|---|
| First launch clipboard is empty | Activity is not focused yet; JS startup read raced the window | Native focus callbacks, cached clipboard bridge, bounded retry calls |
| Debug works, release loses channel URL | `Linking.getInitialURL()` timing or Intent lifecycle gap | `MainActivity` saved initial/new Intent, release cold-start test |
| Channel becomes `None` despite a valid link | Generic device/config request initialized SDK before attribution | Initialization call order and single initialization Promise |
| Channel ID appears but channel name is `--` | SDK sent the ID; console has no display-name mapping | Raw channel ID/time and channel-management configuration |
| Dashboard stays at zero | Wrong App ID/product/SDK package, build mismatch, upload delay, or no successful session | Merged manifest, runtime SDK version/App ID/channel, network logs, fresh install timestamp |
| Custom channel is a hardcoded test value | ADB/test code bypassed real URL parser | Search runtime source and verify launch Intent URL |
| Android creates duplicate guests | Android ID/installation UUID fallback or inconsistent header/body | Guest body, `Device-Id`, stored backend profile ID, source classification |
| App ID override has no effect | Expo dotenv overwrote shell env or Gradle used another source | Build command environment, generated bundle, merged manifest/APK |
| SDK method missing at runtime | JAR and bridge target different SDK versions; native app not rebuilt | JAR hash/version, demo API, `yarn android`/Gradle build output |
| HTTP 502 during custom backend reporting | No durable retry/idempotency in the app-owned submission path | Request ID, queue state, retry schedule, server response |

## 2. Lessons and traps

### Do not equate channel ID with channel display name

Seeing `Jile-Test01` with name `--` proves a channel identifier reached the reporting system. It does not prove the console has a human-readable name mapping. Fix mapping in the console or its supported channel-management flow; do not rewrite the ID to a hardcoded name.

### Do not use a test channel as runtime fallback

ADB values such as `codex_adb_*` are test inputs, not defaults. Runtime channel must originate from the real URL/clipboard parser. Use `None` only after all real sources and locked storage are empty.

### Do not add compatibility parameters to a new project

If the promotion contract is `channelSource`, do not also accept `td_channelid` just because TalkingData H5 uses that name internally. Unverified aliases create two sources of truth.

### Do not initialize analytics from device information

`getUnifiedDeviceInfo()` is often called by configuration/CMS requests before authentication. If it initializes TalkingData, it can lock `None` before clipboard attribution. It may read an already-initialized SDK ID, but it must not start the SDK.

### Do not infer delivery from the dashboard alone

Console metrics can be delayed. First prove local integration: exact App ID, SDK version, channel, session start, event invocation, and collector traffic. Then compare the event timestamp with the console. Data APIs expose computed metrics; they are not a substitute for local SDK diagnostics and may require separate credentials/permissions.

### Distinguish retry ownership

- TalkingData SDK transport: let the SDK manage its own collection queue unless official APIs expose delivery callbacks.
- App-owned backend request: implement bounded durable retry, backoff, idempotency, and persisted pending state for 5xx/network failures.
- Never store “reported=true” as proof of server receipt when the called SDK method returns no acknowledgement; name such state “invoked/enqueued” or rely on SDK semantics.

### Device ID can exist offline

The SDK device ID may be generated/read locally even when collectors are unreachable. Test this explicitly. Network failure should prevent backend guest creation but must not cause a fallback identity. Restoring network and retrying should recover/create using the same SDK identity.

### Clipboard access is observable

Android 12+ can show a system toast when reading clipboard content from another app. Android 10+ restricts reads to the focused app. Build a single, purpose-limited first-attribution read and align it with the application's privacy/consent policy; do not repeatedly scrape clipboard in the background.

## 3. Test matrix

| Case | Setup | Expected result |
|---|---|---|
| URL channel | Fresh install, launch quoted deep link | URL channel locked, clipboard cannot overwrite |
| Clipboard channel | Fresh install, copy prose containing promotion URL, normal launcher start | focus-safe retry captures channel before SDK init |
| No channel | Fresh install, empty/non-matching clipboard, normal start | channel `None`, one initialization |
| Later different channel | Existing locked install, launch another channel | original channel remains |
| ID delayed | Native mock returns empty then ID | bounded wait returns ID; guest created once |
| ID unavailable | Native mock always empty | no guest request, no token/credential write |
| Offline first start | disable Wi-Fi/data, clear app data, cold start | SDK initializes/ID remains stable; backend failure creates no alternate ID |
| Network restore | re-enable network and restart/bootstrap retry | same SDK identity creates or restores one guest |
| Existing guest | saved backend profile ID differs from current SDK mock | recovery uses profile ID |
| Web landing | visit `?channelSource=web-campaign` | H5 transport receives channel; Web clipboard untouched |

## 4. ADB recipes

Resolve the explicit ADB path from the development environment. Always quote URLs so the shell does not interpret `&`.

```bash
adb devices -l
adb logcat -c
adb uninstall com.example.app
adb install path/to/app-release.apk
adb shell am start -W -a android.intent.action.VIEW \
  -d 'exampleapp://share?channelSource=Jile-Test01' com.example.app
adb logcat -d -v brief | rg -i 'TalkingData|TDLog|tendcloud|AndroidRuntime|FATAL'
```

Offline test with restoration:

```bash
adb shell svc wifi disable
adb shell svc data disable
adb shell pm clear com.example.app
adb shell am start -W -a android.intent.action.VIEW \
  -d 'exampleapp://share?channelSource=Jile-Test01' com.example.app

# Always restore, even when the test fails.
adb shell svc wifi enable
adb shell svc data enable
adb shell dumpsys connectivity | rg 'Active default network|CONNECTED'
```

Useful checks:

```bash
adb shell dumpsys activity activities | rg 'mResumedActivity'
adb shell dumpsys package com.example.app | rg 'versionCode|versionName'
adb exec-out screencap -p > /tmp/app-check.png
```

Do not print AsyncStorage databases or complete backend responses into shared logs: they can contain member tokens, guest credentials, device IDs, or account identifiers. Compare redacted hashes/sources instead.

## 5. Delivery checklist

- State the exact customized SDK version and whether the native app was rebuilt.
- State which App ID source was used without exposing unrelated secrets.
- Report typecheck, related tests, full tests, release build, and real-device results separately.
- Confirm URL/clipboard/no-channel cases and first-valid lock.
- Confirm Android new-guest no-fallback behavior and old-guest recovery behavior.
- Confirm Wi-Fi/mobile data were restored after offline tests.
- Provide the release artifact path and metadata.
- Separate “local SDK invocation verified” from “TalkingData console data observed.”
