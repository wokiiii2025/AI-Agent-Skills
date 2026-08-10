# Floor Patterns

Use structural titles in component-library pages. Use business titles only in real product pages.

## Standard floors

### HomeSectionBlock + rail/grid

```tsx
<HomeSectionBlock title="横向滑动 Rail 标题栏">
  <ConfigurableMediaLayout items={items} layout={layout} />
</HomeSectionBlock>
```

- Parent preview: full width.
- `HomeSectionBlock`/child layout owns real internal spacing.
- Structural showcase titles: `横向滑动 Rail 标题栏`, `竖版三列 Grid 标题栏`, `横版排行 Rail 标题栏`.

### HomeHerald

- Full-width parent.
- Text not bold.
- Must not touch screen edges.

### HomeQuickEntries

- Full-width parent.
- Component controls 15dp margin.
- Icons/text compact.

### HomeTextAdGrid

- Business floor; do not model as generic button group.
- Keep existing grid styles.

## Adult floors

These live in `src/components/adult/AdultSpecialFloors.tsx`. Caller supplies standard 15dp content container.

```tsx
<View style={{ paddingHorizontal: 15 }}>
  <AdultRankingFloor items={items} onItemPress={handlePress} />
</View>
```

| Floor | Structure | Key standard |
| --- | --- | --- |
| `AdultRankingFloor` | Left TOP1 large card + right TOP2-4 compact list | 15dp outer content zone, height 184dp. |
| `AdultMosaicFloor` | Left large card + right two stacked cards | 15dp outer content zone, height 210dp, internal gap 8dp. |
| `AdultUpdateFloor` | 3-column update grid | 15dp outer content zone; card width from real screen width. |
| `AdultAuthorFloor` | Horizontal author cards | 15dp outer content zone; component handles horizontal scroll. |
| `AdultNovelCategoryRail` | Category header card + 3 rows | 15dp outer content zone; card width ~68% screen. |
| `AdultNovelRankingSection` | Section header + tabs + 3-row ranking rail | Supports `title` prop for structural showcase title. |

## Title policy

- Component library title text describes structure, not actual content business:
  - Good: `标准楼层标题`, `横向滑动 Rail 标题栏`, `小说排行 Tabs 标题栏`.
  - Avoid in component library: actual movie/novel/manga promotion titles.
- Real product pages may pass business titles from API/CMS.
