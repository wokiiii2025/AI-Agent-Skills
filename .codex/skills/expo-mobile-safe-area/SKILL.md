---
name: expo-mobile-safe-area
description: Diagnose, design, and fix Expo / React Native / Expo Router mobile safe-area, viewport, system bar, sticky or collapsible headers, fixed bottom actions/tabs, Android navigation bar, iOS Safari browser, iOS WebClip/PWA fullscreen, mobileconfig, browser-to-fullscreen handoff, pull-to-refresh, keyboard/visual viewport, and device/browser detection issues. Use when Codex works on top notch/status-bar overlap, sticky-header jank, fixed controls scrolling away, iPhone Safari address-bar collapse, bottom controls clipped during browser chrome changes, installed web app fullscreen resume, viewport-fit=cover, VisualViewport, safe-area-inset CSS env variables, or multi-platform Expo page layout.
---

# Expo Mobile Safe Area

用这个 skill 处理 Expo / React Native / Expo Router 项目里的移动端安全区、系统栏、移动 Web viewport、iOS Safari、iOS WebClip/PWA 全屏、Android 三键导航栏和底部固定栏问题。

这个 skill 是规范、标准和避坑清单，不是某个项目的代码地图。处理具体项目时，先用本 skill 建立判断框架，再读取目标项目代码、文档和变更记录来落地；不要把某个项目的文件路径、提交号或临时实现当成通用标准。

## First Steps

1. 先读目标项目入口规范，例如 `AGENTS.md`、UI/工程规范、运行脚本和已有安全区实现。
2. 修改前执行 `git status --short`，不要覆盖用户或其他 agent 的改动。
3. 先定位终端和显示模式：native Android、native iOS、iOS Safari browser、iOS standalone/fullscreen WebClip/PWA、Android Chrome browser、desktop web。
4. 用本 skill 的标准判断责任边界：根布局、页面容器、叶子组件、固定栏、系统栏、Web runtime、安装链路分别该负责什么。
5. 再检查目标项目代码和变更记录，确认已有封装、命名和测试；按现有架构落地，不复制本 skill 的示例命名。
6. 涉及 Expo、React Native、Apple、Android、Chrome 或 Web 平台行为时，优先查官方资料，并核对当前日期下的最新行为。

## Load References By Problem

- 不确定属于哪类问题，或要从症状快速定位根因：读 `references/decision-tree.md`。
- 通用安全区架构、责任边界、防重复垫高：读 `references/safe-area-architecture.md`。
- iPhone Safari 普通浏览器模式、上滑收缩底部地址栏、文档滚动、丝滑吸顶、固定底栏：读 `references/ios-safari-browser.md`。
- iOS 配置描述文件、WebClip 桌面应用、standalone/fullscreen、重开后底部固定栏：读 `references/ios-webclip-mobileconfig.md`。
- Safari 非全屏到 WebClip/fullscreen 的用户信息、登录态、设备上下文带入：读 `references/fullscreen-handoff.md`。
- Android 真机状态栏、底部三键/手势导航栏、沉浸式隐藏、透明 Modal：读 `references/android-system-bars.md`。
- 设备型号、浏览器、display mode、WebKit 媒体能力区分：读 `references/device-detection.md`。
- Expo 多端页面结构、Header、底部 Tab、播放器/全屏布局模式：读 `references/layout-patterns.md`。
- Web 首屏 meta/CSS/runtime 注入、根节点 data attribute、CSS variable、开发/生产漂移：读 `references/web-runtime-contract.md`。
- 键盘弹起、输入框遮挡、VisualViewport shrink、fixed bottom 与键盘冲突：读 `references/keyboard-viewport.md`。
- 三端下拉刷新、native `RefreshControl`、Web/PWA 自定义刷新、浏览器原生刷新冲突：读 `references/pull-to-refresh.md`。
- 快速查常见错误做法：读 `references/anti-patterns.md`。
- 改完要验收哪些真机、浏览器和状态：读 `references/verification-matrix.md`。

## Core Rules

- 安全区 padding 只在页面级或容器级做一次；叶子 Header、图标、普通业务组件不要再次叠加 `insets.top`。
- 顶部状态栏/刘海区域背景必须来自页面或主题背景，文字和按钮必须位于安全区下方。
- 底部固定栏的背景必须延伸到 bottom inset 或 Android 系统导航区；图标和文字位于可点击安全区域内。
- Web 端 `viewport-fit=cover` 以后，重要 UI 必须用 CSS `env(safe-area-inset-*)`、VisualViewport 或目标项目的 Web safe-area hook 保护。
- iOS Safari 普通浏览器模式要让 `window/document` 承担纵向滚动，才能保留地址栏随上滑自动收缩；不要把所有页面锁成内部 `ScrollView` 滚动。
- iOS Safari document scroll 下，吸顶外层和底部操作栏不能继续使用随文档移动的 `absolute`；分别使用 viewport `fixed`，并让底栏跟随 VisualViewport bottom offset。
- 高频滚动路径只读取必要的 `scrollY` 并更新动画值；不要每帧构造完整 RN 合成事件、读取整页尺寸或额外套一层会增加延迟的调度。
- iOS WebClip/PWA 全屏模式要锁住根高度，底部固定栏贴 `bottom: 0`，内部内容 padding 交给 CSS `env(safe-area-inset-bottom)`。
- Android 普通页面不要默认隐藏系统导航栏；只有短视频/播放器这类明确沉浸式路由才隐藏，并且退出时必须恢复。
- Android 透明 `Modal` 默认不要开启 `navigationBarTranslucent`；否则部分真机三键导航区会透出 Dialog 默认白/灰底。
- 不要用设备型号猜安全区尺寸；优先用 `react-native-safe-area-context`、CSS `env()`、`VisualViewport`、display mode 和运行时真实能力判断。
- 不要把 Web browser、PWA/WebClip fullscreen、native Android 的底部问题混成一种 inset 公式；它们的根滚动、系统栏和底部 viewport 行为不同。
- 下拉刷新要按 native iOS、native Android、Web browser/PWA 分开设计；不要指望 WebClip/fullscreen 的锁根布局还能使用浏览器原生下拉刷新。
- 键盘弹起时不要强行套用普通 fullscreen 高度锁定；输入可见性优先，fixed bottom 和 root height 要响应 VisualViewport/keyboard 状态。

## Verification Minimum

- TypeScript、hook、service、组件逻辑改动：跑 `npx tsc --noEmit` 和相关 Jest。
- Web 安全区、CSS 注入、iOS WebClip 改动：至少跑相关 Web safe-area、display mode、profile/mobileconfig 测试，并用 iPhone Safari 或 WebClip 真机复测。
- Android 系统栏、三键导航栏、沉浸式或 Modal 改动：必须 Android 真机构建/运行或 ADB 截图验证。
- 最终说明要写清：改了哪些文件、影响哪些终端、typecheck/tests/android device 是否通过，哪些平台未验证。
