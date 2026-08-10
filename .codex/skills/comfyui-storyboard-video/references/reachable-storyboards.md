# Reachable Storyboard Prompting

## Principle

A storyboard keyframe sequence is a chain of adjacent states. The video model can bridge adjacent states, but it usually cannot make a clean transition between unrelated images.

Design each next keyframe by asking: "Could a 4 second clip plausibly move from the previous frame to this frame?"

## State Ladder Template

Use this structure before generating images:

```json
[
  {
    "id": "kf_01",
    "state": "wide establishing frame",
    "delta_from_previous": "none",
    "storyboard": "..."
  },
  {
    "id": "kf_02",
    "state": "same place, character starts walking",
    "delta_from_previous": "position and posture only",
    "storyboard": "..."
  }
]
```

## Good Deltas

- Wide shot to medium-wide shot.
- Standing to beginning to walk.
- Looking forward to looking back.
- Walking left-to-right to pausing.
- Neutral expression to slight concern or confidence.
- Camera push-in while scene and outfit stay fixed.
- Same street, slightly deeper position in the street.

## Bad Deltas

- Street scene to indoor room.
- Day to night unless the transition is explicitly long enough.
- Casual outfit to different costume.
- Full-body rear view to unrelated close-up portrait.
- Character identity, hairstyle, body type, or art style changes.
- High-action leap, fight, or sudden vehicle appearance from a calm frame.

## Prompt Pattern

For keyframes:

```text
Create keyframe {n} for the same cinematic manga sequence and same reference person.
Preserve identity, hairstyle, outfit, rainy neon street, palette, and manga line art.
Delta from previous keyframe: {one small change}.
Camera: {wide/medium/close but reachable}.
Safety: fully clothed, safe composition, no body emphasis, no text, no watermark.
```

For transitions:

```text
Transition naturally from keyframe {n} to keyframe {n+1}.
The same fully clothed character {one intended motion}.
Preserve identity, outfit, scene, weather, lighting, camera continuity, and manga style.
Do not introduce new characters, new clothes, or a new location.
```

## Moderation-Safer Defaults

When using human reference photos:

- Prefer loose coats, jackets, scarves, or layered clothing.
- Prefer wide or medium-wide shots.
- Emphasize environment, rain, camera movement, and lighting.
- Avoid body-focused wording, close-up body framing, lingerie, swimwear, or see-through clothing.

If a generated clip fails moderation, keep the run directory and retry only the failed keyframe/transition with safer framing.
