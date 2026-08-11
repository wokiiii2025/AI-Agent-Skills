# iOS Safari Browser Mode

适用问题：iPhone 真机 Safari 普通浏览器模式下，页面上滑不能收缩底部地址栏、底部固定 Tab 被裁剪、顶部被信号/刘海区域压住、页面切换后滚动位置异常。

## Mode Contract

- 只有 `web-ios + browser` 才启用文档滚动模式；standalone/fullscreen 不走这套。
- 根节点应有可被 CSS 读取的终端和 display mode 标记，例如 `data-web-terminal="web-ios"`、`data-web-display-mode="browser"`、`data-web-document-scroll="true"`。
- 这个模式下不要把 `html/body/#root` 锁成固定高度内部滚动。要让 `window/document` 成为纵向滚动链路。
- 横向列表仍可用内部横向滚动；主纵向内容要走文档滚动。

## Implementation Pattern

1. 在 Web runtime/frame hook 同步：
   - `data-web-terminal`
   - `data-web-display-mode`
   - `data-web-document-scroll`
   - `--app-viewport-height`
   - `--app-visual-viewport-bottom-offset`
2. 在全局 Web CSS 中：
   - browser mode 下 `html/body` 使用 `height: auto` 和 `overflow-y: auto`。
   - `data-web-document-scroll="true"` 下解锁 Expo Router / RN Web 祖先容器的 `height`、`position`、`overflow-y`。
   - 隐藏 DOM 物理滚动条，但保留 document scroll 和触摸/滚轮滚动。
3. 页面主滚动容器使用文档滚动兼容容器或等价模式：
   - iOS Safari browser mode：渲染 `View`，并把 `window.scrollY` 转成 RN `onScroll` 事件。
   - 其他终端：正常 `ScrollView`。
   - 只有确实依赖完整 `NativeScrollEvent` 的页面才合成事件；吸顶动画优先直接消费 `window.scrollY`。
4. 底部固定栏：
   - `position: fixed`。
   - `bottom: var(--app-visual-viewport-bottom-offset, 0px)`。
   - 用 `::after` 或同背景容器填满底部变化区域，避免地址栏动画时露底。
5. 页面切换：
   - 只在 `web-ios + browser` 调 `window.scrollTo({ top: 0 })`。
   - 不影响 native、desktop web、standalone/fullscreen。

## Smooth Collapsible Or Sticky Header

在 `web-ios + browser` 的 document scroll 模式下，页面内 `position: absolute` 会随文档滚走。需要吸顶时：

1. 让 Header 外层在该模式下使用 viewport `position: fixed; top: 0`，其他终端保留项目原有布局。
2. 让滚动内容预留 Header 展开高度，避免首屏被遮挡。
3. 让顶部 logo/search 行和 tabs 在同一个 fixed overlay 内做 transform；收起后 tabs 的最终 `getBoundingClientRect().top` 应为 `0` 或约定的 top inset。
4. 让 collapse distance 来自真实顶部行高度或同一个共享常量。不要让动画使用 `56`、布局却使用 `52`。
5. 复用项目中已经流畅的基准页监听链路，不要为相似页面另套一层滚动桥接。

对于 React Native `Animated.Value`，高频路径保持轻量：

```tsx
React.useEffect(() => {
  if (!useIosBrowserDocumentScroll) return;

  const handleDocumentScroll = () => {
    updateScrollOffset(window.scrollY || document.documentElement.scrollTop || 0);
  };

  handleDocumentScroll();
  window.addEventListener("scroll", handleDocumentScroll, { passive: true });
  return () => window.removeEventListener("scroll", handleDocumentScroll);
}, [updateScrollOffset, useIosBrowserDocumentScroll]);
```

- 只读取 scroll offset，不在每帧读取 document/body 的完整尺寸。
- 不在 scroll handler 里 `setState` 或重算页面数据。
- 不为只需要 offset 的动画构造完整 RN `NativeSyntheticEvent`。
- `Animated.Value` 自身已经在绘制阶段提交 transform 时，不要再给 scroll 转发额外套一层 rAF；否则可能比手指晚一帧。若直接写 DOM 且需要读写分离，可按实测选择 rAF，但不能叠加多层调度。
- 使用 passive listener，并在卸载时移除同一个函数引用。

## Fixed Bottom Tabs And Actions

底部 Tab、详情 CTA、阅读工具栏应共用同一种 outer/inner 结构：

