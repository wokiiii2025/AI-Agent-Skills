# Banner Patterns

## Pattern 1: top overlay full-width carousel

Use `HomeBanner` with a full-width parent. Header/search/tabs can overlay above it. Do not wrap in 15dp content padding.

```tsx
<HomeBanner autoPlay={false} height={260} items={bannerItems} />
```

Standards:
- Parent width: full screen.
- Image: cover.
- Text/pagination: component controls internal 15dp.
- Bottom blend should connect to page background.

## Pattern 2: channel/page-flow full-width carousel

Use `HomeBanner` in ordered module/page flow. Parent full width. Optional `aspectRatio` controls height.

```tsx
<HomeBanner items={items} aspectRatio={16 / 7.8} movieTitle />
```

Standards:
- No external horizontal padding.
- Use `compactTitle` only for denser content modes.
- Keep full-width image edges.

## Pattern 3: standard content-area rounded carousel

Use when the real page first creates a 15dp content zone, then renders the rounded banner inside it.

```tsx
<View style={{ paddingHorizontal: 15 }}>
  <HomeBanner items={items} borderRadius={10} compactTitle height={180} />
</View>
```

Standards:
- Caller owns 15dp margin.
- Banner fills content width.
- Radius usually 10dp.
- Height commonly `contentWidth * 0.5`, clamped 180-260.

## Pattern 4: action/ad banner

`HomeAdBanner` default includes 15dp content padding:

```tsx
<HomeAdBanner item={item} />
```

If caller already supplies a 15dp content container:

```tsx
<View style={{ paddingHorizontal: 15 }}>
  <HomeAdBanner item={item} contentPaddingHorizontal={0} />
</View>
```

## Pattern 5: embedded carousel in split card

Used inside a local panel. The page still supplies standard 15dp margin; carousel viewport is inside a card/panel.

Standards:
- Outer content zone: 15dp.
- Panel gap: 10dp.
- Embedded viewport height: keep current component/page baseline, do not enlarge for showcase.
- Panel headings in component library should use structural names, not business floor names.
