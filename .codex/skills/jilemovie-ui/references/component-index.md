# Component Index

Use this index before creating UI. Prefer the listed component over a custom implementation.

## Foundation

| Need | Component | File | Notes |
| --- | --- | --- | --- |
| App background | `AppBackground` | `src/components/ui/AppBackground.tsx` | Use for global page visual background. |
| Text | `ThemedText` | `src/components/ui/ThemedText.tsx` | Use theme colors and typography styles. |
| View/container | `ThemedView`, `Container` | `src/components/ui/*` | Do not invent page-level padding. |
| Icon | `Icon`, `SvgIcon` | `src/components/ui/Icon.tsx`, `src/components/ui/SvgIcon.tsx` | Do not inline new SVG paths in pages. |

Icon semantics:

- Like/dislike: use `thumbsUp`, `thumbsUpOutline`, `thumbsDown`, `thumbsDownOutline`.
- Favorite/collect: use `favorite` / `favoriteOutline`, both are heart icons. Do not use star for collect.
- Rating: use `star` / `starOutline`.
- Sound on/off: use `announcement` / `announcementOff`.
- LeBi currency: use `LeBiCoinIcon` from `SvgIcon.tsx`, not generic `coin`.

## Header / navigation

| Need | Component | File | Margin owner |
| --- | --- | --- | --- |
| Home logo/search row | `HomeTopArea` | `src/components/home/HomeTopArea.tsx` | Component controls 15dp. |
| Top channel tabs | `HomeTopTabs` | `src/components/home/HomeTopTabs.tsx` | Component controls 15dp and horizontal scroll. |
| Secondary page title | `AppPageHeader` | `src/components/ui/AppPageHeader.tsx` | Component controls title centering and side action slots. |
| Section header | `SectionHeader` | `src/components/ui/SectionHeader.tsx` | Place in standard 15dp section container if caller owns page margin. |
| Category filters | `CategoryFilterPanel` | `src/components/ui/CategoryFilterPanel.tsx` | Full-width parent; component controls row padding. |
| Category more drawer | `LeftDrawer` | `src/components/ui/LeftDrawer.tsx` | Use from right-side "更多" trigger when filter tags exceed row capacity. |
| CMS compact sort/price row | category route compact renderer | `app/[contentMode]/category.tsx` | Sort segment first, divider, price segment second; all price label is `全部`. |
| Bottom tabs | `BottomTabBar` | `src/components/home/BottomTabBar.tsx` | Component controls 15dp + safe area; use `inlinePreview` only in component library. |

## Banners / carousels

| Need | Component | File | Margin owner |
| --- | --- | --- | --- |
| Top full-width hero carousel | `HomeBanner` | `src/components/home/HomeBanner.tsx` | Full-width parent. |
| Channel full-width carousel | `HomeBanner` | `src/components/home/HomeBanner.tsx` | Full-width parent; optional `aspectRatio`. |
| Rounded content-area carousel | `HomeBanner` | `src/components/home/HomeBanner.tsx` | Caller supplies standard 15dp content container; pass `borderRadius={10}`. |
| Single action banner | `HomeAdBanner` | `src/components/home/HomeAdBanner.tsx` | Default controls 15dp; pass `contentPaddingHorizontal={0}` only when caller already provides 15dp. |
| Search ranking horizontal carousel | `SearchRankingCarousel` | `src/components/search/SearchRankingCarousel.tsx` | Component controls 15dp. |

## Media cards and layouts

| Need | Component | File | Notes |
| --- | --- | --- | --- |
| Media rail/grid/masonry | `ConfigurableMediaLayout` | `src/components/home/ConfigurableMediaLayout.tsx` | Preferred entry for card floors. |
| Poster/landscape card | `MediaPosterCard` | `src/components/home/MediaPosterCard.tsx` | Do not manually lay out many naked cards. |
| Dense card | `DenseMediaCard` | `src/components/home/DenseMediaCard.tsx` | Special compact card; not full tag matrix. |
| Live card | `LiveMediaCard` | `src/components/home/LiveMediaCard.tsx` | Live badge + viewer count. |
| Ranking number | `RankingNumber` | `src/components/ui/RankingNumber.tsx` | Visual text `TOP1`, `TOP2`, etc. |

## Floors

| Need | Component | File | Notes |
| --- | --- | --- | --- |
| Standard floor shell | `HomeSectionBlock` | `src/components/home/HomeSectionBlock.tsx` | Use structure title; child handles card layout. |
| Notice | `HomeHerald` | `src/components/home/HomeHerald.tsx` | Text not bold; no edge collision. |
| Quick entries | `HomeQuickEntries` | `src/components/home/HomeQuickEntries.tsx` | 5 items row; component controls 15dp. |
| Text ad grid | `HomeTextAdGrid` | `src/components/home/HomeTextAdGrid.tsx` | Business floor, not generic button grid. |
| Adult ranking split | `AdultRankingFloor` | `src/components/adult/AdultSpecialFloors.tsx` | Caller supplies 15dp content container. |
| Adult mosaic | `AdultMosaicFloor` | `src/components/adult/AdultSpecialFloors.tsx` | Caller supplies 15dp content container. |
| Adult update grid | `AdultUpdateFloor` | `src/components/adult/AdultSpecialFloors.tsx` | Caller supplies 15dp content container. |
| Adult author rail | `AdultAuthorFloor` | `src/components/adult/AdultSpecialFloors.tsx` | Caller supplies 15dp content container. |
| Novel category rail | `AdultNovelCategoryRail` | `src/components/adult/AdultSpecialFloors.tsx` | Caller supplies 15dp content container. |
| Novel ranking tabs rail | `AdultNovelRankingSection` | `src/components/adult/AdultSpecialFloors.tsx` | Supports `title` override for structural showcase titles. |

## Feedback / modal

| Need | Component | File | Notes |
| --- | --- | --- | --- |
| Modal | `CommonModal` | `src/components/ui/CommonModal.tsx` | Top icon must be mascot WebP, not vector. |
| Check-in success modal | `CheckInModal` | `src/components/ui/CheckInModal.tsx` | Must render through real viewport modal, screen-centered; success cue uses mascot WebP. |
| Media preview | `MediaPreviewModal` | `src/components/ui/MediaPreviewModal.tsx` | Use for image/video preview. |
| Toast | `ToastProvider` / `useToast` | `src/components/ui/ToastProvider.tsx` | Use global toast. |
| Loading/empty/end | `PageLoadingState`, `MascotEmptyState`, `PageEndFooter` | `src/components/ui/*` | Reuse states. |

## Interaction / content

| Need | Component | File | Notes |
| --- | --- | --- | --- |
| Left drawer | `LeftDrawer` | `src/components/ui/LeftDrawer.tsx` | Modal drawer, 76% width, 8dp tag items. |
| Rating display/input | `RatingStars` | `src/components/ui/RatingStars.tsx` | 5-star UI, displays 10-point score text with numeric font. |
| Comment item | `CommentItem` | `src/components/ui/CommentItem.tsx` | 8dp card, 36dp avatar, optional rating/tags/actions. |
| Detail tags | `DetailTagRail` | `src/components/ui/DetailTagRail.tsx` | Horizontal tag rail for detail pages. |
| Pagination | `PaginationControl` | `src/components/ui/PaginationControl.tsx` | 8dp page buttons. |
| Notification row | `NotificationListItem` | `src/components/ui/NotificationListItem.tsx` | Fixed icon/title/content/state slots. |