- outer：负责 viewport fixed、背景、边框、z-index 和 VisualViewport bottom offset。
- inner：负责按钮布局及 `env(safe-area-inset-bottom)`；页面内容预留实际栏高加 gap。
- background filler：用 `::after` 延伸到 visual viewport 下方，避免地址栏动画期间露底。

```css
html[data-web-document-scroll="true"] [data-fixed-bottom] {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--app-visual-viewport-bottom-offset, 0px);
}

html[data-web-document-scroll="true"] [data-fixed-bottom]::after {
  content: "";
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  height: max(48px, calc(env(safe-area-inset-bottom, 0px) + var(--app-visual-viewport-bottom-offset, 0px)));
  background: inherit;
}
```

不要只给详情页按钮加 `position: fixed` 就结束：还要同步内容底部预留、safe-area padding、VisualViewport offset 和补底背景。优先抽一个公共 fixed bottom 组件，让 BottomTabBar、详情页和阅读页使用同一契约。

## Jank Triage

当一个页面流畅、另一个相似页面卡顿时，先比较可观测链路：

1. 比较两页的 scroll owner、listener 数量和 `position` 计算值。
2. 检查卡顿页是否经过 `window scroll → synthetic event → wrapper onScroll → Animated.Value`，而基准页直接消费 scrollY。
3. 检查每帧是否触发 React state、整页重渲染、DOM 测量、图片 blur/filter 或大面积阴影重绘。
4. 检查 fixed Header 是否只变更 `transform/opacity`，避免滚动中变更 top/height/layout。
5. 先消除多余调度和同步布局读取，再考虑 `will-change`；不要用强制 GPU 合成掩盖逻辑问题。

## Header And Bottom Rules

- 顶部：页面级 wrapper 使用 `paddingTop: insets.top`；通用 Header 这类叶子组件不要自己加安全区。
- overlay header 仍然是页面级 Header：外层加 `paddingTop: insets.top`，内部子组件不要再吃一次 top inset。
- 底部：内容滚动区域要预留固定 Tab 高度加 gap；固定 Tab 背景必须与页面/主题融合。
- Web browser mode 不要用 JS 把底部 safe area 做减法、封顶或设备猜测；底部 fixed 跟随 `VisualViewport` offset。

## Why Document Scroll Matters

iOS Safari 普通浏览器的底部地址栏收缩依赖浏览器感知页面在滚动。若应用把 `html/body/#root` 全部锁死，只在 React Native Web 内部 `ScrollView` 滚动，Safari 往往不会自动收缩底部地址栏，固定底栏也更容易在地址栏动画中被裁剪。

解决方向不是给某个页面写特例，而是让所有主纵向页面在 `web-ios + browser` 下继承同一套 document scroll 规则。

## Verification

- iPhone Safari 普通浏览器打开长页面，向上滑动，底部地址栏应自动收缩。
- 下滑/上滑过程中底部 Tab 不被裁剪、不漂移、不露白/露黑。
- 切换路由后页面回到顶部。
- 页面仍可自然触摸滑动，DOM 物理滚动条隐藏；如果看到 iOS 系统滚动指示器，那不是 DOM 滚动条。
- standalone/fullscreen 下不应启用 document scroll 锁定破坏全屏底栏。
- 检查根节点：`data-web-terminal=web-ios`、`data-web-display-mode=browser`、`data-web-document-scroll=true`。
- 记录 Header/tabs 在滚动前后的 `position` 与 `getBoundingClientRect().top`；吸顶完成后 tabs 不应为负值或留缝。
- 分段设置 scrollY 跨过收起区间，确认 tabs top 连续变化而不是跳跃；至少等待实际绘制帧再测量。
- 在开发浏览器临时设置 `--app-visual-viewport-bottom-offset: 44px`，确认 fixed bottom 精确上移 44px。这个检查只验证 CSS 契约，不能替代真实 iPhone Safari 地址栏动画。
- 用真实 iPhone Safari 上滑验证地址栏确实收缩，并观察 fixed bottom 是否抖动、裁剪或露底；桌面设备模拟只作为预检。

## Official References

- Expo Safe Areas: https://docs.expo.dev/develop/user-interface/safe-areas/
- MDN VisualViewport: https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport
- MDN viewport `viewport-fit=cover`: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/name/viewport
- WebKit safe area insets: https://webkit.org/blog/7929/designing-websites-for-iphone-x/
- MDN `display-mode`: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/display-mode
