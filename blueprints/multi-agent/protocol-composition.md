# Protocol-First Composition

## Problem

Multi-agent systems have many infrastructure dependencies (message brokers, databases, vector stores, search engines). If domain code depends on concrete implementations, testing requires real infrastructure and swapping backends requires rewriting business logic.

## Pattern

Define every cross-module boundary as a `typing.Protocol` (structural typing). Domain code depends on protocols, never on concrete classes. Concrete implementations are injected at startup.

## Protocol Inventory

### Messaging Layer

```python
class MessagePublishing(Protocol):
    async def publish(self, message: Any) -> None: ...

class MessageConsuming(Protocol):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def on_message(self, callback: Callable) -> None: ...
```

### Storage Layer

```python
class MessageStorage(Protocol):
    async def save(self, message: Any) -> None: ...
    async def get_by_channel(self, channel: str, limit: int = 50, before: datetime | None = None) -> list: ...
    async def get_by_id(self, message_id: UUID) -> Any | None: ...
    async def search(self, query: str, channel: str | None = None) -> list: ...

class RegistryStorage(Protocol):
    async def save(self, profile: Any) -> None: ...
    async def delete(self, name: str) -> None: ...
    async def find(self, name: str) -> Any | None: ...
    async def find_all(self, status: Any | None = None) -> list: ...
    async def update_heartbeat(self, name: str, timestamp: datetime) -> None: ...

class VectorStorage(Protocol):
    async def store(self, namespace: str, text: str, metadata: dict) -> str: ...
    async def search(self, namespace: str, query: str, top_k: int = 5, filters: dict | None = None) -> list: ...
    async def delete(self, namespace: str, point_id: str) -> bool: ...

class GraphStorage(Protocol):
    async def create_node(self, label: str, properties: dict) -> str: ...
    async def create_edge(self, source_id: str, target_id: str, relation: str, properties: dict | None = None) -> str: ...
    async def query_neighbors(self, node_id: str, relation: str | None = None, depth: int = 1) -> list[dict]: ...
    async def query_path(self, source_id: str, target_id: str) -> list[dict]: ...
    async def delete_node(self, node_id: str) -> bool: ...
```

### Search Layer

```python
class SearchProvider(Protocol):
    async def search(self, query: str, num_results: int = 5) -> list: ...
```

### Registry Layer

```python
class AgentRegistration(Protocol):
    async def register(self, profile: Any) -> None: ...
    async def unregister(self, name: str) -> None: ...
    async def get(self, name: str) -> Any | None: ...
    async def get_all(self, status: Any | None = None) -> list: ...
    async def update_heartbeat(self, name: str) -> None: ...
```

All protocols use `@runtime_checkable` for structural typing assertions.

## Dependency Composition

Protocols compose into typed dependency containers injected at the agent level:

```python
@dataclass
class MessagingDeps:
    publisher: MessagePublishing

@dataclass
class StorageDeps:
    message_store: MessageStorage
    vector_store: VectorStorage

@dataclass
class AgentDeps:
    identity: AgentIdentity          # Value object (see identity-registry.md)
    messaging: MessagingDeps
    storage: StorageDeps
    registry: AgentRegistration
    search: SearchProvider
    history: HistoryStore
```

The `AgentDeps` container is created once during agent startup and passed to every Pydantic AI tool call via `RunContext[AgentDeps]`.

## Why This Works

1. **Testability**: In-memory fakes satisfy the same protocols. No Docker for unit tests.
2. **Swappability**: Replace Qdrant with Pinecone by implementing `VectorStorage`. No domain code changes.
3. **Clarity**: Reading a protocol tells you exactly what a subsystem needs without chasing imports.
4. **Composition**: Dependency containers group related protocols, keeping constructor signatures small.

## Constraints

- Protocols live in a dedicated `protocols/` package, separate from implementations.
- One protocol file per domain boundary (messaging, storage, search, registry).
- Concrete implementations import protocols for type checking, never the reverse.
- All protocol methods are async (the system is async-first).
