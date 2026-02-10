# The Ultimate Claude Code Toolkit for Solo Founders (2025-2026)

> A comprehensive, research-backed guide to every tool, MCP server, plugin, agent framework, and system that makes Claude Code world-class for building a unicorn as a solo founder.

---

## Table of Contents

1. [Essential MCP Servers](#1-essential-mcp-servers)
2. [Claude Code Plugins & Extensions](#2-claude-code-plugins--extensions)
3. [Multi-Agent / Swarm Orchestration](#3-multi-agent--swarm-orchestration)
4. [Hooks & Automation](#4-hooks--automation)
5. [Memory & Knowledge Management](#5-memory--knowledge-management)
6. [Developer Productivity Tools (Complementary)](#6-developer-productivity-tools)
7. [Solo Founder / Unicorn Stack](#7-solo-founder--unicorn-stack)
8. [CLAUDE.md Best Practices](#8-claudemd-best-practices)
9. [Curated Lists & Directories](#9-curated-lists--directories)

---

## 1. Essential MCP Servers

MCP (Model Context Protocol) is Anthropic's open standard for connecting Claude to external tools. As of early 2026, there are 7,000+ MCP servers cataloged. Here are the best, organized by category.

### How to Add an MCP Server to Claude Code

```bash
# Local stdio server
claude mcp add <name> -- npx -y <package>

# Remote HTTP server
claude mcp add --transport http <name> <url>

# With environment variables
claude mcp add <name> -e KEY=value -- npx -y <package>
```

---

### A. Code & Version Control

| Server | What It Does | Install |
|--------|-------------|---------|
| **GitHub MCP** | PRs, issues, CI/CD, repo management | `claude mcp add github -- npx -y @modelcontextprotocol/server-github` |
| **GitLab MCP** | Merge requests, pipelines, code review | OAuth 2.0 via GitLab Premium/Ultimate |
| **Git MCP** | Local git operations, diffs, history | `claude mcp add git -- npx -y @modelcontextprotocol/server-git` |

### B. Databases

| Server | What It Does | Install |
|--------|-------------|---------|
| **Supabase MCP** | Full Supabase: DB, auth, storage, edge functions, migrations, TypeScript types | `claude mcp add supabase -- npx -y @supabase/mcp-server` with `SUPABASE_ACCESS_TOKEN` |
| **PostgreSQL MCP** | Read-only Postgres queries, schema inspection | `claude mcp add postgres -- npx -y @modelcontextprotocol/server-postgres` |
| **SQLite MCP** | Local SQLite database management | `claude mcp add sqlite -- npx -y @modelcontextprotocol/server-sqlite` |

- **Supabase GitHub**: https://github.com/supabase-community/supabase-mcp
- **Supabase Docs**: https://supabase.com/docs/guides/getting-started/mcp
- **Best Practice**: Use read-only mode for production data. Always scope to a dev project.

### C. Cloud & DevOps

| Server | What It Does | Install / Link |
|--------|-------------|----------------|
| **AWS MCP Servers (Official)** | Cloud Control API, IaC, Lambda, S3, Knowledge Base | https://github.com/awslabs/mcp |
| **AWS Managed MCP** | Hosted by AWS with IAM, CloudTrail audit logging | Remote HTTP via AWS |
| **Vercel MCP** | Deployment management, project creation, env vars | `claude mcp add --transport http vercel https://mcp.vercel.com` |
| **Cloudflare MCP** | Edge deployment, DNS, cache, Workers | Community MCP server |
| **Docker MCP** | Build, run, inspect containers | `claude mcp add docker -- npx -y @modelcontextprotocol/server-docker` |
| **Terraform MCP** | Infrastructure-as-Code lifecycle | Enterprise vendor-maintained |
| **Kubernetes MCP** | AI-driven K8s resource management | Community server |

### D. Documentation & Research

| Server | What It Does | Install |
|--------|-------------|---------|
| **Context7 MCP** | Up-to-date, version-specific docs for any library. Prevents hallucinated APIs | `claude mcp add context7 -- npx -y @upstash/context7-mcp@latest` |
| **Brave Search MCP** | Privacy-first web search with current results | `claude mcp add brave -- npx -y @modelcontextprotocol/server-brave-search` with `BRAVE_API_KEY` |
| **Perplexity MCP** | AI-synthesized research answers with citations | Community server via `@shaunmacfullstack/claude-perplexity-mcp` |
| **Fetch MCP** | Retrieve and process any URL content | `claude mcp add fetch -- npx -y @modelcontextprotocol/server-fetch` |

- **Context7 GitHub**: https://github.com/upstash/context7
- **Pro tip**: Add `use context7` to prompts or set up an auto-invocation rule to always pull fresh docs.

### E. Design & UI

| Server | What It Does | Install |
|--------|-------------|---------|
| **Figma MCP (Official)** | Live design data, auto-layout, tokens, component mapping | Desktop: enable in Figma Dev Mode. Remote: `claude mcp add --transport http figma https://mcp.figma.com/mcp` |
| **Magic UI MCP** | Production-ready React + Tailwind animation components | Community MCP server |
| **claude-talk-to-figma-mcp** | Full read/write Figma access via plugin API | https://github.com/arinspunk/claude-talk-to-figma-mcp |

- **Figma Setup Guide**: https://help.figma.com/hc/en-us/articles/32132100833559
- **Builder.io Guide**: https://www.builder.io/blog/claude-code-figma-mcp-server

### F. Productivity & Project Management

| Server | What It Does | Install |
|--------|-------------|---------|
| **Linear MCP** | Issue tracking, project management from terminal | `claude mcp add --transport http linear https://mcp.linear.app/mcp` |
| **Notion MCP** | Read/write Notion pages, databases, wikis | `claude mcp add --transport http notion https://mcp.notion.com/mcp` |
| **Slack MCP** | Search channels, draft messages, summarize threads | Via Composio or community server |
| **Task Master MCP** | PRD to structured tasks with AI-powered breakdown | `npm install -g task-master-ai` |
| **Google Drive MCP** | Search, summarize, organize cloud documents | `claude mcp add gdrive -- npx -y @modelcontextprotocol/server-gdrive` |

- **Task Master GitHub**: https://github.com/eyaltoledano/claude-task-master (15,500+ stars)
- **Linear Docs**: https://composio.dev/blog/how-to-set-up-linear-mcp-in-claude-code

### G. Payments & Commerce

| Server | What It Does | Install |
|--------|-------------|---------|
| **Stripe MCP (Official)** | Create customers, manage subscriptions, refunds, invoices | `claude mcp add --transport http stripe https://mcp.stripe.com` |

- **Stripe MCP Docs**: https://docs.stripe.com/mcp
- **Security**: Enable human confirmation. Never auto-approve financial operations.

### H. Monitoring & Observability

| Server | What It Does | Install |
|--------|-------------|---------|
| **Datadog MCP (Official)** | Query metrics, logs, traces, dashboards, incidents | `claude mcp add --transport http datadog https://mcp.datadoghq.com` |
| **Sentry / Claude Telemetry** | OpenTelemetry wrapper for Claude Code: traces, costs, usage | `pip install claude-telemetry` (https://github.com/TechNickAI/claude_telemetry) |
| **PostHog MCP** | Product analytics, events, feature flags | https://github.com/PostHog/mcp |

### I. Analytics

| Server | What It Does | Install |
|--------|-------------|---------|
| **PostHog MCP** | HogQL queries, user analytics, feature flags | Official PostHog MCP server |
| **Mixpanel MCP** | Events, funnels, cohorts, JQL queries | Via Composio |
| **Amplitude MCP** | Events, cohorts, user properties, analytics queries | Via Composio or Moonbird AI |

### J. Automation & Workflow

| Server | What It Does | Install |
|--------|-------------|---------|
| **n8n MCP** | Build, deploy, debug n8n workflows via natural language | https://github.com/czlonkowski/n8n-mcp |
| **Zapier MCP** | Cross-app workflow automation | Community server |
| **Composio (Rube)** | Universal MCP gateway to 850+ SaaS apps | https://composio.dev |

- **n8n Skills for Claude Code**: https://github.com/czlonkowski/n8n-skills
- **n8n MCP hosted**: https://www.n8n-mcp.com

### K. System & Terminal

| Server | What It Does | Install |
|--------|-------------|---------|
| **Filesystem MCP** | Secure file operations with permission controls | `claude mcp add fs -- npx -y @modelcontextprotocol/server-filesystem` |
| **Desktop Commander MCP** | Terminal control, process management, file operations | `claude mcp add desktop-commander -- npx -y @wonderwhy-er/desktop-commander` |
| **Playwright MCP** | Browser automation via accessibility trees | `claude mcp add playwright -- npx -y @anthropic/mcp-server-playwright` |
| **Puppeteer MCP** | Web interactions and browser tasks | `claude mcp add puppeteer -- npx -y @modelcontextprotocol/server-puppeteer` |

### L. AI & Reasoning

| Server | What It Does | Install |
|--------|-------------|---------|
| **Sequential Thinking MCP** | Structured, reflective problem-solving with revision capability | `claude mcp add thinking -- npx -y @modelcontextprotocol/server-sequential-thinking` |
| **Memory MCP** | Knowledge graph-based persistent memory | `claude mcp add memory -- npx -y @modelcontextprotocol/server-memory` |

---

## 2. Claude Code Plugins & Extensions

Plugins are now in public beta. Install with the `/plugin` command. They bundle skills, subagents, hooks, and MCP servers into installable units.

### Official Plugins (Anthropic)

| Plugin | What It Does |
|--------|-------------|
| **PR Code Review** | 5 parallel Sonnet agents for automated PR review with confidence scoring |
| **Plugin Dev Toolkit** | 7 expert skills + 8-phase guided workflow for building plugins |
| **Frontend Design** | Production-grade, creative UI code that avoids generic AI aesthetics |
| **Security Guidance** | Hooks that warn about command injection, XSS, unsafe patterns |

- **Official Plugin Repo**: https://github.com/anthropics/claude-code/tree/main/plugins

### Top Community Plugins

| Plugin | What It Does | Stars/Notes |
|--------|-------------|-------------|
| **Oh My Claude Code (OMC)** | 32 agents, 40 skills, 5 execution modes (Autopilot/Ultrapilot/Swarm/Pipeline/Ecomode) | 2.6k stars |
| **Compound Engineering** | 29 specialized agents, 25 commands, 16 skills that improve with use | Community favorite |
| **Session Memory Plugin** | Auto-captures sessions, compresses with AI, injects context into future sessions | By thedotmack |
| **Chrome DevTools MCP** | Inspect network requests, console errors, debug live pages | Underrated but essential |
| **Context7 Plugin** | Official Claude plugin for up-to-date documentation | https://claude.com/plugins/context7 |

### Plugin Marketplaces

- **claude-plugins.dev** - Community registry with CLI install
- **claudemarketplaces.com** - AI development tools marketplace
- **awesome-claude-plugins** (GitHub) - 4,413 repos indexed (as of Feb 2026)
  - https://github.com/quemsah/awesome-claude-plugins

### Editor Integrations

- **Claude Code for VS Code** - Official marketplace extension with inline diffs
- **claudecode.nvim** - Neovim integration (pure Lua)
- **claude-code-ide.el** - Emacs integration with ediff-based suggestions

---

## 3. Multi-Agent / Swarm Orchestration

### Official: Agent Teams (TeammateTool)

Shipped with Opus 4.6. Enable with:

```bash
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1
```

**Architecture:**
- **Team Lead** (your main session) creates the team, spawns teammates, assigns tasks, synthesizes results
- **Teammates** are separate Claude Code instances with their own context windows
- **Shared Task List** provides central work items (pending / in-progress / completed)
- Each agent works in an **independent Git Worktree** preventing code conflicts
- Agents work in **parallel** (frontend, backend, tests simultaneously)

### Third-Party Multi-Agent Frameworks

| Framework | What It Does | Stars | Link |
|-----------|-------------|-------|------|
| **Claude Flow** | Enterprise-grade orchestration with 60+ agents, RAG, distributed swarms | 12.9k | https://github.com/ruvnet/claude-flow |
| **Oh My Claude Code** | 32 agents, 5 execution modes, 3-tier memory, zero learning curve | 2.6k | Community plugin |
| **Claude Squad** | Manages multiple AI coding tools in one interface | 5.8k | GitHub |
| **ccswarm** | Rust-native multi-agent with Git worktree isolation | - | https://github.com/nwiizo/ccswarm |
| **Multiclaude** | Brownian ratchet approach: auto-merge if CI passes | - | By Dan Lorenc |

### Three Approaches

1. **Official Subagents** - Anthropic's built-in, production-ready
2. **Swarm Mode** - Experimental, feature-flagged TeammateTool
3. **Third-party frameworks** - Claude Flow, OMC, etc.

### When to Use Multi-Agent

Multi-agent does NOT make sense for 95% of tasks. Use it for:
- Large refactors spanning many files
- Parallel frontend + backend + tests development
- Tasks that naturally decompose into independent subtasks

**Key Stat**: Multi-agent system inquiries surged 1,445% from Q1 2024 to Q2 2025.

---

## 4. Hooks & Automation

Hooks are user-defined shell commands or LLM prompts that execute at specific lifecycle events.

### Lifecycle Events

| Event | When It Fires | Use Case |
|-------|--------------|----------|
| **SessionStart** | Session begins or resumes | Load dev context, set env vars |
| **PreToolUse** | Before a tool runs | Validate operations, enforce rules |
| **PostToolUse** | After a tool completes | Run tests, format code, notify |
| **PreCompact** | Before context compaction | Save important state |
| **SessionEnd** | Session ends | Cleanup, log stats, save state |

### Hook Examples

**Auto-run tests after file changes:**
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write|Edit",
      "command": "npm test -- --related ${FILE}"
    }]
  }
}
```

**Slack notification when task completes:**
```json
{
  "hooks": {
    "SessionEnd": [{
      "command": "curl -X POST $SLACK_WEBHOOK -d '{\"text\": \"Claude Code session completed\"}'"
    }]
  }
}
```

**Auto-format on save:**
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write",
      "command": "npx prettier --write ${FILE}"
    }]
  }
}
```

### CI/CD Integration

- **GitHub Actions (Official)**: `anthropics/claude-code-action` - AI-powered PR reviews, code generation
- **Headless Mode**: `claude -p "<prompt>" --output-format stream-json` for CI pipelines
- **Git Hooks**: AI-powered pre-commit security checks, deployment validation

### Advanced Automation Frameworks

- **Ralph for Claude Code** - Autonomous AI dev framework with intelligent exit detection, rate limiting, circuit breakers, tmux monitoring, 75+ tests
- **Claude Flow CI/CD** - Pre-task hooks, post-edit hooks, notification hooks with telemetry

### Hooks Reference
- https://code.claude.com/docs/en/hooks

---

## 5. Memory & Knowledge Management

### Built-in Memory Systems

**Auto Memory** (Built-in, 2026):
- Claude automatically saves project patterns, key commands, preferences
- Stored at `~/.claude/projects/<project>/memory/`
- `MEMORY.md` acts as index; first 200 lines loaded into system prompt
- Topic files (`debugging.md`, `patterns.md`) loaded on demand
- Enable: `CLAUDE_CODE_DISABLE_AUTO_MEMORY=0`

**Session Memory** (Built-in, 2026):
- Automatic background summarization of sessions
- "Recalled X memories" at session start
- "Wrote X memories" during session
- Stored at `~/.claude/projects/[project]/[session]/session_memory`
- Compaction is now instant thanks to continuous background summarization

### Third-Party Memory Solutions

| Solution | Approach | Install |
|----------|---------|---------|
| **Claude-Mem** | SQLite + FTS5 search, ~10x token reduction via progressive disclosure | `/plugin marketplace add thedotmack/claude-mem` |
| **Memory-MCP** | Two-tier system (CLAUDE.md + deep store), LLM-powered extraction, auto git snapshots | `npm install -g claude-code-memory` |
| **MCP Knowledge Graph** | Persistent memory via local knowledge graph with entities/observations | https://github.com/shaneholloman/mcp-knowledge-graph |
| **Neo4j Memory Server** | Graph database for relationship mapping, contextual dev assistance | Community MCP server |
| **Code-Graph-RAG** | Tree-sitter-based codebase knowledge graph with NL queries | https://github.com/vitali87/code-graph-rag |
| **Supermemory** | Plug-and-play memory APIs: vector + graph retrieval, evaluation | Claude Code plugin available |

### Memory Architecture Approaches

1. **Vector Search (Embeddings)** - Good for semantic similarity. Use sqlite-vec or Pinecone.
2. **Knowledge Graphs** - Good for structured relationships. Use Neo4j or local graph.
3. **Hybrid (RAG + Graph)** - Best of both. "RAGs are divergent thinking, Graphs are convergent thinking."
4. **SQLite + sqlite-vec** - Lightweight, zero-config, single-file. Often sufficient for solo dev.

### Context Management Best Practices

- Use `/compact` for instant context compression
- Avoid the last 20% of context window for multi-file work
- `/clear` aggressively between unrelated tasks
- Use CLAUDE.md for static context, auto memory for dynamic

---

## 6. Developer Productivity Tools (Complementary)

### AI Coding Tool Comparison (2026)

| Tool | Interface | Best For | Price | Rating |
|------|-----------|----------|-------|--------|
| **Claude Code** | Terminal/CLI | Large codebases, architecture, reasoning | ~$20/mo (Pro) | 4.5/5 |
| **Cursor** | AI-native IDE (VS Code fork) | Daily coding, structured workflows, Composer v3 refactors | $20/mo Pro, $200/mo Ultra | 4.9/5 |
| **Windsurf** | AI-native IDE | Enterprise-scale, persistent context ("Flow") | $15/mo (500 credits) | - |
| **Aider** | CLI (git-native) | Structured refactors, bring-your-own-model | Free (BYOK) | - |
| **GitHub Copilot** | VS Code extension + Agent HQ | Quick completions, inline suggestions | $10-39/mo | - |

### Best Strategy: Combine Tools

Many top developers run **Cursor or Windsurf for daily coding** while keeping **Claude Code open for big-picture reasoning, architecture decisions, and complex multi-file changes**.

**Claude Code + Cursor Integration**: The Claude Code Cursor extension gives you Claude's reasoning + Cursor's IDE workflow.

### Testing Frameworks Optimized for AI

| Tool | What It Does |
|------|-------------|
| **Playwright MCP + Agents** | Planner, Generator, Healer agents for automated E2E testing |
| **Playwright Skill Plugin** | Claude writes and executes Playwright automation on-the-fly |
| **Vitest** | Auto-detected by Claude from package.json; generates Vue Test Utils |
| **Jest / React Testing Library** | Auto-detected; Claude generates RTL component tests |
| **Cypress** | Command-based automation, auto-detected |

- **Playwright Skill**: https://github.com/lackeyjb/playwright-skill
- Claude **auto-detects** your testing framework from package.json and generates appropriate tests.

### Task Management

| Tool | What It Does | Link |
|------|-------------|------|
| **Task Master AI** | PRD -> structured tasks with AI breakdown, dependency management | https://github.com/eyaltoledano/claude-task-master |
| **PRD Taskmaster** | "I have an idea" -> complete, validated PRD in minutes | https://github.com/anombyte93/prd-taskmaster |

Task Master workflow:
1. Write detailed PRD at `.taskmaster/docs/prd.txt`
2. Run `task-master parse-prd` to generate tasks
3. Use `task-master next` to get the next task
4. Claude Code works through tasks sequentially

---

## 7. Solo Founder / Unicorn Stack

### The State of Solo Founding (2026)

- **36.3%** of all new global startups are solo-founded
- AI unicorns reach $1B valuation in **~2 years** (vs 9 years for non-AI)
- Dario Amodei (Anthropic CEO) predicted the one-person unicorn by 2026
- 65% of US deal value in Jan 2026 flows into AI-centric ventures

### Notable Solo Founder Exits

- **Base44**: Solo founder, $80M exit to Wix in 6 months, 300K users
- **n8n**: Solo-founded side project -> $2.5B valuation
- **Lovable**: 45 employees, unicorn in 8 months
- **Cursor**: $500M ARR with <50 employees
- **Gumloop**: $17M Series A with 2 full-time staff

### The Recommended Solo Founder AI Stack

```
DEVELOPMENT
├── Claude Code (primary reasoning + architecture)
├── Cursor or Windsurf (daily IDE coding)
├── Task Master AI (PRD -> tasks -> execution)
├── GitHub Actions + Claude Code Action (CI/CD)
└── Playwright agents (automated testing)

INFRASTRUCTURE
├── Vercel (frontend hosting, Next.js)
├── Supabase (database, auth, storage, edge functions)
├── Cloudflare Workers (edge compute, DNS)
├── Stripe MCP (payments)
└── Docker MCP (containerization)

DESIGN
├── Figma MCP (design -> code pipeline)
├── Magic UI MCP (animation components)
├── v0.dev (UI generation)
└── Frontend Design plugin (production-grade UI)

PRODUCTIVITY
├── Linear MCP (issue tracking)
├── Notion MCP (knowledge base, docs)
├── Slack MCP (communication)
├── n8n MCP (workflow automation)
└── Composio (850+ SaaS integrations)

ANALYTICS & MONITORING
├── PostHog MCP (product analytics)
├── Datadog MCP (infrastructure monitoring)
├── Sentry / Claude Telemetry (error tracking)
└── Mixpanel/Amplitude MCP (user behavior)

RESEARCH & CONTEXT
├── Context7 MCP (up-to-date library docs)
├── Brave Search MCP (web search)
├── Perplexity MCP (synthesized research)
└── Sequential Thinking MCP (complex reasoning)

MEMORY
├── Auto Memory (built-in)
├── Session Memory (built-in)
├── Claude-Mem plugin (cross-session context)
└── Memory-MCP (persistent + git snapshots)
```

### Deployment Automation

Claude Code can now handle end-to-end deployment:
1. Create projects on Vercel/Cloudflare
2. Set environment variables
3. Debug build failures
4. SSH into servers and inspect logs
5. Manage DNS on Cloudflare

**Cost efficiency**: ~$7-8/month for 30+ backends + 40+ frontends using Vercel (free) + Cloudflare (free) + Hetzner VPS.

---

## 8. CLAUDE.md Best Practices

### File Placement

| Location | Scope | Notes |
|----------|-------|-------|
| `~/.claude/CLAUDE.md` | All sessions globally | Personal preferences |
| `./CLAUDE.md` | Project root, shared via git | Team standards |
| `./CLAUDE.local.md` | Project root, .gitignored | Personal project overrides |
| `./subfolder/CLAUDE.md` | Loaded when working in subfolder | Module-specific rules |

### What to Include (Sweet Spot: 100-200 Lines)

```markdown
# Project: [Name]

## Tech Stack
- Framework: Next.js 15 (App Router)
- Language: TypeScript strict mode
- Database: Supabase (PostgreSQL)
- Styling: Tailwind CSS + shadcn/ui
- State: Zustand
- Testing: Vitest + Playwright

## Architecture
- `src/app/` - Next.js App Router pages
- `src/components/` - Reusable UI components
- `src/lib/` - Utility functions and API clients
- `src/stores/` - Zustand state management
- `supabase/migrations/` - Database migrations

## Commands
- `npm run dev` - Start dev server
- `npm run build` - Production build
- `npm run test` - Run Vitest
- `npm run test:e2e` - Run Playwright
- `npm run lint` - ESLint check

## Rules
- MUST use TypeScript strict mode
- MUST write tests for all new components
- MUST use ES modules, never CommonJS
- MUST handle errors with proper try/catch
- MUST use Supabase RLS policies for data access
- NEVER commit .env files or secrets
- NEVER use `any` type
```

### Key Principles

1. **Be directive, not suggestive**: "MUST use TypeScript" not "Prefer TypeScript"
2. **Keep it concise**: Every line competes for attention with actual work
3. **Use subfolder overrides**: Move module-specific rules to `subfolder/CLAUDE.md`
4. **Start with `/init`**: Generates a starter file, then delete what you don't need
5. **Context is king**: Obsessively manage context with CLAUDE.md + `/clear` + memory systems
6. **Follow the pattern**: Plan -> small diff -> tests -> review. Never skip steps.

### Maturity Levels

- **L0 Absent** - No file
- **L1 Basic** - File exists, tracked
- **L2 Scoped** - Project-specific constraints
- **L3 Structured** - External references, modular
- **L4 Abstracted** - Path-scoped loading
- **L5 Maintained** - Structural discipline
- **L6 Adaptive** - Dynamic context, skills, MCP integration

### Showcase Template
- https://github.com/ChrisWiles/claude-code-showcase - Complete project config with hooks, skills, agents, commands, and GitHub Actions workflows

---

## 9. Curated Lists & Directories

### Awesome Lists (GitHub)

| List | Scope | Link |
|------|-------|------|
| **punkpeye/awesome-mcp-servers** | Most popular MCP server list | https://github.com/punkpeye/awesome-mcp-servers |
| **wong2/awesome-mcp-servers** | Official + community servers | https://github.com/wong2/awesome-mcp-servers |
| **appcypher/awesome-mcp-servers** | Production-ready + experimental | https://github.com/appcypher/awesome-mcp-servers |
| **TensorBlock/awesome-mcp-servers** | 7,260+ servers cataloged | https://github.com/TensorBlock/awesome-mcp-servers |
| **modelcontextprotocol/servers** | Official reference implementations | https://github.com/modelcontextprotocol/servers |
| **hesreallyhim/awesome-claude-code** | Skills, hooks, commands, plugins | https://github.com/hesreallyhim/awesome-claude-code |
| **jmanhype/awesome-claude-code** | Plugins, MCP servers, editor integrations | https://github.com/jmanhype/awesome-claude-code |
| **ComposioHQ/awesome-claude-skills** | Claude Skills collection | https://github.com/ComposioHQ/awesome-claude-skills |
| **quemsah/awesome-claude-plugins** | 4,413 repos indexed, auto-tracked | https://github.com/quemsah/awesome-claude-plugins |

### Directories & Marketplaces

| Directory | URL |
|-----------|-----|
| **mcp-awesome.com** | https://mcp-awesome.com/ (1,200+ quality-verified servers) |
| **claude-plugins.dev** | https://claude-plugins.dev/ (Community plugin registry with CLI) |
| **claudemarketplaces.com** | https://claudemarketplaces.com/ (Plugin marketplace) |
| **Composio Toolkits** | https://composio.dev/ (850+ SaaS integrations) |
| **Glama MCP Directory** | https://glama.ai/mcp/servers |
| **PulseMCP** | https://www.pulsemcp.com/ |
| **claudefa.st** | https://claudefa.st/blog/tools/mcp-extensions/best-addons |

### Documentation

| Resource | URL |
|----------|-----|
| **Claude Code Official Docs** | https://code.claude.com/docs/en/ |
| **Claude Code Best Practices** | https://code.claude.com/docs/en/best-practices |
| **Claude Code Hooks Reference** | https://code.claude.com/docs/en/hooks |
| **Claude Code Memory Docs** | https://code.claude.com/docs/en/memory |
| **Claude Code MCP Docs** | https://code.claude.com/docs/en/mcp |
| **Claude Code Plugins Docs** | https://code.claude.com/docs/en/plugins |

---

## Quick Start: The "Solo Founder Starter Kit"

If you want to get up and running fast, here are the highest-impact tools to install first:

```bash
# 1. Essential MCP Servers
claude mcp add context7 -- npx -y @upstash/context7-mcp@latest
claude mcp add supabase -- npx -y @supabase/mcp-server
claude mcp add --transport http stripe https://mcp.stripe.com
claude mcp add --transport http linear https://mcp.linear.app/mcp
claude mcp add --transport http notion https://mcp.notion.com/mcp
claude mcp add brave -- npx -y @modelcontextprotocol/server-brave-search
claude mcp add playwright -- npx -y @anthropic/mcp-server-playwright
claude mcp add github -- npx -y @modelcontextprotocol/server-github
claude mcp add thinking -- npx -y @modelcontextprotocol/server-sequential-thinking

# 2. Task Management
npm install -g task-master-ai

# 3. Memory (install the plugin)
# /plugin marketplace add thedotmack/claude-mem
# /plugin install claude-mem

# 4. Enable Agent Teams (experimental)
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 5. Initialize your project
claude /init
```

Then create your `CLAUDE.md`, write your PRD, parse it with Task Master, and start building.

---

*Research compiled: February 8, 2026*
*Sources: 50+ web searches across developer blogs, GitHub repositories, official documentation, and industry reports.*
