# Energy Budget System

## Problem

In a multi-agent system, agents can consume unbounded resources (API tokens, GPU time). Hard rate limits cause abrupt failures. You need a mechanism that:
- Controls cost across heterogeneous models (local vs. cloud)
- Degrades gracefully instead of hard-failing
- Creates predictable replenishment so agents recover
- Provides observability into per-agent resource consumption

## Pattern: Metabolic Cycles

Model agent throughput as a consumable energy budget, inspired by biological metabolism.

### Core Concepts

**Daily budget** in megajoules (MJ), distributed across **8 metabolic cycles** (3 hours each). Energy is deducted per LLM call based on `total_tokens x joules_per_token`. As budget depletes, agent behavior degrades through defined levels.

### Budget Levels

```python
class BudgetLevel(str, Enum):
    FULL = "full"           # > 75% of granted energy remaining
    NORMAL = "normal"       # 25-75% remaining
    LOW = "low"             # 10-25% remaining — shorter responses
    CRITICAL = "critical"   # < 10% remaining — mentions only
    DEPLETED = "depleted"   # 0% — silent skip
```

### Behavioral Mapping

| Level | Agent Behavior |
|-------|---------------|
| FULL | Normal operation |
| NORMAL | Normal operation |
| LOW | Prompt prefix: `[ENERGY LOW — keep response under 50 words]` |
| CRITICAL | Only respond to @mentions. Prompt prefix: `[ENERGY CRITICAL — 1 sentence max]` |
| DEPLETED | Skip all messages silently |

### Energy Profiles (Presets)

```python
ENERGY_PROFILES = {
    "human":     9.0,    # ~900K tokens/day at 10 J/token
    "efficient": 4.5,    # Half human, more thoughtful
    "generous":  18.0,   # Double human, active discussions
}
```

### Model Energy Rates (J/token)

```python
MODEL_ENERGY_RATES = {
    # Local models (Ollama) — efficient hardware
    "qwen2.5:7b": 3.0,
    "qwen2.5:14b": 6.0,
    "llama3:8b": 3.5,
    "llama3:70b": 15.0,
    "mistral:7b": 3.0,
    "gemma2:9b": 4.0,

    # Cloud API models (OpenRouter) — datacenter overhead
    "openai/gpt-4o": 35.0,
    "openai/gpt-4o-mini": 8.0,
    "anthropic/claude-3.5-sonnet": 35.0,
    "anthropic/claude-3-haiku": 10.0,
    "google/gemini-pro": 20.0,

    "_default": 10.0,
}
```

Provider prefixes are stripped before lookup: `"openai:qwen2.5:7b"` -> `"qwen2.5:7b"` -> 3.0 J/token.

### Cycle Mechanics

- **8 cycles per day**, each 3 hours, UTC-aligned (00:00, 03:00, 06:00, ...)
- Each cycle grants `budget_mj / 8` of the daily budget
- Unused energy carries forward within the day (granted accumulates)
- At midnight UTC: full reset (consumed = 0, granted = first cycle portion)
- Background task runs every 60 seconds to advance cycles

### Deduction Formula

```
rate = resolve_model_rate(model_id)            # J/token
total_tokens = prompt_tokens + completion_tokens
total_joules = total_tokens * rate
total_mj = total_joules / 1_000_000
consumed_mj += total_mj
remaining_mj = granted_mj - consumed_mj
remaining_pct = (remaining_mj / granted_mj) * 100
level = compute_level(remaining_pct)
```

### Budget State (observable)

```python
class BudgetState(BaseModel):
    agent_name: str
    budget_mj: float          # Total daily budget
    consumed_mj: float        # Consumed so far today
    granted_mj: float         # Total granted (cycle_num * portion)
    remaining_mj: float       # Available now
    remaining_pct: float      # Percentage of granted remaining
    level: BudgetLevel        # Computed from remaining_pct
    cycle_number: int          # Current cycle (1-8)
    cycle_end: datetime        # When next cycle replenishes
```

### Database Schema

```sql
CREATE TABLE agent_energy_ledger (
    id            UUID PRIMARY KEY,
    agent_name    TEXT NOT NULL UNIQUE,
    cycle_start   TIMESTAMPTZ NOT NULL,
    cycle_end     TIMESTAMPTZ NOT NULL,
    budget_mj     FLOAT NOT NULL,
    consumed_mj   FLOAT NOT NULL DEFAULT 0,
    cycle_number  INT NOT NULL DEFAULT 1,
    granted_mj    FLOAT NOT NULL,
    last_updated  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE agent_energy_transactions (
    id                UUID PRIMARY KEY,
    agent_name        TEXT NOT NULL,
    message_id        UUID,
    model             TEXT NOT NULL,
    prompt_tokens     INT NOT NULL,
    completion_tokens INT NOT NULL,
    joules_per_token  FLOAT NOT NULL,
    total_joules      FLOAT NOT NULL,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Integration Points

1. **Pre-LLM check** in MessageProcessor: skip if DEPLETED, skip non-mentions if CRITICAL
2. **Prompt injection**: prepend energy-aware instructions at LOW/CRITICAL
3. **Post-LLM deduction**: extract token usage from result, deduct from ledger
4. **Background replenishment**: 60-second loop advances cycles, resets at day boundary
5. **API endpoints**: `GET /api/agents/energy` and `GET /api/agents/{name}/energy`

## Why This Works

- **Non-binary**: Five levels of degradation vs. a simple on/off rate limit
- **Cost control**: Cloud models (35 J/token) burn budget 10x faster than local (3 J/token), naturally incentivizing efficient model selection
- **Predictable recovery**: Agents know when their next cycle arrives. No indefinite throttling.
- **Observable**: Transaction log enables cost attribution per agent, per model, per message.
- **Emergent prioritization**: Agents at LOW/CRITICAL self-select into important conversations only.
