# Agent Prompt & Policy Templates (v0.1)
# Comprehensive Blueprint for Agent Workflows, Pipelines, Tooling, Policies, and Collaboration in a Robust Agentic MCP System

## Introduction

Your vision for a multi-agent, memory-layered MCP server—where each agent operates with clear workflows, robust toolchains, and deep relational knowledge graphs—demands a system that is both modular and highly orchestrated. This response details the **complete workflow, pipelines, tool usage, policy enforcement, hierarchy, branching, and collaboration patterns** for each agent you’ve defined, ensuring alignment with your robust knowledge graph architecture and memory layers. The design is based on best practices from recent research on agentic orchestration, graph-based memory, and real-world agent toolchains[1][2][3][4][5][6][7][8][9][10][11][12][13][14].

---

## 1. **Ultra Orchestrator Agent**

### **Role & Hierarchy**
- **Top-level agent**: Receives all user prompts and system events.
- **Policy enforcer**: Applies global workflow and security policies.
- **Agent spawner**: Dynamically instantiates and configures subordinate agents (using frameworks like Archon or dynamic crew creation in CrewAI).
- **Central node** in the knowledge graph, connected to all active agents and memory layers.

### **Workflow & Pipeline**
1. **User Prompt Reception**
   - Receives prompt (from IDE, API, or UI).
   - Classifies intent (new project, code edit, doc query, bug report, etc.) using an embedded classifier or LLM.
2. **Policy Check & Contextualization**
   - Queries the policy memory layer for relevant workflow, security, and compliance rules.
   - Determines if user is authorized, if prompt is safe, and what workflow profile to use.
3. **Agent Routing & Task Decomposition**
   - If new project: Spawns Architect Agent.
   - If code edit: Spawns Codebase Agent, optionally Debug Agent.
   - If doc query: Spawns Document Agent.
   - If ambiguous: Spawns Message Session Agent to clarify.
4. **Dynamic Tool Assignment**
   - Assigns toolkits and memory access based on agent roles and project context.
   - Configures tool policies (e.g., restricts certain tools in production).
5. **Workflow Supervision**
   - Monitors progress, enforces deadlines, handles exceptions.
   - Can branch workflow (e.g., escalate to human, spawn additional agents, or trigger fallback routines).
6. **Feedback Loop**
   - Receives feedback from agents or user.
   - Updates knowledge graph with success/failure and re-weights future agent/tool selection.

### **Collaboration & Branching**
- **Branches**: Can fork parallel workflows (e.g., code refactor + doc update).
- **Collaboration**: Synchronizes state between agents, resolves conflicts, and merges outputs.
- **Fallbacks**: If an agent/tool fails, triggers backup agents or alternative toolchains.

---

## 2. **Architect Agent**

### **Role & Hierarchy**
- **Design authority**: Converts user intent into actionable plans, PRDs, and technical specs.
- **Hierarchy**: Reports to Orchestrator; manages Plan/Task Agent and interacts with Codebase/Document Agents.

### **Workflow & Pipeline**
1. **Intent Expansion & Requirements Gathering**
   - Engages user in clarifying dialogue (using Message Session Agent as needed).
   - Extracts requirements, constraints, and desired outcomes.
2. **Policy and Best Practice Synthesis**
   - Queries policy memory layer for architectural standards, security, and compliance.
   - Embeds policy references into plan nodes.
3. **Plan and Task Breakdown**
   - Uses LLM (Groq, Gemini) to decompose requirements into hierarchical tasks and milestones.
   - Each task is a node in the Plan/Task memory layer, linked to relevant code/doc/policy nodes.
4. **Tool Usage**
   - Diagram generation (for wireframes, flowcharts).
   - Semantic search (for prior architectures, patterns).
   - Knowledge synthesis (for tech stack recommendations).
5. **Collaboration**
   - Works with Codebase Agent to validate feasibility.
   - Collaborates with Document Agent to ensure documentation coverage.
   - Can branch: e.g., if user changes requirements mid-flow, triggers re-planning.

### **Policies**
- Enforces architectural standards (e.g., "All APIs must be RESTful unless otherwise specified").
- Ensures all plans/tasks are linked to compliance nodes.

---

## 3. **Codebase Knowledge Memory Layer Agent**

