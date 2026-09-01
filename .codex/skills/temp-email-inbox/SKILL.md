---
name: temp-email-inbox
description: Create and use free temporary email inboxes through HTTP REST APIs for QA, signup/reset/OTP testing, and automation. Use when Codex needs disposable email addresses, multi-provider temp-mail receiving, polling inboxes, reading email bodies, extracting OTP codes, or validating that a test email was delivered without using a real mailbox. Supports the private xxpo.cc.cd mailbox API as the bold/default first option, plus tempmailc, catchmail, mail.tm, and mail.cx adapters.
---

# Temp Email Inbox

Use this skill to create disposable test inboxes and receive email through provider REST APIs.

## Default workflow

**1. 默认首选 `xxpo` 私有邮箱 API（`https://xxpo.cc.cd/api`）：用于 AI agent 自动创建别名、轮询最新邮件，并优先读取接口返回的 `code` 验证码字段。**
2. 只有当 `xxpo` 不适合当前任务或不可用时，再使用 no-auth providers：`tempmailc`，然后 `catchmail`。
3. Use `mailtm` when an account-backed mailbox and bearer-token flow is useful.
4. Use `mailcx` when `MAIL_CX_TOKEN` is present or `config/providers.json` contains `mailcx.token`. Environment variables override config values.
5. Run `scripts/temp_inbox.py create --provider PROVIDER` to obtain an address; because `xxpo` is the CLI default, `python scripts/temp_inbox.py create` creates an `@xxpo.cc.cd` mailbox unless another provider is specified.
6. Trigger the app flow that sends email to that address.
7. Run `scripts/temp_inbox.py wait --provider PROVIDER --address ADDRESS --timeout 120 --otp` to poll, read the matched message, and extract a code when requested. For `xxpo`, pass `--account-id ACCOUNT_ID` from `create` when available to target that alias.
8. Use `scripts/temp_inbox.py read --provider PROVIDER --address ADDRESS --id MESSAGE_ID` for full message content; `read` deletes the message after successful retrieval by default when the provider supports deletion. Use `--keep` only when debugging and a retained message is explicitly needed.

## Provider selection

- **`xxpo`：默认第一选项，私有邮箱 API。Base `https://xxpo.cc.cd/api`；`POST /login` 获取 token；`POST /account/add` 创建任意前缀别名；`GET /email/latest?accountId=ID` 轮询最新邮件；当前后端若管理员 token 访问 `/email/*` 返回非 200（实测可能出现 401 或 D1_TYPE_ERROR 500），则自动回退到 `GET /allEmail/list?page=1&size=50` 管理员全局列表；优先使用响应里的 `code` 字段作为验证码，无需自行正则。实测当前后端要求 `Authorization: <TOKEN>` 裸 token；如接口后续兼容 Bearer 再按文档切换。**
- `tempmailc`: no auth, generated mailbox, short retention; use only when `xxpo` is unavailable or a public disposable mailbox is preferred.
- `catchmail`: no auth, generated `@catchmail.io` mailbox, simple list/read endpoints.
- `mailtm`: no API key; creates a mailbox account and password, then uses JWT bearer token. Preserve the `password`/`token` fields returned by `create` for later calls.
- `mailcx`: requires `MAIL_CX_TOKEN` or `config/providers.json` `mailcx.token`; supports long-polling-style inbox endpoint. Generate an address locally or pass a chosen address.

Read `references/providers.md` only when endpoint details or provider caveats are needed.

## xxpo 多域名邮箱

`xxpo` 支持在同一 API 下创建多个已绑定域名的邮箱别名。默认域名是 `xxpo.cc.cd`；需要指定其他域名时，使用环境变量或配置：

- 临时指定：`XXPO_DOMAIN=apice.cc.cd python scripts/temp_inbox.py create`
- 指定完整邮箱：`python scripts/temp_inbox.py create --address agent-test@apice.cc.cd`

实测已可创建：

- `@xxpo.cc.cd`
- `@apice.cc.cd`

