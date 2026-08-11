# Symptom Decision Tree

适用问题：已经看到一个 UI/安全区/系统栏/WebClip 现象，需要快速判断该读哪个 reference、先查哪一层、优先修哪里。

## Quick Routing

| Symptom | First Read | Likely Root Cause | First Checks |
| --- | --- | --- | --- |
| 顶部内容被刘海、状态栏、移动信号区遮挡 | `safe-area-architecture.md`, `layout-patterns.md` | top inset owner 不明确，Header 叶子组件/页面 wrapper 责任混乱 | 根布局是否有 `SafeAreaProvider`；页面级 wrapper 是否加 top inset；Header 内部是否二次加 inset |
| 顶部背景和状态栏区域断层 | `safe-area-architecture.md`, `android-system-bars.md` | 状态栏背景未取页面顶部真实视觉背景 | 状态栏颜色、图标明暗、overlay header 背景、冷启动默认色 |
| 底部 Home Indicator 区域黑边/白边/透明露底 | `safe-area-architecture.md`, `layout-patterns.md`, `ios-webclip-mobileconfig.md` | 固定栏外层未铺到底，内外层 padding 职责反了 | 固定栏 outer 是否贴底铺背景；inner 是否用 bottom inset；Web CSS 是否用 `env()` |
| Android 三键导航区白底/灰底 | `android-system-bars.md` | navigation bar 颜色未同步，或透明 Modal Dialog Window 露底 | 普通页导航栏颜色；有底部 Tab 页面取 Tab 底色；Modal 是否开了 `navigationBarTranslucent` |
| Android 底部物理按键需要隐藏 | `android-system-bars.md` | 把沉浸式需求误用到普通页面，或退出恢复不完整 | 是否确实是短视频/播放器等沉浸式页面；进入/退出 flag 是否成对；AppState 恢复是否同步 |
| iPhone Safari 非全屏上滑后底部地址栏不收缩 | `ios-safari-browser.md` | 主纵向滚动被锁在内部 `ScrollView`，window/document 没滚动 | `html/body/#root` 是否锁高；主滚动容器是否 document-aware；是否只给单页写了特例 |
| iPhone Safari 吸顶导航滚走、停不住或位置差几像素 | `ios-safari-browser.md`, `layout-patterns.md` | document scroll 下仍用 `absolute`；收起距离与顶部行真实高度不一致 | 吸顶外层是否 viewport `fixed`；滚动后 `getBoundingClientRect().top`；collapse distance 与布局高度 |
| iPhone Safari 吸顶动画比同项目其他页面卡或晚一帧 | `ios-safari-browser.md` | scrollY 经多层转发、完整 RN 合成事件或多余 rAF 后才更新 Animated.Value | 对比流畅基准页监听链路；高频回调是否只读 scrollY；是否每帧读 scrollHeight/clientHeight |
| iPhone Safari 地址栏收缩时底部 Tab 被裁剪 | `ios-safari-browser.md` | fixed bottom 没跟随 VisualViewport bottom offset | 是否监听 `visualViewport.resize/scroll`；fixed bottom 是否使用 viewport offset 变量；底部背景是否有补底 |
| 详情/阅读页按钮只在滚到底后出现 | `ios-safari-browser.md`, `layout-patterns.md` | 底栏是文档末尾 `absolute`，不是 viewport fixed；内容未预留栏高 | 首屏 `getBoundingClientRect()`；position 计算值；主内容 paddingBottom |
| iOS WebClip 打开不是全屏 | `ios-webclip-mobileconfig.md`, `device-detection.md` | WebClip payload 或 display mode 识别不完整 | mobileconfig `FullScreen`；WebClip URL；`navigator.standalone`/display-mode/query/session/window 标记 |
| WebClip 退出再进后底栏漂移或大黑边 | `ios-webclip-mobileconfig.md` | fullscreen viewport height 首帧不稳定，bottom padding 双重计算 | 根高度锁定；iOS fullscreen 下 screen height fallback；outer/inner padding 职责 |
| 非全屏已登录，进入全屏后用户丢失 | `fullscreen-handoff.md` | 依赖 Safari browser storage/cookie 自动继承，没有 handoff exchange | 是否有一次性 handoff code；exchange 是否成功；URL 是否清理；失败 fallback |
| 首屏闪一下、开发正常生产错位 | `web-runtime-contract.md` | head bootstrap、runtime CSS、生产注入不一致或执行太晚 | viewport meta；root data attribute；CSS variable；生产构建注入来源 |
| 输入框被键盘遮挡或底部栏顶飞 | `keyboard-viewport.md` | 键盘状态下仍强锁 fullscreen 高度，或 native/Web 键盘避让混用 | VisualViewport/keyboard events；focus 状态；fixed bottom 是否隐藏/上移；输入容器是否 scrollable |
| 下拉刷新在 iOS/Android 原生不触发 | `pull-to-refresh.md` | `refreshing` 不是受控状态，滚动容器不在顶部，或嵌套滚动/高度错误 | `refreshing/onRefresh`；ScrollView/FlatList 高度；是否只在 `scrollY=0` 触发；是否被横向/嵌套滚动抢手势 |
| WebClip/PWA 下拉刷新无效 | `pull-to-refresh.md`, `ios-webclip-mobileconfig.md` | fullscreen 锁根后浏览器原生刷新不可用，没有注册自定义刷新 | display mode；root lock；页面是否注册 refresh handler；gesture threshold/fallback |
| Android Chrome 下拉触发整个页面 reload | `pull-to-refresh.md` | 浏览器原生 pull-to-refresh 没被隔离，应用自定义刷新与原生刷新冲突 | `overscroll-behavior`；document scroll owner；是否需要禁用原生刷新并接管 |
| Chrome 响应式 iPhone 和真机结果不一致 | `device-detection.md` | 把 UA 模拟当成真实设备能力 | 是否区分 layout terminal、display mode、媒体能力、安装能力；是否有真机验证 |
| 播放器全屏控制栏顶部太高或被遮挡 | `layout-patterns.md`, `device-detection.md` | inline/fullscreen 两套 safe area owner 混用 | 非全屏由页面/容器处理；fullscreen controls 才加 top inset；媒体能力判断不要复用布局判断 |

## Triage Order

1. 先确认终端：native Android、native iOS、iOS Safari browser、iOS WebClip/PWA fullscreen、Android Chrome browser、desktop web。
2. 再确认 display mode：browser、standalone、fullscreen。
3. 再确认 owner：top inset、bottom inset、system bar color、fixed bottom background 分别由哪一层负责。
4. 最后查实现：目标项目已有 hook/service/component、CSS 注入、native module、测试和历史变更。

## Fix Order

1. 先修责任边界，避免继续叠 padding。
2. 再修平台 runtime：Web data attributes、VisualViewport、Android system bars、WebClip detection。
3. 再修具体组件：Header、bottom tab、modal、player controls。
4. 最后补测试和真机验收。

## Do Not Start With

- 不要先写设备型号分支。
- 不要先用 magic number 垫高。
- 不要把 Android native 三键导航栏和 Android Chrome browser bottom viewport 当成同一种问题。
- 不要用桌面 Chrome 响应式模式替代 iPhone Safari/WebClip 真机。
- 不要通过把 token 放进 URL 解决 browser 到 fullscreen 的用户带入。
- 不要只改 React runtime 而漏掉 head/bootstrap/生产注入。
