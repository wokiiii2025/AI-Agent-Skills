# Theme Rules

## Theme tokens

Use `useTheme()` and semantic tokens from `src/theme/tokens.ts`.

Available color tokens:

```ts
background
surface
surfaceAlt
border
overlay
mediaOverlay
mediaTextPrimary
mediaTextSecondary
mediaAccent
textPrimary
textSecondary
textMuted
accent
accentFill
accentSoft
accentSecondary
accentSecondarySoft
accentGold
accentGoldSoft
tabActive
tabInactive
searchBackground
```

Supported skins:

```ts
classic | cyberpunk | mint | youth | neon
```

Supported modes:

```ts
light | dark
```

## Rules

- Layout geometry is not theme-specific unless an existing component already defines a minor skin adjustment.
- Use semantic tokens rather than hardcoded colors.
- If a hardcoded color exists in a component, keep it only when it is an established media overlay color (for example white text over image gradient) or a legacy component-specific visual.
- New business UI should not introduce one-off brand colors; extend theme tokens only when reused.
- Search inputs use `theme.colors.searchBackground`.
- Cards/surfaces use `surface`, `surfaceAlt`, `border`, `background`.
- Active/selected state uses `accent`, `accentFill`, `accentSoft`.

## Text hierarchy baseline

- Page title: around 20-22dp, weight 900.
- Section title: around 16dp, weight 800-900.
- Card title: 12-13dp, weight 500-600.
- Auxiliary description: 11-12dp.
- Overlay meta: 8-10dp.

Do not create oversized marketing typography for normal app floors.

## Numeric typography

For prominent scores, rewards, rankings, prices, and counters, use `numericTextStyle` from `src/theme/typography.ts`.

- iOS: `AvenirNextCondensed-Heavy`
- Android: `sans-serif-condensed`
- Web: `Impact, Arial Black, sans-serif`

Do not introduce remote fonts for numeric UI. Keep the numeric style system-font based and three-platform safe.

## Multi-theme QA

When modifying visual components, check at least classic + one high-contrast skin (`neon` or `cyberpunk`) + one light/soft skin if available. Structure must remain stable.
# Typography groups

- Keep English and numeric fonts centralized in `src/theme/typography.ts`.
- Use `latinUiFontFamily` for ordinary English UI copy.
- Use `tagLatinTextStyle` for compact labels/tags.
- Use `numericTextStyle` for ordinary numbers, counters, prices, and scores.
- Use `displayNumberTextStyle` for large reward numbers.
- Use `rankingNumberTextStyle` for ranking labels and list sequence numbers.
- Do not use Impact/Arial Black style display fonts for normal numeric UI; they look too heavy in the mobile component library.
- Do not import remote fonts or Google Fonts.

## Background image surfaces

- `AppBackground` owns theme-level background image/gradient layers; youth skin uses `assets/home/youth-soft-bg.webp`.
- `PosterCard` uses `ImageBackground` for content poster cover backgrounds.
- `PosterPromotionComponents` uses `ImageBackground` for exportable promotion poster backgrounds.
- `LaunchGate` uses `ImageBackground` for startup/entry backgrounds.
- Background images are visual layers only; typography, chips, buttons, overlays, and radius still follow tokens and layout rules.