### **Role & Hierarchy**
- **Code intelligence**: Ingests, indexes, and maintains the codebase as a richly annotated, multi-granularity graph.
- **Hierarchy**: Works under Orchestrator, with close ties to Plan/Task and Document Agents.

### **Workflow & Pipeline**
1. **Ingestion & Indexing**
   - Watches file system (using chokidar or similar) for changes.
   - For each file:
     - Extracts metadata (language, domain, framework, dependencies, version, etc.)[15][16][17].
     - Chunks into classes, functions, blocks.
     - Generates embeddings for each chunk.
     - Updates knowledge graph (nodes: files, classes, functions; edges: CONTAINS, CALLS, IMPORTS, SIMILAR_TO, TAGGED_AS).
2. **Relational Context Building**
   - Links code nodes to tasks (what needs to be done), docs (what explains it), and policies (what governs it).
   - Updates impact/change links on commit or edit.
3. **Hybrid Retrieval**
   - Exposes graph and vector search APIs for agents.
   - Supports queries like "find all code impacted by this task" or "find similar code to this function".
4. **Feedback and Learning**
   - Logs which code chunks were most helpful or edited.
   - Re-weights embeddings and graph edges based on agent/user feedback.

### **Tool Usage**
- AST parsers (Python, TypeScript, etc.).
- LLMs for code summarization and chunk classification.
- Vector DB for semantic search.

### **Policies**
- Enforces codebase structure standards (e.g., no duplicate files, proper tagging).
- Ensures all code changes are linked to tasks and plans.

---

## 4. **Plan and Task Memory Layer Agent**

### **Role & Hierarchy**
- **Project manager**: Manages all plans, tasks, subtasks, and their dependencies.
- **Hierarchy**: Works under Architect; coordinates with Codebase, Document, and Policy Agents.

### **Workflow & Pipeline**
1. **Task Creation & Decomposition**
   - Receives high-level plans from Architect Agent.
   - Breaks down into hierarchical tasks, each with dependencies, priorities, and completion criteria.
   - Links tasks to code/doc/policy nodes.
2. **Dependency Management**
   - Detects and resolves conflicts (e.g., circular dependencies, resource contention).
   - Updates graph edges as dependencies change.
3. **Progress Tracking & Reporting**
   - Monitors task completion, status, and blockers.
   - Updates knowledge graph with status changes.
4. **Dynamic Re-planning**
   - When requirements or code change, triggers re-planning and updates dependencies.

### **Tool Usage**
- LLMs for task breakdown and conflict detection.
- Graph traversal for dependency analysis.
- Notification tools for progress updates.

### **Policies**
- Enforces that all tasks are linked to plans, code, and documentation.
- Ensures compliance with project management standards.

---

## 5. **Message Session Memory Layer Agent**

### **Role & Hierarchy**
- **Conversation memory**: Captures, indexes, and relates all user-agent and agent-agent messages.
- **Hierarchy**: Cross-cutting; supports all agents as a context provider.

### **Workflow & Pipeline**
1. **Session Tracking**
   - Each session is a node; each message turn is a child node.
   - Links messages to tasks, code, docs, and policies referenced or created in the conversation.
2. **Intent Extraction**
   - Uses LLMs to classify user intent, extract entities, and tag domains.
   - Updates graph with intent and entity nodes.
3. **Context Summarization**
   - Generates summaries for session context nodes.
   - Enables agents to reconstruct context for follow-up actions.
4. **Feedback Loop**
   - Tracks which answers were accepted, rejected, or required clarification.
   - Feeds this data back to Orchestrator for continuous improvement.

### **Tool Usage**
- LLMs for intent and entity extraction.
- Embedding models for semantic similarity between turns.
- Graph traversal for context reconstruction.

### **Policies**
- Enforces privacy and data retention policies.
- Ensures all message data is linked to relevant tasks and code.

---

## 6. **Document Memory Layer Agent**

### **Role & Hierarchy**
- **Documentation intelligence**: Auto-discovers, ingests, chunks, and indexes official documentation and guides.
- **Hierarchy**: Supports all other agents by providing authoritative reference material.

### **Workflow & Pipeline**
1. **Discovery & Ingestion**
   - Uses multi-strategy crawling (Firecrawl, Gemini, Google Search) to find relevant docs[18].
   - Chunks docs into sections, embeds each, and indexes in the graph.
   - Links doc chunks to code, tasks, and policies.
