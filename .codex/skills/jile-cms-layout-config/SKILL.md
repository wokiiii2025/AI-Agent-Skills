---
name: jile-cms-layout-config
description: Project-specific skill for configuring JileMovie/极乐影视 CMS layout pages in the admin backend and aligning them with Expo front-end rendering. Use when Codex needs to edit, audit, or explain CMS 楼层配置, 成人/观影模式推荐页, 底部菜单页面, 视频/漫画/小说综合楼层, right-side data configuration, module types, display modes, card variants, tag configs, or verify how CMS pages render in the app.
---

# 极乐 CMS 楼层 UI 配置

## 先选对操作面

- 用户明确说后台已在“内置浏览器”打开时，直接使用 in-app browser 当前/指定标签，不切换到外部 Chrome。
- 进入 `运营管理 / CMS配置` 后，先确认：`watch_mode`（观影/成人）、页面分组（频道页面/底部菜单页面/其他菜单页面/公共数据配置）、当前页面名。
- 配置前先读取当前右侧配置和底部“配置 JSON”，记录模块 `title/type/componentCode/displayMode/cardVariant/config/dataSource`。
- 右侧具体数据配置优先以当前页面 UI 实际字段为准，不凭旧记忆补字段。

## 页面选择规则

- 成人模式底部菜单“推荐”页：`mode = 2`，`pageType = bottom_menu_page`，`channel = home`，页面标题通常显示为“推荐 · 成人”。
- 视频/漫画/小说底部菜单页分别在“底部菜单页面”下选择对应菜单；频道页在“频道页面”下选择。
- 公共数据配置只维护频道列表、底部菜单、其他菜单，不等同于首页楼层。

## 前端映射要点

前端主要入口在仓库：

- `src/types/cmsHome.ts`
- `src/services/api/cmsApi.ts`
- `src/components/home/*`
- `src/components/cms/*`

常用模块映射：

- `carousel`：轮播，App 映射到 banner；需要媒体 items。
  - 单表轮播：直接从 `items` 返回视频/漫画/小说资源。
  - 混合轮播：允许视频 + 漫画 + 小说混排；前端支持读取 `items` 或 `categoryGroups[].items`，每条资源必须保留可识别字段（视频 `id/thumbDisplay/channelCode`，漫画 `mainComicsId/thumbLink`，小说 `novelId/thumbUrl`），以便点击跳转到各自详情。
  - 成人底部菜单推荐页的单表视频 Banner 必须补右侧“查询频道 channel_code”，常用 `video`，否则发布后只剩 `mode=2 + status=0` 的泛查条件，数据范围过宽且看起来像少筛选条件。
  - 当前后台右侧 `carousel` 在 `home` 页面只放出单个“业务表”选择，常见为 `vod`；视频 + 漫画 + 小说混合在同一个 Banner 时，需要后台返回 `items` 混排或提供多资源源配置。配置时不要只改前端映射，也不要把漫画/小说误配成视频表条件。
- `notice_bar`：公告条；右侧业务表通常是 `sys_notice`。
- `tag_grid` / `quick` + `displayMode=icon_grid`：
  - 如果返回分类项，会被当作导航 tabs；
  - 如果返回广告/快捷入口项，会被当作 quick entries。
- `video_row`、`live_row`、`ranking_page`、`actor_row`、`promo`：进入媒体/演员/运营横幅楼层。
- `vod_category_page` / `vod_filter_page`：频道分类/筛选页能力，不适合当成综合首页的主要丰富楼层。
- `category_group`：后台“热门分类组”，用于按分类聚合资源卡片；前端已扩展为普通媒体 section 路径消费返回 items，支持首页聚合漫画/小说/视频/抖阴等资源，配置时要确保右侧分类来源、资源表、contentType 与返回 items 匹配。

展示字段：

- `displayMode=horizontal`：横向楼层；`grid`：平铺网格楼层；`icon_grid`：图标/快捷入口。
- `cardVariant=landscape`：横卡；`portrait`：竖卡。成人模式下视频资源默认横卡；观影模式下影视资源默认竖卡；漫画/小说默认竖卡。
- `displayMode=grid` 平铺规则：横卡 2 列、竖卡 3 列；显示数量优先设置 6，形成横卡三行两列或竖卡两行三列。前端对 grid 楼层也只露出前 6 张作为兜底。
- `tagConfig` 只控制 App 标签显隐：评分、播放量、时长/连载、VIP、质量。数据仍由后端卡片返回。默认规则：所有媒体/聚合楼层的卡片标签选项均默认勾选；只有产品明确要求隐藏时才在 CMS 中取消对应项。前端未收到完整 `tagConfig` 时按全勾选默认值补齐。

