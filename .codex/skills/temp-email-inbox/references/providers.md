# Temporary email providers

Source checks performed August 2026. Free temp-mail providers change frequently; verify endpoints during use.

## tempmailc

Base: `https://tempmailc.com/api/v1`

- `GET /new` creates a random address.
- `GET /domains` lists domains.
- `GET /inbox?email=ADDRESS` lists messages.
- `GET /message?email=ADDRESS&msg_id=ID` reads one message.
- `DELETE /message?email=ADDRESS&msg_id=ID` deletes one message.
- No authentication.

## catchmail

Base: `https://api.catchmail.io/api/v1`

- Mailbox addresses can be chosen locally, usually `random@catchmail.io`.
- `GET /mailbox?address=ADDRESS` lists messages.
- `GET /message/ID?mailbox=ADDRESS` reads one message.
- `DELETE /message/ID?mailbox=ADDRESS` deletes one message.
- No authentication.

## mail.tm

Base: `https://api.mail.tm`

- `GET /domains` lists available domains.
- `POST /accounts` with `address` and `password` creates an account.
- `POST /token` returns a bearer token.
- `GET /messages` lists messages with `Authorization: Bearer TOKEN`.
- `GET /messages/ID` reads a message with the same bearer token.
- `DELETE /messages/ID` deletes one message with the same bearer token.

## mail.cx

Base: `https://api.mail.cx/v1`

- Requires header `x-api-token: $MAIL_CX_TOKEN`.
- No mailbox create call is needed; choose an address on an accepted domain.
- `GET /inbox/ADDRESS` lists or long-polls messages.
- `GET /email/ID` reads one message.
- `GET /email/ID/raw` returns raw `.eml`.
- `DELETE /email/ID` deletes one message.
