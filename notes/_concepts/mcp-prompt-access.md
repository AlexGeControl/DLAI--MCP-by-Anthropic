---
title: Selecting & running MCP prompts
slug: mcp-prompt-access
tags: [concept, mcp, prompts]
---

# Selecting & running MCP prompts

The prompt counterpart of [[mcp-resource-access]] — *how a prompt template gets
selected, rendered, and run*. Like resources, prompts are **user-controlled**, but
what comes back differs:

> A prompt has no model-driven trigger (it's not a `tool_use`). The **user** invokes
> it — the course/assignment surfaces this as a **`/prompt <name> <k=v>…`** slash
> command. And unlike a resource (read-only *data* you inject), a prompt returns
> **conversation messages you run** through the model.

## Two phases: discover, then invoke

1. **Discover** — `list_prompts()` (gated on the `prompts` capability — see
   [[mcp-session-init]]) yields `Prompt`s: `name`, `description`, and
   **`arguments`** (each a `PromptArgument` = `name`, `description`, `required`).
   A `/prompts` command lists these so the user knows what to call and which args
   are required.
2. **Invoke** — `get_prompt(name, arguments)` renders the template server-side and
   returns messages — see [[mcp-prompt-result]].

## The argument gotcha: `dict[str, str]`

`get_prompt(name, arguments)` types `arguments` as **`dict[str, str]`** — *every
value is a string*. 

A prompt like `generate_search_prompt(topic, num_papers=5)` must be called with `num_papers` **stringified**:

```python
await session.get_prompt(
    "generate_search_prompt",
    {"topic": "diffusion models", "num_papers": "3"},   # "3", not 3
)
```

Parse `/prompt generate_search_prompt topic=… num_papers=…` into a `{str: str}` map
and **don't coerce numbers** — the server does its own typing from the string.

## The run workflow

```python
# 1. user: /prompt generate_search_prompt topic=diffusion num_papers=3
result = await session.get_prompt(name, args)        # → GetPromptResult.messages
# 2. turn the rendered message(s) into a query and run them through the loop
text = result.messages[0].content.text               # single-message prompt → its text
await self.process_query(text)                        # reuse the tool-use loop
```

For multi-message prompts, map each `PromptMessage` (role + content) into an
Anthropic message and seed `process_query` / the loop with the whole list.

## Selection — same rule as resources

Prompts are picked by the **user** (the `/prompt` command), not the model. If you
ever want the model to invoke one, promote it to a [[tools|tool]] and reuse the
[[tool-use-loop]] — don't build a bespoke selector. (Same reasoning as
[[mcp-resource-access]].)

> [!tip] Phone takeaway
> Prompts are **user-invoked** (`/prompt name k=v`), two-phase: `list_prompts`
> (name / description / **arguments**) → `get_prompt(name, {str:str})`. Args are
> **all strings**. The result is **messages to run** (feed to `process_query`),
> not data to inject.

Related: [[mcp-prompt-result]] · [[prompt-templates]] · [[mcp-resource-access]] · [[mcp-session-init]] · [[tool-use-loop]] · [[06-creating-an-mcp-client]] · [[08-adding-prompt-and-resource-features]]
