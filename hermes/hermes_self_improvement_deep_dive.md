# Hermes Agent — Self-Improvement Loop: Deep Dive & Implementation Guide

> **Source Repo:** https://github.com/NousResearch/hermes-agent  
> **Self-Evolution Repo:** https://github.com/NousResearch/hermes-agent-self-evolution  
> **Purpose:** Mapping Hermes's learning loop to our multi-agent provider + skill + memory setup

---

## 1. Overview: What Makes Hermes "Self-Improving"

Hermes is not a static agent. It is built around a **closed learning loop** — a set of interlocking mechanisms that cause the agent to get better over time by observing its own work, storing what it learns, and refining its reusable procedures.

There are **five core sub-loops** that together constitute the self-improvement cycle:

| Sub-Loop | What Improves | When It Fires |
|---|---|---|
| **Skill Creation** | Procedural memory (SKILL.md files) | After complex tasks (5+ tool calls) |
| **Skill Patching** | Accuracy of existing skills | When a skill is loaded and found outdated |
| **Memory Nudges** | Persistent facts (MEMORY.md, USER.md) | Proactively during and after conversations |
| **Session Search** | Cross-session recall | When user references "last time" / "before" |
| **Evolutionary Optimization** | Skill content quality via DSPy+GEPA | Nightly / on-demand via separate repo |

These are reinforcing: skills improve from sessions, memory provides session context, session search retrieves past state, and the evolutionary optimizer mutates skills toward measurably better versions.

---

## 2. Key Files in the Repository

### Root-Level Core Files

| File | Role |
|---|---|
| `run_agent.py` | `AIAgent` class — the main conversation loop. All self-improvement hooks live inside or are called from here. |
| `model_tools.py` | `_discover_tools()` and `handle_function_call()` — dispatches every tool call. Skills and memory tools are registered here. |
| `hermes_state.py` | `SessionDB` — SQLite session store with FTS5 full-text search for cross-session recall. |
| `toolsets.py` | Toolset groupings. `_HERMES_CORE_TOOLS` list defines which tools are always present. |
| `trajectory_compressor.py` | Compresses long conversation histories into training-format trajectories for RL / SFT. |

### `agent/` Subdirectory — Intelligence Infrastructure

| File | Role in Self-Improvement |
|---|---|
| `agent/prompt_builder.py` | Assembles system prompt — injects MEMORY.md, USER.md, skills index, and SOUL.md into every turn. |
| `agent/context_compressor.py` | Auto-compresses old turns when context fills. Flushes memory nudges before compression. |
| `agent/prompt_caching.py` | Caches the static prefix of the system prompt (Anthropic API). Prevents skills/memory updates from breaking cache mid-session. |
| `agent/trajectory.py` | Saves each turn as a trajectory entry for RL training. |
| `agent/auxiliary_client.py` | Auxiliary LLM calls for vision, summarization, and session search summarization. |

### `tools/` Subdirectory — Self-Improvement Tools

| File | Tool(s) | Self-Improvement Role |
|---|---|---|
| `tools/skills_tool.py` | `skills_list`, `skill_view` | Discovery + loading of procedural memory |
| `tools/skill_manager_tool.py` | `skill_manage` | Create / patch / edit / delete skills |
| `tools/memory_tool.py` | `memory` | Add / replace / remove persistent facts |
| `tools/session_search_tool.py` | `session_search` | Full-text search across all past sessions |
| `tools/honcho_tools.py` | `honcho_profile`, `honcho_search`, `honcho_context`, `honcho_conclude` | Dialectic user modeling across sessions |
| `tools/delegate_tool.py` | `delegate_task` | Spawn subagents for parallel work (isolated contexts) |
| `tools/cronjob_tools.py` | `cronjob` | Schedule recurring self-improvement tasks |
| `tools/code_execution_tool.py` | `execute_code` | Run Python that calls tools programmatically (reduces context cost) |
| `tools/rl_training_tool.py` | `rl_*` | Launch RL training runs via Tinker-Atropos |

