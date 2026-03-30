# Tool Plugin System

## Problem

Different agents need different tool sets. Hardcoding tool imports in the agent harness creates tight coupling. You need a mechanism where tools are configured per-agent and loaded dynamically.

## Pattern: Registry + Module Entry Point

### Tool Registry

A simple dict mapping short names to module paths:

```python
TOOL_REGISTRY: dict[str, str] = {
    "web_search": "{app}.tools.web_search",
    "filesystem": "{app}.tools.filesystem",
    "vectordb":   "{app}.tools.vectordb",
    "graphdb":    "{app}.tools.graphdb",
    "memory":     "{app}.memory.tools",
}
```

### Dynamic Loading

```python
import importlib

def register_tools(agent: Agent[AgentDeps, Any], enabled_tools: list[str]) -> None:
    for tool_name in enabled_tools:
        if tool_name not in TOOL_REGISTRY:
            raise KeyError(f"Unknown tool {tool_name!r}")
        module = importlib.import_module(TOOL_REGISTRY[tool_name])
        module.register(agent)
```

### Tool Module Contract

Every tool module exports a `register(agent)` function that decorates the Pydantic AI agent with tool functions:

```python
def register(agent: Agent[AgentDeps, Any]) -> None:
    @agent.tool
    async def web_search(ctx: RunContext[AgentDeps], query: str, num_results: int = 5) -> str:
        """Search the web for information."""
        client = SearchClient(provider=SearXNGProvider(...))
        results = await client.search(query, num_results)
        return "\n".join(f"- {r.title}: {r.snippet}" for r in results)
```

Tools access agent context via `RunContext[AgentDeps]` — identity, messaging, storage, registry are all available.

### Configuration

Agents specify their tools via a comma-separated config string:

```python
# In AgentConfig
agent_tools: str = "web_search,filesystem,memory"
```

Loaded at agent creation:

```python
enabled_tools = [t.strip() for t in config.agent_tools.split(",") if t.strip()]
if enabled_tools:
    register_tools(agent, enabled_tools)
```

---

## Filesystem ACL Sidecar Pattern

### Problem

Agents sharing a filesystem need ownership and permission control without a database. The permission model must be lightweight, inspectable, and co-located with the files.

### Pattern: JSON Sidecar Metadata

Every file gets a companion `<filename>.meta.json` sidecar containing ownership and ACL:

```python
class FilesystemACL(BaseModel):
    owner: str
    readers: list[str] = ["*"]    # Default: all agents can read
    writers: list[str] = []       # Default: only owner can write

    def can_read(self, agent_name: str) -> bool:
        return "*" in self.readers or agent_name in self.readers

    def can_write(self, agent_name: str) -> bool:
        return agent_name in self.writers

class FileMetadata(BaseModel):
    path: str
    owner: str
    acl: FilesystemACL
    size: int
    created_at: datetime
    modified_at: datetime
```

### Operations

**Write** (creates sidecar on first write):
```python
async def write(self, path: str, content: str, agent_name: str) -> FileMetadata:
    file_path = self._validate_path(path)  # Traversal protection
    self._check_write_permission(file_path, agent_name)
    file_path.write_text(content)

    existing = self._load_metadata(file_path)
    if existing:
        metadata = FileMetadata(owner=existing.owner, acl=existing.acl, ...)
    else:
        metadata = FileMetadata(owner=agent_name, acl=FilesystemACL(owner=agent_name), ...)

    self._save_metadata(metadata)  # Writes <file>.meta.json
    return metadata
```

**Share** (only owner can grant):
```python
async def share(self, path, agent_name, target_agent, permission="read"):
    meta = self._load_metadata(file_path)
    if meta.owner != agent_name:
        raise PermissionError("Only the owner can share")
    # Add target_agent to readers or writers list
    self._save_metadata(updated_meta)
```

**Path traversal protection**:
```python
def _validate_path(self, path: str) -> Path:
    resolved = (self._base / path.lstrip("/")).resolve()
    if not str(resolved).startswith(str(self._base)):
        raise PermissionError(f"Path traversal detected: {path}")
    return resolved
```

### Why Sidecars

- No database dependency for file permissions
- Permissions are inspectable (just read the JSON)
- Permissions travel with the file (copy the sidecar too)
- Works in any filesystem (Docker volumes, local disk, NFS)

## Why This Pattern Works

- **Zero coupling**: Agent harness has no tool imports. Tools are loaded by name at runtime.
- **Per-agent configuration**: Different agents get different tool sets via config.
- **Simple contract**: `register(agent)` is all a tool module needs to implement.
- **Extensible**: Adding a new tool = write a module + add one line to `TOOL_REGISTRY`.
- **Testable**: Mock the `AgentDeps` in `RunContext` — no infrastructure needed.
