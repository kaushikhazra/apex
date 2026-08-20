# MCP Strict Arguments Blueprint

An MCP server **must reject** arguments it does not recognise, and name the ones it accepts. This blueprint says why that is not the default, which of two implementations to choose, and how to prove your server actually does it.

It is prescriptive. Every MCP server built from `mcp_base.md` or from a domain blueprint in this category follows it.

## Overview

The MCP SDK ships its own FastMCP at `mcp.server.fastmcp`. It builds each tool's arguments into a Pydantic model and leaves `extra` at Pydantic's default, `ignore`. An argument the tool never declared is therefore dropped before the tool body runs, and the call returns success.

Nothing in your code does the dropping. It is a library default, and it is invisible.

## The failure this prevents

The damage is not that a key is discarded. It is that **whether you find out depends on something unrelated to your mistake**:

| You misspell the name of a... | What happens |
|---|---|
| **required** argument | Loud error — the declared field is now missing, so validation fails |
| **optional** argument | **Silent success** — your key is discarded, the default is used, and the response looks correct |

So the same typo is caught or not caught depending on whether the argument you fat-fingered happened to have a default. A caller who misnames an optional argument gets a success response describing work that was done with values they did not choose, and no signal anywhere. The cost is paid later, hunting a bug in the tool that does not exist.

This is not hypothetical: it cost an afternoon of debugging across twelve tool calls before the cause was found in a library default rather than in any of the code being debugged.

## Reproduction

Same tool, same call, two libraries. `mcp` 1.26.0 and `fastmcp` 2.14.4:

```python
@server.tool()
async def store(text: str, kind: str = "note") -> str:
    return f"kind={kind}"

# 'typ' is a typo for 'kind'
await call("store", {"text": "hello", "typ": "fact"})
```

| Import | Result |
|---|---|
| `from mcp.server.fastmcp import FastMCP` | **accepted**, returns `kind=note` — the typo vanished |
| `from fastmcp import FastMCP` | **rejected**, `ToolError: unexpected keyword argument` |

The mechanism is visible at source. On the SDK-bundled version the generated argument model reports `model_config['extra'] is None`, which is Pydantic's default of `ignore`:

```python
tool = server._tool_manager.get_tool("store")
tool.fn_metadata.arg_model.model_config.get("extra")   # -> None
```

Run both arms, not one. A single arm tells you the bundled version does something; the pair is what shows the behaviour belongs to the library and not to your calling code.

## The rule

> A tool call carrying an argument the server does not declare **must fail**, and the error **must name the accepted arguments**.

Naming them is half the value. `unexpected keyword argument 'typ'` tells a caller they made a typo; it does not tell them the word they wanted was `kind`.

## Two ways to satisfy it

### Preferred — standalone `fastmcp` 2.x

```python
from fastmcp import FastMCP
```

Rejection happens upstream. There is nothing of ours to write, nothing to maintain, and nothing to forget to copy into the next server. **Reuse before build** applies exactly here: this is a solved problem in a maintained library, and the alternative is a subclass we own forever.

One API difference from the SDK-bundled version, which the domain blueprints in this category now reflect: **`port` is not a constructor argument.** It is passed to `run()`:

```python
server = FastMCP(name="Example MCP")
...
server.run(transport="http", port=port)
```

Valid transports are `stdio`, `http`, `sse`, and `streamable-http`.

The `@server.tool` decorator works with or without parentheses, so existing `@server.tool()` registrations need no change.

### Alternative — a `StrictArgumentFastMCP` subclass

Override `call_tool` on the SDK-bundled class to compare incoming keys against the tool signature before dispatch. A reference implementation exists on `cognitive-memory`, branch `bugfix/mcp-type-override`, head `ce9690c`.

**This is the faster path and it will drift.** One copy per repository, each free to fall behind the others, with no mechanism making them agree — the same shape as a tenant row-security contract copy-pasted across four repositories. Choose it only when migrating off the bundled SDK is genuinely blocked, and record why in the server that carries it.

#### `_meta` and underscore-prefixed keys

Only relevant on this path. `_meta` is MCP-reserved and rides as a **sibling of `arguments`** at `params` level, not as a key inside `arguments` — so a well-behaved client never puts it where your check can see it.

A hand-rolled check sits at a layer where a misbehaving client could, so exempting underscore-prefixed keys there is cheap insurance against failing every call rather than catching a typo.

**Do not state this as a general rule.** `fastmcp` 2.x rejects `_meta` and `_hint` inside `arguments` exactly like any other unknown key, and that costs nothing precisely because they never arrive there. Written as a blanket rule, it tells anyone on the preferred path something that is false for them — which is the failure this blueprint exists to stop.

## Verifying it

Two things need proving, and they are different questions.

**That your server rejects unknown arguments.** Drive it in-process and assert the failure:

```python
from fastmcp import Client

async with Client(server) as c:
    await c.call_tool("store", {"text": "x", "kind": "fact"})      # succeeds
    with pytest.raises(Exception):
        await c.call_tool("store", {"text": "x", "typ": "fact"})   # must fail
```

**That the real client sends nothing extra.** A strict server is only safe if the client is not injecting keys of its own. Test against an isolated instance rather than a live one:

```bash
claude -p --mcp-config ./one-server.json --strict-mcp-config "call the tool"
```

`--strict-mcp-config` loads **only** the servers named in the file, so nothing else in the environment is reached. The harsh case is a **zero-parameter tool**: with no declared arguments, any injected key at all raises, so success is positive evidence that the client sent a clean `arguments` object.

Verified this way, the Claude Code client puts nothing inside `arguments` beyond what the caller supplies.

## Migrating an existing server

1. Change the import to `from fastmcp import FastMCP`.
2. Move `port` from the constructor to `run()`.
3. Add the rejection test above for at least one tool.
4. Re-run the tool calls the server actually receives — a call that was silently succeeding on a discarded argument now fails, and that failure is the bug surfacing, not a regression.

Tool registrations do not change. Step 4 is the one that gets skipped. Callers that have been relying on a discarded argument have been getting the wrong behaviour all along; making the server strict is what tells you which ones.

## Related

- `mcp_base.md` — base MCP server structure
- `web/mcp_web_search.md`, `web/mcp_web_crawler.md`, `filesystem/mcp_filesystem.md`, `knowledge_base/mcp_knowledge_base.md` — domain servers, all built on the rule above
