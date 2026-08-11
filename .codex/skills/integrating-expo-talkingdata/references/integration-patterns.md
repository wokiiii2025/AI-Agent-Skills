# Expo + TalkingData Integration Patterns

## Contents

1. Architecture
2. Attribution storage
3. Android clipboard bridge
4. TalkingData service
5. Device identity and authentication
6. Environment and build injection
7. Web/PWA
8. Official documentation routing

## 1. Architecture

Keep these boundaries even if filenames differ:

```text
MainActivity/native bridge
  -> launch URL + focus-safe initial clipboard text
referrerStore
  -> parse, normalize, first-valid lock
talkingdata service
  -> configure, initialize once, event calls, SDK device ID wait
deviceInfo
  -> read SDK ID for ordinary request context; never initialize analytics
auth service
  -> orchestrate attribution -> init -> ID -> new guest
http client
  -> conditional headers; guest header/body equality
```

Pages should consume session/referrer services and never read clipboard, call the SDK, or build device headers directly.

## 2. Attribution storage

Use a persisted record such as:

```ts
type ReferrerData = {
  channelSource?: string;
  invitationCode?: string;
  sourceType?: "deep_link" | "clipboard";
};
```

Rules:

- Extract `channelSource` from regular URLs, custom schemes, and clipboard prose containing a URL.
- Normalize whitespace and unsafe channel characters, but preserve meaningful ASCII `-`, `_`, and `.`.
- Save only the first valid channel. Later URL/clipboard reads return the locked record without overwriting it.
- Keep invitation codes separate from analytics channel IDs and never send invitation secrets as TalkingData event properties.
- A clipboard without a valid URL/channel is not an error and must not lock `None` before retries finish.

## 3. Android clipboard bridge

Android 10+ permits clipboard reads only while the app has focus. A JavaScript call during React startup may run before the Activity window is focused, especially on release cold starts.

Preferred native pattern:

```kotlin
class MainActivity : ReactActivity() {
  override fun onWindowFocusChanged(hasFocus: Boolean) {
    super.onWindowFocusChanged(hasFocus)
    if (hasFocus) cacheInitialClipboardTextOnce()
  }

  override fun onCreate(savedInstanceState: Bundle?) {
    cacheInitialIntentUrl(intent)
    super.onCreate(savedInstanceState)
  }

  override fun onNewIntent(intent: Intent) {
    super.onNewIntent(intent)
    setIntent(intent)
    cacheInitialIntentUrl(intent)
  }
}
```

Expose cached values through a native module returning Promises. In JavaScript, use bounded delays such as `[0, 150, 350, 600, 900]`; stop on the first valid attribution. Avoid endless polling and never read the clipboard on every foreground transition.

`expo-clipboard` remains suitable for user-triggered copy/paste. For automatic first-launch attribution on Android, the focus-safe native cache is more deterministic. On Android 12+, system clipboard-access notifications are expected. Do not hide or misrepresent this access.

## 4. TalkingData service

The service owns a single initialization Promise. Device ID reads must return `null` before initialization instead of implicitly initializing with a fallback channel.

```ts
let initializationPromise: Promise<RuntimeState> | null = null;

export function initializeTalkingData(referrer?: ReferrerData) {
  initializationPromise ??= initializeInternal(referrer);
  return initializationPromise;
}

export async function getTalkingDataDeviceId() {
  if (Platform.OS !== "android" || !initializationPromise) return null;
  const state = await initializationPromise;
  if (!state.available) return null;
  return normalize(await NativeModules.TalkingDataSDK.getDeviceID()) || null;
}

export async function waitForTalkingDataDeviceId(
  delays: readonly number[] = [0, 100, 200, 400, 800],
) {
  for (const delay of delays) {
    if (delay > 0) await new Promise((resolve) => setTimeout(resolve, delay));
    const id = await getTalkingDataDeviceId();
    if (id) return id;
  }
  return null;
}
```

Use the method names and signatures from the downloaded customized SDK/demo. A generic online example can target another SDK version or product line.

Call custom events only after the runtime reports available. An SDK event call is an enqueue/invocation signal, not server-delivery acknowledgement; do not mark business delivery successful solely from a void SDK call.

## 5. Device identity and authentication

For Android new-guest creation:

```ts
const deviceId = (await waitForTalkingDataDeviceId())?.trim();
if (!deviceId) throw new Error("无法取得 TalkingData 设备标识，请重试");
await createGuest({ deviceId, channelSource, invitationCode });
```

Do not write auth tokens, guest credentials, or installation IDs before this check passes. Keep the bootstrap Promise retryable by clearing its in-flight guard in `finally` after failure.

For old sessions, use `profile.deviceId` for guest credential recovery and refresh-token recovery. This is backend identity continuity, not a fallback for new identity creation.

## 6. Environment and build injection

Use one public variable name consistently, for example:

```text
EXPO_PUBLIC_TALKINGDATA_APP_ID
```

Verify all paths:

- `.env.development`, `.env.local`, `.env.production` provide local values but remain subject to repository secret policy.
- `app.config.js` reads the environment for Expo/JS config.
- Gradle reads the same variable into a manifest placeholder such as `TD_APP_ID`.
- Docker build declares and forwards the build argument into Expo export.
- release commands control dotenv precedence; Expo auto-dotenv can overwrite a shell override unless deliberately disabled/configured.

Never log the full App ID as part of routine application logs. It is not an authentication secret in the same sense as a token, but centralizing it avoids packaging the wrong application during tests.

After building, inspect the artifact rather than trusting source files:

```bash
aapt dump badging app-release.apk | head -1
aapt dump xmltree app-release.apk AndroidManifest.xml | rg -A2 'TD_APP_ID'
```

## 7. Web/PWA

Use the TalkingData HTML5 product documentation and script for Web. Resolve and lock inbound `channelSource` first. If the H5 SDK requires `td_channelid`, write it to the current URL only as an SDK transport parameter before loading the script, and optionally remove it afterward if the SDK permits.

Do not read the Web clipboard automatically at startup. Browser clipboard APIs can prompt or require user activation. Web attribution should normally come from the landing URL.

## 8. Official documentation routing

Re-check current official pages before implementation:

- Android application analytics: https://doc.talkingdata.com/posts/21
- SDK 5.x Android integration: https://doc.talkingdata.com/posts/1025
- React Native integration: https://doc.talkingdata.com/posts/1028
- HTML5 integration: https://doc.talkingdata.com/posts/36
- Expo Clipboard: https://docs.expo.dev/versions/latest/sdk/clipboard/
- Android 10 clipboard focus restriction: https://developer.android.com/about/versions/10/privacy/changes
- Android clipboard access behavior: https://developer.android.com/develop/ui/views/touch-and-input/copy-paste

Treat the customized SDK ZIP and its demo as the final API source for that generated package when it differs from generic documentation.
