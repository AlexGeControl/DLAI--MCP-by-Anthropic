---
title: MCP control model → UX surface
slug: mcp-control-model
tags: [concept, mcp]
---

# MCP control model → UX surface

The single axis that distinguishes the three server primitives: **who decides to
invoke it?** That control model isn't academic — it *determines how each primitive
surfaces in a real MCP host* (Claude Desktop, Claude Code, Cursor). The client you
built in [[06-creating-an-mcp-client]] is a miniature of those hosts, so the same
mapping holds.

| primitive | who controls invocation | real-client surface | what it delivers |
|---|---|---|---|
| [[tools]] | the **model** | the autonomous "🔧 using *X*…" actions, behind a permission gate | an action result spliced back into the [[tool-use-loop]] |
| [[resources]] | the **app / user** | the **`@`-mention / attach-context** affordance | read-only **data to inject** ([[mcp-resource-access]]) |
| [[prompt-templates]] | the **user** | the **`/` slash command** | a **conversation to run** ([[mcp-prompt-access]]) |

## Why this is the load-bearing idea

Every design decision across the consumption notes falls out of this one axis:

- **Tools** run through `tool_choice` + the agentic loop *because the model drives
  them* — and the host gates them behind approval *because the model is acting*.
- **Resources** are `@`-attached by the user, so "should an LLM pick the resource?"
  is the wrong question — the user picks (or you promote it to a [[tools|tool]]). No
  bespoke selector; see the routing discussion in [[mcp-resource-access]].
- **Prompts** are `/`-invoked by the user, returning messages to *run* (not data to
  inject) — which is why `execute_prompt` feeds them straight to `process_query`.

So the result-shape trio lines up the same way: **tool → answer to splice ·
resource → data to inject · prompt → conversation to run.**

## A validation you stumbled into

Claude Code exposes MCP prompts as slash commands named **`/mcp__<server>__<prompt>`**
and `@`-mentions MCP resources the same way. That `__` delimiter is the **exact
scheme you reverse-engineered** when Anthropic's tool-name regex rejected
`@server/tool` — you independently landed on the real product's convention.

> [!note] Keep it honest
> `@file` in a real client is sometimes a *built-in* filesystem read rather than an
> MCP resource — but the **pattern** (user-selected, app-injected, read-only) is
> identical. And production hosts add what this assignment skips: tool **permission
> gating**, **remote transport + OAuth**, and further primitives (**sampling,
> roots, elicitation, `listChanged`**) — see [[11-conclusion]].

> [!tip] Phone takeaway
> One axis — **who invokes?** — sets everything: **tool** = model-driven → auto
> actions (gated); **resource** = user-driven `@`-context (data to inject);
> **prompt** = user-driven `/`-command (conversation to run). The control model
> *is* the UX surface.

Related: [[tools]] · [[resources]] · [[prompt-templates]] · [[anthropic-tool-use-schema]] · [[mcp-resource-access]] · [[mcp-prompt-access]] · [[mcp-client]] · [[09-configuring-servers-for-claude-desktop]] · [[11-conclusion]]
