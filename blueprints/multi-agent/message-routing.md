# Message Routing & Mentions

## Problem

In a multi-agent system with named channels, agents subscribe to channels they care about. But when an agent is @mentioned in a channel it hasn't subscribed to, the message is lost. You need guaranteed delivery for directed messages without requiring all agents to subscribe to all channels.

## Pattern: Dual-Path Routing with Urgency Escalation

### Message Model

```python
class AgentMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    sender: str                    # agent name or "human"
    channel: str                   # e.g., "#general", "#research"
    mentions: list[str] = Field(default_factory=list)
    urgency: MessageUrgency = MessageUrgency.CONVERSATIONAL
    type: MessageType = MessageType.THOUGHT
    content: str
    reply_to: UUID | None = None
    timestamp: datetime = Field(default_factory=utc_now)
```

### Message Types (Semantic Intent)

```python
class MessageType(str, Enum):
    QUESTION = "question"
    THOUGHT = "thought"
    RESPONSE = "response"
    ACKNOWLEDGMENT = "acknowledgment"
    REDIRECT = "redirect"
    SYSTEM = "system"
```

### Routing Key Patterns

| Purpose | Pattern | Example |
|---------|---------|---------|
| Channel broadcast | `channel.{name}` | `channel.general` |
| Direct mention | `mention.{agent_name}` | `mention.alice` |

### Queue Naming

Each agent owns a durable queue named `agent.{agent_name}`. On startup, the consumer binds:
1. `mention.{agent_name}` — always bound, guarantees @mention delivery
2. `channel.{name}` — for each subscribed channel

### Publish Flow (5 steps)

```python
async def publish(self, message: AgentMessage) -> None:
    # 1. Parse mentions from content
    if not message.mentions:
        message.mentions = parse_mentions(message.content)

    # 2. Escalate urgency for mentions
    if message.mentions and message.urgency != MessageUrgency.IMMEDIATE:
        message.urgency = MessageUrgency.IMMEDIATE

    # 3. Serialize once
    body = message.model_dump_json().encode()
    amqp_message = aio_pika.Message(body=body, content_type="application/json")

    # 4. Publish to channel routing key (fan-out to all subscribers)
    await self._exchange.publish(amqp_message, routing_key=f"channel.{channel}")

    # 5. Publish to mention routing keys (only for non-subscribers)
    subscribers = await self._get_channel_subscribers(message.channel)
    for name in message.mentions:
        if name in subscribers:
            continue  # Already receives via channel binding — skip
        await self._exchange.publish(amqp_message, routing_key=f"mention.{name}")

    # 6. Persist
    if self._store is not None:
        await self._store.save(message)
```

### Mention Parsing

```python
MENTION_PATTERN = re.compile(r"@([\w-]+)")

def parse_mentions(content: str) -> list[str]:
    """Deduplicated, order-preserving mention extraction."""
    seen: set[str] = set()
    result: list[str] = []
    for match in MENTION_PATTERN.finditer(content):
        name = match.group(1)
        if name not in seen:
            seen.add(name)
            result.append(name)
    return result
```

### Smart Deduplication

The publisher checks channel subscribers before sending mention routing. If `@alice` is already subscribed to `#general`, she receives the message via `channel.general` — no duplicate `mention.alice` publish needed.

This prevents double-delivery while ensuring agents NOT subscribed to the channel still receive their @mentions.

### Channel Registry

Channels are persisted in PostgreSQL with a subscriber join table:

```sql
CREATE TABLE channels (name TEXT PRIMARY KEY, description TEXT, creator TEXT, created_at TIMESTAMPTZ);
CREATE TABLE channel_subscribers (channel_name TEXT, agent_name TEXT, PRIMARY KEY (channel_name, agent_name));
```

The `ChannelRegistry` synchronizes DB subscriptions with RabbitMQ queue bindings:

```python
async def subscribe(self, channel_name: str, agent_name: str) -> None:
    # 1. Persist to DB
    await conn.execute("INSERT INTO channel_subscribers ... ON CONFLICT DO NOTHING", ...)
    # 2. Bind RabbitMQ queue
    queue = await rmq_channel.declare_queue(f"agent.{agent_name}", durable=True)
    await queue.bind(exchange, routing_key=f"channel.{clean_name}")
```

### Message Persistence

PostgreSQL-backed with channel + timestamp indexing:

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY, sender TEXT, channel TEXT, mentions TEXT[],
    urgency TEXT, type TEXT, content TEXT, reply_to UUID, timestamp TIMESTAMPTZ
);
CREATE INDEX idx_messages_channel ON messages (channel, timestamp DESC);
```

## Why This Works

- **Guaranteed delivery**: @mentions always reach the target agent regardless of subscription state
- **No duplicates**: Subscriber check prevents double-delivery on the hot path
- **Urgency escalation**: Mentions auto-promote to IMMEDIATE, bypassing throttle and circuit breaker
- **Durable queues**: If an agent is temporarily offline, messages queue and deliver on reconnect
- **Clean separation**: Publisher handles routing logic, consumer handles delivery pacing
