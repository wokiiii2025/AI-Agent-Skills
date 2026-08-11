# Anti-Patterns

适用问题：快速检查方案里是否有高概率导致多端安全区、系统栏、WebClip、刷新或键盘问题的做法。

## Safe Area

- 用设备型号、屏幕高度、品牌写死 safe area。
- 页面 wrapper 和 Header 叶子组件都加 top inset。
- CSS `env(safe-area-inset-bottom)` 和 JS bottom inset 双重叠加。
- 安全区 spacer 背景色和页面/Tab 真实背景不一致。

## Web Runtime

- 只在 React mount 后修正 meta/CSS，首屏先错位再跳正。
- 开发模板、runtime 注入、生产构建注入各写一份 CSS。
- browser、standalone、fullscreen 共用同一套 root height 和 scroll lock。
- iOS Safari browser 被锁成内部滚动，导致地址栏不收缩。
- document scroll 模式仍把吸顶 Header 或底部按钮设为页面内 `absolute`，导致它们随整页滚走或只在文档末尾出现。
- 为了驱动一个吸顶动画，每次滚动都读取 `scrollHeight`、`scrollWidth`、`clientHeight` 并构造完整 RN 合成事件。
- React Native `Animated.Value` 已经在下一次绘制提交 transform，却再用 `requestAnimationFrame` 包一层 scroll 转发，造成额外一帧跟手延迟。
- 吸顶收起距离写死为近似值，和实际顶部行高度不一致，最终导航停在 `-4px` 或留出缝隙。
- 每个详情页、阅读页分别复制一套 fixed bottom 与 safe-area 公式，造成地址栏动画行为不一致。

## Android

- 普通页面默认隐藏三键导航栏。
- 底部三键区露白后只给页面加 spacer，不同步 navigation bar color。
- 透明 `Modal` 默认开启 `navigationBarTranslucent`。
- 进入沉浸式后退出只恢复 JS 状态栏，不清 native Window flags。

## WebClip / Handoff

- 把 token、refresh token、user id、手机号、昵称写进 URL 或 mobileconfig。
- 依赖 Safari browser storage 一定能被 WebClip 继承。
- handoff code 长期有效、可重复使用或不清 URL。
- mobileconfig 下载地址和 WebClip 打开的 Web app URL 混淆。

## Pull To Refresh

- native 和 Web/PWA 共用一套手势实现。
- PWA/fullscreen 锁根后仍依赖浏览器原生下拉刷新。
- `refreshing` 失败、取消、离开页面后不复位。
- 下拉刷新和加载更多共用一个 `loading` 状态。

## Keyboard

- 键盘弹起时仍强行套 fullscreen 物理屏幕高度。
- fixed bottom 提交按钮遮住输入框或错误提示。
- 所有页面统一包 KeyboardAvoidingView，导致非输入页抖动。
- 只验证 iOS，不验证 Android 三键/手势导航和 Modal 输入。

## Verification

- 用桌面 Chrome 响应式模式替代 iPhone Safari/WebClip 真机。
- 用 Web 预览替代 Android 真机构建。
- 改原生依赖或 Window flags 后只重启 Metro。
- 只看默认主题，不看亮色/暗色、横屏、键盘、切后台恢复。
