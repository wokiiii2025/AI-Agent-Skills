# Device And Browser Detection

适用问题：不同设备型号、浏览器、iOS Safari/Chrome 响应式模式、Android Web/native、PWA/WebClip 之间逻辑混用。

## Terminal Detection

建议为布局层定义有限终端类型：

- `native`
- `web-ios`
- `web-android`
- `web-pc`
- `unknown`

判断顺序：

1. Native 端：`Platform.OS !== "web"` 返回 `native`。
2. UA 包含 Android：`web-android`。
3. UA 包含 iPhone/iPad/iPod，或 `navigator.platform === "MacIntel"` 且 `maxTouchPoints > 1`：`web-ios`。
4. 其他：`web-pc`。

注意：

- iOS 上第三方浏览器也使用 WebKit，但地址栏、安装引导和调试行为可能不同。涉及 iOS 配置描述文件或桌面应用安装时，必须说明是否在 Safari 真机验证。
- Chrome DevTools 响应式模式会伪装 iPhone UA，不能当作 iPhone 真机结论。
- iPadOS 桌面 UA 可能看起来像 Mac，需要结合 touch 点判断。

## Display Mode Detection

布局 display mode：

- `browser`
- `standalone`
- `fullscreen`
- `unknown`

判断顺序：

1. WebClip handoff：URL query 包含 `webClip`。
2. session 持久化：`sessionStorage` 或同类短期标记。
3. window 级兜底：`window.name` 或同类不会随 SPA 路由消失的标记。
4. iOS home-screen PWA：`navigator.standalone`。
5. 标准 Web：`matchMedia("(display-mode: fullscreen)")` / `standalone`。
6. 默认 `browser`。

不要只靠 `matchMedia`，Managed WebClip 恢复和 client-side navigation 可能拿不到稳定结果。

## Browser Capability Detection

布局终端、浏览器 UI、媒体能力和安装能力是四件事：

- 布局终端回答：该按 native、iOS web、Android web 还是 desktop web 布局。
- 显示模式回答：browser、standalone、fullscreen 是否锁根滚动、是否要文档滚动。
- 媒体能力回答：是否可信任 Apple WebKit 原生 HLS、是否需要 hls.js 或代理。
- 安装能力回答：是否能触发 mobileconfig、是否能引导 Add to Home Screen。

不要用一个 UA 判断同时驱动所有分支。每个能力都要有单独函数、测试和 fallback。

## Media Capability Is Not Layout Terminal

不要把布局终端判断拿来判断播放器 WebKit/HLS 能力。

- 布局判断可用 UA、platform 和 touch 特征。
- 播放器原生 Apple WebKit 媒体能力要结合 vendor、真实浏览器能力和目标项目已有播放器策略。
- Chrome DevTools 响应式 iPhone SE 会伪装 UA；不能因此把它当真实 iOS Safari 原生 HLS。

## Avoid Model Guessing

- 不要为 iPhone 型号、Android 品牌、屏幕高度写硬编码安全区。
- 优先顺序：真实 inset (`react-native-safe-area-context`) -> CSS `env()` -> `VisualViewport` -> display mode -> 目标项目 fallback。
- 只有 WebClip fullscreen 恢复 bug 这类已验证场景，才允许使用 `window.screen` 物理高度兜底，并且要限定 `web-ios + displayMode !== browser`。

## Tests To Keep

- WebClip query 能持久化到 sessionStorage/window.name 这类短期标记。
- iPadOS desktop UA + touch 点识别为 `web-ios`。
- Desktop Chrome 不被误判为 `web-ios`。
- Chrome 响应式 iPhone 不被误判为真实 iPhone Safari 媒体能力。
- browser、standalone、fullscreen 三种 display mode 都能设置到根节点数据属性或等价状态。

## Official References

- MDN `display-mode`: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/display-mode
- MDN VisualViewport: https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport
- Apple standalone web apps: https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html