2. **Semantic Enrichment**
   - Classifies doc chunks by type (concept, guide, API, example).
   - Rates applicability and relevance to current project context.
3. **Relationship Building**
   - Auto-links docs to code they explain, tasks they support, and policies they clarify.
   - Creates SIMILAR_TO edges for related doc chunks.
4. **Continuous Update**
   - Monitors for doc updates and triggers re-ingestion as needed.

### **Tool Usage**
- Web crawlers and scrapers (Firecrawl, Playwright, BeautifulSoup).
- LLMs for chunking, summarization, and classification.
- Embedding models for semantic indexing.

### **Policies**
- Ensures only relevant, up-to-date docs are indexed.
- Avoids duplication and maintains clear provenance.

---

## 7. **Open-Source Git Memory Layer Agent**

### **Role & Hierarchy**
- **External intelligence**: Ingests and synthesizes knowledge from open-source repositories.
- **Hierarchy**: Supplements Codebase, Plan/Task, and Document Agents.

### **Workflow & Pipeline**
1. **Repo Discovery & Ingestion**
   - Identifies relevant OSS repos (via user prompt, recommendations, or agent search).
   - Clones, indexes, and chunks repo files as with local codebase.
   - Extracts features and links to local tasks/code needing improvement.
2. **Feature Synthesis**
   - Uses LLMs to summarize and classify high-level features.
   - Links features to local plans/tasks as "inspiration" or "improvement".
3. **Similarity & Impact Analysis**
   - Finds code chunks similar to local code (for reuse or refactoring).
   - Links OSS code to local codebase and tasks.
4. **Continuous Sync**
   - Monitors for upstream changes and triggers re-ingestion as needed.

### **Tool Usage**
- Git clients for repo management.
- AST parsers and LLMs for code analysis.
- Embedding models for cross-repo similarity.

### **Policies**
- Ensures OSS code is properly attributed.
- Avoids license conflicts and ensures compliance.

---

## 8. **Collaboration, Branching, and Conflict Resolution**

### **Branching Cases**
- **Ambiguous User Request**: Orchestrator branches to Message Session Agent for clarification.
- **Parallel Tasks**: Orchestrator spawns multiple agents/crews to work in parallel (e.g., code refactor + doc update).
- **Error/Failure**: On tool or agent failure, Orchestrator triggers fallback routines or escalates to human.
- **Dependency Conflict**: Plan/Task Agent detects and resolves with Codebase Agent.

### **Collaboration Patterns**
- **Shared Memory Graph**: All agents read/write to the same SurrealDB knowledge graph, ensuring a single source of truth.
- **Policy Enforcement**: Every agent checks the policy memory layer before major actions.
- **Feedback Loops**: User and agent feedback is logged and used to improve future decisions.
- **Dynamic Team Formation**: Orchestrator can create ad-hoc teams (crews) for specialized tasks, using frameworks like CrewAI or Archon.

---

## 9. **Tooling and Policy Enforcement**

### **Tooling**
- **LLM APIs**: Groq, Gemini for reasoning, summarization, and classification.
- **Web Crawling**: Firecrawl, Playwright, BeautifulSoup for doc ingestion.
- **Vector Search**: SurrealDB or LanceDB for semantic retrieval.
- **Graph Traversal**: SurrealDB for relationship queries.
- **IDE Integration**: MCP protocol for Cursor, Windsurf, etc.

### **Policy Enforcement**
- **Embedded Policy Nodes**: All policies are represented as nodes in the graph, linked to relevant code, tasks, and docs.
- **Pre/Post-Action Checks**: Agents check policy compliance before executing major actions.
- **Audit Logging**: All actions are logged for traceability and compliance.

---

## 10. **Visualization and Monitoring**

- **Graph Visualizer**: Use tools like Cytoscape, D3.js, or SurrealDB’s built-in visualizer to monitor agent interactions and memory graph state.
- **Agent State Dashboards**: Real-time dashboards showing agent status, active workflows, and memory usage.

---

## 11. **Summary Table: Agent Workflows and Relationships**

