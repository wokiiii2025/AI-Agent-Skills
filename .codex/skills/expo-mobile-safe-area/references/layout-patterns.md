# Expo Multi-Platform Layout Patterns

适用问题：新增页面、改 Header、改底部固定区域、播放器 inline/fullscreen、安全区重复垫高、Web 与 Android 真机布局不一致。

## Contents

- Root Layout Responsibilities
- Page Header Pattern
- Overlay Header Pattern
- Collapsible Sticky Header Pattern
- Fixed Bottom Action Bar
- Player / Fullscreen Pattern
- Web CSS Synchronization
- Validation Matrix
- Official References

## Root Layout Responsibilities

根布局必须提供：

- `SafeAreaProvider`
- 主题 provider
- Android 系统栏运行时同步
- Web meta/CSS/viewport/display mode 注入
- 全局 `StatusBar`

不要在单个页面重复创建全局 provider 或独立设置与全局冲突的系统栏颜色，除非该页面有明确特殊需求。

## Page Header Pattern

通用页面：

```tsx
const insets = useSafeAreaInsets();

return (
  <View style={[styles.screen, { backgroundColor: theme.colors.background }]}>
    <View style={{ paddingTop: insets.top }}>
      <PageHeader title="..." />
    </View>
    <DocumentAwareScrollView
      testID="main-document-scroll"
      contentContainerStyle={{
        paddingBottom: Math.max(insets.bottom, 10) + fixedBottomHeight,
      }}
    >
      ...
    </DocumentAwareScrollView>
  </View>
);
```

规则：

- Header 叶子组件不加 safe area。
- 需要沉浸式全屏时，由全屏容器或播放器 controls 按状态单独处理。
- 页面级 wrapper 加 `insets.top`。
- 滚动内容底部预留底部固定栏和 bottom inset。
- Web 端要支持 iOS Safari 地址栏收缩时，主滚动容器使用 document-aware 容器。

## Overlay Header Pattern

首页、播放页、详情页封面区经常使用 overlay header。规则：

- 背景图/视频可以延伸到刘海和状态栏区域。
- 可读文本、返回按钮、搜索按钮等交互元素必须位于 `insets.top` 下方。
- overlay header 的外层负责 `paddingTop: insets.top`。
- 内部展示组件不要再次接收并叠加同一个 top inset。
- 状态栏文字颜色要与 overlay 背景对比足够；滚动后如背景变化，需要同步状态栏 style。

## Collapsible Sticky Header Pattern

- native/standalone 可以沿用项目现有 ScrollView 与 absolute overlay；iOS Safari browser document scroll 下，吸顶 overlay 使用 viewport fixed。
- 内容容器预留展开 Header 高度，fixed overlay 不参与文档布局。
- logo/search 行与 tabs 的收起距离使用真实测量值或共享高度常量；最终 tabs top 必须精确落在目标位置。
- 高频滚动回调只更新动画 offset，不更新页面 state；优先复制项目内已验证流畅的基准页链路。
- 若 document-aware 容器为通用 onScroll 合成完整事件，允许吸顶页面绕过该桥接，直接订阅 window scroll；非 document-scroll 终端仍使用普通 onScroll。
- 变更 transform/opacity，避免滚动期间反复变更 height/top 或测量整页。

## Fixed Bottom Action Bar

用于安装按钮、提交按钮、工具栏等：

- 外层 `position: absolute` 或 Web fixed，`bottom: 0`。
- 背景色或半透明遮罩必须覆盖到底部边缘。
- 内容区域 `paddingBottom: Math.max(insets.bottom, 10)`。
- 主内容 `paddingBottom` 要包含固定栏高度，避免最后内容被盖住。
- Web standalone/fullscreen 下优先让 CSS `env(safe-area-inset-bottom)` 处理 Home Indicator。
- Android native 下底部系统导航栏背景由系统栏同步处理，不要只给内容加空白 spacer。
- 底部 Tab、详情 CTA、阅读工具栏应复用公共 fixed bottom primitive，而不是各页面分别计算 Safari 地址栏偏移。
- iOS Safari browser 下 outer 使用 VisualViewport bottom offset 并补底背景；inner 独占 safe-area padding。

## Player / Fullscreen Pattern

- 非全屏 inline 播放器的 safe area 由页面/播放器容器处理。
- 播放器内部 controls、watermark、badge 只有 `isFullscreen === true` 时才加 `insets.top`。
- Web fullscreen/standalone inline fallback 可以在页面容器上加 `inlinePlayerTopInset`，但 controls 内不要再叠加。
- 修改播放器 Web HLS / iOS Safari 逻辑时，要把布局终端判断和媒体能力判断分开。

## Web CSS Synchronization

Web 全局样式应有单一事实来源，并被这些入口复用或生成：

- Expo/React head 模板中的首屏样式。
- React runtime 注入或更新的样式。
- 生产构建/部署脚本注入的 PWA/head 样式。

如果生产注入脚本改为拷贝或解析源码，测试必须覆盖关键 CSS 字符串，避免开发/生产漂移。

关键 CSS 能力：

- `viewport-fit=cover`。
- `env(safe-area-inset-top|bottom|left|right)`。
- `VisualViewport` offset 对应的 CSS variable。
- iOS Safari browser 的 document scroll 解锁。
- standalone/fullscreen 的根高度锁定。
- DOM 物理滚动条隐藏但保留触摸/鼠标滚动。

## Validation Matrix

- iPhone Safari browser：document scroll、地址栏收缩、底部 fixed 跟随 VisualViewport、切页回顶。
- iPhone WebClip：全屏无地址栏、重开后底栏不漂移、Home Indicator 区域背景融合。
- Android native dark/light：状态栏图标对比度、三键导航区背景、底部 Tab 背景。
- Android immersive：进入隐藏系统栏，退出恢复。
- Android transparent modal：三键区不露白/灰。
- Desktop web：不应被 iOS/Android mobile CSS 锁死或固定错位。

## Official References

- Expo Safe Areas: https://docs.expo.dev/develop/user-interface/safe-areas/
- react-native-safe-area-context in Expo: https://docs.expo.dev/versions/latest/sdk/safe-area-context/
- Expo system bars: https://docs.expo.dev/develop/user-interface/system-bars/
- WebKit safe areas: https://webkit.org/blog/7929/designing-websites-for-iphone-x/
- Chrome Android edge-to-edge: https://developer.chrome.com/docs/css-ui/edge-to-edge
