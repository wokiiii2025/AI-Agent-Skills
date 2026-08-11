---
name: integrating-expo-talkingdata
description: Use when an Expo or React Native app needs Android first-launch clipboard attribution, dynamic channelSource parsing, TalkingData App Analytics Android or HTML5 integration, SDK device ID identity, channel reporting, zero-dashboard-data diagnosis, release APK verification, or ADB cold-start testing.
---

# Integrating Expo TalkingData

## Core principle

Treat clipboard attribution, analytics initialization, and guest identity as one ordered pipeline: lock the first valid channel before initializing TalkingData, then obtain the SDK device ID before creating a new Android guest.

## Workflow

1. Read repository rules, `git status --short`, Expo config, native Android code, services, tests, and build scripts.
2. Verify current official TalkingData documentation and inspect the exact customized SDK ZIP/demo for the target App ID. Generic examples may target another product or SDK generation.
3. Run `scripts/audit_expo_talkingdata.sh <project-root>`. Warnings require inspection; they are not proof of failure.
4. Write failing tests for attribution order and identity invariants before implementation.
5. Implement Android cold start in this order:
   - capture initial/new Intent URL in `MainActivity` and expose it to JS;
   - parse inbound `channelSource` and separate invitation fields;
   - when no channel is locked, read clipboard only after window focus through a native cached bridge with bounded retries;
   - normalize and persist the first valid channel; never overwrite it;
   - use `None` only when URL, clipboard, and storage have no channel;
   - initialize TalkingData exactly once with the locked channel;
   - bounded-wait for the TalkingData SDK device ID;
   - create a new Android guest only with that non-empty ID.
6. Rebuild after native SDK/bridge changes. Verify tests, release APK metadata, online/offline cold starts, recovery after restoring network, and console data separately.

Never initialize TalkingData inside a generic device-info getter. Early CMS/config requests can otherwise initialize `None` before attribution finishes.

## Invariants

| Concern | Required behavior |
|---|---|
| Promotion links | Accept `channelSource`; do not invent compatibility aliases. |
| First attribution | First valid channel wins permanently; later URL/clipboard values cannot overwrite it. |
| Android clipboard | Android 10+ requires app focus; do not depend on a single JS startup read. Android 12+ access notifications are expected. |
| TalkingData Android | Use the customized SDK's actual `initSDK`, `startA`, event, and device-ID APIs. |
| TalkingData H5 | Convert inbound `channelSource` to `td_channelid` only for H5 SDK transport. Do not expose `td_channelid` as a second promotion input. |
| New Android guest | TalkingData ID only; no Android ID, installation ID, random UUID, or cached fallback. |
| Existing guest | Recover with the backend profile's originally registered `deviceId`; never replace it with the current SDK ID. |
| HTTP headers | Omit missing Android `Device-Id`; guest header/body IDs must match. |
| App ID | Inject through environment/build config into JS and the merged manifest; do not hardcode runtime test IDs or commit `.env`. |
| Delivery state | SDK event invocation is not server acknowledgement; distinguish invoked/enqueued from observed console data. |

## Required verification

Test URL/clipboard/no-channel paths, first-valid locking, initialization order, delayed/missing SDK IDs, no fallback identity, old-guest recovery, header/body equality, and Web landing attribution. Build release, inspect the APK rather than source config, install on a real device, test offline then restore networking, and redact tokens, credentials, account IDs, and device IDs from logs.

## Resource routing

- Read [references/integration-patterns.md](references/integration-patterns.md) before implementing or reviewing code.
- Read [references/troubleshooting-and-verification.md](references/troubleshooting-and-verification.md) when clipboard is empty, channel name is `--`, dashboard metrics remain zero, debug/release differ, App IDs appear mismatched, or ADB verification is needed.

Stop and report evidence instead of guessing when the SDK archive, App ID, product line, backend identity contract, or privacy/consent behavior cannot be verified.
