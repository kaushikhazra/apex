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

### Spec-Enhanced (`e-spec` plugin)

A spec-driven development workflow where every feature follows a lifecycle before code is written. Distributed as a Claude Code plugin under the `e-spec` namespace — skills are invoked as `/e-spec:requirement`, `/e-spec:design`, `/e-spec:dryrun-code`, etc.

**Lifecycle**: `/e-spec:spec` → `/e-spec:requirement` → `/e-spec:design` → `/e-spec:implement`

**Quality gates**: `/e-spec:dryrun-design`, `/e-spec:dryrun-code`, `/e-spec:dryrun-plan`, `/e-spec:dryrun-blueprint`, `/e-spec:dryrun-context`

**Includes**:
- 10 Claude Code skills (full spec lifecycle + validation)
- 8 hooks (branch guard, security, formatting, context evaluation) — auto-fire on tool use, no per-project wiring needed
- Portable `CLAUDE.md` with coding principles, git flow, and task rules

**Install in any project**:

```bash
# From this repo (after pushing develop)
/plugin install https://github.com/kaushikhazra/apex.git#develop:sdlc/spec-enhanced

# Or local path during development
claude --plugin-dir <path-to-apex>/sdlc/spec-enhanced
```

Optional dependency: install `ruff` (`pip install ruff` or `pipx install ruff`) on the target machine to enable the `ruff_format.py` post-edit hook.

Plugin internals: see `sdlc/spec-enhanced/README.md`.

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

**Spec-Enhanced (preferred — plugin install)**:

```bash
/plugin install https://github.com/kaushikhazra/apex.git#develop:sdlc/spec-enhanced
```

After install, skills are available under `/e-spec:*` and hooks auto-fire on tool use. No per-project wiring; one `git pull` of APEX bumps every consumer project on the next plugin update.

**Other methods + blueprints (copy-paste, until plugin-packaged)**:

1. Clone the repo
2. Copy the SDLC method that fits your project into your `.claude/` directory
3. Copy relevant blueprints into `.claude/blueprints/`
4. Customize hook configs (marked with `# CONFIGURE`) for your project
5. Start building

Methods and blueprints are independent — mix and match as needed.

---

## License

Private repository. Internal use only.
