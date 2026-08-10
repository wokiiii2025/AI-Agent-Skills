#!/usr/bin/env python3
"""Generate storyboard images with ComfyUI, then turn them into UpToken videos."""

from __future__ import annotations

import argparse
import copy
import json
import mimetypes
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


DEFAULT_COMFY_URL = ""
DEFAULT_COMFY_TOKEN = ""
UPTOKEN_URL = "https://uptoken.cc"

DEFAULT_STORYBOARD_PROMPT = (
    "Create a cinematic manga storyboard panel based on the reference person. "
    "Preserve the person's identity, face, hairstyle, and overall appearance. "
    "Make the person fully clothed in a stylish modern outfit. "
    "Scene: rainy neon city street at night, dramatic rim light, reflective pavement, "
    "the character turns back toward camera, medium shot, dynamic comic composition, "
    "clean line art, rich color, high detail, no text, no watermark."
)

DEFAULT_NEGATIVE_PROMPT = (
    "nudity, explicit content, lingerie, underwear, see-through clothing, watermark, logo, "
    "text, bad hands, deformed face, extra fingers, low quality, blurry"
)

VIDEO_PROMPT = (
    "Cinematic manga storyboard animation. Preserve the same character identity and outfit. "
    "Rainy neon city street at night, subtle camera push-in, rain motion, reflective pavement, "
    "dramatic lighting, coherent comic style."
)

DEFAULT_SHOTS = [
    {
        "id": "shot_01",
        "storyboard": (
            "Create storyboard panel 1 based on the reference person. Preserve identity, face, hairstyle, "
            "and overall appearance. Fully clothed stylish modern outfit. Establishing medium-wide shot: "
            "the character stands at the entrance of a rainy neon city alley at night, reflective pavement, "
            "cinematic manga style, clean line art, no text, no watermark."
        ),
        "video": (
            "Storyboard shot 1 animation. Establishing shot in a rainy neon alley at night. "
            "The character stands still, rain falls, neon reflections shimmer, slow cinematic push-in."
        ),
    },
    {
        "id": "shot_02",
        "storyboard": (
            "Create storyboard panel 2 based on the same reference person. Preserve identity and outfit. "
            "Medium shot: the character turns back toward the camera under neon signs, rain streaks in the air, "
            "dramatic rim light, dynamic comic composition, no text, no watermark."
        ),
        "video": (
            "Storyboard shot 2 animation. The same character slowly turns back toward camera, "
            "rain motion and neon glow, subtle handheld camera movement."
        ),
    },
    {
        "id": "shot_03",
        "storyboard": (
            "Create storyboard panel 3 based on the same reference person. Preserve identity and outfit. "
            "Tracking shot: the character walks through the wet neon street, side angle, city signs and rain reflections, "
            "cinematic manga panel, high detail, no text, no watermark."
        ),
        "video": (
            "Storyboard shot 3 animation. Side tracking shot of the same character walking through the wet neon street, "
            "rain falls, pavement reflections move, coherent manga style."
        ),
    },
    {
        "id": "shot_04",
        "storyboard": (
            "Create storyboard panel 4 based on the same reference person. Preserve identity and outfit. "
            "Close-up finale: the character pauses beneath a bright sign, confident expression, rain droplets on hair and jacket, "
            "dramatic cinematic manga lighting, no text, no watermark."
        ),
        "video": (
            "Storyboard shot 4 animation. Close-up finale under a bright neon sign. "
            "The same character pauses with a confident expression, rain droplets move, slow camera push-in."
        ),
    },
]

