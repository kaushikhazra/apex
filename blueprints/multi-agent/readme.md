# Multi-Agent Consortium — Architectural Blueprints

These patterns govern how multiple LLM agents operate as persistent, autonomous peers with distinct roles, communicating through a shared message bus.

## Blueprints

| # | Blueprint | What It Captures |
|---|-----------|-----------------|
| 1 | [Protocol-First Composition](protocol-composition.md) | Structural typing for all cross-module boundaries |
| 2 | [Energy Budget System](energy-budget.md) | Metabolic cycles, graceful degradation, per-model cost tracking |
| 3 | [Dual Backpressure](dual-backpressure.md) | Circuit breaker + heat-scaled throttle + dead-letter redelivery |
| 4 | [Message Routing & Mentions](message-routing.md) | Topic exchange, dual-path mention routing, urgency escalation |
| 5 | [Agent Lifecycle & Processing](agent-lifecycle.md) | Runner orchestration, message pipeline, layered response parser |
| 6 | [Tool Plugin System](tool-plugins.md) | Dynamic tool loading, filesystem ACL sidecars |
| 7 | [CQRS & WebSocket Bridge](cqrs-bridge.md) | Backend sole writer, MQ-to-WebSocket relay, connection management |
| 8 | [Identity & Registry](identity-registry.md) | Value-object identity, heartbeat protocol, agent process manager |

## Assumed Stack

These blueprints assume a specific technology stack but the patterns are transferable:

**Runtime**: Python 3.12+ (async-first), **LLM Framework**: Pydantic AI, **Message Broker**: RabbitMQ (AMQP), **Persistence**: PostgreSQL, **Vector DB**: Qdrant, **Graph DB**: Neo4j, **API**: FastAPI, **Frontend**: React

## What's Novel vs. Standard

| Novel | Standard (well-executed) |
|-------|--------------------------|
| Energy budgets as metabolic cycles | Protocol-based composition |
| Heat-scaled throttle delays | Circuit breaker (3-state) |
| Dual-path mention routing | CQRS sole-writer |
| Filesystem ACL sidecars | Plugin tool registry |
| Graceful degradation by energy level | LRU history store |
