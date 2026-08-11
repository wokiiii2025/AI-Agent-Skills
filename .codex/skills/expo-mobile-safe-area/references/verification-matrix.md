# Verification Matrix

适用问题：完成安全区、系统栏、WebClip、handoff 或多端布局修改后，需要确定最低验收范围和不能替代的真机检查。

## Device And Mode Matrix

| Target | Must Verify | Cannot Substitute With |
| --- | --- | --- |
| iPhone Safari browser | 上滑收缩底部地址栏；主纵向 document scroll；底部 fixed 不裁剪；切路由回顶 | 桌面 Chrome 响应式 iPhone |
| iPhone WebClip fullscreen | 无 Safari 地址栏；根高度稳定；底部栏贴底；Home Indicator 背景融合；退出再进仍稳定 | 普通 Safari browser |
| iPhone WebClip handoff | browser 已登录/游客进入 fullscreen 后恢复正确会话；URL 清理；过期/重复 code fallback | 只看 UI 是否显示用户名 |
| Android native 三键导航 | 状态栏/导航栏颜色和主题一致；底部三键区不露白/黑；Modal 不露 Dialog 默认色 | Android 手势导航 |
| Android native 手势导航 | bottom inset 不遮挡内容；导航栏/手势区域背景融合；沉浸式退出恢复 | Android 三键导航 |
| Android immersive route | 进入隐藏系统栏；滑出行为正确；切后台回来仍隐藏；退出完整恢复 | 普通页面系统栏检查 |
| Android Chrome browser | fixed bottom 使用 CSS safe-area/VisualViewport；Chrome edge-to-edge 下不露底 | native Android safe-area 结果 |
| Desktop web | 不被 mobile CSS 锁死；滚动、固定栏、宽屏布局正常 | 移动真机 |
| iPad / tablet / landscape | left/right inset、横屏刘海、分屏高度、播放器 controls | iPhone portrait |
| Keyboard input | iOS/Android 键盘弹起时输入不被锁高遮挡；恢复后底部 fixed 正常 | 无输入框页面 |
| Pull-to-refresh native iOS/Android | 顶部下拉只在滚动到顶时触发；刷新状态受控；刷新中切路由不残留 spinner | Web pull-to-refresh |
| Pull-to-refresh Web/PWA | browser 模式不破坏地址栏收缩；fullscreen/WebClip 使用自定义刷新；失败 fallback 明确 | native `RefreshControl` |
| Web runtime first paint | 首屏就有正确 meta、data attribute、CSS variable、root lock/document scroll 策略 | 只看 React hydrate 后的状态 |

## Visual Checks

- 顶部交互元素不进入刘海、状态栏、移动信号区。
- 顶部安全区背景与页面顶部视觉一致。
- 底部 fixed 外层铺满到屏幕最底部。
- 底部 fixed 内层给按钮、Tab item、文字留出可点击安全距离。
- Home Indicator 或 Android 三键区域不出现孤立黑边、白边、透明底。
- 暗色/亮色主题下状态栏和导航栏图标对比度足够。
- 页面切换、返回、切后台再回来后布局不漂移。

## Functional Checks

- iOS Safari browser 的主纵向滚动发生在 `window/document`，不是只在内部 scroll view。
- iOS Safari browser 下地址栏收缩过程中 fixed bottom 跟随 VisualViewport。
- iOS Safari browser 下吸顶外层计算值为 fixed；跨过收起区间后 tabs 的 viewport top 精确落在目标位置。
- 详情 CTA、阅读工具栏在页面首屏就可见，不需要滚到文档末尾；主内容末项不被固定栏遮挡。
- WebClip/fullscreen 下根高度锁定，页面不会因为地址栏假高度产生底部空洞。
- Browser 到 fullscreen handoff 成功后，业务状态来自服务端 exchange，不来自 URL 明文。
- Android 沉浸式页面退出后，system bars、window flags、button style 全部恢复。
- Android transparent Modal 不默认开启 `navigationBarTranslucent`，除非真机验证通过。
- 下拉刷新不会和顶部安全区、sticky header、document scroll、PWA root lock、Android Chrome 原生刷新互相打架。
- 键盘弹起时输入框、提交按钮、错误提示可见；键盘收起后 root height、bottom fixed、safe-area padding 恢复。

## Automated Tests To Prefer

- Terminal detection：native/web-ios/web-android/web-pc。
- Display mode detection：browser/standalone/fullscreen/query/session/window fallback。
- WebClip handoff：success、expired、used twice、missing code、guest、authenticated。
- URL cleanup：exchange 成功/失败后不残留敏感参数。
- Web CSS contract：`viewport-fit=cover`、safe-area `env()`、document scroll class/data attribute、fullscreen root lock。
- Bottom fixed layout：outer no padding, inner owns safe-area padding。
- Collapsible header：document-scroll 路径直接消费 scrollY、监听清理、collapse distance 与布局高度一致。
- VisualViewport contract：改变 bottom-offset CSS variable 后，fixed bottom 按相同像素量移动。
- Android system bar routing：普通页、底部 Tab 页、沉浸式页、Modal。
- Pull-to-refresh：native `refreshing/onRefresh` 受控、Web refresh handler 注册/注销、重复触发去重、失败后状态复位。
- Keyboard viewport：focus/blur、VisualViewport resize/scroll、输入页 fixed bottom 策略、键盘关闭后状态复位。

## Delivery Notes

最终说明要明确：

- 影响了哪些目标：native Android、iOS Safari browser、iOS WebClip/fullscreen、Android Chrome、desktop web。
- 哪些命令通过：typecheck、lint、unit tests、build。
- 哪些真机验证通过：设备型号、系统版本、浏览器、display mode、三键/手势导航。
- 哪些未验证以及原因。
