# Safe Area Architecture

适用问题：不知道安全区应该在根布局、页面、Header、底部 Tab、播放器还是系统栏里处理；新增页面后顶部重复垫高；底部背景和 Home Indicator/Android 三键区割裂。

## Responsibility Layers

按职责分层，避免到处散落 inset 公式：

- Root layer：提供 `SafeAreaProvider`、主题、全局 `StatusBar`、Android 系统栏同步、Web runtime/meta/CSS 注入。
- Runtime layer：识别 native/web、iOS/Android/desktop、browser/standalone/fullscreen，并把结果同步到 JS 状态和根节点数据属性。
- Page layout layer：根据页面形态一次性处理 top/bottom safe area，组织 Header、滚动区、固定底栏。
- Leaf component layer：Header、按钮、卡片、图标、Tab item 等只负责自身视觉和交互，不自行读取并叠加全局 safe area。
- System bar layer：Android 状态栏/导航栏颜色、明暗、可见性；iOS native 状态栏样式；Web browser/PWA 的 CSS safe-area。
- Native escape hatch：只有 Expo API 覆盖不足时，才用 Android 原生模块或 config plugin 管理 Window flags。

## One Inset, One Owner

同一个方向的 safe area 只能有一个 owner：

- Top inset：通常由页面级 Header wrapper、播放器容器或全屏 controls 拥有。
- Bottom inset：通常由固定底栏 inner、页面滚动内容底部 padding 或 native 系统栏同步拥有。
- Left/right inset：横屏、foldable、iPad 分屏或 landscape fullscreen 才重点处理。

禁止模式：

- 页面 wrapper 加了 `paddingTop: insets.top`，Header 组件内部又加一次。
- Web CSS 已用 `env(safe-area-inset-bottom)`，JS 又用设备型号猜一段 bottom padding。
- Android 三键导航栏背景没同步，只在页面底部放一个 spacer。
- PWA/fullscreen 根高度锁住后，仍期待浏览器原生 document 下拉刷新。

## Background Fusion

安全区不是透明空白，它必须和当前视觉区域融合：

- 顶部刘海/状态栏区域：背景取页面顶部真实视觉背景，可能是主题背景、封面图、渐变或视频容器。
- 底部 Home Indicator/三键导航区：背景取底部固定栏或页面底部真实视觉背景。
- 固定栏外层负责铺满到屏幕边缘，固定栏内层负责给可点击内容留 safe area。
- 亮色/暗色主题切换时，同步状态栏/导航栏图标明暗。

## Cross-Platform Rule Split

不要把所有端写成一个公式：

- Native Android：靠 `react-native-safe-area-context` 加页面布局，靠 `StatusBar` / `expo-navigation-bar` / 原生 Window flags 同步系统栏。
- Native iOS：靠 `react-native-safe-area-context` 保护刘海、Home Indicator；状态栏样式走 RN/Expo。
- iOS Safari browser：主纵向滚动必须走 `window/document` 才能让底部地址栏收缩；底部 fixed 跟随 `VisualViewport`。
- iOS WebClip/PWA fullscreen：根高度锁住；底部 fixed 贴底；inner padding 用 CSS `env(safe-area-inset-bottom)`。
- Android Chrome browser：Chrome edge-to-edge 和 safe-area 行为可能随版本变化；Web fixed 元素用 CSS `env()` 和 `VisualViewport`，不要复用 native Android 导航栏逻辑。

## Implementation Checklist

新增或修改页面时先回答：

- 页面是否有顶部 Header、overlay header、播放器、固定底栏或 bottom tab？
- 哪一层拥有 top inset？哪一层拥有 bottom inset？
- 底部固定栏外层是否铺满到屏幕最底部？
- Web iOS browser 是否仍允许 document scroll？
- PWA/WebClip fullscreen 是否锁根高度并使用 CSS `env()`？
- Android 页面是否需要普通系统栏、沉浸式系统栏，还是透明 Modal？
- 目标项目是否已有统一 hook/service/component 可复用？

## Official References

- Expo Safe Areas: https://docs.expo.dev/develop/user-interface/safe-areas/
- react-native-safe-area-context in Expo: https://docs.expo.dev/versions/latest/sdk/safe-area-context/
- Expo system bars: https://docs.expo.dev/develop/user-interface/system-bars/
- WebKit safe areas: https://webkit.org/blog/7929/designing-websites-for-iphone-x/
- MDN `env()` safe-area variables: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env
