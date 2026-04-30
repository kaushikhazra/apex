# Identity, Registry & Process Management

## Problem

Agents need a consistent identity throughout the system. The consortium needs to know who's online, what they do, and when they were last seen. And agents need to be started/stopped dynamically at runtime — not just at deploy time.

## Pattern 1: Value-Object Identity

A frozen Pydantic model created once from configuration and threaded through the entire system:

```python
class AgentIdentity(BaseModel, frozen=True):
    name: str
    role: str
    model_id: str
```

**Used in**: system prompt construction, message headers, registry lookup, energy tracking, memory namespacing, logging.

**Extended for registry**:

```python
class AgentProfile(BaseModel):
    name: str
    role: str
    model_id: str
    description: str | None = None
    avatar_url: str | None = None
    status: AgentStatus = AgentStatus.OFFLINE
    channels: list[str] = []
    last_heartbeat: datetime | None = None
```

```python
class AgentStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
```

### Why Value Object

- Immutable: can't accidentally mutate identity mid-conversation
- Lightweight: 3 fields, passes easily through any function
- Single source: no scattered `agent_name`, `agent_role` strings

## Pattern 2: Heartbeat Protocol

Agents publish heartbeats every 30 seconds. Backend consumes them and updates `last_heartbeat` in the registry. A stale detection loop marks agents OFFLINE if no heartbeat for 90 seconds.

```python
# Agent side (runner.py)
async def _heartbeat_loop(self):
    while self.running:
        await self._heartbeat_publisher.publish()
        await asyncio.sleep(30)

# Backend side (main.py)
async def _stale_agent_detection_loop(registry, interval=90):
    while True:
        await asyncio.sleep(interval)
        agents = await registry.get_all(status=AgentStatus.ONLINE)
        for agent in agents:
            if agent.last_heartbeat and (utc_now() - agent.last_heartbeat).total_seconds() > interval:
                await registry.unregister(agent.name)
```

### Registration Flow

```python
async def register(self, profile: AgentProfile) -> None:
    await self._storage.save(profile)
    # Publish SYSTEM message announcing arrival
    if self.publisher:
        msg = AgentMessage(
            sender=profile.name,
            channel="#general",
            type=MessageType.SYSTEM,
            content=f"@{profile.name} ({profile.role}) has joined the consortium.",
        )
        await self.publisher.publish(msg)
```

## Pattern 3: Agent Process Manager

Replaces static Docker agent containers with dynamic, database-backed lifecycle management.

### Agent Configuration (persisted)

```python
class AgentProvider(str, Enum):
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"

class AgentConfigRecord(BaseModel):
    id: UUID
    name: str
    role: str
    provider: AgentProvider
    model: str
    system_prompt: str
    description: str | None = None
    avatar_url: str | None = None
    default_channels: str = "#general"
    tools: str = "memory"
    energy_budget_mj: float = 9.0
    energy_profile: EnergyProfile = EnergyProfile.HUMAN
```

### Process Manager

Starts each agent as an `asyncio.Task`, not a Docker container:

```python
class AgentProcessManager:
    _agents: dict[str, RunningAgent]       # name -> RunningAgent
    _ollama_semaphore: asyncio.Semaphore   # GPU serialization for Ollama

    async def start_agent(self, record: AgentConfigRecord) -> None:
        config = self._build_config(record)
        runner = AgentRunner(config, energy_manager=self._energy_manager,
                            llm_semaphore=self._ollama_semaphore if record.provider is AgentProvider.OLLAMA else None)
        task = asyncio.create_task(self._run_agent(runner, record.name))
        self._agents[record.name] = RunningAgent(name=record.name, config=record, runner=runner, task=task)

    async def _run_agent(self, runner, name):
        try:
            await runner.start()
            while runner.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await runner.stop()

    async def stop_agent(self, name):
        running = self._agents.pop(name)
        running.runner.running = False
        running.task.cancel()
        await running.task

    async def start_all(self):
        configs = await self._storage.find_all()
        for record in configs:
            await self.start_agent(record)
```

### Key Design Decisions

**Semaphore for Ollama**: Local LLM inference is GPU-bound. All Ollama agents share `asyncio.Semaphore(1)` to serialize GPU access. Cloud agents (OpenRouter) get no semaphore — they're IO-bound and can run concurrently.

**Channel rehydration**: On restart, `_ensure_channel_subscriptions()` reads all DB-stored subscriptions for each agent and re-binds RabbitMQ queues. Subscriptions survive backend restarts.

**REST API for lifecycle**:

```
POST   /api/agents         → Create + start agent
PUT    /api/agents/{name}  → Update config (restart if running)
DELETE /api/agents/{name}  → Stop + delete agent
GET    /api/agents/{name}/config → Get persisted config
```

### Dynamic System Prompt Injection

The moderator agent gets a live roster injected via `@agent.system_prompt` decorator:

```python
@agent.system_prompt
async def add_agent_roster(ctx: RunContext[AgentDeps]) -> str:
    if "moderator" not in ctx.deps.identity.role.lower():
        return ""
    agents = await ctx.deps.registry.get_all()
    roster_lines = [f"- @{a.name}: {a.role}" for a in agents if a.name != ctx.deps.identity.name]
    return (
        "\nAVAILABLE AGENTS IN THE CONSORTIUM:\n"
        + "\n".join(roster_lines)
        + "\n\nORCHESTRATION GUIDELINES:\n"
        "- Direct agents by @mentioning them\n"
        "- Summarize discussion threads when they stall\n"
        "- Use [ACTION:pass] when discussion proceeds well\n"
    )
```

This means the moderator always has an up-to-date view of who's online — no stale config.

## Why This Works

- **Value-object identity**: Single source of truth for "who am I" that can't be mutated
- **Heartbeat + stale detection**: Automatic cleanup of crashed agents without manual intervention
- **asyncio tasks over Docker**: Sub-second agent startup, no container overhead, shared memory for semaphores
- **Database-backed config**: Agents survive backend restarts, configs are editable via API
- **Dynamic roster injection**: Moderator's system prompt stays current without manual updates
