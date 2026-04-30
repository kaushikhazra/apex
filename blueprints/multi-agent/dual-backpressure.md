# Dual Backpressure (Circuit Breaker + Heat-Scaled Throttle)

## Problem

Multiple autonomous agents can generate message storms. Without backpressure:
- One chatty agent spikes all others
- The UI renders 10 messages simultaneously, overwhelming the human
- Downstream services (LLM APIs, databases) get hammered

You need two things: **protection** (stop cascades) and **pacing** (natural conversation rhythm).

## Pattern: Two Independent Mechanisms

### 1. Circuit Breaker (Protection)

A 3-state machine that gates message delivery based on system-wide message rate.

```
CLOSED ───(rate >= 30 msg/min)──→ HALF_OPEN
HALF_OPEN ─(rate >= 60 msg/min)──→ OPEN
OPEN/HALF_OPEN ─(rate < 30 for 60s)──→ CLOSED
```

**State behavior:**

| State | What Gets Delivered Immediately |
|-------|-------------------------------|
| CLOSED | Everything |
| HALF_OPEN | Only `IMMEDIATE` urgency |
| OPEN | Only `IMMEDIATE` urgency OR `QUESTION` type |

**Configuration (env vars):**

```python
CIRCUIT_BREAKER_THRESHOLD_HALF = 30     # msgs/min to trip HALF_OPEN
CIRCUIT_BREAKER_THRESHOLD_OPEN = 60     # msgs/min to trip OPEN
CIRCUIT_BREAKER_COOLDOWN_SECONDS = 60   # seconds below threshold to recover
```

**Rate tracking**: Sliding window using a `deque` of timestamps. Prune entries older than 60 seconds on each `record_message()` call.

```python
def _prune(self, now: datetime) -> None:
    cutoff = now - timedelta(seconds=60)
    while self._timestamps and self._timestamps[0] < cutoff:
        self._timestamps.popleft()
```

**Recovery requires sustained calm**: Rate must stay below `threshold_half` for the full `cooldown_seconds` duration. A single spike during cooldown resets the timer.

### Dead-Letter Redelivery

Messages that fail the circuit breaker are not dropped — they route to a **dead-letter exchange** (`{app}.dlx`) and accumulate in a deferred queue (`{app}.deferred`). A background task batch-redelivers them at intervals that vary by circuit state:

| State | Batch Interval |
|-------|---------------|
| HALF_OPEN | 10 seconds |
| OPEN | 30 seconds |
| CLOSED | 0 (no batching needed) |

This creates **backpressure without data loss**.

### 2. Throttle Engine (Pacing)

Injects delivery delays based on message urgency, human presence, and channel activity.

**Urgency-based delays:**

| Urgency | Human Active | Human Idle |
|---------|-------------|------------|
| IMMEDIATE | 0s | 0s |
| CONVERSATIONAL | 1.0s | 0.5s |
| REFLECTIVE | 5.0s (heat-scaled) | 2.0s (heat-scaled) |
| BACKGROUND | 3.0s | 0s |

**Human presence detection**: UI sends periodic heartbeats via WebSocket. Human is "active" if last heartbeat was within 30 seconds.

```python
def _is_human_active(self) -> bool:
    if self.human_last_seen is None:
        return False
    elapsed = (utc_now() - self.human_last_seen).total_seconds()
    return elapsed < self._human_timeout_seconds  # default 30s
```

### Heat-Scaled Delay (Novel)

Channel heat = messages per minute in that channel, tracked via a per-channel sliding window (60 seconds). The heat factor scales REFLECTIVE delays:

```python
heat_factor = 1.0 - min(heat / 60.0, 0.8)
delay = base_delay * heat_factor
```

| Channel Heat (msgs/min) | Heat Factor | Effective Delay (base 5s) |
|--------------------------|-------------|--------------------------|
| 0 | 1.0 | 5.0s |
| 15 | 0.75 | 3.75s |
| 30 | 0.5 | 2.5s |
| 48+ | 0.2 | 1.0s (floor) |

**Effect**: Hot channels deliver faster (agents keep up with active discussion), quiet channels slow down (no need to rush background observations). The floor at 20% of base prevents zero-delay storms.

### Integration Point

The throttle runs in the **consumer**, not the publisher. After deserializing a message, the consumer computes the delay and sleeps before invoking the callback:

```python
async def _on_raw_message(self, raw: AbstractIncomingMessage) -> None:
    async with raw.process():
        message = AgentMessage.model_validate_json(raw.body)

        if self._throttle is not None:
            delay = self._throttle.compute_delay(message)
            if delay > 0:
                await asyncio.sleep(delay)
            self._throttle.record_channel_activity(message.channel)

        if self._callback is not None:
            await self._callback(message)
```

## Message Urgency Levels

```python
class MessageUrgency(str, Enum):
    IMMEDIATE = "immediate"           # Direct questions, @mentions
    CONVERSATIONAL = "conversational" # Active discussion (default)
    REFLECTIVE = "reflective"         # Observations, background thoughts
    BACKGROUND = "background"         # Low priority, housekeeping
```

Urgency is **auto-escalated to IMMEDIATE** when a message contains @mentions (see message-routing.md).

## RabbitMQ Topology

```
Exchange: {app}.messages (topic, durable)
  ├── Routing: channel.{name}  → agent queues bound to that channel
  ├── Routing: mention.{name}  → agent queue bound to its own mention key
  └── Dead-letter → {app}.dlx → {app}.deferred (batch redelivery)
```

## Why This Works

- **Circuit breaker protects the system** — prevents cascade when one agent spirals
- **Throttle paces the conversation** — humans see messages at a natural rate
- **Heat scaling adapts to context** — no single "correct" delay, it adjusts automatically
- **Dead-letter preserves messages** — backpressure without data loss
- **Human presence awareness** — different behavior when human is watching vs. away
- **Two independent mechanisms** — circuit breaker doesn't care about urgency, throttle doesn't care about rate. They compose orthogonally.
