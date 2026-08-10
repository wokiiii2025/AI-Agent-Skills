# UpToken Video API Reference

Base URL: `https://uptoken.cc`

Authentication:

```text
Authorization: Bearer $UPTOKEN_API_KEY
```

Do not store real API keys in this skill. Keep keys in environment variables, local secret files, or server-side deployment secrets.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/v1/account/balance` | Query account balance |
| POST | `/v1/video/generations` | Create a video generation task |
| GET | `/v1/video/generations/:task_id` | Poll task status/result |
| POST | `/v1/assets` | Upload image/video/audio asset |
| GET | `/v1/assets` | List assets |
| GET | `/v1/assets/:id` | Query one asset |
| DELETE | `/v1/assets/:id` | Delete asset |

## Video Request Fields

| Field | Type | Notes |
|---|---|---|
| `model` | string | `seedance-2.0-pro`, `seedance-2.0-fast`, or `seedance-1.5-pro` |
| `content` | array | Text and media references in multimodal content format |
| `prompt` | string | Text prompt when not using `content` |
| `duration` | integer | 4-15 seconds |
| `resolution` | string | `480p`, `720p`, or model-supported higher values |
| `ratio` | string | `16:9`, `9:16`, `1:1`, `4:3`, `3:4`, `21:9`, or `adaptive` |
| `generate_audio` | boolean | Whether to generate audio |
| `image_urls` | string[] | Reference images or `asset://...` URLs |
| `video_urls` | string[] | Reference videos or `asset://...` URLs |
| `audio_urls` | string[] | Reference audio or `asset://...` URLs |
| `first_frame_url` | string | First-frame image URL |
| `last_frame_url` | string | Last-frame image URL |

## Multimodal Content Example

```json
{
  "model": "seedance-2.0-pro",
  "content": [
    { "type": "text", "text": "将视频1中的物品替换成图片1里的物体" },
    {
      "type": "image_url",
      "image_url": { "url": "https://example.com/object.jpg" },
      "role": "reference_image"
    },
    {
      "type": "video_url",
      "video_url": { "url": "https://example.com/source.mp4" },
      "role": "reference_video"
    }
  ],
  "duration": 5,
  "resolution": "720p",
  "ratio": "16:9",
  "generate_audio": true
}
```

## Task Result Fields

`status` is one of `queued`, `running`, `succeeded`, or `failed`. Successful tasks include `content.video_url` plus `usage.total_tokens`, `usage.total_cost_microcents`, and `usage.currency`.

Recommended polling interval is 5 seconds. Typical generation time is 30-120 seconds. Task lifetime is about 2 hours.