DEFAULT_KEYFRAMES = [
    {
        "id": "kf_01",
        "storyboard": (
            "Create keyframe 1 for a cinematic manga sequence based on the reference person. Preserve identity, "
            "face, hairstyle, and overall appearance. Fully clothed in a loose modern coat. Wide establishing shot: "
            "the character stands at the entrance of a rainy neon city street at night, reflective pavement, rich "
            "environment, safe composition, no body emphasis, no text, no watermark."
        ),
    },
    {
        "id": "kf_02",
        "storyboard": (
            "Create keyframe 2 for the same cinematic manga sequence and same reference person. Preserve identity "
            "and loose modern coat. Medium-wide shot: the character starts walking into the rainy neon street, "
            "city signs glowing, reflections on pavement, safe composition, no body emphasis, no text, no watermark."
        ),
    },
    {
        "id": "kf_03",
        "storyboard": (
            "Create keyframe 3 for the same cinematic manga sequence and same reference person. Preserve identity "
            "and outfit. Side tracking composition: the fully clothed character walks past neon shopfronts in the "
            "rain, umbrella-like street lights, dynamic but safe manga panel, no body emphasis, no text, no watermark."
        ),
    },
    {
        "id": "kf_04",
        "storyboard": (
            "Create keyframe 4 for the same cinematic manga sequence and same reference person. Preserve identity "
            "and loose coat. Medium shot from the front: the character pauses beneath a bright neon sign, rain "
            "droplets on coat and hair, cinematic lighting, safe upper-body framing, no text, no watermark."
        ),
    },
    {
        "id": "kf_05",
        "storyboard": (
            "Create keyframe 5 for the same cinematic manga sequence and same reference person. Preserve identity "
            "and outfit. Finale shot: the character looks toward the glowing city skyline from a rainy street corner, "
            "wide cinematic manga frame, emotional but safe composition, no body emphasis, no text, no watermark."
        ),
    },
]

DEFAULT_TRANSITIONS = [
    "Transition naturally from keyframe 1 to keyframe 2. The same fully clothed character begins walking into the rainy neon street. Preserve identity, outfit, manga style, lighting, and environment continuity.",
    "Transition naturally from keyframe 2 to keyframe 3. The same fully clothed character continues walking through the rainy neon street. Preserve identity, outfit, manga style, rain, and reflections.",
    "Transition naturally from keyframe 3 to keyframe 4. The same fully clothed character slows down and pauses beneath a bright neon sign. Preserve identity, outfit, manga style, and cinematic lighting.",
    "Transition naturally from keyframe 4 to keyframe 5. The same fully clothed character turns toward the glowing city skyline at the rainy street corner. Preserve identity, outfit, manga style, and emotional continuity.",
]


def authed_url(base: str, path: str, token: str, params: dict[str, str] | None = None) -> str:
    query = dict(params or {})
    if token:
        query["token"] = token
    return f"{base.rstrip('/')}{path}?{urllib.parse.urlencode(query)}"


def read_api_key(args: argparse.Namespace) -> str:
    if args.uptoken_api_key:
        return args.uptoken_api_key.strip()
    if args.uptoken_api_key_file:
        return Path(args.uptoken_api_key_file).read_text(encoding="utf-8").strip()
    key = os.environ.get("UPTOKEN_API_KEY", "").strip()
    if key:
        return key
    raise SystemExit("Missing UpToken key. Set UPTOKEN_API_KEY or pass --uptoken-api-key-file.")


def require_comfy_config(args: argparse.Namespace) -> None:
    args.comfy_url = (args.comfy_url or os.environ.get("COMFYUI_URL", "")).strip().rstrip("/")
    args.comfy_token = (args.comfy_token or os.environ.get("COMFYUI_TOKEN", "")).strip()
    if not args.comfy_url:
        raise SystemExit("Missing ComfyUI URL. Pass --comfy-url or set COMFYUI_URL.")
    if not args.comfy_token:
        raise SystemExit("Missing ComfyUI token. Pass --comfy-token or set COMFYUI_TOKEN.")


def request_json(method: str, url: str, body: dict | None = None, headers: dict | None = None, timeout: int = 120) -> dict:
    data = None
    request_headers = {"User-Agent": "Codex-Jimeng-Storyboard/1.0"}
    if headers:
        request_headers.update(headers)
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        request_headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {exc.reason}: {details}") from exc


