# Agent Checklist

Before finishing UI work:

## Component choice

- [ ] Reused existing component from `component-index.md`.
- [ ] Did not duplicate existing button, modal, icon, card, banner, or floor.
- [ ] Page code stays in `app/*`; reusable component code stays in `src/components/*`.

## Layout

- [ ] Exactly one owner for horizontal 15dp margin.
- [ ] No double padding around HomeTopTabs, CategoryFilterPanel, BottomTabBar, HomeAdBanner default, ConfigurableMediaLayout default.
- [ ] Preview/showcase parent is full width unless the sample is a local token/text demo.
- [ ] Horizontal rails start at 15dp and expose next item correctly.
- [ ] Bottom tab and safe area rules unchanged.

## Visual standards

- [ ] Image radius follows 6dp baseline unless component already defines another value.
- [ ] Card gap is 10dp within a floor.
- [ ] Text sizes are compact and consistent with existing components.
- [ ] Rating includes `分`.
- [ ] Media card tags use fixed slots.
- [ ] Component-library floor titles are structural, not business content names.

## Theme

- [ ] Uses `useTheme`, `ThemedText`, and semantic tokens.
- [ ] No new one-off hardcoded color unless justified by media overlay.
- [ ] Structure does not shift between skins.

## Validation

- [ ] Run `npx tsc --noEmit` for TS changes.
- [ ] For visual changes, inspect `/jilemovie-ui/<category>` at 375px width.
- [ ] For Android-critical UI, run Android/device verification before claiming final visual parity.
