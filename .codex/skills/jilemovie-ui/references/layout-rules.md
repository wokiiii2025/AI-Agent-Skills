# Layout Rules

## Page margin ownership

Default mobile page margin is 15dp. The key rule is ownership: exactly one layer owns horizontal page margin.

- Full-width parent: use for components that internally manage spacing or must touch screen edges.
- Standard content container: use only when the real page already creates a 15dp content zone before rendering the child.
- Do not put `paddingHorizontal: 15` around a component that already has its own 15dp.

## Component-library showcase rules

- Showcase page header/meta text: 15dp padding.
- Preview parent for page/floor components: full width, transparent, no border, no padding.
- Local token samples may use contained display (`maxWidth` + 15dp), because they are not real page-width components.
- Notes/description boxes must be `marginHorizontal: 15` and no `width: "100%"`; otherwise they overflow mobile width.

## Common numeric standards

| Token | Value |
| --- | --- |
| Page horizontal margin | 15dp |
| Card gap in same floor | 10dp |
| Image radius | 6dp |
| Small tag radius | 2-4dp |
| Common card/surface radius | 8dp |
| Rect button radius | 8dp |
| Banner radius | 10dp |
| Modal/sheet radius | 16dp |
| Pill/circle radius | 999 or size / 2 |
| Banner content text inset | 15dp |
| Bottom tab columns | 5 fixed items |

## Radius scale

- Media images/posters: 6dp.
- Normal surfaces, text cards, neutral containers, rectangular buttons: 8dp.
- Banner/carousel visual container: 10dp.
- Modal cards and sheets: 16dp.
- Pills and round icon buttons: fully rounded (`999`) or exactly half of size.
- Do not use arbitrary 10/12/20/24dp radius for normal buttons or cards unless matching an existing production component with a named reason.

## Rail/grid sizing

- Portrait rail: default visible columns about 3.35.
- Landscape rail: default visible columns about 2.1.
- Portrait grid: 3 columns; home default often 6 items (3 x 2).
- Landscape image ratio: 5/3.
- Portrait image ratio: 5/7.
- Use `ConfigurableMediaLayout` for rails/grids so widths respond to actual container width.

## Header rules

- `AppPageHeader` title should remain centered; put actions in left/right slots rather than shifting title manually.
- Category page header action order: search button left, filter toggle right.
- Section header right action should visually align with the 15dp right edge.
- `HomeTopTabs` active underline must be visually strong enough to read as selected; classic baseline is 4dp high.
- Brand logo image may compensate transparent asset padding, but the first logo visual must align to the content left edge and the logo/name gap should stay compact.

## Category filter expansion

- `CategoryFilterPanel` keeps each filter group on its own row.
- Use `LeftDrawer` for right-side "更多" expansion when categories exceed the horizontal row.
- CMS category result pages include a compact horizontal sort/price row copied from `app/[contentMode]/category.tsx`: sort segment first, hairline divider, price segment second; price all label is `全部`, not `全部资费`.
- Manga/novel standalone discover pages may still use multi-row `CategoryFilterPanel`; document which source page the showcase is representing.
- Do not merge channel, subject, price, and sort into one tag pool.

## Safe area

- Use `react-native-safe-area-context`; do not create mismatched color spacer views.
- Bottom tab background extends into bottom safe area.
- For component-library bottom tab preview, pass `inlinePreview`; real app pages use fixed behavior.

## Modal and overlay rules

- Overlay components must render from `Modal` or an equivalent viewport-fixed portal, not as an absolute child inside `ScrollView` or page content.
- Modal overlay root must cover the real screen (`flex: 1`; Web may add `WEB_MODAL_FULLSCREEN_STYLE`) and use `alignItems: "center"` + `justifyContent: "center"`.
- Business modal card radius baseline is 16dp unless an existing production component intentionally defines a different shape.
- `CommonModal` and success/warning/info/error prompt modals must use mascot WebP images for the leading visual cue; do not replace that cue with vector icons.
