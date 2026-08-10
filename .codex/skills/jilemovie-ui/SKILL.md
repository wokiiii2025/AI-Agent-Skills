---
name: jilemovie-ui
description: Project-specific UI implementation skill for Expo-Movie/JILEMOVIE. Use when Codex needs to create, modify, audit, or standardize project UI pages/components with existing JileMovie components, including headers, tabs, banners, floors, media cards, adult-mode video/manga/novel layouts, spacing, typography, radius, theme tokens, safe areas, and /jilemovie-ui component-library standards.
---

# JILEMOVIE UI Skill

Use this skill for any Expo-Movie UI work. The goal is to build page parts from real project components, not approximate demo UI.

## Mandatory workflow

1. Read `AGENTS.md` and `docs/ui-theme-standards.md` in the target repo.
2. Open `/jilemovie-ui` category or read `docs/jilemovie-ui-agent-guide.md` before choosing a component.
3. Pick the closest existing component from `references/component-index.md`.
4. Apply layout, spacing, typography, radius, tags, and token rules from the relevant reference:
   - Layout/spacing: `references/layout-rules.md`
   - Media cards/tags: `references/card-tag-matrix.md`
   - Banners/carousels: `references/banner-patterns.md`
   - Floors: `references/floor-patterns.md`
   - Theme tokens: `references/theme-rules.md`
5. Implement minimal changes in the correct project boundary: route in `app/*`, reusable UI in `src/components/ui/*`, domain UI in `src/components/<domain>/*`.
6. Verify with `references/agent-checklist.md`; at least run `npx tsc --noEmit` for TS changes.

## Hard rules

- Use existing components first. Do not handwrite a lookalike when a project component exists.
- Demonstration parents must be full width. Real 15dp page margin must come from the component or a clearly named standard content container.
- Do not add a second padding wrapper around components that already control their own margin.
- Use `useTheme`, `ThemedText`, `ThemedView`, and theme tokens. Do not hardcode new page colors when a token exists.
- Keep structure stable across all skins; themes change color, not layout geometry.
- Android mobile experience is primary; Web is only an auxiliary preview.
