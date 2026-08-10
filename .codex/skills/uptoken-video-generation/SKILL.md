---
name: uptoken-video-generation
description: Generate, poll, upload reference assets for, and locally download videos using the UpToken video generation API. Use when Codex needs to create reusable video generation workflows, test UpToken/Seedance models, turn prompts or storyboards into videos, use reference images/videos/audio, save generated MP4 files locally, inspect balance/costs, or automate text-to-video/image-to-video tasks.
---

# UpToken Video Generation

## Overview

Use the UpToken API to create asynchronous video generation tasks, poll results, download MP4 outputs, and manage reusable media assets. Never hardcode API keys in generated files or client-side code; read them from `UPTOKEN_API_KEY`, an explicit secret file, or a user-provided server-side environment.

## Core Workflow

1. Choose the lowest adequate model and settings for tests: `seedance-2.0-fast`, `duration=4`, `resolution=480p`, `generate_audio=false`.
2. Submit the task to `/v1/video/generations`.
3. Poll `/v1/video/generations/:task_id` every ~5 seconds until `succeeded` or `failed`.
4. Download `content.video_url` to a local MP4 file and save the full JSON result beside it.
5. Report task id, model/settings, local path, elapsed time, and usage/cost when available.

## Decision Guide

- **Prompt only**: use `prompt` or `content` text for fast text-to-video tests.
- **Storyboard / comic panel to video**: generate or provide a panel image first, upload it if needed, then use `first_frame_url` or `image_urls`.
- **Consistent character/product**: use reference images via `image_urls` or `content[].role="reference_image"` with `seedance-2.0-pro` or `seedance-2.0-fast`.
- **Video rewriting or motion reference**: use `video_urls` or `content[].role="reference_video"` with a 2.0 model.
- **Audio-aware generation**: use `audio_urls` and/or `generate_audio=true`; verify behavior with a small sample because audio control is model-dependent.

## Models

- `seedance-2.0-pro`: higher-quality video generation, supports multimodal references, up to 15 seconds.
- `seedance-2.0-fast`: faster iteration, supports multimodal references, up to 15 seconds.
- `seedance-1.5-pro`: text-to-video plus first-frame/optional last-frame image-to-video.

Common parameters: `duration` 4-15 seconds, `resolution` `480p`/`720p`/model-supported higher values, `ratio` `16:9`/`9:16`/`1:1`/`4:3`/`3:4`/`21:9`/`adaptive`.

## Script

Use `scripts/uptoken_video.py` for repeatable operations:

```powershell
$env:UPTOKEN_API_KEY = "ut-..."
python C:\Users\Administrator\.codex\skills\uptoken-video-generation\scripts\uptoken_video.py balance
python C:\Users\Administrator\.codex\skills\uptoken-video-generation\scripts\uptoken_video.py generate `
  --prompt "comic storyboard style, rainy neon street, a girl turns back, slow camera push-in" `
  --model seedance-2.0-fast --duration 4 --resolution 480p --ratio 16:9 `
  --output-dir C:\work\jimeng\outputs
```

Useful commands:

- `balance`: check account balance.
- `upload-asset --file path`: upload a reusable image/video/audio asset and return its id/status.
- `generate --prompt ... --download`: create, poll, save result JSON, and download MP4. Download is enabled by default.
- `poll --task-id ut-... --output-dir ...`: inspect or download an existing task.

Use `--api-key-file` when the key is stored in a local secret file. Prefer this or `UPTOKEN_API_KEY`; do not copy keys from project docs into skill files.

## Storyboard Video Pattern

For story or comic storyboard-to-video:

1. Split the prose into short shots: scene, character, action, camera movement, style.
2. For quick validation, generate prompt-only videos for 1-2 shots.
3. For production, create a first-frame image per shot with consistent character/style, upload it, and call video generation with `first_frame_url` or `image_urls`.
4. Save each shot as `shot_001.mp4`, `shot_001.result.json`, etc.; keep prompts in a manifest for reruns.

## References

Read `references/api-reference.md` when exact endpoint shapes, fields, roles, or webhook/rate-limit details are needed.