## 成人推荐综合页模板

配置成人底部菜单“推荐”页时，优先形成视频 + 漫画 + 小说混合楼层：

1. `carousel`：成人精选。普通配置可用 `bizTable=vod`、`contentType=vod`；如产品要求视频 + 漫画 + 小说混合 Banner，则 CMS 必须返回混合媒体 items 或 `categoryGroups[].items`，并确保每条 item 带自身资源类型字段，前端按视频/漫画/小说分别跳转。
   - 单表视频 Banner 右侧建议：`bizTable=vod`、`queryChannelCode=video`、`filter.rules=[status=0]`，系统条件保留 `mode=2`，排序 `sort_index desc + update_time desc`。
   - 混合 Banner 目标配置结构建议：`sources=[vod/video, comics_main/comics, novel_main/novel]`，每个 source 都单独设置 `status=0`、资源频道、limit 和排序；前端只消费最终返回的混合 `items/categoryGroups[].items`。
2. `notice_bar`：站内公告，`bizTable=sys_notice`，`notice_type=2`。
3. `tag_grid` 或 `quick`：频道入口/福利入口，右侧使用 `sys_ad` + 广告位字典，不要误配成分类 tabs。
4. `ranking_page`：成人热榜，`bizTable=vod`，保留排序组：最新/最热/好评。
5. `video_row`：最新上新/猜你喜欢/编辑严选，`bizTable=vod`，视频用 `landscape`。
6. `actor_row`：人气演员，`bizTable=vod_actor`。
7. `category_group` 小说口味馆：`bizTable=novel_main`，`contentType=novel`，资源详情 `/adult/novel/{resourceId}` 或后台字段对应的 novel 模板。
8. `category_group` 漫画口味馆：`bizTable=comics_main`，`contentType=comics`，`cardVariant=portrait`，资源详情 `/adult/comics/{resourceId}`。
9. `video_row` 抖阴热播：`bizTable=vod`，`contentType=vod`，`channel_code=douyin`，视频仍用 `landscape`，更多 URL 归属抖阴频道或分类页。
10. `promo`：会员福利/运营横幅，通常取 `sys_ad` 或运营指定资源。

## 右侧具体数据配置检查清单

每个模块保存前检查右侧：

- 模块标题：App 楼层标题；标题显示是否开启。
- 组件编码：保持组件类型语义，如 `first`、`notice_bar`、`tag_grid`、`ranking_list`、`video_row`、`category_group`。
- 显示数量：横向滑动楼层可用 6/8；平铺 grid 楼层固定优先 6，横卡对应 3 行 × 2 列，竖卡对应 2 行 × 3 列。
- 跳转目标：更多按钮所属页面；分类组还要单独设置 `moreUrl`、`categoryUrlTemplate`、`resourceUrlTemplate`。
- 业务表：视频 `vod`；演员 `vod_actor`；公告 `sys_notice`；广告/快捷入口 `sys_ad`；漫画 `comics_main`；小说 `novel_main`。
- 查询频道 `channel_code`：只覆盖当前组件查询，不改变页面自身 channel/cache key。
- 内容来源：自动查询 / 手动选择 / 接口动态；接口动态通常用于实时观看等动态模块。
- 卡片标签：评分、播放量、时长、VIP标签、质量标签必须默认全部勾选；批量新增/复制楼层后逐个选中模块核对，避免旧楼层继承半勾选状态。
- 筛选条件：系统条件如 `mode = 2` 不可删；业务条件至少保留 `status = 0`。
- 排序规则：最新用 `update_time/source_update_time 降序`，最热用 `view_count 降序`，榜单用后台提供的 rank mappings。
- 业务首页楼层假筛选：不要给每个楼层都配置。每个业务页面/频道（如漫画页、小说页、视频页）只保留 1 个代表性的普通资源楼层或排行楼层配置多个 `sortOptions`（如最新/最热/好评/人气），作为该业务的“可切换榜单/排行”楼层。前端只在这个楼层标题右侧、“更多”按钮前展示轻量 chip；点击 chip 时在当前页面原地按该楼层 `componentId + sort` 重新拉取第一页数据。这个交互不等同于跳转更多页，也不要配置成顶部频道 tab，更不要批量铺到所有楼层。
- 分类组配置：分类来源表、分类频道、分类模式、分类状态、每类数量、资源频道、资源分类字段、前端参数名、更多 URL、分类 URL 模板、资源详情 URL 模板。

## 后台枚举/筛选异常记录

