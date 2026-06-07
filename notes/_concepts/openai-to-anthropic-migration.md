---
title: OpenAI → Anthropic Python SDK migration
slug: openai-to-anthropic-migration
tags: [concept, anthropic, sdk, gotchas]
---

# OpenAI → Anthropic Python SDK migration

The `mcp_research` client talks to Claude through the **`anthropic` SDK**, but a
lot of "Anthropic-compatible" hub docs (e.g. the NVIDIA inference hub) are written
for the **OpenAI** SDK. 

The two SDKs differ in small, high-friction ways — each one below was a real 400/404 hit while wiring up [[06-creating-an-mcp-client]].

See [[anthropic-tool-use-schema]] for the target shapes.

| Concern | OpenAI SDK | Anthropic SDK (`AsyncAnthropic`) |
|---|---|---|
| **Base URL** | includes `/v1` (`…/v1`) | **bare host** — SDK appends `/v1/messages` itself. A `…/v1` value → `…/v1/v1/messages` → **404** |
| **System prompt** | a `{"role": "system"}` message | **top-level `system=` string**; `messages` is user/assistant only |
| **`tool_choice`** | string `"auto"` | **tagged object** `{"type": "auto"}` — a bare string 400s (`expected internally tagged enum`) |
| **Tool definition** | `{"type":"function","function":{… "parameters":…}}` | flat `{"name","description","input_schema"}` |
| **Tool name chars** | lenient | must match `^[a-zA-Z0-9_-]{1,128}$` (no `@` `/` `.`) → namespace with `__` |
| **Response** | `resp.choices[0].message` | `message.content` = list of typed blocks; branch on `.type` |
| **Tool call** | `message.tool_calls[]` | `tool_use` content blocks (`.id`/`.name`/`.input`) |
| **Stop field** | `finish_reason` | `stop_reason` (`tool_use`/`end_turn`/`max_tokens`/`refusal`) |
| **Tool result** | a `{"role":"tool","tool_call_id":…}` message | a **`user`** turn with `tool_result` blocks keyed by `tool_use_id` |
| **`max_tokens`** | optional | **required** |
| **Async** | `AsyncOpenAI` | `AsyncAnthropic` + `await` — no `nest_asyncio` hack (modernization #6) |

## Credentials via env

`AsyncAnthropic()` (no args) auto-reads `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL`
from the environment — load `.env` *before* constructing the client. On a gateway,
the **model id is a provider-routed string** (e.g. `us/aws/anthropic/eccn-claude-opus-4-8`),
not the bare `claude-…` alias.

> [!tip] Phone takeaway
> Three traps, in the order they bite: **base URL** drops the `/v1`; **system** is a
> param not a message; **`tool_choice`** is `{"type":"auto"}` not `"auto"`. Then tool
> **names** can't contain `@`/`/`, and tool **results** are a `user` turn of
> `tool_result` blocks — not a `role:"tool"` message.

Related: [[anthropic-tool-use-schema]] · [[tool-use-loop]] · [[06-creating-an-mcp-client]] · [[mcp-client]]
