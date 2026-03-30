# Agent Lifecycle & Processing Pipeline

## Problem

Each agent needs to connect to infrastructure, register itself, consume messages, process them through an LLM, parse the response, publish replies, and shut down gracefully. This involves many concerns that must be cleanly separated.

## Pattern: Runner + Processor Separation

### AgentRunner (Lifecycle Orchestrator)

Handles infrastructure wiring. Six-stage lifecycle:

**Stage 1 — Connect**: Establish RabbitMQ connection with retry.

**Stage 2 — Build Dependencies**: Create publisher, consumer, message store, vector store, registry. Compose into `AgentDeps` container.

**Stage 3 — Self-Register**: Announce presence to the consortium via `AgentRegistry.register()`, which publishes a SYSTEM join message.

**Stage 4 — Start Heartbeat**: Background task publishes heartbeat every 30 seconds.

**Stage 5 — Consume**: Bind to channels, start consuming. Each message passes through guards before reaching the processor:

```python
async def _on_message(self, message: AgentMessage) -> None:
    # Guard 1: Skip self-messages
    if message.sender == self.identity.name:
        return

    # Guard 2: Skip system messages
    if message.type == MessageType.SYSTEM:
        return

    # Guard 3: Dedup (bounded set, evict oldest half at 1000)
    if str(message.id) in self._seen_messages:
        return
    self._seen_messages.add(str(message.id))

    # Guard 4: Chain filter — only respond to @mentions unless moderator
    is_mentioned = self.identity.name in message.mentions or "all" in message.mentions
    is_moderator = "moderator" in self.identity.role.lower()
    if message.sender != "human" and not is_mentioned and not is_moderator:
        return

    # Guard 5: Rate limit (sliding window, 60s)
    if len(self._response_timestamps) >= self.config.agent_max_messages_per_minute:
        return

    # Delegate to processor
    await self.message_processor.process(message, self.deps)
```

**Stage 6 — Shutdown**: Unregister from consortium, cancel heartbeat, stop consumer, close connections. All in `try/except` blocks so partial failures don't block cleanup.

### MessageProcessor (Domain Logic)

Handles the LLM pipeline. Nine-step processing:

```
1. Add to history      → In-memory LRU store
2. Build prompt        → Conversation context + auto-recalled memories
3. Energy pre-check    → Skip if DEPLETED, skip non-mentions if CRITICAL
4. Chain depth guard   → Count consecutive non-human messages, force pass at limit
5. LLM call           → Pydantic AI agent.run(), wrapped in retry + semaphore
6. Energy deduction    → Extract token usage, deduct from ledger
7. Parse response      → Layered fallback parser (see below)
8. Publish reply       → AgentMessage with correct type + urgency
9. Auto-remember       → Store significant responses in vector DB
```

### Prompt Construction

```python
async def _build_prompt(self, message, is_mentioned, history, deps) -> str:
    parts = []

    # Recent conversation (last 10 messages, excluding current)
    if history and len(history) > 1:
        context_lines = [f"  {msg.sender}: {msg.content}" for msg in history[:-1]]
        parts.append(f"Recent conversation in {message.channel}:\n" + "\n".join(context_lines[-10:]))

    # Auto-recalled memories from vector DB
    if self.auto_recall and message.content:
        memories = await memory_manager.recall(message.content, top_k=3, namespace="both")
        relevant = [m for m in memories if (m.similarity or 0) >= 0.7]
        if relevant:
            parts.append("[RELEVANT PAST CONTEXT]\n" + "\n".join(f"  [{m.similarity:.2f}] {m.text}" for m in relevant))

    # Current message with mention note
    mention_note = " (You were @mentioned — you should respond.)" if is_mentioned else ""
    parts.append(f"[{message.channel}] {message.sender}: {message.content}{mention_note}")

    return "\n".join(parts)
```

### Layered Response Parser

Three-tier fallback that decouples structured behavior from LLM output format capability:

**Layer 1 — Tag Parsing**: Look for `[ACTION:value]` and `[URGENCY:value]` on the first line.

```python
_ACTION_RE = re.compile(r"\[ACTION:(\w+(?::\w+)?)\]", re.IGNORECASE)
_URGENCY_RE = re.compile(r"\[URGENCY:(\w+)\]", re.IGNORECASE)
```

Handles `[ACTION:redirect:agent_name]` as a special case.

**Layer 2 — Keyword Fallback**: If no tags found, check for keyword patterns.

```python
if stripped.upper().startswith("PASS"):
    return ParsedResponse(action="pass", content="", urgency="background")
```

**Layer 3 — Plain Text Fallback**: Any remaining text is treated as `action="respond"`.

```python
return ParsedResponse(action="respond", content=stripped, urgency="conversational")
```

**Output structure:**

```python
@dataclass(frozen=True, slots=True)
class ParsedResponse:
    action: str              # respond, pass, acknowledge, redirect
    content: str
    urgency: str             # immediate, conversational, reflective, background
    redirect_to: str | None = None
```

### Chain Depth Guard

Prevents infinite agent-to-agent chatter by counting consecutive non-human messages at the tail of history:

```python
@staticmethod
def _chain_depth(history: list) -> int:
    depth = 0
    for msg in reversed(history):
        if msg.sender in ("human", "user"):
            break
        depth += 1
    return depth
```

Default limit: 5. Bypassed if the agent is @mentioned (humans can always break through).

### LRU History Store

Per-channel message lists with dual-level eviction:

```python
class InMemoryHistoryStore:
    def __init__(self, max_channels=20, window_size=50):
        self._store: OrderedDict[str, list[AgentMessage]] = OrderedDict()

    def add(self, channel, message):
        if channel not in self._store:
            if len(self._store) >= self._max_channels:
                self._store.popitem(last=False)  # Evict LRU channel
            self._store[channel] = []
        else:
            self._store.move_to_end(channel)  # Mark as recently used

        self._store[channel].append(message)
        if len(self._store[channel]) > self._window_size:
            self._store[channel] = self._store[channel][-self._window_size:]
```

- **Channel-level LRU**: When max channels exceeded, drop least-recently-used channel entirely
- **Message-level FIFO**: Within each channel, keep only the most recent N messages

### History Summarization

When conversation history exceeds 50 messages, a Pydantic AI history processor summarizes the middle section using the agent's own model, preserving the first message and the 20 most recent messages verbatim.

## Why This Works

- **Runner/Processor split**: Infrastructure wiring (runner) is testable separately from LLM logic (processor)
- **Guard chain**: Five independent guards prevent unnecessary LLM calls. Each is a simple condition.
- **Layered parser**: Works with any LLM output quality — from perfectly formatted tags to raw text
- **Chain depth**: Prevents runaway agent loops without disabling agent-to-agent communication
- **LRU history**: Bounded memory with no DB queries on the hot path