def upload_multipart(
    url: str,
    file_path: Path,
    field_name: str,
    extra_fields: dict[str, str] | None = None,
    auth_key: str | None = None,
    filename: str | None = None,
) -> dict:
    boundary = f"----codex-{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    parts: list[bytes] = []
    for key, value in (extra_fields or {}).items():
        parts.append(
            (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
                f"{value}\r\n"
            ).encode("utf-8")
        )
    parts.append(
        (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{field_name}"; filename="{filename or file_path.name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(file_path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    headers = {
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "User-Agent": "Codex-Jimeng-Storyboard/1.0",
    }
    if auth_key:
        headers["Authorization"] = f"Bearer {auth_key}"
    req = urllib.request.Request(url, data=b"".join(parts), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} {exc.reason}: {details}") from exc


def download_file(url: str, output_path: Path, headers: dict | None = None) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    request_headers = {"User-Agent": "Codex-Jimeng-Storyboard/1.0"}
    if headers:
        request_headers.update(headers)
    req = urllib.request.Request(url, headers=request_headers)
    with urllib.request.urlopen(req, timeout=180) as resp:
        output_path.write_bytes(resp.read())


def prepare_workflow(template_path: Path, remote_image_name: str, prompt: str, negative: str, prefix: str, seed: int | None = None) -> dict:
    workflow = json.loads(template_path.read_text(encoding="utf-8"))
    workflow = copy.deepcopy(workflow)
    workflow["1"]["inputs"]["image"] = remote_image_name
    workflow["6"]["inputs"]["prompt"] = prompt
    workflow["7"]["inputs"]["prompt"] = negative
    workflow["11"]["inputs"]["filename_prefix"] = prefix
    workflow["11"]["inputs"]["foldername_prefix"] = "jimeng_storyboards"
    workflow["11"]["inputs"]["output_format"] = ".png"
    workflow["11"]["inputs"]["quality"] = 95
    if seed is not None and "9" in workflow and "seed" in workflow["9"].get("inputs", {}):
        workflow["9"]["inputs"]["seed"] = seed
    return workflow


def submit_comfy(args: argparse.Namespace, image_path: Path, prompt: str, negative: str, output_dir: Path, shot_id: str, seed: int) -> tuple[Path, dict]:
    run_id = time.strftime("%Y%m%d_%H%M%S")
    remote_name = f"jimeng_{image_path.stem}_{shot_id}_{run_id}{image_path.suffix.lower()}"
    upload_url = f"{args.comfy_url.rstrip()}/upload/image"
    upload_multipart(
        upload_url,
        image_path,
        "image",
        {"type": "input", "overwrite": "true", "subfolder": ""},
        auth_key=args.comfy_token,
        filename=remote_name,
    )

    prefix = f"{image_path.stem}_{shot_id}_{run_id}"
    workflow = prepare_workflow(Path(args.workflow), remote_name, prompt, negative, prefix, seed)
    prompt_url = f"{args.comfy_url.rstrip()}/prompt"
    queued = request_json(
        "POST",
        prompt_url,
        {"prompt": workflow, "client_id": str(uuid.uuid4())},
        headers={"Authorization": f"Bearer {args.comfy_token}"},
        timeout=120,
    )
    prompt_id = queued["prompt_id"]

    history_url = authed_url(args.comfy_url, f"/history/{prompt_id}", args.comfy_token)
    deadline = time.time() + args.comfy_timeout
    history = {}
    while time.time() < deadline:
        history = request_json("GET", history_url, headers={"Authorization": f"Bearer {args.comfy_token}"}, timeout=120)
        if prompt_id in history:
            break
        time.sleep(args.poll_interval)
    else:
        raise SystemExit(f"Timed out waiting for ComfyUI prompt {prompt_id}")

    record = history[prompt_id]
    outputs = record.get("outputs", {})
    images = []
    for node_output in outputs.values():
        images.extend(node_output.get("images", []))
    if not images:
        raise SystemExit(f"ComfyUI prompt {prompt_id} finished without image output")

    image_info = images[0]
    params = {
        "filename": image_info["filename"],
        "subfolder": image_info.get("subfolder", ""),
        "type": image_info.get("type", "output"),
    }
    view_url = f"{args.comfy_url.rstrip()}/view?{urllib.parse.urlencode(params)}"
    storyboard_path = output_dir / "storyboards" / image_info["filename"]
    download_file(view_url, storyboard_path, {"Authorization": f"Bearer {args.comfy_token}"})

    meta = {
        "source_image": str(image_path),
        "remote_image_name": remote_name,
        "prompt_id": prompt_id,
        "workflow_prompt": prompt,
        "negative_prompt": negative,
        "history": record,
        "storyboard_path": str(storyboard_path),
        "storyboard_view_url": view_url,
    }
    (output_dir / "metadata").mkdir(parents=True, exist_ok=True)
    meta_path = output_dir / "metadata" / f"{shot_id}.{image_path.stem}_{run_id}.comfy.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return storyboard_path, meta


def upload_uptoken_asset(file_path: Path, api_key: str) -> dict:
    return upload_multipart(f"{UPTOKEN_URL}/v1/assets", file_path, "file", auth_key=api_key)


def create_uptoken_video(args: argparse.Namespace, storyboard_path: Path, asset_url: str, api_key: str, output_dir: Path, shot_id: str, video_prompt: str) -> dict:
    body = {
        "model": args.video_model,
        "prompt": video_prompt,
        "first_frame_url": asset_url,
        "duration": args.video_duration,
        "resolution": args.video_resolution,
        "ratio": args.video_ratio,
        "generate_audio": args.generate_audio,
    }
    task = request_json(
        "POST",
        f"{UPTOKEN_URL}/v1/video/generations",
        body,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
    )
    task_id = task["id"]
    deadline = time.time() + args.video_timeout
    result = task
    while time.time() < deadline:
        result = request_json(
            "GET",
            f"{UPTOKEN_URL}/v1/video/generations/{urllib.parse.quote(task_id)}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120,
        )
        status = result.get("status")
        print(f"[UpToken] {task_id} status={status}", flush=True)
        if status in {"succeeded", "failed"}:
            break
        time.sleep(args.poll_interval)
    else:
        raise SystemExit(f"Timed out waiting for UpToken task {task_id}")

    video_path = None
    video_url = result.get("content", {}).get("video_url")
    if video_url:
        video_path = output_dir / "videos" / f"{shot_id}.{storyboard_path.stem}.{task_id}.mp4"
        download_file(video_url, video_path)

    result_payload = {
        "storyboard_path": str(storyboard_path),
        "shot_id": shot_id,
        "asset_url": asset_url,
        "video_prompt": video_prompt,
        "video_result": result,
        "video_path": str(video_path) if video_path else None,
    }
    (output_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (output_dir / "metadata" / f"{shot_id}.{storyboard_path.stem}.{task_id}.video.json").write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result_payload


def create_uptoken_transition_video(
    args: argparse.Namespace,
    first_frame: Path,
    last_frame: Path,
    first_url: str,
    last_url: str,
    api_key: str,
    output_dir: Path,
    shot_id: str,
    video_prompt: str,
) -> dict:
    body = {
        "model": args.video_model,
        "prompt": video_prompt,
        "first_frame_url": first_url,
        "last_frame_url": last_url,
        "duration": args.video_duration,
        "resolution": args.video_resolution,
        "ratio": args.video_ratio,
        "generate_audio": args.generate_audio,
    }
    task = request_json(
        "POST",
        f"{UPTOKEN_URL}/v1/video/generations",
        body,
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=120,
    )
    task_id = task["id"]
    deadline = time.time() + args.video_timeout
    result = task
    while time.time() < deadline:
        result = request_json(
            "GET",
            f"{UPTOKEN_URL}/v1/video/generations/{urllib.parse.quote(task_id)}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=120,
        )
        status = result.get("status")
        print(f"[UpToken] {shot_id} {task_id} status={status}", flush=True)
        if status in {"succeeded", "failed"}:
            break
        time.sleep(args.poll_interval)
    else:
        raise SystemExit(f"Timed out waiting for UpToken task {task_id}")

    video_path = None
    video_url = result.get("content", {}).get("video_url")
    if video_url:
        video_path = output_dir / "videos" / f"{shot_id}.{first_frame.stem}_to_{last_frame.stem}.{task_id}.mp4"
        download_file(video_url, video_path)

    result_payload = {
        "shot_id": shot_id,
        "first_frame_path": str(first_frame),
        "last_frame_path": str(last_frame),
        "first_frame_url": first_url,
        "last_frame_url": last_url,
        "video_prompt": video_prompt,
        "video_result": result,
        "video_path": str(video_path) if video_path else None,
    }
    (output_dir / "metadata").mkdir(parents=True, exist_ok=True)
    (output_dir / "metadata" / f"{shot_id}.{task_id}.transition_video.json").write_text(
        json.dumps(result_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result_payload


def asset_url_from_response(response: dict) -> str:
    for key in ("url", "asset_url", "uri"):
        if response.get(key):
            return response[key]
    asset_id = response.get("id") or response.get("asset_id")
    if asset_id:
        return f"asset://{asset_id}"
    raise SystemExit(f"Could not find asset id/url in UpToken asset response: {response}")


def select_images(args: argparse.Namespace) -> list[Path]:
    if args.image:
        return [Path(args.image)]
    image_dir = Path(args.image_dir)
    images = sorted(
        p for p in image_dir.iterdir()
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    )
    if args.limit:
        images = images[: args.limit]
    return images


def ffmpeg_exe() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise SystemExit("ffmpeg was not found and imageio-ffmpeg is unavailable; cannot merge videos.") from exc


def quote_concat_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "/").replace("'", "'\\''")


def merge_videos(video_paths: list[Path], final_path: Path) -> Path:
    if not video_paths:
        raise SystemExit("No video clips available to merge.")
    final_path.parent.mkdir(parents=True, exist_ok=True)
    concat_file = final_path.parent / "concat_list.txt"
    concat_file.write_text(
        "".join(f"file '{quote_concat_path(path)}'\n" for path in video_paths),
        encoding="utf-8",
    )
    exe = ffmpeg_exe()
    copy_cmd = [exe, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(final_path)]
    result = subprocess.run(copy_cmd, text=True, capture_output=True)
    if result.returncode == 0:
        return final_path
    encode_cmd = [
        exe,
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(final_path),
    ]
    result = subprocess.run(encode_cmd, text=True, capture_output=True)
    if result.returncode != 0:
        raise SystemExit(f"ffmpeg merge failed:\n{result.stderr}")
    return final_path


def load_shots(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.shots_json:
        shots = json.loads(Path(args.shots_json).read_text(encoding="utf-8"))
    else:
        shots = DEFAULT_SHOTS
    return shots[: args.shots]


def load_keyframes(args: argparse.Namespace) -> list[dict[str, str]]:
    if args.keyframes_json:
        keyframes = json.loads(Path(args.keyframes_json).read_text(encoding="utf-8"))
    else:
        keyframes = DEFAULT_KEYFRAMES
    return keyframes[: args.keyframes]


def transition_prompts(count: int, args: argparse.Namespace) -> list[str]:
    if args.transitions_json:
        prompts = json.loads(Path(args.transitions_json).read_text(encoding="utf-8"))
    else:
        prompts = DEFAULT_TRANSITIONS
    if len(prompts) < count:
        prompts = prompts + [args.video_prompt] * (count - len(prompts))
    return prompts[:count]


def make_run_dir(args: argparse.Namespace, image_path: Path) -> Path:
    if args.run_dir:
        run_dir = Path(args.run_dir)
    else:
        run_dir = Path(args.output_dir) / f"{image_path.stem}_{time.strftime('%Y%m%d_%H%M%S')}_{args.shots}shots"
    for name in ("original", "storyboards", "videos", "final", "metadata"):
        (run_dir / name).mkdir(parents=True, exist_ok=True)
    shutil.copy2(image_path, run_dir / "original" / image_path.name)
    return run_dir


def run_transition_mode(args: argparse.Namespace, image_path: Path, api_key: str | None, output_dir: Path) -> dict:
    run_dir = make_run_dir(args, image_path)
    keyframes = load_keyframes(args)
    frame_items = []
    for index, keyframe in enumerate(keyframes, start=1):
        frame_id = keyframe.get("id") or f"kf_{index:02d}"
        prompt = keyframe.get("storyboard") or args.storyboard_prompt
        seed = int(time.time() * 1000) % 10_000_000_000 + index
        print(f"[ComfyUI] generating {frame_id} keyframe for {image_path}", flush=True)
        storyboard_path, comfy_meta = submit_comfy(args, image_path, prompt, args.negative_prompt, run_dir, frame_id, seed)
        item = {
            "keyframe_id": frame_id,
            "storyboard_path": str(storyboard_path),
            "storyboard_prompt": prompt,
            "comfy_prompt_id": comfy_meta["prompt_id"],
        }
        if api_key:
            print(f"[UpToken] uploading {frame_id} keyframe asset {storyboard_path}", flush=True)
            asset = upload_uptoken_asset(storyboard_path, api_key)
            item["asset"] = asset
            item["asset_url"] = asset_url_from_response(asset)
        frame_items.append(item)

    clips: list[Path] = []
    transition_items = []
    if api_key:
        prompts = transition_prompts(len(frame_items) - 1, args)
        for index in range(len(frame_items) - 1):
            shot_id = f"transition_{index + 1:02d}"
            first = frame_items[index]
            last = frame_items[index + 1]
            first_path = Path(first["storyboard_path"])
            last_path = Path(last["storyboard_path"])
            print(f"[UpToken] generating {shot_id} with first+last frames", flush=True)
            video = create_uptoken_transition_video(
                args,
                first_path,
                last_path,
                first["asset_url"],
                last["asset_url"],
                api_key,
                run_dir,
                shot_id,
                prompts[index],
            )
            transition_items.append(video)
            if video.get("video_path"):
                clips.append(Path(video["video_path"]))

    run_item = {
        "source_image": str(image_path),
        "run_dir": str(run_dir),
        "mode": "transition",
        "keyframes": frame_items,
        "transitions": transition_items,
    }
    if clips and args.merge:
        final_path = merge_videos(clips, run_dir / "final" / f"{image_path.stem}_{len(clips)}transition_final.mp4")
        run_item["final_video_path"] = str(final_path)
    (run_dir / "manifest_transition.json").write_text(json.dumps(run_item, ensure_ascii=False, indent=2), encoding="utf-8")
    return run_item


def main() -> None:
    parser = argparse.ArgumentParser(description="ComfyUI storyboard image -> UpToken video pipeline")
    parser.add_argument("--comfy-url", default=DEFAULT_COMFY_URL)
    parser.add_argument("--comfy-token", default=DEFAULT_COMFY_TOKEN)
    parser.add_argument("--workflow", default="comfyui_workflow/Qwen-Edit-Rapid-AIO.json")
    parser.add_argument("--image-dir", default="Original_image")
    parser.add_argument("--image")
    parser.add_argument("--limit", type=int, default=1)
    parser.add_argument("--output-dir", default="outputs/storyboard_runs")
    parser.add_argument("--run-dir")
    parser.add_argument("--shots", type=int, default=1)
    parser.add_argument("--shots-json", help="JSON list with id, storyboard, and video fields.")
    parser.add_argument("--transition-mode", action="store_true")
    parser.add_argument("--keyframes", type=int, default=5)
    parser.add_argument("--keyframes-json", help="JSON list with id and storyboard fields.")
    parser.add_argument("--transitions-json", help="JSON list of transition video prompts.")
    parser.add_argument("--storyboard-prompt", default=DEFAULT_STORYBOARD_PROMPT)
    parser.add_argument("--negative-prompt", default=DEFAULT_NEGATIVE_PROMPT)
    parser.add_argument("--skip-video", action="store_true")
    parser.add_argument("--uptoken-api-key")
    parser.add_argument("--uptoken-api-key-file")
    parser.add_argument("--video-model", default="seedance-2.0-fast")
    parser.add_argument("--video-prompt", default=VIDEO_PROMPT)
    parser.add_argument("--video-duration", type=int, default=4)
    parser.add_argument("--video-resolution", default="480p")
    parser.add_argument("--video-ratio", default="16:9")
    parser.add_argument("--generate-audio", action="store_true")
    parser.add_argument("--merge", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--poll-interval", type=int, default=5)
    parser.add_argument("--comfy-timeout", type=int, default=1800)
    parser.add_argument("--video-timeout", type=int, default=7200)
    args = parser.parse_args()
    require_comfy_config(args)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    api_key = None if args.skip_video else read_api_key(args)
    manifest = []

    for image_path in select_images(args):
        if args.transition_mode:
            manifest.append(run_transition_mode(args, image_path, api_key, output_dir))
            continue
        run_dir = make_run_dir(args, image_path)
        clips: list[Path] = []
        run_item = {"source_image": str(image_path), "run_dir": str(run_dir), "shots": []}
        for index, shot in enumerate(load_shots(args), start=1):
            shot_id = shot.get("id") or f"shot_{index:02d}"
            storyboard_prompt = shot.get("storyboard") or args.storyboard_prompt
            video_prompt = shot.get("video") or args.video_prompt
            seed = int(time.time() * 1000) % 10_000_000_000 + index
            print(f"[ComfyUI] generating {shot_id} storyboard for {image_path}", flush=True)
            storyboard_path, comfy_meta = submit_comfy(args, image_path, storyboard_prompt, args.negative_prompt, run_dir, shot_id, seed)
            shot_item = {
                "shot_id": shot_id,
                "source_image": str(image_path),
                "storyboard_path": str(storyboard_path),
                "comfy_prompt_id": comfy_meta["prompt_id"],
                "storyboard_prompt": storyboard_prompt,
            }
            if not args.skip_video:
                print(f"[UpToken] uploading {shot_id} storyboard asset {storyboard_path}", flush=True)
                asset = upload_uptoken_asset(storyboard_path, api_key)
                asset_url = asset_url_from_response(asset)
                print(f"[UpToken] generating {shot_id} video from {asset_url}", flush=True)
                video = create_uptoken_video(args, storyboard_path, asset_url, api_key, run_dir, shot_id, video_prompt)
                video_path = video.get("video_path")
                if video_path:
                    clips.append(Path(video_path))
                shot_item.update({"asset": asset, "asset_url": asset_url, "video": video})
            run_item["shots"].append(shot_item)
        if clips and args.merge:
            final_path = merge_videos(clips, run_dir / "final" / f"{image_path.stem}_{len(clips)}shot_final.mp4")
            run_item["final_video_path"] = str(final_path)
        manifest.append(run_item)

    manifest_path = Path(manifest[-1]["run_dir"]) / "manifest.json" if len(manifest) == 1 else output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(manifest_path), "items": manifest}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
