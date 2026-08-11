# Pull To Refresh

适用问题：Expo 多端项目要做下拉刷新，且需要同时兼顾 native iOS、native Android、Web browser、iOS WebClip/PWA fullscreen、Android Chrome browser 的滚动、安全区和刷新体验。

## Contents

- Platform Split
- Native iOS / Android
- Web Browser
- WebClip / PWA Fullscreen
- Data And State Rules
- Safe Area And Layout
- Anti-Patterns
- Verification
- Official References

## Platform Split

不要把三端写成同一套手势：

- Native iOS：优先使用 React Native `RefreshControl` 或 `FlatList` / `SectionList` 的 `onRefresh` + `refreshing`。
- Native Android：同样使用 `RefreshControl` / list built-in refresh，并额外设置 Android 指示器颜色、背景、可用状态和 progress offset。
- Web browser：先决定使用浏览器原生刷新还是应用内自定义刷新；iOS Safari browser 还要保留 document scroll 以支持地址栏收缩。
- WebClip/PWA fullscreen：根滚动通常被锁住，浏览器原生下拉刷新不可依赖；必须用应用内自定义 refresh provider/hook。

## Native iOS / Android

首选模式：

```tsx
<FlatList
  data={items}
  refreshing={refreshing}
  onRefresh={refresh}
/>
```

或：

```tsx
<ScrollView
  refreshControl={
    <RefreshControl
      refreshing={refreshing}
      onRefresh={refresh}
      progressViewOffset={headerOffset}
    />
  }
/>
```

规则：

- `refreshing` 必须是受控状态；`onRefresh` 开始时置 `true`，完成、失败、取消、离开页面时都要复位。
- 列表优先用 `FlatList` / `SectionList`，长列表不要用 `ScrollView` 承载所有 item。
- 刷新只代表重新拉当前页面第一页或当前视图数据；不要和 infinite scroll 的加载更多状态混用。
- 顶部有 fixed/sticky/header/safe area 时，用 `progressViewOffset` 或等价布局让指示器不被 Header/状态栏遮挡。
- Android 设置 `colors`、`progressBackgroundColor`、`enabled` 等平台属性时，颜色来自主题 token。
- 刷新中切路由、切 tab、进入后台或请求取消时，必须复位 `refreshing`，避免 spinner 卡住。

## Web Browser

Web browser 模式先选一种策略：

- 保留浏览器原生刷新：适合普通网页；不要锁死 `html/body`；iOS Safari browser 需要 document scroll。
- 应用内自定义刷新：适合沉浸式 Web app、feed、WebClip 入口一致体验；需要避免触发浏览器整页 reload。

实现要点：

- iOS Safari browser 下，不要为了自定义下拉刷新破坏 document scroll，否则底部地址栏可能不再随上滑收缩。
- Android Chrome browser 下，`overscroll-behavior` 可以控制 scroll chaining 和浏览器原生 pull-to-refresh，但要真机验证。
- 只在主纵向滚动位于顶部、手势主要为纵向下拉、没有横向 carousel/slider 抢手势时触发刷新。
- 自定义刷新阈值要有最小距离和阻尼；短距离误触不要刷新。
- Desktop web 默认提供显式刷新按钮或命令，不要强行模拟触摸手势。

## WebClip / PWA Fullscreen

Fullscreen/standalone 通常会锁定 `html/body/#root` 高度和 overscroll，浏览器原生下拉刷新不可作为功能依赖。

推荐模式：

- 在根部放统一 Web pull-to-refresh provider。
- 页面进入时注册当前页面 refresh handler，离开时注销。
- provider 只在 scroll top、非输入聚焦、非横向拖动、非 modal/播放器手势时接管 touch。
- 没有页面 handler 时 fallback 到页面 reload 或显式提示。
- 刷新中禁止重复触发，失败后仍复位 UI 状态。

## Data And State Rules

- 区分 `initialLoading`、`refreshing`、`loadingMore`、`mutating`。
- 刷新时保留旧数据，除非业务明确要求清空。
- 刷新请求要可去重、可取消；快速重复下拉只保留一个有效请求。
- 刷新只更新当前页面必要数据；跨页面缓存用目标项目的 query/cache 机制统一失效。
- 错误提示要轻量，不要把页面打回全屏错误态，除非当前数据完全不可用。
- 有登录态/游客态的页面，刷新前先确认当前 session，不要用过期用户信息刷新敏感数据。

## Safe Area And Layout

- 下拉指示器不应进入刘海、状态栏、移动信号区。
- fixed header 页面要明确 refresh indicator 从 Header 下方还是 Header 上方出现，并保持全端一致。
- fixed bottom tab 不参与下拉刷新手势；刷新只由主纵向内容区触发。
- PWA/WebClip fullscreen 的下拉刷新不能破坏 bottom fixed 安全区和 root height lock。
- Android 沉浸式页面只有在内容确实可刷新时才开放手势；播放器全屏、横向滑动、modal 打开时通常禁用。

## Anti-Patterns

- Native 端自己写 touch gesture 替代 `RefreshControl`，但没有处理系统回弹、可访问性和取消状态。
- Web 端直接复用 native `RefreshControl` 并假设 react-native-web 会自动支持。
- PWA/fullscreen 锁根后还依赖浏览器原生下拉刷新。
- 下拉刷新和加载更多共用一个 `loading` 布尔值。
- 失败时不复位 `refreshing`。
- 为了阻止 Android Chrome 整页刷新，全局粗暴 `overscroll-behavior: none`，结果破坏 iOS Safari browser 地址栏收缩或桌面滚动体验。

## Verification

- Native iOS：顶部下拉触发；indicator 不被 status bar/header 遮挡；完成/失败/离开页面都会停止。
- Native Android：三键/手势导航下都可触发；indicator 颜色符合主题；Modal/沉浸式页面不误触。
- iOS Safari browser：下拉刷新策略不破坏 document scroll 和地址栏上滑收缩。
- iOS WebClip/PWA：使用自定义刷新；退出重进后 handler 仍正确注册；底部 fixed 不漂移。
- Android Chrome browser：不会意外整页 reload；自定义刷新与浏览器 overscroll 行为一致。
- Offline/slow network：重复下拉去重；取消和失败后状态复位。

## Official References

- React Native RefreshControl: https://reactnative.dev/docs/refreshcontrol
- React Native FlatList `onRefresh`: https://reactnative.dev/docs/flatlist
- React Native ScrollView: https://reactnative.dev/docs/scrollview
- MDN overscroll-behavior: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/overscroll-behavior
- Chrome overscroll behavior: https://developer.chrome.com/blog/overscroll-behavior/
