---
tags: [concept]
aliases: [claude_desktop_config, desktop-config, mcpServers]
---

# claude-desktop-config

**The JSON config file Claude Desktop reads to discover and launch MCP servers**
(Settings → Developer → Edit Config). It is the product-grade equivalent of the
`server_config.json` the hand-built chatbot used — same idea, no client code.

Each entry names a server plus the `command`/`args` to start it; for local
[[stdio-transport]] servers you give the **absolute file path** so Desktop can
spawn the subprocess. Restart Desktop to pick up changes.

Related: [[mcp-host]] · [[mcp-server]] · [[stdio-transport]] · [[09-configuring-servers-for-claude-desktop]]
