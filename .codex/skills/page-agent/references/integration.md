# Integration notes

## What Page Agent is for

Use Page Agent when the user wants a web page to respond to natural-language GUI instructions, such as form filling, admin workflows, SaaS copilots, accessibility commands, and page-local UI automation.

## Integration paths

### CDN demo path

The README advertises a one-line script for technical evaluation using a demo LLM endpoint. Verify the latest version before using it:

```bash
npm view page-agent version
```

Then check the upstream README for the current `page-agent.demo.js` URL.

Use this path only for quick evaluation, not production.

### npm / application path

For a production app or local project:

```bash
npm install page-agent
```

Then import `PageAgent` in the app and configure the model provider according to upstream docs.

## Implementation checklist

- Confirm framework: plain HTML, React, Vue, Next.js, etc.
- Confirm whether the agent should run only on one page or across tabs.
- Confirm model provider and whether keys live server-side or client-side.
- Keep secrets out of committed files; prefer environment variables or backend proxy endpoints.
- Add a small demo route/component first, then expand.
- Validate with a real browser interaction, not only type checks.
