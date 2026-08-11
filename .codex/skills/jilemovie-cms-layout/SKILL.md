---
name: jilemovie-cms-layout
description: Use when configuring JileMovie / 极乐影视 CMS layout floors, channel home pages, banner carousel, ads, card labels, display counts, card shape, filters, sorting, publishing, or verifying CMS data in the ops CMS.
---

# JileMovie CMS Layout

## Core rule

Configure CMS as production content, not as placeholder layout. Floor names, filters, sorting, card shape, item count, and published frontend data must agree.

## Workflow

1. Use the in-app browser skill for `http://162.250.126.10:8760/ops/cmsLayout`.
2. Confirm the active page title, such as `电影 · 观影`, before editing. If the title and left active channel disagree, stop; the CMS page can show stale/cross-channel draft state.
3. Edit only the intended channel/module. Do not batch-publish across channels when the page state is unstable.
4. For each edited content floor, verify the selected module form or `配置 JSON` before publishing:
   - `config.queryChannelCode` matches the page channel.
   - `dataSource.filter` matches the floor intent.
   - `dataSource.sort` matches the floor title.
   - card labels are all enabled.
   - `displayMode`, `cardVariant`, and `limit` match the rules below.
5. Save draft, publish the whole page when adding/removing/reordering floors, then verify the published frontend endpoint:
   `GET http://162.250.126.10:8080/api/cms/page?channelCode=<channel>&watchMode=1`

## Channel layout rules

- First floor on every channel page must be Banner carousel.
- Every page must have at least 8 floors; more than 8 is allowed when the structure remains useful and readable.
- Keep structure diverse. Do not build pages from only repeated resource-list shelves. For homepage/channel floor configuration, use data-display components that can render meaningful floor content: banner carousel, quick entries, ranking, channel hot, category/filter, live/recommend, content rows, promo/ad, and other supported floor components. `搜索发现` is for the search page, not a normal homepage/channel data-display floor. When component capability is unclear, inspect the UI component library in the `ui` branch before deciding what CMS floor type to use.
- Every page should contain exactly one ad/promo floor unless the user explicitly asks for a different count.
- Announcement/notice floors are allowed only on the 观影 and 成人 homepage/recommend pages. They must be directly below the Banner carousel. Do not place announcement/notice floors on channel pages.
- Do not delete or rename existing ad floors unless the user explicitly asks. If the user says “不要加广告位”, interpret it as “do not add new ads”; existing ads remain. If a page has zero or multiple ads, ask or fix toward exactly one ad depending on the current task scope.
- Documentary can be skipped only when the user explicitly says so.

## Card labels and display

For content card floors, enable all card labels by default:

- 评分
- 播放量
- 时长
- VIP 标签
- 质量标签

Display count must match card layout and avoid more than 3 rows:

| Mode / card shape | Default use | Columns | Max limit |
| --- | --- | ---: | ---: |
| 观影 + 竖版 poster/portrait | movies, dramas, anime, variety, short plays | 3 | 9 |
| 观影 + 横版 landscape | live rows, special horizontal shelves | 2 | 6 |
| 成人 + 横版 landscape | adult content shelves | 2 | 6 |
| Banner carousel | top focus | n/a | usually 5 |

Prefer portrait/竖版 cards for 观影模式 content shelves because poster art fits better. Prefer landscape/横版 cards for 成人模式 unless the user specifies otherwise.

## Component diversity

When adding floors, choose the component by the page's missing structure instead of defaulting to 资源列表:

| Need | Prefer CMS component |
| --- | --- |
| Top focus | Banner 轮播 |
| Navigation shortcuts | 快捷入口 |
| Ranked discovery | 排行榜页 |
| Channel popularity | 频道热播榜 or 实时观看推荐 |
| Category exploration | 热门分类组, 频道分类页, or 分类筛选页 |
| Curated content shelf | 资源列表 |
| Operations placement | 运营横幅 / 广告组件 |
| Notices | 公告栏, only on homepage under Banner |
| Search page only | 搜索发现 |

