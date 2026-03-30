# APEX — AI Powered Enterprise Execution

A library of reusable development methodologies and architectural blueprints for AI-powered software delivery with Claude Code.

Pick a methodology. Grab the blueprints you need. Go.

---

## Structure

```
apex/
  sdlc/                          # HOW you work — development methodologies
    spec-enhanced/               # Spec-driven development with skills + hooks
    scaled-agile/                # SAFe-based agent hierarchy
  blueprints/                    # WHAT you build — reusable technical patterns
    interfaces/                  # CLI and web UI patterns
    libs/                        # Library patterns (memory, parsers, web, utils)
    mcps/                        # MCP server patterns
    multi-agent/                 # Multi-agent consortium runtime patterns
    pydantic/                    # Pydantic AI agents, graphs, prompts
```

---

## SDLC Methods

### Spec-Enhanced

A spec-driven development workflow where every feature follows a lifecycle before code is written.

**Lifecycle**: `/spec` → `/requirement` → `/design` → `/implement`

**Quality gates**: `/dryrun-design`, `/dryrun-code`, `/dryrun-plan`, `/dryrun-blueprint`, `/dryrun-context`

**Includes**:
- 10 Claude Code skills (full spec lifecycle + validation)
- 8 hooks (branch guard, security, formatting, context evaluation)
- Portable `CLAUDE.md` with coding principles, git flow, and task rules

### Scaled Agile

A SAFe-based multi-level agent hierarchy for enterprise software delivery.

**Levels**: Portfolio → Solution → Program (ART) → Team → Pipeline

**Includes**:
- 15 agent personas mapped to SAFe roles
- 15 slash commands (one per role)
- Human-in-the-loop control points
- User story and command templates

---

## Blueprints

| Category | What's inside |
|----------|--------------|
| **Interfaces** | CLI (async, batch, interactive, subcommand) and Web (frontend, backend, integration) |
| **Libraries** | Agent memory, embeddings, filesystem, knowledge base, parsers, config, web crawling |
| **MCPs** | Base MCP pattern, filesystem, knowledge base, web crawler, web search |
| **Multi-Agent** | Protocol composition, energy budgets, backpressure, message routing, agent lifecycle, tool plugins, CQRS bridge, identity registry |
| **Pydantic AI** | Orchestrator, stateful/stateless subagents, graphs (base, stateful, with agents), prompt engineering |

---

## Usage

1. Clone the repo
2. Copy the SDLC method that fits your project into your `.claude/` directory
3. Copy relevant blueprints into `.claude/blueprints/`
4. Customize hook configs (marked with `# CONFIGURE`) for your project
5. Start building

Methods and blueprints are independent — mix and match as needed.

---

## License

Private repository. Internal use only.
