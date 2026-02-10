# Claude Code Beast Mode: Your Complete Arsenal Guide

> Everything installed on your machine, what it does, and how to use it to ship like a solo unicorn founder.

---

## Table of Contents

1. [Your Setup at a Glance](#1-your-setup-at-a-glance)
2. [MCP Servers - Your Superpowers](#2-mcp-servers---your-superpowers)
3. [Plugins - Your Agent Army](#3-plugins---your-agent-army)
4. [Hooks - Your Autopilot](#4-hooks---your-autopilot)
5. [Agent Teams - Your Swarm](#5-agent-teams---your-swarm)
6. [Custom Commands & Skills](#6-custom-commands--skills)
7. [Memory System - Your Brain](#7-memory-system---your-brain)
8. [CLAUDE.md - Your Rulebook](#8-claudemd---your-rulebook)
9. [Task Master AI - Your PM](#9-task-master-ai---your-pm)
10. [Complementary Tools](#10-complementary-tools)
11. [The Solo Founder Workflow](#11-the-solo-founder-workflow)
12. [Daily Operations Cheat Sheet](#12-daily-operations-cheat-sheet)
13. [Advanced Techniques](#13-advanced-techniques)
14. [What Needs Your Auth Keys](#14-what-needs-your-auth-keys)
15. [Troubleshooting](#15-troubleshooting)
16. [Future Upgrades to Watch](#16-future-upgrades-to-watch)

---

## 1. Your Setup at a Glance

```
SUBSCRIPTION: Claude Code Pro Max (20x rate limit)
MODEL: Claude Opus 4.6 (primary) + Claude Sonnet 4 (bulk tasks)
MACHINE: Windows, RTX 4090 16GB, Ollama local LLMs

MCP SERVERS: 12 global + 9 project-specific
PLUGINS: 27 official + 15 external (42 total)
HOOKS: 7 lifecycle events covered
AGENT TEAMS: Enabled (experimental)
CUSTOM COMMANDS: 2 (generate-prp, execute-prp)
TASK MASTER AI: v0.43.0 installed
LOCAL LLM: Qwen2.5-Coder:14B + Qwen2.5:3B (dual-model)
```

---

## 2. MCP Servers - Your Superpowers

MCP servers give Claude real-time access to external tools and services. They run as background processes and Claude calls them automatically when relevant.

### Currently Active Global Servers

| Server | What It Does | How to Use |
|--------|-------------|------------|
| **browser-tools** | Inspect browser tabs, take screenshots, check console errors, run audits | Just ask: "take a screenshot" or "check console errors" or "run accessibility audit" |
| **context7** | Pulls live, version-specific documentation for any library | Add `use context7` to any prompt, e.g. "how do I use Next.js App Router? use context7" |
| **github-mcp** | Create repos, PRs, issues, manage CI/CD from terminal | "Create a GitHub issue for...", "List open PRs", "Create a new repo called..." |
| **sequential-thinking** | Structured reasoning for complex problems - thinks step by step with revision | Activated automatically for complex reasoning. Or ask: "think through this step by step" |
| **playwright-mcp** | Browser automation - navigate, click, fill forms, screenshot, test | "Navigate to localhost:3000 and test the login flow", "Fill out the signup form" |
| **memory** | Persistent knowledge graph memory across sessions | "Remember that the API key format is...", "What do you remember about...?" |
| **vercel** | Deploy to Vercel, manage projects, env vars, domains | "Deploy this to Vercel", "List my Vercel projects", "Set env var X on project Y" |
| **stripe** | Payments, subscriptions, customers, invoices, refunds | "Create a Stripe customer", "List recent payments", "Set up a subscription plan" |
| **linear** | Issue tracking, project management, sprints | "Create a Linear issue for...", "What's in the current sprint?", "Mark issue as done" |
| **notion** | Read/write Notion pages, databases, wikis | "Search my Notion for...", "Create a new page in...", "Update the roadmap" |
| **figma** | Read design files, extract tokens, component specs | "Get the design specs for the login page", "What colors are used in the header?" |
| **docker** | Build, run, inspect, manage containers | "Build the Dockerfile", "List running containers", "Show logs for container X" |

### How to Manage MCP Servers

```bash
# List all servers and their health
claude mcp list

# Add a new server (globally)
claude mcp add <name> -- npx -y <package>

# Add an HTTP server
claude mcp add <name> --transport http <url>

# Remove a server
claude mcp remove <name>

# Add with environment variable
claude mcp add <name> -e API_KEY=xxx -- npx -y <package>
```

### Project-Specific Servers (feature-dev project)

These are only active when working in `D:\YC-PG\feature-dev\design-assess`:

| Server | Purpose |
|--------|---------|
| semgrep | Security scanning (SAST) |
| exa | AI-powered web search |
| firecrawl | Web scraping and crawling |
| mcp-obsidian | Obsidian vault access |
| memory-bank-mcp | Persistent memory bank |
| neo4j-memory-server | Graph-based relationship memory |

### Servers You Can Add Anytime

```bash
# Web search (needs API key from https://brave.com/search/api/)
claude mcp add brave-search -- npx -y @modelcontextprotocol/server-brave-search -e BRAVE_API_KEY=<key>

# Supabase (needs access token from https://supabase.com/dashboard/account/tokens)
claude mcp add supabase -- npx -y @supabase/mcp-server -e SUPABASE_ACCESS_TOKEN=<token>

# PostHog analytics (needs API key from https://posthog.com)
claude mcp add posthog -- npx -y @posthog/mcp-server -e POSTHOG_API_KEY=<key>

# Filesystem (explicit file access)
claude mcp add filesystem -- npx -y @modelcontextprotocol/server-filesystem <path>

# Datadog monitoring
claude mcp add datadog --transport http https://mcp.datadoghq.com

# n8n workflow automation
claude mcp add n8n -- npx -y @czlonkowski/n8n-mcp
```

---

## 3. Plugins - Your Agent Army

Plugins bundle skills, subagents, hooks, and MCP servers into installable units. They extend Claude's capabilities without manual configuration.

### How to Use Plugins

```bash
# List installed plugins
/plugins

# Install from marketplace
/plugin marketplace add <author>/<plugin-name>
/plugin install <plugin-name>

# Enable/disable a plugin
/plugin enable <plugin-name>
/plugin disable <plugin-name>
```

### Your Most Powerful Installed Plugins

| Plugin | What It Does | When to Use |
|--------|-------------|-------------|
| **feature-dev** | 3-agent system (explorer, architect, reviewer) for building features | "Build a new feature for X" or `/feature-dev` |
| **frontend-design** | Production-grade UI code, avoids generic AI aesthetics | When building UIs: "Design a dashboard page" |
| **code-review** | 5 parallel Sonnet agents review PRs with confidence scoring | Before merging: "Review this PR" |
| **pr-review-toolkit** | Deep PR analysis with security and performance checks | `/pr-review` |
| **security-guidance** | Warns about XSS, injection, unsafe patterns as you code | Always active - watches for security issues |
| **code-simplifier** | Identifies over-engineering and simplifies code | "Simplify this function" or "Is this over-engineered?" |
| **commit-commands** | Smart git commits with conventional messages | `/commit` |
| **plugin-dev** | Build your own plugins with 7 expert skills | When creating custom plugins |
| **typescript-lsp** | TypeScript language server for type checking | Auto-active in TS projects |
| **pyright-lsp** | Python type checking via Pyright | Auto-active in Python projects |
| **agent-sdk-dev** | Build custom Claude agents using the Agent SDK | When building agent systems |
| **playground** | Interactive code experimentation | Quick prototyping |
| **hookify** | Generate and manage hooks via natural language | "Create a hook that runs tests after edits" |
| **claude-md-management** | Manage CLAUDE.md files across projects | "Update my CLAUDE.md" |
| **claude-code-setup** | Setup and configure Claude Code optimally | Initial project setup |

### External Plugins Available

These are from third-party developers in the marketplace:

| Plugin | What It Does |
|--------|-------------|
| **Supabase** | Deep Supabase integration (DB, auth, storage, RLS) |
| **Firebase** | Firebase project management |
| **GitHub** | Enhanced GitHub workflows beyond the MCP server |
| **Playwright** | Enhanced testing workflows |
| **Slack** | Team communication integration |
| **Stripe** | Enhanced payment workflow support |
| **Linear** | Enhanced project management |
| **Greptile** | Codebase search and understanding |
| **Serena** | Code navigation and analysis |

### Plugins to Add Next

```bash
# Oh My Claude Code - 32 agents, 40 skills, 5 execution modes
/plugin marketplace add omc

# Claude-Mem - Cross-session memory with 10x token reduction
/plugin marketplace add thedotmack/claude-mem

# Compound Engineering - 29 agents, 25 commands, 16 self-improving skills
/plugin marketplace add compound-engineering
```

---

## 4. Hooks - Your Autopilot

Hooks are shell commands that fire automatically at specific lifecycle events. Your setup uses them to send voice notifications to a local service on port 3456.

### Your Current Hook Events

| Event | What Fires | Your Setup Does |
|-------|-----------|----------------|
| **SessionStart** | When a new session begins | Speaks "Session started" |
| **PreToolUse** | Before any Bash command runs | Speaks "Executing command" |
| **PostToolUse** | After any tool completes | Speaks "Task completed" / "File created" / "File modified" |
| **UserPromptSubmit** | When you send a message | Speaks "Processing request" |
| **PostToolUseFailure** | When a tool fails | Speaks "Error occurred" |
| **PreCompact** | Before context window compresses | Speaks "Compacting context" |
| **SessionEnd** | When session ends | Speaks "Session ended" |

### How Hooks Work

Hooks are defined in `~/.claude/settings.json`. Each hook has:
- **Event**: When it fires
- **Matcher** (optional): Only fires for specific tools (e.g., "Write", "Edit|MultiEdit", "Bash")
- **Command**: The shell command to execute

### Adding Custom Hooks

Edit `~/.claude/settings.json` or use the **hookify** plugin:

```
"Create a hook that runs prettier on any file I write"
"Create a hook that runs tests after file edits"
"Create a hook that logs all bash commands to a file"
```

### Hook Ideas for Solo Founders

| Hook | Event | What It Does |
|------|-------|-------------|
| Auto-format | PostToolUse (Write) | Run prettier/eslint on saved files |
| Auto-test | PostToolUse (Edit) | Run related tests after file changes |
| Git auto-stage | PostToolUse (Write) | Auto `git add` new files |
| Slack notify | SessionEnd | Post session summary to Slack |
| Cost tracking | SessionEnd | Log token usage and estimated cost |
| Security scan | PostToolUse (Write) | Run semgrep on changed files |
| Screenshot | PostToolUse (Bash) | Auto-screenshot after dev server starts |

---

## 5. Agent Teams - Your Swarm

Agent Teams let Claude spawn multiple parallel agents that work on different parts of a task simultaneously. This is now enabled on your machine.

### How It Works

```
YOU (Team Lead session)
  ├── Teammate 1: Frontend (own git worktree, own context)
  ├── Teammate 2: Backend (own git worktree, own context)
  ├── Teammate 3: Tests (own git worktree, own context)
  └── Shared Task List (coordination layer)
```

Each teammate:
- Gets its own Claude Code instance
- Works in its own git worktree (no merge conflicts)
- Has its own context window
- Reports back to the Team Lead
- Can be assigned specific files/tasks

### How to Use Agent Teams

Agent Teams activate automatically when you give Claude a task that decomposes naturally. You can also explicitly request it:

```
"Build a full-stack feature with auth: create the API routes,
the React components, and the tests in parallel"

"Refactor the authentication system - have one agent handle the
backend changes and another handle the frontend updates"

"Set up the project: one agent handles the database schema,
another sets up the API layer, another does the UI scaffold"
```

### When to Use Agent Teams

**Good for:**
- Full-stack features (frontend + backend + tests)
- Large refactors spanning many files
- Setting up new projects with multiple layers
- Running tests while building features

**Not good for:**
- Small, focused tasks (adds overhead)
- Tasks with heavy dependencies between parts
- Quick fixes or single-file changes

### Third-Party Swarm Tools

| Tool | What It Does | Install |
|------|-------------|---------|
| **Claude Flow** | Enterprise-grade 60+ agent orchestration | `npm install -g @ruvnet/claude-flow` |
| **Claude Squad** | Manage multiple AI coding tools in one interface | GitHub: claude-squad |
| **ccswarm** | Rust-native multi-agent with git worktree isolation | GitHub: nwiizo/ccswarm |

---

## 6. Custom Commands & Skills

### Your Installed Commands

| Command | What It Does | How to Invoke |
|---------|-------------|---------------|
| **generate-prp** | Analyzes your codebase, researches externally, generates a comprehensive Product Requirements Prompt | `/generate-prp` or ask "generate a PRP for feature X" |
| **execute-prp** | Takes a PRP and implements it in 4 phases: Foundation, Core Logic, Integration, Polish | `/execute-prp` or ask "execute this PRP" |

### The PRP Workflow

This is your most powerful custom workflow:

```
Step 1: /generate-prp "I need a user dashboard with analytics"
        -> Claude researches, analyzes codebase, generates full PRP

Step 2: Review the PRP, adjust requirements

Step 3: /execute-prp
        -> Phase 1: Foundation (file structure, configs, types)
        -> Phase 2: Core Logic (business logic, API routes)
        -> Phase 3: Integration (connect frontend to backend)
        -> Phase 4: Polish (error handling, edge cases, tests)
        -> Each phase has validation gates
```

### Built-in Skills Available

| Skill | What It Does |
|-------|-------------|
| `/init` | Initialize a new project with CLAUDE.md, proper structure |
| `/compact` | Compress context window (instant now) |
| `/clear` | Clear context and start fresh |
| `/review` | Review current code changes |
| `/commit` | Smart git commit with conventional message |
| `/help` | Show all available commands |

---

## 7. Memory System - Your Brain

### Three Memory Layers

**Layer 1: Auto Memory (Built-in, Always Active)**
- Claude automatically remembers project patterns, key commands, preferences
- Stored at `~/.claude/projects/<project>/memory/`
- First 200 lines of `MEMORY.md` loaded into every prompt
- Topic files loaded on demand

**Layer 2: Session Memory (Built-in, Always Active)**
- Automatic background summarization of your sessions
- "Recalled X memories" appears at session start
- Context survives compaction and restarts
- Stored at `~/.claude/projects/<project>/session_memory/`

**Layer 3: MCP Memory Server (New - Knowledge Graph)**
- Persistent knowledge graph with entities and relationships
- Explicitly tell Claude to remember: "Remember that X relates to Y"
- Query: "What do you remember about the auth system?"
- Survives across all sessions and projects

### How to Use Memory Effectively

```
# Explicitly store important context
"Remember that the production database is on Supabase project xyz"
"Remember that the Stripe webhook secret is stored in STRIPE_WEBHOOK_SECRET env var"
"Remember that we use Zustand for state management in this project"

# Query memory
"What do you remember about our deployment process?"
"What patterns have you noticed in this codebase?"

# Clear stale memory
"Forget what you know about the old auth system, we've migrated"
```

### CLAUDE.md as Static Memory

Your CLAUDE.md files act as permanent, version-controlled memory:

| File | Scope | Purpose |
|------|-------|---------|
| `~/.claude/CLAUDE.md` | All projects | Your personal coding preferences |
| `./CLAUDE.md` | This project | Project-specific rules and architecture |
| `./CLAUDE.local.md` | This project (gitignored) | Personal overrides for this project |
| `./subfolder/CLAUDE.md` | Module-specific | Rules for specific modules |

---

## 8. CLAUDE.md - Your Rulebook

### What's Configured

**Global** (`~/.claude/CLAUDE.md`):
- Your identity as a solo founder
- TypeScript strict mode preference
- Async/await patterns
- Functional React components
- Zustand for state, Supabase for backend
- Tailwind + shadcn/ui for styling
- Conventional commits
- Hardware context (RTX 4090, Ollama)

**Project** (`D:\enterprise playground\CLAUDE.md`):
- FastAPI + Python stack definition
- Dual-model Ollama architecture
- Directory structure mapping
- Scraper, playground, fine-tuning commands
- VRAM budget rules
- Rate limiting rules for scraping

### Editing Your CLAUDE.md

Just ask:
```
"Update CLAUDE.md to add that we use Zod for validation"
"Add a rule to CLAUDE.md: always use server components by default"
```

Or use the **claude-md-management** plugin for structured edits.

---

## 9. Task Master AI - Your PM

Task Master AI (v0.43.0) converts PRDs into structured, dependency-tracked task lists.

### Core Workflow

```bash
# Initialize Task Master in your project
task-master init

# Write or paste your PRD
# Save it to .taskmaster/docs/prd.txt

# Parse PRD into tasks
task-master parse-prd

# See all tasks
task-master list

# Get the next recommended task
task-master next

# Mark a task as done
task-master set-status --id=1 --status=done

# Break down a complex task into subtasks
task-master expand --id=3

# Get task details
task-master show --id=5
```

### Integration with Claude Code

Tell Claude about your Task Master setup:
```
"Parse my PRD and create tasks"
"What's my next task?"
"Show me task #5 and implement it"
"Mark task #3 as done and move to the next one"
```

### The Full Pipeline

```
1. You: "I want to build a SaaS for X"
2. /generate-prp -> Full PRD
3. task-master parse-prd -> Structured tasks
4. task-master next -> Get first task
5. Tell Claude: "Implement task #1"
6. Agent Teams: parallel execution
7. Hooks: auto-format, auto-test
8. /commit -> Smart commit
9. task-master set-status --id=1 --status=done
10. Repeat from step 4
```

---

## 10. Complementary Tools

### On Your Machine

| Tool | What It Does | How to Use With Claude |
|------|-------------|----------------------|
| **Ollama** | Local LLM inference (Qwen2.5 models) | Claude can invoke via API for secondary tasks |
| **Continue IDE** | AI coding in VS Code with multiple models | Use alongside Claude for quick completions |
| **RunPod** | Cloud GPU for fine-tuning | Claude can write and deploy training scripts |
| **ComfyUI** | Stable Diffusion workflows | Claude can generate and edit workflows |
| **VS Code** | Primary IDE | Claude Code integrates via the VS Code extension |
| **Docker** | Containerization | Now accessible via Docker MCP |

### Recommended Additions

| Tool | What It Does | Why |
|------|-------------|-----|
| **Cursor** | AI-native IDE (VS Code fork) | Best-in-class for daily coding with Claude + GPT-4 |
| **Aider** | CLI git-native AI coding | Good for structured refactors with BYOK |
| **v0.dev** | UI generation from prompts | Rapid frontend prototyping |
| **Bolt.new** | Full-stack app from description | Quick MVPs |

---

## 11. The Solo Founder Workflow

### The "Idea to Production" Pipeline

```
MORNING PLANNING
├── Review Linear MCP: "What's in my sprint?"
├── Check PostHog (when configured): "Show me yesterday's analytics"
├── Task Master: "What's my next task?"
└── Set context: Open project, Claude loads CLAUDE.md + memory

BUILDING
├── /generate-prp for new features
├── /execute-prp for implementation (4-phase)
├── Agent Teams for parallel work (frontend + backend + tests)
├── Hooks auto-notify you of completions/errors
├── context7 prevents API hallucination
├── Playwright MCP for E2E testing
└── sequential-thinking for architecture decisions

SHIPPING
├── /commit for smart conventional commits
├── /pr-review for automated code review
├── Vercel MCP: "Deploy to production"
├── Stripe MCP: "Set up pricing plans"
└── Linear MCP: "Close issue #42"

MONITORING
├── PostHog: "What features are users using?"
├── Datadog: "Any errors in the last hour?"
├── Browser tools: "Run performance audit"
└── Iterate based on data
```

### Project Setup Checklist (New Project)

```bash
# 1. Initialize project
claude /init

# 2. Set up Task Master
task-master init

# 3. Write PRD
# Save to .taskmaster/docs/prd.txt

# 4. Parse into tasks
task-master parse-prd

# 5. Add project-specific MCP servers if needed
claude mcp add supabase -- npx -y @supabase/mcp-server -e SUPABASE_ACCESS_TOKEN=xxx

# 6. Start building
task-master next
# -> Tell Claude to implement task #1
```

---

## 12. Daily Operations Cheat Sheet

### Essential Commands

| Action | Command / Prompt |
|--------|-----------------|
| Start fresh | `/clear` |
| Compress context | `/compact` |
| Smart commit | `/commit` |
| Review code | `/review` |
| Generate PRD | `/generate-prp "feature description"` |
| Execute PRD | `/execute-prp` |
| Check MCP health | `claude mcp list` |
| List plugins | `/plugins` |
| Next task | `task-master next` |
| Take screenshot | "Take a screenshot" (browser-tools) |
| Check console | "Check console errors" (browser-tools) |
| Run audit | "Run accessibility audit" (browser-tools) |
| Fresh docs | "How does X work? use context7" |
| Deploy | "Deploy to Vercel" (vercel MCP) |

### Power Prompts

```
# Architecture decisions
"Think through the best architecture for X using sequential thinking"

# Full-stack parallel build
"Build feature X: create API routes, React components, and tests in parallel"

# Security review
"Run a security review on the auth module"

# Performance check
"Run a performance audit on the current page"

# Design implementation
"Get the Figma design specs for the dashboard and implement them"

# Database setup
"Create a Supabase migration for the users table with RLS policies"

# Payment integration
"Set up Stripe subscription plans: Basic $9/mo, Pro $29/mo, Enterprise $99/mo"

# Research with live docs
"How do I implement middleware in Next.js 15? use context7"

# Project management
"Create a Linear issue: 'Implement user onboarding flow' with high priority"
```

### Keyboard Shortcuts (Claude Code CLI)

| Shortcut | Action |
|----------|--------|
| `Ctrl+C` | Cancel current operation |
| `Ctrl+D` | End session |
| `Tab` | Autocomplete |
| `Up/Down` | Navigate history |
| `Esc` | Clear current input |
| `Shift+Tab` | Switch between plan/act modes |

---

## 13. Advanced Techniques

### Prompt Chaining

Chain multiple capabilities in a single prompt:
```
"Search my Notion for the product roadmap, create Linear issues for
the next 3 features, generate PRPs for each, and create a task list
in Task Master"
```

### Model Switching

```
# Use Opus for complex reasoning (your default)
# Switch to Sonnet for bulk/fast tasks
/model sonnet

# Switch back to Opus
/model opus
```

### Context Management

```
# Check context usage
/context

# Compact when getting full (or let it auto-compact)
/compact

# Clear between unrelated tasks
/clear

# Use CLAUDE.md to front-load essential context
# Use memory MCP for dynamic context
```

### Multi-Project Workflow

```
# Each project has its own:
# - CLAUDE.md (project rules)
# - MCP servers (project-specific)
# - Memory (project-specific)
# - Task Master (project-specific)

# Global settings apply everywhere:
# - Your CLAUDE.md preferences
# - Global MCP servers
# - Hooks
# - Plugins
```

### Building Custom Plugins

Use the **plugin-dev** plugin:
```
"Create a plugin that automatically generates API documentation
for every new endpoint I create"
```

The plugin-dev toolkit guides you through an 8-phase workflow to build, test, and publish plugins.

---

## 14. What Needs Your Auth Keys

These services require authentication. You'll be prompted on first use for HTTP-based MCPs (OAuth flow), or you need to provide API keys for stdio-based ones.

### OAuth (Browser-based, Auto-prompted)

| Service | Auth Method | First Use |
|---------|------------|-----------|
| **Vercel** | OAuth | Opens browser to authorize |
| **Stripe** | OAuth | Opens browser to authorize |
| **Linear** | OAuth | Opens browser to authorize |
| **Notion** | OAuth | Opens browser to authorize |
| **Figma** | OAuth | Opens browser to authorize |
| **GitHub MCP** | GitHub token | Set `GITHUB_TOKEN` env var |

### API Key Based (Manual Setup)

| Service | How to Get Key | Install Command |
|---------|---------------|-----------------|
| **Brave Search** | https://brave.com/search/api/ | `claude mcp add brave-search -- npx -y @modelcontextprotocol/server-brave-search -e BRAVE_API_KEY=<key>` |
| **Supabase** | https://supabase.com/dashboard/account/tokens | `claude mcp add supabase -- npx -y @supabase/mcp-server -e SUPABASE_ACCESS_TOKEN=<token>` |
| **PostHog** | https://posthog.com (Project Settings > API Keys) | `claude mcp add posthog -- npx -y @posthog/mcp-server -e POSTHOG_API_KEY=<key>` |
| **Exa** | https://exa.ai | Already configured in feature-dev project |
| **Firecrawl** | https://firecrawl.dev | Already configured in feature-dev project |
| **Datadog** | https://app.datadoghq.com | `claude mcp add datadog --transport http https://mcp.datadoghq.com` |

### Setting Environment Variables Permanently (Windows)

```bash
SETX GITHUB_TOKEN ghp_xxxxxxxxxxxx
SETX BRAVE_API_KEY BSA_xxxxxxxxxxxx
SETX SUPABASE_ACCESS_TOKEN sbp_xxxxxxxxxxxx
```

---

## 15. Troubleshooting

### MCP Server Issues

```bash
# Check server health
claude mcp list

# If a server shows "Failed to connect":
# 1. Remove and re-add it
claude mcp remove <name>
claude mcp add <name> -- npx -y <package>

# 2. Check if the package is installed
npx -y <package> --help

# 3. For HTTP servers, check the URL in a browser

# Docker MCP requires Docker Desktop to be running
# Start Docker Desktop, then restart Claude Code
```

### Hooks Not Firing

```bash
# Verify hooks in settings.json
# Open: C:\Users\deepc\.claude\settings.json

# Verify localhost:3456 is running (your notification service)
curl http://localhost:3456/health

# Check if hook command works standalone
curl -s -X POST http://localhost:3456/speak -H "Content-Type: application/json" -d "{\"message\": \"test\"}"
```

### Agent Teams Not Working

```bash
# Verify env var is set
echo %CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS%
# Should output: 1

# If not, set it:
SETX CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS 1
# Then restart your terminal
```

### Context Running Out

```
1. Run /compact to compress context
2. Run /clear between unrelated tasks
3. Use CLAUDE.md instead of repeating instructions
4. Keep CLAUDE.md under 200 lines
5. Use memory MCP for dynamic context
```

### Plugin Issues

```bash
# List installed plugins
/plugins

# Reinstall a plugin
/plugin uninstall <name>
/plugin install <name>

# Check marketplace for updates
/plugin marketplace search <name>
```

---

## 16. Future Upgrades to Watch

### Coming Soon (Track These)

| Tool | What It Is | Status | Link |
|------|-----------|--------|------|
| **Oh My Claude Code (OMC)** | 32 agents, 40 skills, 5 execution modes | Install next | `/plugin marketplace add omc` |
| **Claude-Mem** | 10x token reduction, cross-session SQLite memory | Install next | `/plugin marketplace add thedotmack/claude-mem` |
| **Claude Flow** | 60+ agent enterprise swarm | Evaluate | `npm install -g @ruvnet/claude-flow` |
| **Composio** | 850+ SaaS integrations via single MCP | Evaluate | https://composio.dev |
| **Code-Graph-RAG** | Knowledge graph from codebase | Evaluate | https://github.com/vitali87/code-graph-rag |
| **Claude Telemetry** | OpenTelemetry tracing, cost tracking | Evaluate | `pip install claude-telemetry` |
| **GitHub Actions CI/CD** | Auto PR review with Claude | Set up when repo is ready | `anthropics/claude-code-action` |
| **n8n MCP** | Workflow automation (1,084 nodes) | Add when needed | `claude mcp add n8n -- npx -y @czlonkowski/n8n-mcp` |

### Ecosystem Resources

| Resource | URL | What It Is |
|----------|-----|-----------|
| Awesome Claude Code | https://github.com/hesreallyhim/awesome-claude-code | Skills, hooks, commands, plugins |
| Awesome MCP Servers | https://github.com/punkpeye/awesome-mcp-servers | 7,000+ MCP servers |
| Awesome Claude Plugins | https://github.com/quemsah/awesome-claude-plugins | 4,413 repos indexed |
| Claude Code Docs | https://code.claude.com/docs/en/ | Official documentation |
| Claude Code Showcase | https://github.com/ChrisWiles/claude-code-showcase | Example configs |
| MCP Directory | https://mcp-awesome.com/ | 1,200+ quality-verified servers |
| Plugin Marketplace | https://claude-plugins.dev/ | Community plugin registry |

### Monthly Maintenance Checklist

```
[ ] Check for plugin updates: /plugin marketplace search <name>
[ ] Review and prune MCP servers: claude mcp list
[ ] Update Task Master: npm update -g task-master-ai
[ ] Review CLAUDE.md - still accurate?
[ ] Check awesome-claude-code for new tools
[ ] Review hooks - add any new automation?
[ ] Clear stale memory entries
[ ] Review permissions in settings.local.json
```

---

## Quick Reference Card

```
START SESSION          -> Claude loads CLAUDE.md + memory automatically
PLAN FEATURE           -> /generate-prp "description"
BREAK INTO TASKS       -> task-master parse-prd
GET NEXT TASK          -> task-master next
BUILD IN PARALLEL      -> "Build X with agent teams"
CHECK LIVE DOCS        -> "How does Y work? use context7"
TEST IN BROWSER        -> "Navigate to localhost and test Z"
REVIEW CODE            -> /review or /pr-review
COMMIT                 -> /commit
DEPLOY                 -> "Deploy to Vercel"
TRACK ISSUES           -> "Create Linear issue for..."
REMEMBER THINGS        -> "Remember that..."
COMPRESS CONTEXT       -> /compact
FRESH START            -> /clear
```

---

*Your Claude Code is now configured with 12+ global MCP servers, 42 plugins, 7 lifecycle hooks, Agent Teams, Task Master AI, persistent memory, and a complete solo founder workflow. Use this guide as your daily reference.*

*Last updated: February 8, 2026*