### `plugins/memory/` — External Memory Providers

Contains 7 memory provider plugins that run **alongside** built-in memory:
- **Honcho** — dialectic user modeling
- **OpenViking**, **Mem0**, **Hindsight**, **Holographic**, **RetainDB**, **ByteRover**

Each plugs into `run_agent.py`'s session start and provides additional memory signals injected into the system prompt.

### Self-Evolution Repo (`hermes-agent-self-evolution/`)

| File/Dir | Role |
|---|---|
| `evolution/skills/evolve_skill.py` | Main entry point — runs DSPy + GEPA optimization on a SKILL.md file |
| `evolution/` | Full GEPA loop: read traces → generate eval → mutate → evaluate → select |
| `datasets/` | Eval datasets (synthetic or from real session history) |
| `reports/` | Optimization reports for each run |
| `PLAN.md` | 5-phase roadmap: skills → tool descriptions → system prompts → tool code → continuous loop |

---

## 3. The Self-Improvement Loop — Step by Step

### Step 1: Session Start — Memory Injection
```
MEMORY.md (2,200 char limit)  →  Frozen snapshot injected into system prompt
USER.md   (1,375 char limit)  →  Frozen snapshot injected into system prompt
skills/   index               →  List of available skills in system prompt
```
The agent "wakes up" with its accumulated knowledge already in context, without any tool calls needed.

### Step 2: Task Execution — Observation

During the task, `run_agent.py`'s `run_conversation()` loop runs:
```python
while api_call_count < self.max_iterations and self.iteration_budget.remaining > 0:
    response = client.chat.completions.create(...)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
        api_call_count += 1
    else:
        return response.content
```
Every tool call is executed and its result appended to conversation history. This forms the **execution trace**.

### Step 3: Skill Creation Trigger

After 5+ tool calls completing a non-trivial task, the system prompt instructs the agent to evaluate whether a skill should be created. The agent calls `skill_manage(action="create", name=..., content=...)`.

A SKILL.md file is written to `~/.hermes/skills/` containing:
```yaml
---
name: my-workflow
description: Brief description
version: 1.0.0
metadata:
  hermes:
    tags: [tag1, tag2]
    category: devops
---
# Skill Title

## When to Use
## Procedure
## Pitfalls
## Verification
```

### Step 4: Skill Patching During Use

When the agent loads a skill via `skill_view()` and detects the content is outdated, incomplete, or incorrect, it **immediately patches it** using `skill_manage(action="patch", old_string=..., new_string=...)`. This happens **without user intervention** — the skill improves itself in-flight.

### Step 5: Memory Nudges

At natural pause points (and before context compression), the agent writes to memory:
- **Environment facts** → `memory(action="add", target="memory", content=...)`
- **User preferences** → `memory(action="add", target="user", content=...)`
- **Corrections** → `memory(action="replace", target="memory", old_text=..., content=...)`

The **frozen snapshot pattern** means these changes take effect at the **next session start** — protecting the LLM's prefix cache from being invalidated mid-session.

### Step 6: Session Persistence

After every session, the full conversation is stored in SQLite (`state.db`) with FTS5 indexing. The agent can later call `session_search(query="...")` to retrieve and summarize relevant past sessions.

### Step 7: Honcho User Modeling

When Honcho is active, `honcho_conclude()` writes persistent conclusions about the user. In future sessions, `honcho_profile()` retrieves a curated peer card, and `honcho_context()` answers natural language questions about the user using dialectic reasoning over stored context.

### Step 8: Evolutionary Optimization (Nightly / On-Demand)

The separate `hermes-agent-self-evolution` repo runs:
```
Current SKILL.md  
→ Generate eval dataset (synthetic or from session history)  
→ GEPA reads execution traces to understand WHY failures happen  
→ Generates candidate mutations  
→ Evaluates each candidate  
→ Passes constraint gates (tests, size limits, semantic preservation)  
→ Best variant submitted as PR to hermes-agent
```
Cost: ~$2–10 per optimization run. No GPU required.

