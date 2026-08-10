---
name: page-agent
description: "Use when Codex needs to integrate, evaluate, install, or control Alibaba Page Agent: a JavaScript in-page GUI agent for web applications, Chrome extension, and MCP server. Trigger for requests mentioning alibaba/page-agent, Page Agent, in-page GUI agent, natural-language web UI control, SaaS AI copilot, smart form filling, Page Agent Chrome extension, or Page Agent MCP server."
---

# Page Agent

Page Agent is not a Codex skill itself. It is a JavaScript/TypeScript project from `alibaba/page-agent` that lets a web page expose an AI GUI agent through in-page JavaScript, an optional Chrome extension, and an MCP server.

## Default workflow

1. Identify the user's goal:
   - **Embed in a web page / SaaS copilot**: use the JS SDK path.
   - **Control existing browser tabs / multi-page tasks**: use the Chrome extension path.
   - **Let external agent clients control browser pages**: use the MCP server path.
   - **Maintain the upstream repo**: use the upstream `.agents/skills/*` skills if present in the current repo.
2. Check current upstream docs before exact commands or version pins:
   - GitHub: `https://github.com/alibaba/page-agent`
   - Docs: `https://alibaba.github.io/page-agent/`
   - npm: `page-agent`
3. Prefer read-only inspection before modifying a user's app.
4. For live browser control, confirm the extension/MCP session is intentionally running and target the user's selected page/tab.

## Quick command reference

```bash
# Package metadata
npm view page-agent version description

# App integration
npm install page-agent

# Repository inspection
gh repo view alibaba/page-agent
gh repo clone alibaba/page-agent
```

Minimal SDK shape from the README:

```js
import { PageAgent } from 'page-agent'

const agent = new PageAgent({
  // Configure model/provider and options according to upstream docs.
})
```

## When to read references

- Read `references/integration.md` for SDK/CDN integration and implementation notes.
- Read `references/chrome-extension-and-mcp.md` for Chrome extension and MCP usage decisions.
- Read `references/upstream-skills.md` when syncing or using the upstream repository's own `.agents/skills`.

## Boundaries

- Do not treat `alibaba/page-agent` as a drop-in Codex skill package.
- Do not invent Page Agent APIs; verify exact versioned API names from upstream docs or package sources.
- Do not save API keys, model tokens, browser cookies, or Page Agent runtime credentials in a skill repository.
