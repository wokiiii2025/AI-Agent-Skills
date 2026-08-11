# Web Runtime Contract

适用问题：Expo Web / React Native Web 的安全区、display mode、document scroll、fullscreen root lock 在首屏、刷新后、生产构建或 WebClip 重进时不一致。

## Contract

Web 安全区不能只靠 React 组件 mount 后再修。以下能力必须尽量早于首屏生效：

- `viewport-fit=cover` viewport meta。
- terminal/display mode 的根节点 data attribute。
- `--app-viewport-height`、`--app-visual-viewport-bottom-offset` 等 CSS variable。
- iOS Safari browser 的 document scroll 解锁。
- standalone/fullscreen 的 root height lock。
- DOM 物理滚动条隐藏但保留触摸/鼠标滚动。

## Required Layers

- Head template：提供首屏 meta、基础 CSS、bootstrap script。
- Early bootstrap：在 React hydrate 前识别 query/session/window/display mode，写入根节点属性和 CSS variable。
- React runtime：后续响应 route、visibility、resize、orientation、VisualViewport 事件。
- Production injection：生产构建或部署脚本必须复用同一份 CSS/bootstrapping 事实来源，不要手写另一套。

## Data Attributes

建议至少同步：

- `data-web-terminal`: `web-ios`、`web-android`、`web-pc`、`native`、`unknown`。
- `data-web-display-mode`: `browser`、`standalone`、`fullscreen`、`unknown`。
- `data-web-document-scroll`: 仅 iOS Safari browser 主纵向文档滚动时启用。
- `data-web-keyboard`: 输入聚焦或键盘可见时启用，避免 fullscreen height fallback 误伤输入。

## CSS Variables

建议至少同步：

- `--app-viewport-height`：当前应用可用高度。
- `--app-visual-viewport-height`：VisualViewport 高度。
- `--app-visual-viewport-bottom-offset`：地址栏/键盘等导致的 bottom offset。
- `--app-safe-area-top` / `--app-safe-area-bottom`：需要桥接 CSS `env()` 或 JS fallback 时使用。

普通 browser 模式下可按当前 layout viewport 与 VisualViewport 的差计算底部遮挡：

```ts
const viewport = window.visualViewport;
const layoutHeight = window.innerHeight;
const visualBottom = viewport
  ? viewport.height + viewport.offsetTop
  : layoutHeight;
const bottomOffset = Math.max(0, layoutHeight - visualBottom);

document.documentElement.style.setProperty(
  "--app-visual-viewport-bottom-offset",
  `${bottomOffset}px`,
);
```

- 在 `visualViewport.resize` 和 `visualViewport.scroll` 时更新这个 CSS variable。
- 高频事件只写必要变量；不要因此更新整棵 React 页面 state。
- 键盘也会改变 VisualViewport，输入页要结合 focus/keyboard 状态使用 `references/keyboard-viewport.md`，不能把所有 shrink 都当成地址栏。

## Event Sync

需要监听并节流：

- `pageshow`
- `focus` / `blur`
- `visibilitychange`
- `resize`
- `orientationchange`
- `visualViewport.resize`
- `visualViewport.scroll`
- SPA route change / navigation focus

对 `focus/pageshow/orientationchange` 可安排少量延迟复测以等待 Safari viewport 稳定；对持续的 `visualViewport.scroll` 不要无限累积 rAF 和多个 timeout。保持可取消、可去重，并在卸载时清理。

## Drift Prevention

- 不要在 head、runtime、生产注入脚本中维护三份手写 CSS。
- 关键 CSS 字符串或生成结果要有测试覆盖。
- 修改 display mode、safe-area 或 root lock 时，同时检查开发模板和生产构建。
- 生产环境如果通过服务端注入 mobileconfig/PWA head，确保它和本地 Web 预览一致。

## Verification

- 刷新首屏不先错位再跳正。
- Safari browser、WebClip fullscreen、Android Chrome、desktop web 的根节点属性正确。
- WebClip 退出再进、后台切回、横竖屏切换后 CSS variable 更新。
- 输入框聚焦时不会继续强套 fullscreen 物理屏幕高度。

## Official References

- MDN viewport meta: https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/meta/name/viewport
- MDN VisualViewport: https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport
- MDN `env()`: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env
- WebKit safe areas: https://webkit.org/blog/7929/designing-websites-for-iphone-x/