---

## 4. The SKILL.md Standard (agentskills.io)

Skills are not Hermes-specific. They follow the **agentskills.io open standard**, meaning they can be shared across agents.

### Progressive Disclosure Pattern (Key for Token Efficiency)

```
Level 0: skills_list()           → [{name, description, category}]   ~3k tokens total
Level 1: skill_view(name)        → Full SKILL.md content              varies per skill
Level 2: skill_view(name, path)  → Specific file (references/scripts) varies
```

The agent only pays the token cost for a skill when it actually needs to execute it.

### Skill File Structure
```
~/.hermes/skills/
├── category/
│   └── skill-name/
│       ├── SKILL.md          # Main instructions (required)
│       ├── references/       # Supplementary docs
│       ├── templates/        # Output formats
│       ├── scripts/          # Helper scripts
│       └── assets/           # Other files
└── .hub/                     # Hub metadata
```

### Conditional Activation
Skills can self-hide based on tool availability:
```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # Show ONLY if web tools unavailable
    requires_toolsets: [terminal]     # Show ONLY if terminal available
```

---

## 5. Memory Architecture

### Two-Layer Memory Model

```
Layer 1: System Prompt (frozen at session start)
  ├── MEMORY.md   → 2,200 chars / ~800 tokens  (environment facts, lessons, conventions)
  └── USER.md     → 1,375 chars / ~500 tokens  (user preferences, profile, style)

Layer 2: Session Search (on-demand)
  └── SQLite FTS5 → unlimited (all past sessions, LLM-summarized on query)

Layer 3: External Providers (optional, alongside built-in)
  └── Honcho / Mem0 / Hindsight / etc. → knowledge graphs, semantic search
```

### Memory Security Scanning
Every memory entry is scanned for:
- Prompt injection patterns
- Credential exfiltration
- Invisible Unicode characters

Entries matching threat patterns are blocked before storage.

### Capacity Management Pattern
When memory is near capacity (>80%), the agent:
1. Reads current entries (returned in error response)
2. Consolidates related entries
3. Replaces multiple entries with one dense entry
4. Then adds new entry

---

## 6. Implementation Strategy for Our Multi-Agent Setup

This section maps Hermes's patterns to our existing multi-agent provider skill and memory infrastructure.

### 6.1 Shared Skill Registry (Provider-Agnostic)

**Hermes Pattern:** Skills are plain Markdown files in `~/.hermes/skills/`. Any agent can read them via `skills_list()` and `skill_view()`.

**Our Implementation:**
- Store skills in a shared directory (e.g., `/mnt/skills/`) accessible to all agents (Claude, GPT-4, Gemini, etc.)
- Use the **agentskills.io SKILL.md format** — it's already supported by multiple agents
- Add provider-specific conditional activation via `requires_tools` in frontmatter
- Each agent writes skills it creates to the shared path; they become available to all other agents immediately

```yaml
# Example: Multi-provider skill
---
name: api-error-recovery
description: Recover from API errors across providers
metadata:
  hermes:
    tags: [error-handling, resilience]
    # No provider restriction = available to all agents
---
```

### 6.2 Autonomous Skill Creation Trigger

**Hermes Pattern:** After 5+ tool calls completing a complex task, the agent evaluates whether to create/update a skill.

**Our Implementation:**
Add a post-task hook in each agent's system prompt:
```
After completing any task requiring 5+ steps or where you discovered a non-obvious 
approach, evaluate whether a SKILL.md should be created or patched in the shared 
skill directory. Use skill_manage(action="patch") for incremental fixes (preferred) 
and skill_manage(action="create") for genuinely new procedures.
```

This is a **system prompt instruction**, not code — it works across any LLM.

### 6.3 Unified Memory Store

**Hermes Pattern:** Two bounded files (MEMORY.md, USER.md) injected at session start; SQLite for session history.