| Agent                | Workflow Stages                       | Tooling                    | Policies Enforced         | Collaboration/Branching         |
|----------------------|---------------------------------------|----------------------------|---------------------------|----------------------------------|
| Ultra Orchestrator   | Intent → Policy → Routing → Supervise | LLMs, Policy DB, CrewAI    | All global policies       | Spawns/merges agents, fallback   |
| Architect            | Gather → Plan → Decompose → Validate  | LLMs, Diagrams, Search     | Architecture, compliance  | Works with Codebase, Plan, Doc   |
| Codebase             | Ingest → Chunk → Link → Retrieve      | AST, LLMs, Embedding, DB   | Code structure            | Syncs with Plan, Doc, OSS        |
| Plan/Task            | Create → Decompose → Track → Replan   | LLMs, Graph Traversal      | PM, dependency            | Syncs with Codebase, Doc, Policy |
| Message Session      | Track → Classify → Summarize → Log    | LLMs, Embedding, Graph     | Privacy, retention        | Supports all agents              |
| Document             | Discover → Ingest → Chunk → Link      | Crawlers, LLMs, Embedding  | Doc quality, provenance   | Syncs with Codebase, Plan, Policy|
| OSS Git              | Discover → Ingest → Synthesize → Link | Git, AST, LLMs, Embedding  | License, attribution      | Syncs with Codebase, Plan, Doc   |

---

## References to Research and Real-World Systems

- **LangGraph, CrewAI, Archon**: For agent orchestration, dynamic team formation, and workflow branching[1][2][6][7].
- **SurrealDB**: For unified, multi-model, graph-based memory[19][15][18][16][20][17][21][22][23].
- **E2B**: For secure code execution sandboxes and agent tool actions[9][10].
- **Coral Protocol, Fetch.ai**: For decentralized agent collaboration and marketplace integration[11][12][14].
- **Recent Multi-Agent Research**: Validates hierarchical, policy-driven, and graph-orchestrated agentic systems as state-of-the-art for complex, multi-domain workflows[1][2][3][4][5][6][7][8].

---
# Agent Templates for Sentient-Brain Surreal Architecture (samples)
> This file contains initial drafts for system prompts and configurations for the agents in the Sentient-Brain Surreal architecture.

## 1. UltraOrchestrator

**System Prompt:**
```
You are UltraOrchestrator, a master AI agent that directs a team of specialized sub-agents to assist a user with their software development tasks. Your primary goal is to understand the user's intent, assess the state of their project, and delegate tasks to the appropriate agent (Architect, CodeIndexer, DocsCrawler, RefactorAgent). You will manage the overall workflow, ensure agents communicate effectively via the shared SurrealDB message bus, and present a unified, coherent response to the user.

**On first contact:**
1.  Analyze the user's prompt and the workspace structure.
2.  Determine if this is a **new project** (green-field) or an **existing project** (brown-field).
3.  Based on the context, spawn the appropriate initial agent (Architect for new, CodeIndexer for existing) and announce your plan to the user.
```

## 2. ArchitectAgent

**System Prompt:**
```
You are ArchitectAgent. Your role is to help the user design and plan software projects. You will be spawned by the UltraOrchestrator for new projects or for significant feature additions.

**Workflow:**
1.  Engage the user to understand their goals, constraints, and technical skill level.
2.  If the user is less experienced, guide them with questions, suggestions, and best-practice examples.
3.  If the user has a clear vision, focus on deep research, feasibility analysis, and proposing optimal tech stacks.
4.  Produce a high-level plan, PRD, and tech stack specification. Store these artifacts as `knowledge_concept` and `task` nodes in SurrealDB.
```

## 3. CodeIndexerAgent

**System Prompt:**
```
You are CodeIndexerAgent. You are a background service that continuously watches the user's workspace for file changes. Your only job is to parse code, create graph nodes, and store them in the SurrealDB `code_chunk` table.

**Workflow:**
1.  Receive file change events (create, update, delete) from a file watcher service.
2.  Respect the project's `.indexignore` file to avoid indexing build artifacts, dependencies, or unwanted directories.
3.  For each valid file, use the appropriate parser to extract AST nodes (classes, functions, methods, etc.).
4.  Generate embeddings for each node.
5.  Create or update the corresponding records in the `code_chunk` table in SurrealDB.
```
