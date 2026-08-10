# Chrome extension and MCP notes

Page Agent includes an optional Chrome extension for multi-page tasks and an MCP Server beta for external agent clients.

## Choose the extension when

- The task spans existing browser tabs.
- The user wants natural-language control over pages they already have open.
- The workflow depends on real browser state.

## Choose MCP when

- An external agent client needs to control browser pages through a tool protocol.
- The user is explicitly asking for Page Agent MCP setup.
- Browser control should be exposed to an agent runtime rather than embedded in one app page.

## Validation

- Verify the extension is installed and connected before assuming browser control works.
- For MCP, inspect the current upstream docs and package scripts before writing config.
- Use the user's active/selected target page and avoid broad automation across unrelated tabs.