**Our Implementation:**
- Maintain one `MEMORY.md` and `USER.md` per user/workspace, shared across all agents
- Each agent reads these at session start (inject into system prompt)
- Write-access coordination: use file locking or a simple memory API to prevent simultaneous writes
- For cross-agent session search: store all agent sessions in a unified SQLite database with FTS5

```
Shared memory structure:
~/.agents/memories/
├── MEMORY.md          # Shared facts (all agents can read/write)
├── USER.md            # Shared user profile
└── sessions.db        # SQLite FTS5 — all agents write sessions here
```

### 6.4 Cross-Agent Session Search

**Hermes Pattern:** `session_search` tool queries SQLite FTS5, uses auxiliary LLM call to summarize results.

**Our Implementation:**
- Every agent session (Claude, GPT-4, Gemini) writes a session summary to shared `sessions.db`
- Include `agent_id` column so searches can be filtered by agent or across all
- Expose a `session_search` MCP tool that all agents share

Schema:
```sql
CREATE VIRTUAL TABLE sessions USING fts5(
  session_id, agent_id, timestamp, user_query, summary, full_transcript,
  tokenize='porter ascii'
);
```

### 6.5 Skill Self-Patching Protocol

**Hermes Pattern:** When an agent loads a skill and detects it's wrong/incomplete, it patches it immediately.

**Our Implementation:**
Add to each agent's system prompt:
```
When you load a skill from the skill registry and discover the instructions are 
incomplete, outdated, or incorrect:
1. Use the skill as a starting point
2. After completing the task, call skill_manage(action="patch") with the specific 
   correction using old_string/new_string
3. Log the correction reason in the skill's ## Changelog section
```

This creates a **positive feedback loop**: every agent encounter with a skill improves it.

### 6.6 Evolutionary Optimization (Scheduled)

**Hermes Pattern:** `hermes-agent-self-evolution` runs DSPy+GEPA optimization nightly.

**Our Implementation:**
- Schedule nightly runs of the self-evolution pipeline against the shared skill directory
- Use real session history from all agents as the eval source: `--eval-source sessiondb`
- Constraint gates ensure quality: tests must pass, size limits enforced, semantic preservation checked
- All changes go through PR review before applying

```bash
# Nightly cron
python -m evolution.skills.evolve_skill \
    --skill-dir /mnt/skills/ \
    --eval-source sessiondb \
    --sessiondb ~/.agents/memories/sessions.db \
    --iterations 10
```

### 6.7 Tool Registration Pattern

**Hermes Pattern:** Tools self-register at import time via `tools/registry.py`. Each tool has a `check_fn` that gates on environment availability.

**Our Implementation:**
Use the same pattern for our MCP tools:
```python
# tool file pattern
def check_fn() -> bool:
    return bool(os.getenv("REQUIRED_API_KEY"))

registry.register(
    name="tool_name",
    schema=TOOL_SCHEMA,
    handler=handler_fn,
    check_fn=check_fn,
)
```

This means tools are automatically excluded when their dependencies aren't available — no manual configuration per agent.

### 6.8 Memory Nudge Scheduling

**Hermes Pattern:** Agent is instructed to proactively save memory without being asked. Cron runs periodic memory consolidation.

**Our Implementation:**
- Add memory-writing instructions to all agents' system prompts
- Schedule a weekly memory consolidation cron: an agent reviews MEMORY.md and USER.md, removes stale entries, and merges duplicates
- Security-scan all incoming memory entries before writing

### 6.9 Subagent Delegation

**Hermes Pattern:** `delegate_task` spawns isolated subagents. Only final summary returns to parent context — intermediate results don't pollute context window.

**Our Implementation:**
- Implement delegation as an MCP tool available to orchestrator agents
- Each spawned subagent gets its own conversation, skill set, and toolset
- Parent agent receives only the summary (not raw tool outputs)
- This is critical for context budget management in long workflows

---

## 7. Key Design Principles to Preserve

These are non-negotiable architectural constraints from Hermes that we must replicate:

