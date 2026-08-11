# Browser To Fullscreen Handoff

适用问题：用户先在 Safari 普通浏览器模式登录、选择设备/观影模式/偏好、点击安装或打开桌面应用，然后进入 WebClip/PWA fullscreen/standalone 后需要恢复正确用户、游客态、设备上下文和目标页面。

## Best-Practice Contract

- 不要假设 Safari browser 的 `localStorage`、`sessionStorage`、内存状态或 cookie 一定会被 WebClip/fullscreen 容器稳定继承。
- 不要把 access token、refresh token、手机号、昵称、邀请码、user id 等敏感或可识别信息写入 mobileconfig、WebClip URL、manifest、日志或截图链路。
- 只允许在 URL 中放短期、一次性、不含 PII 的 opaque handoff code，以及非敏感上下文，例如 display mode 标记、return path、source。
- Fullscreen 首屏必须主动恢复会话：优先读 fullscreen 容器已有会话；没有会话时用 handoff code exchange；失败时进入登录、游客态或重新安装引导。
- Exchange 成功后立即清理 URL 中的 handoff 参数，避免进入历史、日志、分享链路。

## Recommended Flow

1. Browser 模式安装/进入全屏前，前端请求后端创建 handoff session。
2. 后端校验当前 browser 会话，生成短 TTL、一次性、绑定用户/游客态/设备/安装意图的 opaque code。
3. mobileconfig 的 WebClip `URL` 或打开全屏的跳转 URL 只携带 `webClip=1`、handoff code、return path 和必要的非敏感模式参数。
4. Fullscreen/WebClip 首屏尽早识别 `webClip=1`，写入 display mode 兜底标记。
5. Fullscreen runtime 调用后端 exchange endpoint。
6. 后端校验 code 未过期、未使用、来源/设备约束合理后，下发 fullscreen 容器自己的会话或当前用户 ViewModel。
7. 前端持久化 fullscreen 容器会话，拉取当前用户、设备、偏好、目标页面所需数据。
8. 前端用 `history.replaceState` 清理 handoff code、临时 return path 和一次性参数。
9. 后续重开 WebClip 时优先用 fullscreen 容器会话，不再依赖旧 handoff code。

## Server Requirements

- Code 必须高熵、不可预测、短 TTL、一次性消费。
- Code 对应的服务端记录保存用户/游客态、设备上下文、来源、return path、创建时间、使用时间。
- Exchange 成功后立即标记已使用；重复使用返回明确错误。
- 未登录用户和游客用户要有不同 handoff 类型，避免把游客设备上下文误升级为登录用户。
- Return path 必须做 allowlist 或同源校验，避免 open redirect。
- Exchange endpoint 不要把长期 refresh token 放在 URL 或响应日志中；按目标项目会话策略写入安全 cookie/storage 或返回短期会话材料。

## Client Requirements

- 创建 handoff 前确认当前 browser 会话状态，不要凭页面上的旧 UI 文案生成 handoff。
- Fullscreen 首屏先建立 display mode，再做业务恢复，避免 UI 按 browser 布局闪一下。
- Exchange 期间显示中性恢复状态，不要提前展示旧用户名、金币、会员态等业务信息。
- Exchange 失败要清楚区分：code 过期、code 已使用、用户未登录、网络失败、服务端拒绝、设备不匹配。
- 清理 URL 后再进入主要路由；错误页也不要保留 handoff code。

## Anti-Patterns

- `?token=...`、`?refreshToken=...`、`?userId=...`、`?phone=...`。
- mobileconfig 里写长期有效登录 URL。
- 用明文 URL 参数直接驱动用户身份、余额、会员态、邀请关系。
- 只在 browser 里写 storage，然后假设 WebClip 一定能读到。
- handoff code 可重复使用、不过期、没有绑定来源或设备上下文。
- exchange 成功后不清 URL。

## Verification

- 已登录 browser 用户进入 fullscreen 后恢复同一用户，会话来自 exchange 结果而不是 URL 明文。
- 游客 browser 用户进入 fullscreen 后仍是游客态，不误认为登录用户。
- Code 过期、重复使用、伪造、缺失时都有明确 fallback。
- Exchange 成功后 URL 不再包含 handoff code。
- 退出 WebClip 再进入时使用 fullscreen 容器自己的会话，不重复消费旧 code。
- 服务端日志、前端日志、崩溃日志不输出 token、PII 或完整敏感 URL。

## References

- Apple Web Clips payload: https://support.apple.com/guide/deployment/web-clips-payload-settings-depbc7c7808/web
- OWASP query string exposure: https://owasp.org/www-community/vulnerabilities/Information_exposure_through_query_strings_in_url
- RFC 9700 OAuth 2.0 Security Best Current Practice: https://datatracker.ietf.org/doc/rfc9700/
