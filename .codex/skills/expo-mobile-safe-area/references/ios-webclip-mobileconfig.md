# iOS WebClip / Mobileconfig / Fullscreen

适用问题：iPhone 通过配置描述文件安装桌面应用、全屏打开、退出后重进底部栏错位、WebClip 被误判为普通浏览器、PWA/standalone 下拉刷新或底部 Home Indicator 间距异常。

## Mobileconfig Contract

- 配置描述文件下载地址应来自后端/APP 配置提供的原始 iOS profile URL，或同源专用 mobileconfig endpoint fallback。
- 不能把 Expo Web dev server 地址、`manifest.webmanifest` 或普通页面 URL 当配置描述文件下载地址。
- response 必须使用 `Content-Type: application/x-apple-aspen-config`。
- payload 使用 `PayloadType = com.apple.webClip.managed`。
- WebClip payload 至少包含：
  - `Label`
  - `URL`
  - `FullScreen = true`
  - `IsRemovable`
  - icon data
  - payload identifiers / UUID / version
- WebClip 的 `URL` 指向真实 Web app，并附带 `webClip=1`。身份、安装设备 ID、观影模式等 handoff 参数追加到这个 URL，而不是写死在前端。
- 安装引导页要清楚区分“下载描述文件”和“打开 Web 应用 URL”。前者是系统配置入口，后者才是 WebClip 打开的页面。

## Display Mode Detection

不要只依赖 `matchMedia("(display-mode: standalone)")` 或 `navigator.standalone`。Managed WebClip 和恢复过程可能不稳定。

推荐顺序：

1. `?webClip=1` 或包含 `webClip` 的启动 URL。
2. 写入 sessionStorage 或同类短期标记。
3. 写入 `window.name` 或同类窗口级兜底，解决 private/opaque/sessionStorage 不稳定场景。
4. 后续路由跳转或重进时，先读短期标记，再读窗口级兜底。
5. 再检查 `navigator.standalone` 和 `matchMedia("(display-mode: fullscreen|standalone)")`。

这套逻辑必须同时存在于早期 head bootstrap 和 React runtime。早期 bootstrap 负责首帧 CSS 与 viewport，React runtime 负责后续路由和状态。

## Browser To Fullscreen User Handoff

用户先在 Safari browser 模式完成登录或安装引导，再进入 WebClip/fullscreen 时，不要依赖 browser storage 自动继承，也不要把长期 token 或 PII 写进 WebClip URL。详细流程读 `references/fullscreen-handoff.md`。

## Fullscreen Viewport Contract

- `standalone/fullscreen` 下锁定 `html/body/#root`：
  - `height: var(--app-viewport-height, 100dvh)`
  - `overflow: hidden`
  - `overscroll-behavior: none`
- iOS WebClip 重开后，`visualViewport.height` / `innerHeight` 可能短暂像普通浏览器一样变小。已验证时，可在 `web-ios + displayMode !== browser` 下用 `window.screen` 物理高度作为 viewport height 兜底。
- 输入框聚焦时不要强行覆盖 viewport shrink，避免键盘遮挡输入。
- 需要在 `pageshow`、`focus`、`visibilitychange`、`resize`、`orientationchange`、`visualViewport.resize/scroll` 后多次 schedule 同步。

## Bottom Fixed Area In Fullscreen

- 固定底栏外层贴底：`bottom: 0`。
- 外层不要再吃 bottom padding；inner 承担内容安全区 padding。
- Web 端 JS bottom padding 固定为默认值，例如 `4`；不要在 JS 中用 iOS inset 减法。
- CSS 原则：

```css
.fixed-bottom-bar {
  bottom: 0;
  padding-bottom: 0;
}

.fixed-bottom-bar__inner {
  padding-bottom: max(4px, env(safe-area-inset-bottom, 0px)) !important;
}

html[data-web-display-mode="standalone"] .fixed-bottom-bar__inner,
html[data-web-display-mode="fullscreen"] .fixed-bottom-bar__inner {
  padding-bottom: max(4px, env(safe-area-inset-bottom, 0px)) !important;
}
```

背景规则：

- 外层负责把主题背景、半透明背景或 Tab 背景铺到屏幕最底部。
- 内层负责图标/文字/按钮的可点击安全距离。
- Home Indicator 区域不应出现额外黑边、白边或透明露底。

## Pull To Refresh

Standalone/fullscreen 下全局 CSS 会锁定根滚动，浏览器原生下拉刷新不可依赖。页面如有刷新语义，应使用应用内 Web pull-to-refresh provider/hook；详细规则读 `references/pull-to-refresh.md`。

## Verification

- iPhone Safari 打开安装引导页，触发 `.mobileconfig` 下载并进入系统安装流程。
- 从桌面 WebClip 打开后无 Safari 地址栏。
- Browser 模式已登录用户进入 WebClip/fullscreen 后，能通过 handoff exchange 恢复正确用户；URL 中不残留 handoff 参数。
- handoff code 过期、重复使用、未登录、游客态都要有明确 fallback。
- 退出应用再重进，底部 Tab 仍贴底，Home Indicator 区域背景融合，无额外大黑边/空隙。
- 页面切换后仍保持 `data-web-display-mode="standalone"`。
- 键盘输入页不会因强锁 screen height 而遮住输入。
- 删除/重装 WebClip 后，profile URL、WebClip URL 和 handoff 参数仍正确。

## Official References

- Apple Web Clips payload: https://support.apple.com/guide/deployment/web-clips-payload-settings-depbc7c7808/web
- Apple Safari web app meta tags: https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariWebContent/ConfiguringWebApplications/ConfiguringWebApplications.html
- Apple Safari viewport meta: https://developer.apple.com/library/archive/documentation/AppleApplications/Reference/SafariHTMLRef/Articles/MetaTags.html
- MDN `env()` and safe-area variables: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Values/env
- MDN `display-mode`: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/%40media/display-mode
