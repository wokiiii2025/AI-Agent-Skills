# Android System Bars

适用问题：Android 真机状态栏/移动信号区遮挡、底部三键导航栏白边/黑边、底部物理按键隐藏、沉浸式页面退出后系统栏没恢复、透明 Modal 让三键区透出白底。

## Normal Route Contract

普通页面不要隐藏系统栏。目标是：

- 状态栏可见，背景与当前主题顶部区域一致。
- Android 三键/手势导航栏可见，背景与底部 Tab 或页面底部背景一致。
- 有固定底部 Tab 的页面，导航栏颜色应取底部 Tab 最底层视觉背景，而不是盲目取页面 background。
- 亮色皮肤要同步深色状态栏/导航栏图标，避免移动信号、电量、三键按钮不可见。

推荐分层：

- 主题层提供 status bar background、navigation bar background、按钮明暗策略。
- 路由层判断当前页面是否有底部 Tab、是否为沉浸式页面、是否需要特殊系统栏。
- React Native 层用 `StatusBar` 和 `expo-navigation-bar` 同步可见性、颜色和按钮样式。
- Android 原生层只补足 Expo API 无法稳定覆盖的窗口 flag、导航栏颜色、按钮明暗和沉浸式恢复。
- 冷启动层在 native theme、activity 或资源文件中给系统栏默认色，避免首帧白底/黑底闪烁。

## Immersive Routes

只有明确的沉浸式页面才隐藏系统栏，例如短视频、全屏播放器、横屏沉浸式媒体页。普通列表、详情页、登录页和弹窗不要默认隐藏系统栏。

实现要点：

- 进入时：
  - `NativeStatusBar.setHidden(true, "fade")`
  - `setAndroidImmersiveMode(true)`
  - `NavigationBar.setVisibilityAsync("hidden")`
  - `setBehaviorAsync("overlay-swipe")` 或同类临时滑出行为
  - AppState active 后再次恢复隐藏，防止切后台回来系统栏显示。
- 原生 `setImmersiveMode(true)`：
  - `WindowCompat.setDecorFitsSystemWindows(window, false)`
  - 清除 translucent flags，设置 transparent status/nav color。
  - 设置 `SYSTEM_UI_FLAG_IMMERSIVE_STICKY`、`FULLSCREEN`、`HIDE_NAVIGATION`、`LAYOUT_FULLSCREEN`、`LAYOUT_HIDE_NAVIGATION`。
  - display cutout 使用 short edges。
- 退出时：
  - `setAndroidImmersiveMode(false)`
  - `NativeStatusBar.setHidden(false)`
  - `NavigationBar.setVisibilityAsync("visible")`
  - `setBehaviorAsync("inset-touch")`
  - 原生恢复方法必须清掉所有 immersive/fullscreen/hide-navigation flags，并显式 `show(systemBars())`。

避坑：

- 隐藏 Android 三键导航栏不是底部安全区的通用解法。只有沉浸式场景才隐藏；否则应设置导航栏背景色并让内容避让。
- 进入沉浸式后要监听 AppState/生命周期，切后台再回来时系统栏可能被系统恢复，需要再次同步。
- 退出沉浸式必须恢复窗口 fitsSystemWindows、navigation bar 可见性、behavior 和按钮明暗；只恢复 JS `StatusBar` 不够。

## Transparent Modal Rule

- React Native `Modal` 可按需 `statusBarTranslucent`，但不要默认 `navigationBarTranslucent`。
- RN Modal 在 Android 上是单独 Dialog Window。部分 Vivo/Oppo/Xiaomi 真机上，开启 `navigationBarTranslucent` 会让三键导航区透出 Dialog 默认白/灰底。
- 弹窗根容器必须铺满主题背景或遮罩色。
- 如果确实需要 `navigationBarTranslucent`，必须用 Android 真机/ADB 截图验证三键区背景。

## Android Web / Chrome

Android 浏览器安全区不是 native app 系统栏。Chrome 135+ edge-to-edge 会动态改变底部可视区域和 `safe-area-inset-bottom`。Web 固定底部元素优先使用 CSS `env(safe-area-inset-bottom)` / VisualViewport 方案，不要复用 native Android 三键导航栏的 JS inset 减法。

## Expo Notes

- `expo-navigation-bar` 适合设置 Android navigation bar 的可见性、背景色和按钮样式，但并不覆盖所有 Window flag 和厂商 Dialog Window 问题。
- `expo-system-ui` 可用于设置系统 UI 背景，不能替代页面级安全区布局。
- 新增或改动原生模块、config plugin、Android window flag 后，必须重新 native build/run；Metro reload 不能验证原生变更。

## Verification

```bash
adb devices
yarn android
adb exec-out screencap -p > current.png
```

检查：

- 暗色/亮色主题状态栏图标对比度。
- 有底部 Tab 页面三键导航栏背景与 Tab 底部完全一致。
- 非底部 Tab 页面导航栏背景与页面底部一致。
- 打开/关闭透明 Modal，三键区不露白/灰。
- 进入沉浸式路由系统栏隐藏；退出或切后台回来后系统栏恢复正常。
- 手势导航和三键导航都要看；不同品牌真机可能表现不同。

## Official References

- Expo system bars: https://docs.expo.dev/develop/user-interface/system-bars/
- Expo NavigationBar: https://docs.expo.dev/versions/latest/sdk/navigation-bar/
- React Native Modal props: https://reactnative.dev/docs/modal
- Android immersive mode: https://developer.android.com/develop/ui/views/layout/immersive
- Android edge-to-edge and insets: https://developer.android.com/develop/ui/views/layout/edge-to-edge
- Android system bars design: https://developer.android.com/design/ui/mobile/guides/foundations/system-bars