### Frozen Snapshot Pattern
Memory is injected **once** at session start and never changes mid-session. This preserves the LLM prefix cache. Don't invalidate mid-session — buffer changes to disk, apply at next session start.

### Token-Efficient Progressive Disclosure
Never load all skill content upfront. Always use three levels:
1. Index only (names + descriptions)
2. Full SKILL.md on demand
3. Reference files on demand

### Return JSON Strings, Never Raise Exceptions
All tool handlers must catch exceptions and return `{"error": "message"}`. The LLM must always receive a structured response to reason about — not a Python traceback.

### Semantic Preservation Gate
When evolving skills or prompts, enforce that the mutation doesn't drift from the original purpose. Evaluate this with the LLM itself as a judge.

### One Skill Per Task Category
Don't create a new skill for every task. Evaluate: does this fit an existing skill? If yes, patch it. If genuinely new, create it.

---

## 8. File-by-File Implementation Checklist

For our current multi-agent setup, here's what to build/adapt:

### Must Build
- [ ] `tools/skill_manager_tool.py` — skill create/patch/edit/delete with shared path support
- [ ] `tools/skills_tool.py` — skills_list and skill_view with progressive disclosure
- [ ] `tools/memory_tool.py` — add/replace/remove for shared MEMORY.md and USER.md
- [ ] `tools/session_search_tool.py` — FTS5 search across all agent sessions
- [ ] `tools/registry.py` — self-registering tool registry with check_fn gating
- [ ] `agent/prompt_builder.py` — assemble system prompt with memory + skills index injection
- [ ] `agent/context_compressor.py` — flush memory before compression, preserve tool-call ordering

### Can Adapt Directly from Hermes
- [ ] SKILL.md format (agentskills.io standard) — copy exactly
- [ ] Memory security scanner — copy from Hermes's memory_tool.py
- [ ] Frozen snapshot pattern — copy from prompt_builder.py
- [ ] SQLite FTS5 schema from hermes_state.py

### Must Integrate
- [ ] `hermes-agent-self-evolution` — point at our shared skill directory
- [ ] Honcho (optional) — for deep user modeling if needed

---

## 9. Quick Reference: Self-Improvement Trigger Map

| Trigger Event | What Happens | File Responsible |
|---|---|---|
| Task completes with 5+ tool calls | Evaluate → create skill | `run_agent.py` + system prompt |
| Skill loaded and found outdated | Patch skill immediately | `tools/skill_manager_tool.py` |
| User reveals a preference | Write to USER.md | `tools/memory_tool.py` |
| Environment fact discovered | Write to MEMORY.md | `tools/memory_tool.py` |
| Context nearing limit | Flush memory, compress | `agent/context_compressor.py` |
| User says "we did this before" | session_search | `tools/session_search_tool.py` |
| Nightly cron fires | DSPy+GEPA evolution run | `hermes-agent-self-evolution/` |
| Tool call fails | Log error, update skill pitfalls | System prompt instruction |

---

## 10. Relevant Links

| Resource | URL |
|---|---|
| Main Repository | https://github.com/NousResearch/hermes-agent |
| Self-Evolution Repo | https://github.com/NousResearch/hermes-agent-self-evolution |
| Official Docs | https://hermes-agent.nousresearch.com/docs/ |
| Agent Loop Internals | https://hermes-agent.nousresearch.com/docs/developer-guide/agent-loop |
| Skills System | https://hermes-agent.nousresearch.com/docs/user-guide/features/skills |
| Memory System | https://hermes-agent.nousresearch.com/docs/user-guide/features/memory |
| Architecture | https://hermes-agent.nousresearch.com/docs/developer-guide/architecture |
| Tools Reference | https://github.com/mudrii/hermes-agent-docs/blob/main/tools.md |
| agentskills.io Standard | https://agentskills.io/specification |
| DSPy + GEPA | https://github.com/gepa-ai/gepa |
| Honcho User Modeling | https://github.com/plastic-labs/honcho |
| Community Resources | https://github.com/0xNyk/awesome-hermes-agent |
