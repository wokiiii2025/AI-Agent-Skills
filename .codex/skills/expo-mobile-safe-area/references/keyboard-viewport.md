# Keyboard And Visual Viewport

适用问题：输入框被键盘遮挡、底部固定栏被键盘顶飞、WebClip/fullscreen 输入页高度异常、iOS Safari/Android Chrome 键盘弹起后 fixed 元素错位。

## Core Rules

- 输入可见性优先于 fullscreen root height 稳定性。
- 键盘可见时，不要继续强行使用物理屏幕高度兜底。
- fixed bottom action bar 在输入页要有明确策略：隐藏、变成键盘上方 sticky action，或随内容滚动。
- 键盘状态要和 safe-area、VisualViewport、root lock、document scroll 一起处理。

## Native iOS / Android

- 简单表单可使用 React Native `KeyboardAvoidingView`。
- 复杂滚动表单优先让内容区可滚动，聚焦输入时滚到可见区域。
- Android 行为受 window resize/pan、手势导航、三键导航、厂商系统影响，必须真机验证。
- 不要让底部 Tab、提交按钮、错误提示和键盘互相覆盖。
- Modal 内输入框要单独验证，尤其是 Android Dialog Window。

## Web Browser

- 键盘弹起可能只缩小 VisualViewport，不改变 Layout Viewport。
- 用 `visualViewport.height`、`visualViewport.offsetTop`、`visualViewport.resize/scroll` 计算可见区域。
- iOS Safari browser 仍要保留 document scroll 能力，不要为了键盘把页面锁死成内部滚动。
- 输入聚焦时可以暂停地址栏/底部栏的部分动画修正，避免和键盘 resize 抢布局。

## WebClip / PWA Fullscreen

- 输入聚焦时不要使用 `window.screen.height` 强压 `--app-viewport-height`。
- root lock 可以保留，但输入容器必须能滚动到可见区域。
- fixed bottom bar 在输入页通常应隐藏或转为键盘上方操作栏。
- `pageshow`、`focus`、`blur`、`visibilitychange`、VisualViewport 事件后都要重新同步高度。

## Anti-Patterns

- 键盘弹起时仍用 fullscreen 物理屏幕高度覆盖 VisualViewport。
- 所有页面都套同一个 `KeyboardAvoidingView`，导致非输入页或 Android 页面异常抖动。
- fixed bottom 提交按钮既不隐藏也不上移，直接挡住输入框。
- 输入错误提示出现在键盘下方，用户看不到。
- 只在 iOS 模拟器验证键盘，不看 Android 三键/手势真机。

## Verification

- 首个、最后一个输入框都能聚焦并保持可见。
- 键盘打开时提交按钮策略符合设计，不遮挡输入。
- 键盘收起后 bottom fixed、安全区 padding、root height 恢复。
- Safari browser 输入页仍能正常上滑收缩地址栏或至少不破坏主滚动。
- WebClip/fullscreen 退出再进后输入页高度稳定。

## Official References

- Expo keyboard handling: https://docs.expo.dev/guides/keyboard-handling/
- React Native KeyboardAvoidingView: https://reactnative.dev/docs/keyboardavoidingview
- MDN VisualViewport: https://developer.mozilla.org/en-US/docs/Web/API/VisualViewport
- MDN VirtualKeyboard API: https://developer.mozilla.org/en-US/docs/Web/API/VirtualKeyboard_API
- Chrome viewport resize behavior: https://developer.chrome.com/blog/viewport-resize-behavior