域名列表接口当前返回鉴权异常或 404；不要依赖自动发现域名，优先使用用户指定的完整邮箱地址或 `XXPO_DOMAIN`。

## xxpo 实测字段兼容

当前 `xxpo` 后端实测字段与文档存在少量差异，脚本已兼容：

- 创建邮箱返回字段是 `accountId`，脚本归一化为 `account_id`。
- 收件列表里的发件人字段是 `sendEmail`，脚本归一化为 `from`。
- 收件地址字段是 `toEmail`，脚本归一化为 `to` 并用于按地址过滤。
- 邮件 ID 字段是 `emailId`，脚本归一化为 `id`，接收后用它调用删除接口。
- `code` 可能是空字符串；为空时再回退到正文正则提取 OTP。
- 管理员 token 访问 `/email/latest?accountId=ID` 可能返回 401 或 D1 500；脚本会回退到 `/allEmail/list?page=1&size=50` 并继续按 `toEmail` / 地址过滤。

## Local provider config

Store editable provider credentials in `config/providers.json` inside this skill folder. Keep `config/providers.example.json` as the non-secret template. Environment variables override config values for one-off runs.

```json
{
  "xxpo": {
    "base_url": "https://xxpo.cc.cd/api",
    "admin_email": "admin@xxpo.cc.cd",
    "password": "REPLACE_ME",
    "domain": "xxpo.cc.cd"
  },
  "mailcx": {
    "token": "tm_live_REPLACE_ME"
  }
}
```

## Script examples

```bash
python scripts/temp_inbox.py create
python scripts/temp_inbox.py inbox --address user@xxpo.cc.cd --account-id 12
python scripts/temp_inbox.py wait --address user@xxpo.cc.cd --account-id 12 --timeout 120 --interval 3 --otp
python scripts/temp_inbox.py create --provider tempmailc
python scripts/temp_inbox.py wait --provider tempmailc --address user@domain --timeout 120 --interval 5 --otp
python scripts/temp_inbox.py read --provider tempmailc --address user@domain --id MESSAGE_ID
python scripts/temp_inbox.py delete --provider tempmailc --address user@domain --id MESSAGE_ID
python scripts/temp_inbox.py test --provider xxpo
python scripts/temp_inbox.py test --provider tempmailc
```

The script prints JSON for every command. For automation, parse `email`, `account_id`, `messages`, `message`, `otp`, `code`, and `deleted`. For `xxpo`, prefer the API-provided `code` field over regex-derived OTP.

## Delete-after-read requirement

接收完必须删除邮件。Always remove received messages after extracting the needed information when the provider exposes a delete endpoint. The CLI enforces this by default for providers that support deletion:

- `read` performs read-then-delete unless `--keep` is passed.
- `wait` performs inbox polling, reads the matched or first message, then deletes it unless `--keep` is passed.
- `delete` is available for explicit cleanup.
- Treat `deleted: true` as the expected completion state. If a provider delete call fails, inspect `delete_error` and retry `delete` manually.

Provider delete endpoints used by the script:

- `xxpo`: `DELETE /email/delete?emailIds=ID` after reading; admin-global fallback also supports `DELETE /allEmail/delete?emailIds=ID`.
- `tempmailc`: `DELETE /api/v1/message?email=ADDRESS&msg_id=ID`
- `catchmail`: `DELETE /api/v1/message/ID?mailbox=ADDRESS`
- `mailtm`: `DELETE /messages/ID` with bearer token
- `mailcx`: `DELETE /email/ID` with configured token

## Validation expectations

When changing this skill, validate with:

```bash
python scripts/temp_inbox.py test --provider xxpo
python scripts/temp_inbox.py test --provider tempmailc
python scripts/temp_inbox.py test --provider catchmail
python scripts/temp_inbox.py test --provider mailtm
python C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/Administrator/.codex/skills/temp-email-inbox
```

Skip `mailcx` tests unless `MAIL_CX_TOKEN` is configured.