For pages that already have several 资源列表 floors, fill gaps with ranking, channel hot, category, filter, live/recommend, or other true floor data-display components first. Do not use 搜索发现 to increase homepage/channel floor diversity.

## Adult-mode CMS module reference

Adult mode has useful examples for diverse floor structure. Reuse the pattern, but do not blindly copy module types into movie channels without checking frontend support and actual returned items.

| Adult display pattern | CMS module/config | Notes for reuse |
| --- | --- | --- |
| Top carousel | `carousel`, usually `displayMode=horizontal`, `cardVariant=landscape` | Use as first floor. |
| Notice below banner | `notice_bar` | Homepage only; must sit directly below Banner. |
| Quick/topic entries | `tag_grid` or `quick` with `displayMode=icon_grid` | Good for page navigation, categories, and topic shortcuts. |
| Ranking with clickable groups/cycles | `ranking_page` with `rankGroups` and `cycles` | Good reference for 热播榜 / 飙升榜 / 新片榜 and 最新 / 热门 / 好评 tabs. For normal channel floors, use when it returns real `items` or populated rank cycles. |
| Channel hot rank | `search_hot_rank` with `rankGroups` | Treat cautiously: some adult pages expose groups but no items, so it may not render useful channel floors. Verify items before using. |
| Live/realtime recommendation | `live_row` with `componentCode=live_recommend` | Useful data-display floor, especially for “大家都在看 / 实时热播”. |
| Actor shelf | `actor_row` | Adult-specific actor/performer content; not a normal movie-channel floor. |
| Category/filter page | `vod_category_page` or `vod_filter_page` with `componentCode=category_filter` | Good for 分类精选 / 分类筛选 style floors and “更多” pages. |
| Category group | `category_group` | Currently observed on novel/comics style pages; do not assume ordinary video channels have ideal rendering without checking. |
| Ad/promo | `promo` or `ad_banner` / `cms_ad` | Keep one ad/promo floor per page unless explicitly changed. |

Recommended stable mix for movie/channel pages:

`Banner` → `快捷入口` → `ranking_page` → `video_row` → `live_row/live_recommend` → `vod_category_page` or `vod_filter_page` → `promo` → another explicitly filtered/sorted data floor.

Avoid using `search_hot_rank` or `category_group` for ordinary video channel pages unless the published CMS response contains real items and the frontend rendering path has been confirmed.

## Naming, filters, and sorting

Names must be human-readable and backed by actual config:

| Name intent | Required config |
| --- | --- |
| 高分 / 佳作 / 口碑 | sort `score` descending |
| 上新 / 新片 / 新番 | sort `update_time` or `create_time` descending |
| 热播 / 大家都在看 | sort `view_count`, `daily_view_count`, `weekly_view_count`, `daily_score`, or use live/recommend API component |
| 热榜 / 排行 | use ranking component or ranking-compatible sort |
| 分类精选 | use category/filter component and correct channel |

Do not use “高分” when the sort is not score descending. Do not use “上新” when the sort is not time descending. Do not use “热播” for generic unsorted lists.

## Verification checklist

Before saying the CMS change is done, report:

- active CMS page title checked
- changed module title(s)
- query channel
- filters and sorting
- card labels all enabled
- display mode, card shape, and limit
- published frontend endpoint version/count
- whether existing ads were kept or changed

## Known CMS pitfalls

- The CMS editor can show stale or cross-channel drafts after clicking a channel. Always verify the panel title and module list before editing.
- Public `/api/cms/page` verifies published frontend data but does not expose full filters/sorts. Use selected module form or `配置 JSON` for filter/sort validation.
- Adding a component may require the user to drag it manually; normal click and automated drag can fail.
- `发布当前模块` may not publish newly added floors. Use whole-page publish for adds/removals/reorders.
- Do not inspect browser cookies, localStorage, or admin tokens. Use the signed-in browser UI and public verification endpoint.
