---
name: prompt-assist-api-tester
description: Compare and regression-test prompt-assist text generation APIs for the role/create web app. Use when testing Ollama versus the current prompt-assist API, validating text-to-image or image-to-image helper prompts, preserving exact web preset labels, selectMode single/multiple behavior, mutexKey handling, API URLs, model names, auth tokens, and the project system prompts from docs/NSFW系统提示词.md.
---

# Prompt Assist API Tester

## Overview

Use this skill to test whether prompt-assist text APIs correctly transform the role/create web presets into final prompts for text-to-image and image-to-image workflows.

The reusable script keeps the web preset filling rules outside model memory: it loads `references/web_prompt_presets.json`, validates single/multiple selections and mutex groups, reads the project system prompt directly from `docs/NSFW系统提示词.md`, calls each configured API, scores option preservation, and writes JSON reports.
Every run must produce both a machine-readable JSON report and a human-readable HTML comparison report. The HTML report must show each provider's extracted prompt output, status, latency, scoring problems, and a preview/link to the actual raw API response JSON.
The script must not rewrite, downgrade, sanitize, or patch provider output. Program logic is limited to API calls, raw output capture, HTML/JSON reporting, and local scoring flags.

## Workflow

1. Read `.env` in this skill directory first. Do not print tokens in user-facing responses.
2. Use `references/web_prompt_presets.json` as the source of truth for preset labels, `selectMode`, `mutexKey`, and prompt expansion.
3. Use `scripts/prompt_assist_compare.py` for repeatable tests instead of hand-building API requests.
4. For image-to-image Ollama tests, pass the project image-to-image system prompt from `docs/NSFW系统提示词.md` without adapting or downgrading it. For text-to-image, pass the text-to-image system prompt from the same file.
5. Store reports under the project `reports/` directory unless the user asks otherwise.
6. Always return the generated `.html` report path to the user, plus the `.json` path when useful.

## Quick Commands

From `C:\Project\comfyui-3`:

```powershell
C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -X utf8 C:\Users\Administrator\.codex\skills\prompt-assist-api-tester\scripts\prompt_assist_compare.py --mode image_to_image --project C:\Project\comfyui-3
```

Text-to-image:

```powershell
C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -X utf8 C:\Users\Administrator\.codex\skills\prompt-assist-api-tester\scripts\prompt_assist_compare.py --mode text_to_image --project C:\Project\comfyui-3
```

Only one provider:

```powershell
C:\Users\Administrator\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe -X utf8 C:\Users\Administrator\.codex\skills\prompt-assist-api-tester\scripts\prompt_assist_compare.py --mode image_to_image --providers ollama
```

## Configuration

Configure API URLs, model names, and auth tokens in `.env` next to this `SKILL.md`.

Important variables:

- `TEXT_GENERATION_OLLAMA_GENERATE_URL`: Ollama `/api/generate` URL for text generation.
- `TEXT_GENERATION_OLLAMA_MODEL`: Ollama model name for prompt assist and role completion.
- `PROMPT_ASSIST_CURRENT_API_URL`: current production prompt-assist text API, `/chat/char/image/prompt`.
- `PROMPT_ASSIST_TEXT_TO_IMAGE_TYPE`: current API type value for text-to-image prompt assist, usually `text_to_image`.
- `PROMPT_ASSIST_IMAGE_TO_IMAGE_TYPE`: current API type value for image-to-image prompt assist, usually `image_to_image`.
- `IMAGE_GENERATION_ROLECARD_IMAGE_URL`: current production role/create image generation URL, `/cmf/rolecard/image`.
- `IMAGE_GENERATION_TEXT_TO_IMAGE_URL`: text-to-image image generation URL. Body is `{"prompt":"..."}`.
- `IMAGE_GENERATION_IMAGE_TO_IMAGE_URL`: image-to-image image generation URL. Body is `{"image_id":"...","prompt":"...","trans_data":"..."}`.
- `IMAGE_GENERATION_UPLOAD_REFERENCE_URL`: reference image upload URL before image-to-image.
- `IMAGE_GENERATION_CMF_PROMPT_SUBMIT_URL`: generic CMF image task submit URL, `/cmf/prompt`, for messageId-based production flows.
- `IMAGE_GENERATION_CMF_HISTORY_URL_TEMPLATE`: generic CMF status polling URL template.
- `CURRENT_WEB_AUTH_TOKEN`: bearer token shared by current production prompt and image APIs.
- `DEFAULT_PROJECT`: default ComfyUI project path.

Backward-compatible aliases (`OLLAMA_GENERATE_URL`, `OLLAMA_MODEL`, `CURRENT_PROMPT_API_URL`, `CURRENT_PROMPT_AUTH_TOKEN`) are also present for scripts.

## Preset Rules

Use `selectMode: single` as last-choice-wins within the same group. Use `selectMode: multiple` as additive selections unless a tag has a `mutexKey`; for matching `mutexKey`, keep only the last selected tag in that mutex group.

The script expands labels exactly from `web_prompt_presets.json`. If the web app presets change, update that JSON from the web source before comparing APIs.

## Evaluation Focus

Score and inspect:

- Whether selected preset meanings appear in the final generated prompt.
- Whether single-person and two-person constraints stay stable.
- Whether single-choice conflicts use the final selected value only.
- Whether the model invents unselected clothing, people, or relationship/action edits.
- Latency, HTTP status, parseability, and empty output.
- Actual provider output shown in HTML under `Actual extracted API output`.
- Actual raw provider response saved as `*.raw.json` and linked from the HTML report.
- HTML should use a horizontal matrix table: each test input is one row, with adjacent columns for Web preset input, each provider's raw extracted output, local scoring flags, and raw response links.

When reporting results, summarize pass/fail and concrete risks. Avoid exposing auth tokens.
