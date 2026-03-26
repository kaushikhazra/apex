# APEX Scaled Agile (SAFe) Methodology

This document describes how to adopt the APEX agent-based SAFe SDLC in your project. Copy the `.claude/` folder from this directory into your project root to get started.

---

## Agent Hierarchy

APEX maps SAFe's organizational structure to a five-level agent hierarchy. Each level owns a distinct scope of decision-making.

| Level | Agents | Scope |
|-------|--------|-------|
| **Portfolio** | Portfolio Manager, Epic Owner, Enterprise Architect | Strategic planning, investment decisions, value stream funding, enterprise standards |
| **Solution** | Solution Manager, Solution Architect, Solution Train Engineer | Solution vision, integration architecture, cross-ART coordination, NFRs |
| **Program (ART)** | Release Train Engineer, Product Manager, System Architect, Business Owner, Product Owner, Scrum Master | PI planning, feature definition, program backlog, team coordination, impediment resolution |
| **Team** | Developer, QA/Tester, DevOps, UX Designer, System Team, Shared Services | Code, tests, CI/CD, design, platform support, reusable components |
| **Pipeline** | Continuous Exploration, Continuous Integration, Continuous Deployment, Release on Demand | Build automation, test execution, environment management, feature toggles, canary releases |

Work flows downward: Portfolio epics decompose into solution capabilities, then program features, then team-level user stories, then pipeline execution.

---

## Agent Personas

Agent persona files live in `.claude/agents/`. Each file defines a single SAFe role with:

- **Persona**: Who the agent is and what expertise it brings
- **Task**: Specific responsibilities (what the agent does)
- **Constraint**: Guardrails and escalation rules (what the agent cannot do without human approval)
- **Communication Style**: Tone and vocabulary appropriate to the role's level
- **Memory & Context Management**: Per-agent state stored in `/.apex/{agent-name}/memory.json`
- **Output**: Document templates the agent produces, with required data fields

Available agents:

| File | SAFe Role | Level |
|------|-----------|-------|
| `portfolio-manager.md` | Portfolio Manager | Portfolio |
| `epic-owner.md` | Epic Owner | Portfolio |
| `enterprise-architect.md` | Enterprise Architect | Portfolio |
| `solution-manager.md` | Solution Manager | Solution |
| `solution-architect.md` | Solution Architect | Solution |
| `release-train-engineer.md` | Release Train Engineer | Program |
| `product-manager.md` | Product Manager | Program |
| `system-architect.md` | System Architect | Program |
| `product-owner.md` | Product Owner | Program |
| `scrum-master.md` | Scrum Master | Program |
| `business-owner.md` | Business Owner | Program |
| `developer.md` | Developer | Team |
| `quality-assurance.md` | QA/Tester | Team |
| `devops.md` | DevOps Engineer | Team |
| `ux-designer.md` | UX Designer | Team |

---

## Commands

Command files live in `.claude/commands/`. Each command is a slash-command interface to an agent. Running `/command-name <request>` launches the corresponding agent via the Task tool with structured instructions.

Command files follow the template in `templates/command_template.md`:

```
---
description: [What the command does]
argument-hint: [Expected input]
---
## Context
[When to use this command]

## Task
Use the Task tool to launch the [agent-name] agent with:
- Agent Task: [specific task]
- Input: [what the command receives]
- Instructions: [step-by-step agent behavior]
```

Each agent has a matching command file (e.g., `commands/product-owner.md` launches the Product Owner agent). Use the command that matches the SAFe role responsible for the work you need done.

---

## Human-in-the-Loop Control Points

Agents cannot act autonomously on high-impact decisions. Humans intervene at defined gates:

| Level | Human Role | Approval Authority |
|-------|-----------|-------------------|
| Portfolio | Executive Sponsor | Epic approval, budget allocation, strategic pivots |
| Solution | Solution Stakeholder | Architecture reviews, integration approvals, risk mitigation |
| Program | Program Manager | Feature acceptance, PI sign-offs, backlog prioritization |
| Team | Tech Lead | Code reviews, quality gates, deployment approvals |
| Pipeline | Release Manager | Build approvals, release go/no-go, production monitoring |

**Scaling rules**:
- A single human can oversee multiple levels (common in smaller organizations)
- Multiple humans can share responsibilities at any level
- Default mode is exception-based: agents operate autonomously until they hit a constraint that requires escalation
- Every agent's constraint section defines exactly when human approval is required

---

## User Story Template

User stories follow the template in `templates/user-story-template.md`. All stories must include:

| Section | Content |
|---------|---------|
| **User Story** | As a / I want / So that |
| **Story Points** | Numeric estimate |
| **Priority** | Must Have or Good To Have, with Sprint assignment |
| **Acceptance Criteria** | When / Then / And format, numbered |
| **Definition of Done** | Checklist of completion conditions |
| **Technical Notes** | Implementation guidance |
| **Dependencies** | Blockers or upstream requirements |
| **Risks** | Known risks to delivery |

The Product Owner agent produces stories in this format. Other agents reference it when decomposing work.

---

## File Organization

When this methodology is adopted into a project, the expected directory structure is:

```
your-project/
  .claude/
    agents/              # Agent persona files (one per SAFe role)
      portfolio-manager.md
      product-owner.md
      developer.md
      ...
    commands/            # Slash-command files (one per agent)
      portfolio-manager.md
      product-owner.md
      developer.md
      ...
  .apex/                 # Runtime agent state (created automatically)
    portfolio-manager/
      memory.json        # Agent memory: requests and actions taken
      archive-memory.json # Archived memory after feature completion
    product-owner/
      memory.json
      ...
  PDs/                   # Product Documents (agent outputs)
    portfolio/
      strategy/          # Portfolio strategy documents
      decisions/         # Investment decision records
      reports/           # Portfolio performance reports
    ...
```

**Key conventions**:
- Agent personas go in `.claude/agents/`, commands in `.claude/commands/`
- Agent runtime memory goes in `.apex/{agent-name}/`
- Agents archive their `memory.json` to `archive-memory.json` after each feature completes
- Product documents (strategies, decisions, stories, designs) go under `PDs/`
- Templates for commands and user stories live in `templates/`

---

## Adoption Checklist

1. Copy `.claude/agents/` and `.claude/commands/` into your project
2. Copy `templates/` for user story and command templates
3. Identify which SAFe levels apply to your project size (small projects may skip Portfolio and Solution levels)
4. Assign human roles to control points -- one person can cover multiple levels
5. Start using slash commands: `/product-owner define login feature`, `/developer implement US001`, etc.
6. Agents will create their `.apex/` memory folders on first use
7. Review agent outputs at the defined approval gates before they flow to the next level
