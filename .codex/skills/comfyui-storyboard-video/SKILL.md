---
name: comfyui-storyboard-video
description: Build coherent storyboard videos from character reference images by using ComfyUI to generate reachable keyframe images, UpToken/Seedance first-frame plus last-frame video generation to animate transitions, and ffmpeg to merge clips. Use when Codex needs to convert a novel, comic, character image, or storyboard concept into locally saved keyframes, transition clips, final MP4 videos, and manifests while preserving all assets.
---

# ComfyUI Storyboard Video

## Overview

Create a complete local asset package for storyboard video generation:

1. Preserve the original reference image.
2. Generate N+1 reachable keyframe images with ComfyUI.
3. Use adjacent keyframes as first/last frames to generate N transition clips with UpToken.
4. Merge clips into one MP4.
5. Save manifests, prompts, task results, source images, generated keyframes, clips, and final video in one run directory.

Never store real API keys or service tokens in skill files. Read `COMFYUI_URL`, `COMFYUI_TOKEN`, and `UPTOKEN_API_KEY` from environment variables or explicit secret files.

## Continuity Rule

Treat keyframes as a reachable sequence, not as independent illustrations. Each keyframe must be a plausible next state from the previous keyframe.

Hard constraints:

- Keep the same character identity, hairstyle, outfit family, scene, time of day, palette, and visual style across all keyframes.
- Change only one or two dimensions per step: position, gaze, camera distance, camera angle, gesture, lighting emphasis, or background depth.
- Avoid impossible jumps: do not switch locations, outfits, body orientation, weather, art style, or camera scale abruptly.
- Prefer wide or medium-safe framing for real-person-like references; this reduces moderation failures.
- For every video clip, use `keyframe_i` as `first_frame_url` and `keyframe_i+1` as `last_frame_url`.
- If a transition is blocked by moderation, retry with a safer reachable replacement keyframe: looser clothing, wider framing, less body emphasis, more environment.

For detailed prompt construction, read `references/reachable-storyboards.md`.

## Quick Start

```powershell
$env:COMFYUI_URL = "http://host:port"
$env:COMFYUI_TOKEN = "..."
$env:UPTOKEN_API_KEY = "ut-..."

python C:\Users\Administrator\.codex\skills\comfyui-storyboard-video\scripts\storyboard_pipeline.py `
  --transition-mode `
  --workflow .\comfyui_workflow\Qwen-Edit-Rapid-AIO.json `
  --image .\Original_image\img_001.webp `
  --keyframes 5 `
  --video-model seedance-1.5-pro `
  --video-duration 4 `
  --video-resolution 480p `
  --video-ratio 16:9 `
  --output-dir .\outputs\storyboard_runs
```

Output layout:

```text
run_dir/
  original/
  storyboards/
  videos/
  final/
  metadata/
  manifest_transition.json
  manifest.json
```

## Workflow Requirements

The bundled script expects a ComfyUI API prompt JSON with these editable nodes by default:

- `1.inputs.image`: `LoadImage` source image.
- `6.inputs.prompt`: positive keyframe prompt.
- `7.inputs.prompt`: negative prompt.
- `9.inputs.seed`: optional seed override when present.
- `11.inputs.filename_prefix`, `foldername_prefix`, `output_format`, `quality`: output naming.

If a different workflow uses other node ids, inspect the API prompt and patch the script's `prepare_workflow` function before running.

## Modes

Use `--transition-mode` for production storyboard video. It generates N+1 keyframes and N first/last-frame transition videos.

Use the older non-transition mode only for cheap smoke tests where each keyframe becomes an independent clip. For storyboard continuity, prefer transition mode.

## Keyframe Planning

Before running, define a small state ladder:

```text
kf_01: establishing state
kf_02: first reachable movement
kf_03: continued movement
kf_04: pause or reaction
kf_05: final reachable state
```

Then define transition prompts:

```text
transition_01: kf_01 -> kf_02
transition_02: kf_02 -> kf_03
transition_03: kf_03 -> kf_04
transition_04: kf_04 -> kf_05
```

Keep transition prompts descriptive but conservative: "naturally transition from keyframe 2 to keyframe 3" plus the single intended motion. Do not ask the model to invent a new scene inside the clip.

## Script Notes

The script uses:

- ComfyUI `/upload/image`, `/prompt`, `/history/{prompt_id}`, and `/view`.
- UpToken `/v1/assets`, `/v1/video/generations`, and polling.
- `ffmpeg` from PATH or `imageio-ffmpeg` for merging.

It saves all outputs locally and writes JSON metadata for every ComfyUI and UpToken task.
