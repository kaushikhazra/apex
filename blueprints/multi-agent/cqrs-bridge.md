# CQRS & WebSocket Bridge

## Problem

Multiple agents publish messages to a message bus. A web UI needs real-time updates. If agents write directly to the database AND the UI subscribes directly to the message bus, you get distributed transactions, race conditions, and tight coupling between the UI and infrastructure.

## Pattern: Backend Sole Writer + MQ-to-WebSocket Bridge

### Rule

**The backend is the only process that writes to PostgreSQL.** Agents publish state changes via RabbitMQ. The backend consumes and persists. This is CQRS-lite — command (write) responsibility is centralized, query (read) is distributed via REST API.

### What Flows Through This

| Data | Source | Persistence |
|------|--------|-------------|
| Messages | Agents publish, bridge persists | `messages` table |
| Agent profiles | Registry register/unregister | `agent_profiles` table |
| Channel subscriptions | ChannelRegistry sync | `channel_subscribers` table |
| Energy deductions | Agent processor deducts | `agent_energy_ledger` table |

### Backend Lifespan (Startup Sequence)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Persistence layer
    store = MessageStore()
    channel_registry = ChannelRegistry()
    await store.init_schema()
    await channel_registry.init_schema()

    # 2. Agent infrastructure
    registry_storage = PostgresRegistryStorage()
    agent_registry = AgentRegistry(storage=registry_storage)
    energy_manager = EnergyManager(EnergyStorage())

    # 3. Agent process manager
    agent_process_manager = AgentProcessManager(
        storage=agent_config_storage,
        channel_registry=channel_registry,
        energy_manager=energy_manager,
    )

    # 4. RabbitMQ publisher (sole writer to MQ)
    rmq_connection = await connect_rabbitmq()
    publisher = MessagePublisher(rmq_channel, store=store)

    # 5. Background tasks
    bridge_task = asyncio.create_task(mq_to_websocket_bridge(manager, rabbitmq_url, store=store))
    heartbeat_task = asyncio.create_task(run_heartbeat_consumer(...))
    stale_task = asyncio.create_task(stale_agent_detection_loop(...))
    energy_task = asyncio.create_task(energy_replenishment_loop(...))

    # 6. Start all persisted agents
    await agent_process_manager.start_all()

    yield

    # Shutdown: graceful teardown
    await agent_process_manager.stop_all()
    for task in tasks:
        task.cancel()
        await task
```

### MQ-to-WebSocket Bridge

A background task that consumes from RabbitMQ and relays to WebSocket clients:

```python
async def mq_to_websocket_bridge(target: BroadcastTarget, rabbitmq_url: str, store=None):
    connection = await aio_pika.connect_robust(rabbitmq_url)
    channel = await connection.channel()

    exchange = await channel.declare_exchange("{app}.messages", ExchangeType.TOPIC, durable=True)
    queue = await channel.declare_queue("backend.ui", durable=True)
    await queue.bind(exchange, routing_key="channel.#")  # All channel messages

    async with queue.iterator() as queue_iter:
        async for raw in queue_iter:
            async with raw.process():  # Auto-ACK
                message = AgentMessage.model_validate_json(raw.body)

                # Persist agent messages (human messages already saved by publisher)
                if store is not None and message.sender != "human":
                    await store.save(message)

                # Relay to subscribed WebSocket clients
                await target.broadcast_to_channel(message.channel, message)
```

**Key design**:
- `backend.ui` queue is **durable** — survives backend restarts, messages accumulate while offline
- Binds to `channel.#` — receives all channel messages regardless of specific channel name
- Dual responsibility: **persist** (write to DB) + **relay** (push to WebSocket)
- Auto-ACK via context manager — message removed from queue only on success

### WebSocket Connection Manager

Tracks active connections and channel subscriptions:

```python
class ConnectionManager:
    active_connections: dict[str, WebSocket]      # connection_id -> socket
    subscriptions: dict[str, set[str]]            # channel -> {connection_ids}

    async def broadcast_to_channel(self, channel: str, message: Any):
        for conn_id in self.subscriptions.get(channel, set()):
            ws = self.active_connections.get(conn_id)
            if ws is None:
                continue
            try:
                await ws.send_json({"type": "message", "data": message.model_dump(mode="json")})
            except Exception:
                self.disconnect(conn_id)  # Auto-cleanup dead connections
```

### WebSocket Protocol

Client sends JSON commands, server dispatches to handlers:

```python
WS_HANDLERS = {
    "subscribe":   handle_subscribe,    # Join a channel's live feed
    "unsubscribe": handle_unsubscribe,  # Leave a channel's live feed
    "send":        handle_send,         # Publish a message (human -> agents)
    "heartbeat":   handle_heartbeat,    # Human presence signal (throttle input)
}
```

### Dependency Injection

Module-level singletons set during lifespan, accessed by route handlers:

```python
_publisher: MessagePublishing | None = None

def set_publisher(publisher: MessagePublishing) -> None:
    global _publisher
    _publisher = publisher

def get_publisher() -> MessagePublishing | None:
    return _publisher
```

Simple, explicit, no framework magic. The lifespan sets them, routes read them.

### Data Flow Diagram

```
Human (UI) ──WebSocket──→ Backend ──Publisher──→ RabbitMQ
                                                    │
                                    ┌───────────────┤
                                    ▼               ▼
                              Agent Queues    backend.ui Queue
                              (consumer)      (bridge)
                                    │               │
                                    ▼               ├──→ Persist to PostgreSQL
                              LLM Processing        └──→ Relay to WebSocket
                                    │                         │
                                    └──Publisher──→ RabbitMQ   │
                                         (loop)               ▼
                                                         UI renders
```

## Why This Works

- **Single writer**: No concurrent writes to PostgreSQL. No distributed transactions.
- **Durable bridge queue**: Messages survive backend restarts. No data loss.
- **UI decoupled from MQ**: Frontend speaks WebSocket only. Swapping RabbitMQ for Kafka doesn't touch the UI.
- **Auto-cleanup**: Dead WebSocket connections are detected on send failure and removed.
- **Human presence**: Heartbeat from UI feeds into throttle engine, creating adaptive pacing.
