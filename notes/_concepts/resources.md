---
tags: [concept]
aliases: [resource, mcp-resources]
---

# resources

**Read-only data an MCP server exposes for the application to fetch** — the MCP
analogue of an HTTP `GET`. Unlike [[tools]] (which the *model* decides to invoke),
resources are **application-controlled**: the host/client chooses whether to pull
them and whether to hand the contents to the model's context window.

Declared with `@mcp.resource("<uri>")`. URIs can be static (`papers://folders`)
or templated (`papers://{topic}`) so one resource serves many addresses.
Resources update dynamically as the underlying data changes.

Related: [[tools]] · [[prompt-templates]] · [[mcp-server]] · [[08-adding-prompt-and-resource-features]]
