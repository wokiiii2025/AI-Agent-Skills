# Media Card Tag Matrix

Use `ConfigurableMediaLayout` + `MediaPosterCard` for ordinary media floors. Pick a business scenario and set `layout.tagConfig` accordingly.

## Fixed tag slots

| Slot | Content | Rule |
| --- | --- | --- |
| Top-left | Rating | Always first. Format with `formatRatingLabel`, e.g. `9.1分`. |
| Top-left second line | Quality | Only when business requires quality. Use `tag` or `optionLabel`; do not show quality for ordinary movie cards. |
| Top-right | VIP | Only `vip === true`. |
| Bottom-left | Views + likes | Use icon sequence; keep compact. |
| Bottom-right | Duration or serial/completion | Video duration, `连载`, `完结`, or similar state. |
| Outside image | Title + category + update subtitle | Title one line; category chip near title; update text in subtitle. |

## Business matrix

| Business | Inside-image tags | Outside-image info | Recommended layout |
| --- | --- | --- | --- |
| Movie | rating, views, likes | title, category | portrait or landscape rail; no quality by default |
| Video/short/drama/anime/variety | rating, views, likes, serial/completion | title, category, update-to text | portrait rail/grid |
| Adult video | rating, VIP, quality, views, likes, duration | title, category | landscape rail |
| Adult manga | rating, VIP, views, likes, serial/completion | title, category, update-to text | portrait rail/grid or adult update floor |
| Adult novel | rating, views, likes, serial/completion | title, category, update-to text | portrait rail/grid or novel floors |

## TagConfig recipes

### Movie

```ts
const movieTagConfig = {
  rating: true,
  meta: true,
  playCount: true,
  likeCount: true,
  duration: false,
  vip: false,
  primaryTag: false,
  quality: false,
};
```

### Video/short/drama/anime/variety

```ts
const serialVideoTagConfig = {
  rating: true,
  meta: true,
  playCount: true,
  likeCount: true,
  duration: true,
  vip: false,
  primaryTag: false,
  quality: false,
};
```

### Adult video

```ts
const adultVideoTagConfig = {
  rating: true,
  vip: true,
  primaryTag: true,
  quality: true,
  meta: true,
  playCount: true,
  likeCount: true,
  duration: true,
};
```

### Adult manga

```ts
const adultMangaTagConfig = {
  rating: true,
  vip: true,
  meta: true,
  playCount: true,
  likeCount: true,
  duration: true,
  primaryTag: false,
  quality: false,
};
```

### Adult novel

```ts
const adultNovelTagConfig = {
  rating: true,
  vip: false,
  meta: true,
  playCount: true,
  likeCount: true,
  duration: true,
  primaryTag: false,
  quality: false,
};
```

## Typography

- Card title: 12-13dp, weight 500-600, one line.
- Dense card title: use existing `DenseMediaCard` styles; do not enlarge in showcase.
- Meta text in overlay: 8-10dp depending density.
- Rating: compact, accent color, include `分`.

## Do not

- Do not put channel/quality in top-right; top-right is VIP only.
- Do not put update-to text inside a large promo badge; update-to belongs to subtitle, while completion/serial state may be right-bottom tag.
- Do not manually compute card widths when `ConfigurableMediaLayout` can do it.