- 成人推荐聚合页需要漫画/小说资源时，目标配置仍是 `category_group + comics_main/novel_main + contentType=comics/novel + cardVariant=portrait`。
- 如果右侧“业务表/资源表”筛选枚举里选不出 `comics_main` 或 `novel_main`，按后台配置项缺口记录处理，不要改成 `vod` 或分类筛选页绕过；也不要因此把综合页结构改偏。
- 临时核对方式：查看底部“配置 JSON”里模块的 `config.bizTable`、`dataSource.bizTable`、`contentType`、`displayMode`、`cardVariant` 是否符合目标。枚举修复后再通过右侧控件补齐并保存/发布。

## 实操流程

1. 打开/选中后台 CMS 页面与模式。
2. 对照现有页面学习配置：优先查看同类页面（视频、漫画、小说、推荐页）的右侧字段与 JSON。
3. 修改或新增模块：先选组件库模块，再选中模块卡片，最后改右侧字段。
4. 修改后点击“保存草稿”，确认左侧提示变为“当前配置已同步”。
5. 如需要线上生效，再点击“发布整页”；若发布按钮在视口边缘，优先使用精确 locator，而不是坐标点击。
6. 用 App 本地地址验证：成人推荐页通常 `http://localhost:8081/adult`，频道页如 `http://localhost:8081/adult/video`。
7. 仅 CMS 后台配置变更不需要跑前端测试；若改了前端映射代码，再跑 `npx tsc --noEmit` 和相关 Jest。

## 本次沉淀案例

成人模式底部菜单“推荐”页已形成丰富楼层：成人精选、公告、频道入口、成人热榜、最新上新、AI 换脸专区、人气演员、猜你喜欢、会员福利、小说口味馆、分类/筛选、站长精选、编辑严选、本周热榜，并新增“漫画口味馆”分类聚合楼层。

新增“漫画口味馆”的关键右侧配置：

- 模块类型：`category_group` / 热门分类组。
- 标题：`漫画口味馆`。
- 业务表：`comics_main`。
- 内容类型：`comics`。
- 展示：`horizontal` + `portrait`。
- 分类频道：`comics`。
- 资源频道：`comics`。
- 更多 URL：`/adult/comics/discover`。
- 分类 URL：`/adult/comics/discover?categoryId={categoryId}&title={title}`。
- 资源详情：`/adult/comics/{resourceId}`。
- 副标题：`{title}精选漫画`。

小说“热门分类组”的关键右侧配置学习：

- 模块类型：`category_group` / 热门分类组。
- 常用标题：`小说上新` / `小说口味馆`。
- 业务表：`novel_main`。
- 内容类型：`novel`。
- 展示：`horizontal` + `portrait`；小说卡片走竖版。
- 分类来源：`vod_category`，分类 ID 字段 `id`，分类标题字段 `name`。
- 分类筛选：`categoryChannelCode=novel`、`categoryMode=2`、`categoryStatus=0`。
- 分类排序：`sort_index` 升序。
- 每类资源数：`booksPerCategory=3`，前台会形成多个 `categoryGroups`，每组带 3 条小说资源。
- 资源表：`novel_main`。
- 资源筛选：`resourceChannelCode=novel`、`resourceCategoryField=category_id`、`resourceCategoryParam=categoryId`、`status=0`。
- 资源排序：优先 `source_update_time` 降序，用于“上新”；如果做“最热/人气”则改为对应热度字段降序。
- 更多 URL：`/adult/novel/discover`。
- 分类 URL：`/adult/novel/discover?categoryId={categoryId}&title={title}`。
- 资源详情 URL：`/adult/novel/{resourceId}` 或 `novelUrlTemplate=/adult/novel/{novelId}`。
- 副标题模板：`{title}精选好书`。
- 前台返回要点：模块 `contentType=novel`，`categorySource.table=vod_category`，`resourceFilter.table=novel_main`，每个 `categoryGroups[]` 带 `title/subtitle/categoryId/url/query/filter/items`；前端从 `categoryGroups[].items` 拉平或分组展示小说卡片。
- 小说/漫画“人气排行”类普通楼层如果不是 `category_group`，可以使用 `video_row`/资源列表或 `ranking_page` 语义配合 `novel_main`/`comics_main`，并在 `sortOptions` 中配置：
  - `latest`：`source_update_time` 降序；
  - `hot` / `popular`：`view_count`、`externalHits` 或业务人气字段降序；
  - `rating`：`score` 或评分字段降序。
  前端频道首页只针对该页面/业务选定的 1 个代表楼层把这些 `sortOptions` 渲染成楼层标题右侧的当前页内假筛选 chip，点击后原地刷新当前楼层数据；其他普通展示楼层保持固定内容。漫画页如果多个楼层都配置了 `sortOptions`，前端也只在第一个符合条件的代表楼层显示 chip。








