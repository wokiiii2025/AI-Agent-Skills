# Script Usage

Script:

```text
scripts/storyboard_pipeline.py
```

Required configuration:

- `COMFYUI_URL` or `--comfy-url`
- `COMFYUI_TOKEN` or `--comfy-token`
- `UPTOKEN_API_KEY`, `--uptoken-api-key`, or `--uptoken-api-key-file`

Common transition-mode command:

```powershell
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

Custom keyframes:

Use `--keyframes-json keyframes.json`, where each item has:

```json
{
  "id": "kf_01",
  "storyboard": "reachable keyframe prompt"
}
```

Custom transitions:

Use `--transitions-json transitions.json`, a JSON list of strings. It should contain one fewer item than the number of keyframes.

Asset retention:

- `original/`: copied source image.
- `storyboards/`: ComfyUI keyframe images.
- `videos/`: UpToken transition clips.
- `final/`: merged video.
- `metadata/`: per-task JSON records.
- `manifest_transition.json`: transition-mode run manifest.
