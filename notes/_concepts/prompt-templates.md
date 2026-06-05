---
tags: [concept]
aliases: [prompt-template, prompts, mcp-prompts]
---

# prompt-templates

**User-controlled, parameterized prompts created on the server and sent to the
client** so the user can invoke battle-tested prompt engineering without writing
it themselves. The user supplies only the dynamic arguments (e.g. `topic`,
`num_papers`); the server returns the full expanded prompt text.

Declared with `@mcp.prompt()`. The decorated function's parameters become the
template's arguments (required vs. optional from defaults), and its return value
is the prompt string the client feeds to the model.

Related: [[tools]] · [[resources]] · [[mcp-server]] · [[08-adding-prompt-and-resource-features]]
