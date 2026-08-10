---
name: temp-email-inbox
description: Create and use free temporary email inboxes through HTTP REST APIs for QA, signup/reset/OTP testing, and automation. Use when Codex needs disposable email addresses, multi-provider temp-mail receiving, polling inboxes, reading email bodies, extracting OTP codes, or validating that a test email was delivered without using a real mailbox. Supports tempmailc, catchmail, mail.tm, and mail.cx adapters.
---

# Temp Email Inbox

Use this skill to create disposable test inboxes and receive email through provider REST APIs.

## Default workflow

1. Prefer no-auth providers first: `tempmailc`, then `catchmail`.
2. Use `mailtm` when an account-backed mailbox and bearer-token flow is useful.
3. Use `mailcx` when `MAIL_CX_TOKEN` is present or `config/providers.json` contains `mailcx.token`. Environment variables override config values.
4. Run `scripts/temp_inbox.py create --provider PROVIDER` to obtain an address.
5. Trigger the app flow that sends email to that address.
6. Run `scripts/temp_inbox.py wait --provider PROVIDER --address ADDRESS --timeout 120 --otp` to poll, read the matched message, extract a code when requested, then delete the message by default.
7. Use `scripts/temp_inbox.py read --provider PROVIDER --address ADDRESS --id MESSAGE_ID` for full message content; `read` deletes the message after successful retrieval by default. Use `--keep` only when debugging and a retained message is explicitly needed.

## Provider selection

- `tempmailc`: no auth, generated mailbox, short retention; best default.
- `catchmail`: no auth, generated `@catchmail.io` mailbox, simple list/read endpoints.
- `mailtm`: no API key; creates a mailbox account and password, then uses JWT bearer token. Preserve the `password`/`token` fields returned by `create` for later calls.
- `mailcx`: requires `MAIL_CX_TOKEN` or `config/providers.json` `mailcx.token`; supports long-polling-style inbox endpoint. Generate an address locally or pass a chosen address.

Read `references/providers.md` only when endpoint details or provider caveats are needed.

## Local provider config

Store editable provider credentials in `config/providers.json` inside this skill folder. Keep `config/providers.example.json` as the non-secret template. Environment variables override config values for one-off runs.

```json
{
  "mailcx": {
    "token": "tm_live_REPLACE_ME"
  }
}
```

## Script examples

```bash
python scripts/temp_inbox.py create --provider tempmailc
python scripts/temp_inbox.py inbox --provider tempmailc --address user@domain
python scripts/temp_inbox.py wait --provider tempmailc --address user@domain --timeout 120 --interval 5 --otp
python scripts/temp_inbox.py read --provider tempmailc --address user@domain --id MESSAGE_ID
python scripts/temp_inbox.py delete --provider tempmailc --address user@domain --id MESSAGE_ID
python scripts/temp_inbox.py test --provider tempmailc
```

The script prints JSON for every command. For automation, parse `email`, `messages`, `message`, `otp`, and `deleted`.

## Delete-after-read requirement

Always remove received messages after extracting the needed information. The CLI enforces this by default:

- `read` performs read-then-delete unless `--keep` is passed.
- `wait` performs inbox polling, reads the matched or first message, then deletes it unless `--keep` is passed.
- `delete` is available for explicit cleanup.
- Treat `deleted: true` as the expected completion state. If a provider delete call fails, inspect `delete_error` and retry `delete` manually.

Provider delete endpoints used by the script:

- `tempmailc`: `DELETE /api/v1/message?email=ADDRESS&msg_id=ID`
- `catchmail`: `DELETE /api/v1/message/ID?mailbox=ADDRESS`
- `mailtm`: `DELETE /messages/ID` with bearer token
- `mailcx`: `DELETE /email/ID` with configured token

## Validation expectations

When changing this skill, validate with:

```bash
python scripts/temp_inbox.py test --provider tempmailc
python scripts/temp_inbox.py test --provider catchmail
python scripts/temp_inbox.py test --provider mailtm
python C:/Users/Administrator/.codex/skills/.system/skill-creator/scripts/quick_validate.py C:/Users/Administrator/.codex/skills/temp-email-inbox
```

Skip `mailcx` tests unless `MAIL_CX_TOKEN` is configured.
