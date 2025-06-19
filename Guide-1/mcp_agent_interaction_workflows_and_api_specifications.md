# MCP Agent Interaction Workflows & Tool-Call Specification

This document details the core responsibilities, operational logic, and specific API interaction workflows for the five specialized AI agents operating within the Model Context Protocol (MCP) ecosystem. Each workflow describes a sequence of tool calls (RESTful API requests) an agent performs to fulfill its duties, referencing the MCP Server API v1.0.

---

## **1. Codebase Indexer Agent**

The Codebase Indexer is the foundation of the system's self-awareness, responsible for maintaining an accurate and enriched representation of the project's source code within the MCP's Code Memory layer.

*   **Core Responsibilities:**
    *   Scan local repository file systems to discover files and directory structures.
    *   Populate and synchronize the `code_repositories` and `code_files` tables.
    *   Use LLMs (e.g., Google Gemini) to analyze file contents, generating summaries and identifying intra-code dependencies.
    *   Persist these analyses in the `code_summaries` and `code_dependencies` tables.
*   **Triggers:**
    *   Initial onboarding of a new code repository.
    *   Real-time file system events (file creation, modification, or deletion) detected by a file watcher.
*   **Operational Logic:** The agent acts as a bridge between the file system and the structured Code Memory. It uses content hashing (`SHA-256`) to efficiently detect changes. For new or modified files, it orchestrates an analysis pipeline: `Read Content -> Generate Hash -> Call LLM for Summary & Dependencies -> Persist Results`.

### **Workflow 1: Full Repository Scan**

This workflow is executed when a new repository is added to the system.

1.  **Register the Repository:** The agent is given a repository name ("WebApp-Frontend") and a local path (`/var/mcp/repos/webapp-frontend`). It first creates the top-level record in the MCP server.
    *   **API Call:** `POST /api/v1/code/repositories`
    *   **Example Payload:**
        ```json
        {
          "name": "WebApp-Frontend",
          "local_path": "/var/mcp/repos/webapp-frontend"
        }
        ```
    *   **Outcome:** The server returns the new `repository_id` (e.g., `a1b2c3d4-0001-4001-8001-1234567890ab`).

2.  **Scan & Persist File Structure:** The agent recursively walks the local file system. For each file and directory, it creates a corresponding record in the database.
    *   **API Call:** `POST /api/v1/code/repositories/{repoId}/files` (called repeatedly for each item)
    *   **Example Payload (for a file):**
        ```json
        {
          "parent_id": "a1b2c3d4-0001-4001-8002-abcdef123456",
          "is_directory": false,
          "file_path": "src/components/Login.tsx",
          "content": "aW1wb3J0IFJlYWN0IGZyb20gJ3JlYWN0JzsK..."
        }
        ```
    *   **Outcome:** The entire file tree is mirrored in the `code_files` table, with each file record having a `status` of `pending`.

3.  **Analyze and Update Files:** The agent fetches all files for the repository that have a `pending` status. For each file, it performs the following:
    *   **Step 3.1: LLM Analysis:** Sends the file's content to the Gemini API with a prompt to generate a concise summary and identify all imported dependencies.
    *   **Step 3.2: Persist Summary:** Stores the generated summary.
        *   **API Call:** `POST /api/v1/code/files/{fileId}/summaries`
        *   **Example Payload:**
            ```json
            {
              "summary_text": "A React component for the user login form. It handles user input for email and password and includes a submit button.",
              "generating_model": "gemini-1.5-flash"
            }
            ```
    *   **Step 3.3: Persist Dependencies:** For each dependency identified by the LLM (e.g., `import api from '../api/client';`), the agent finds the `id` of the target file (`../api/client.ts`) and creates the dependency link.
        *   **API Call:** `POST /api/v1/code/files/{sourceFileId}/dependencies`
        *   **Example Payload:**
            ```json
            {
              "target_file_id": "a1b2c3d4-0001-4001-8003-fedcba654321"
            }
            ```
    *   **Step 3.4: Mark as Synced:** Updates the file's status to indicate completion.
        *   **API Call:** `POST /api/v1/code/files/{fileId}/sync` (This is a high-level action that could also trigger server-side analysis, but here we assume it primarily updates status after agent-led analysis).

### **Workflow 2: Incremental File Update**

This workflow is triggered by a file watcher detecting a modification.

1.  **Detect Change:** The watcher signals a change to `src/components/Login.tsx`. The agent identifies its corresponding `fileId`.
2.  **Read and Hash:** The agent reads the new file content and computes its SHA-256 hash.
3.  **Compare Hash:** The agent retrieves the file's current metadata (`GET /api/v1/code/files/{fileId}`) and compares the new hash with the stored `content_hash`. They differ.
4.  **Re-analyze and Update:** The agent follows the same analysis pipeline as in the full scan (Steps 3.1 - 3.4) for this single file, overwriting the old summary and dependency information with fresh data.

---

## **2. Knowledge Synthesizer Agent**

This agent acts as a researcher, transforming raw information into structured, actionable knowledge for the other agents.

*   **Core Responsibilities:**
    *   Search across internal and external knowledge sources (`document_chunks`).
    *   Use an LLM to synthesize disparate pieces of information into a coherent, actionable guide.
    *   Store these guides in the `synthesized_guides` table, linking them to source chunks and relevant tasks.
*   **Triggers:**
    *   A new task is created that requires research and planning.
    *   An explicit user command to generate a guide on a specific topic.
*   **Operational Logic:** The agent's goal is to bridge the gap between a high-level task and the low-level information needed to complete it. It uses semantic search to cast a wide net for information and then an LLM to distill that information into a single, canonical guide.

### **Workflow: Creating a Guide for a New Task**

1.  **Identify Need:** The agent is assigned `taskId: "b2c3d4e5-0002-4002-8002-234567890abc"` ("Implement password reset via email").
2.  **Formulate Query:** It derives a search query from the task title and description.
    *   **Query:** `q=password reset token generation email sending`
3.  **Semantic Search:** The agent queries the Guides & Implementation Memory to find relevant existing knowledge from all ingested documentation.
    *   **API Call:** `GET /api/v1/guides/search?q=password+reset+token+generation+email+sending&limit=10&type=chunk`
    *   **Outcome:** The API returns a ranked list of `document_chunks`, including their text, source, and relevance score.
4.  **Synthesize with LLM:** The agent constructs a detailed prompt for the Gemini API. The prompt includes the original task description and the content of the most relevant source chunks.
    > **Example Prompt:** "You are an expert software architect. Based on the following information chunks from our documentation, create a detailed, step-by-step implementation guide for the task: 'Implement password reset via email'. The guide should cover token generation, database storage, email sending, and the token verification endpoint. Source Chunks: [chunk_text_1, chunk_text_2, ...]"
5.  **Persist Synthesized Guide:** The LLM returns a markdown-formatted guide. The agent then saves this guide to the MCP server, linking it back to the original task and the source chunks used in its creation.
    *   **API Call:** `POST /api/v1/guides/synthesized`
    *   **Example Payload:**
        ```json
        {
          "task_id": "b2c3d4e5-0002-4002-8002-234567890abc",
          "title": "Guide: Implementing Password Reset via Email",
          "content": "### Step 1: Generate a Secure Reset Token\nWhen a user requests a password reset, generate a cryptographically secure, single-use token...",
          "source_chunk_ids": [
            "c3d4e5f6-...",
            "d4e5f6g7-..."
          ]
        }
        ```

---

## **3. Implementation Agent**

This agent is the "doer," responsible for writing and modifying code to accomplish defined tasks.

*   **Core Responsibilities:**
    *   Interpret a task and its associated `synthesized_guide`.
    *   Gather necessary context from the existing codebase and dependency documentation.
    *   Generate code modifications using an LLM.
    *   Apply changes to the local file system.
    *   Update task status upon completion.
*   **Triggers:** A task with an associated guide is moved to the `in_progress` status.
*   **Operational Logic:** The agent follows a "Read, Ponder, Write" cycle. It reads the task and guide, ponders the best implementation strategy by gathering context from all memory layers, and then writes the code.

### **Workflow: Implementing a Feature Task**

1.  **Acquire Task:** The agent picks up `taskId: "c3d4e5f6-0003-4003-8003-34567890abcd"` ("Add GET /api/users/:id endpoint").
2.  **Gather Context:** The agent assembles a complete contextual picture for the LLM.
    *   **Task Details:** `GET /api/v1/tasks/c3d4e5f6-0003-4003-8003-34567890abcd`
    *   **Implementation Guide:** `GET /api/v1/guides/synthesized?task_id=c3d4e5f6-0003-4003-8003-34567890abcd`
    *   **Relevant Existing Code:** It searches for code related to API routing.
        *   `GET /api/v1/guides/search?q=API+routing+setup&type=chunk` (searching code summaries)
    *   **Relevant Dependency Docs:** It searches for documentation on how to use the web framework (e.g., Express).
        *   `GET /api/v1/dependencies/docs/search?q=express.js+route+parameter`

3.  **Generate Code:** The agent provides all gathered context to the Gemini API, requesting specific code to be added to a file.
    > **Prompt:** "Given the attached guide and context from existing files, add a new endpoint `GET /api/users/:id` to the `src/routes/users.js` file. The endpoint should retrieve a user by ID from the database and return it."
4.  **Apply Changes:** The agent receives the code block from the LLM and writes it to the local file `/var/mcp/repos/webapp-backend/src/routes/users.js`.
5.  **Trigger Re-index:** The agent notifies the system that the file has changed, triggering the Codebase Indexer's incremental update workflow.
    *   **API Call:** `POST /api/v1/code/files/{fileId}/sync` (for `users.js`).
6.  **Update Task Status:** After applying the code (and ideally running tests), the agent marks the task as ready for review.
    *   **API Call:** `PATCH /api/v1/tasks/c3d4e5f6-0003-4003-8003-34567890abcd`
    *   **Example Payload:**
        ```json
        {
          "status": "review"
        }
        ```

---

## **4. Task Manager Agent**

This agent is the master planner, responsible for breaking down high-level goals into a structured, executable plan.

*   **Core Responsibilities:**
    *   Decompose `grand_plans` into a hierarchical tree of `tasks` and `sub-tasks`.
    *   Assign properties to tasks, such as `feature_classification` and `priority`.
    *   Establish dependencies between tasks.
*   **Triggers:** A new `grand_plan` is created in the system.
*   **Operational Logic:** The agent uses an LLM to perform strategic decomposition. It translates a natural language objective into a formal project plan represented by the relational schema of the Task Memory layer.

### **Workflow: Decomposing a Grand Plan**

1.  **Detect New Plan:** The agent is notified that `planId: "d4e5f6g7-0004-4004-8004-4567890abcde"` has been created with the objective: "Develop a multi-tenant subscription billing system."
2.  **LLM-based Decomposition:** The agent sends the objective to the Gemini API.
    > **Prompt:** "Break down the epic 'Develop a multi-tenant subscription billing system' into a hierarchical list of tasks with dependencies. For each, provide a title, description, and classification (`database`, `backend`, `frontend`). Return the output as a JSON object."
3.  **Create Tasks:** The agent parses the hierarchical JSON returned by the LLM and creates the corresponding records in the MCP server. It traverses the hierarchy, creating parent tasks first to obtain their IDs.
    *   **API Call:** `POST /api/v1/tasks` (called repeatedly)
    *   **Example Payload (for a parent task):**
        ```json
        {
          "grand_plan_id": "d4e5f6g7-0004-4004-8004-4567890abcde",
          "parent_task_id": null,
          "title": "Database Schema for Subscriptions",
          "description": "Design and implement database tables for tenants, plans, subscriptions, and invoices.",
          "priority": 1,
          "feature_classification": "database"
        }
        ```
    *   **Example Payload (for a sub-task):**
        ```json
        {
          "grand_plan_id": "d4e5f6g7-0004-4004-8004-4567890abcde",
          "parent_task_id": "e5f6g7h8-...",
          "title": "Create 'plans' table",
          "description": "Table to store different subscription tiers like 'Free', 'Pro', 'Enterprise'.",
          "priority": 1,
          "feature_classification": "database"
        }
        ```
4.  **Define Dependencies:** After creating the tasks, the agent establishes the dependency links identified by the LLM. For example, the "Backend API for Subscriptions" task depends on the "Database Schema" task.
    *   **API Call:** `POST /api/v1/tasks/{taskId_for_Backend}/dependencies`
    *   **Example Payload:**
        ```json
        {
          "depends_on_task_id": "e5f6g7h8-..."
        }
        ```

---

## **5. Dependency Documenter Agent**

This agent manages the system's knowledge of external libraries and frameworks.

*   **Core Responsibilities:**
    *   Scan dependency manifest files (e.g., `package.json`, `requirements.txt`).
    *   Catalog project dependencies in the `project_dependencies` table.
    *   Trigger the ingestion of dependency documentation into the vector database for semantic search.
*   **Triggers:** A dependency manifest file is created or modified.
*   **Operational Logic:** The agent keeps the Dependency Memory synchronized with the project's actual third-party dependencies. It automates the tedious but critical process of making external documentation available for contextual retrieval by other agents.

### **Workflow: Cataloging a New Dependency**

1.  **Detect Manifest Change:** A file watcher detects a modification to `package.json`.
2.  **Parse and Discover:** The agent parses the file and identifies a new entry: `"chart.js": "4.4.3"`.
3.  **Check for Existence:** It queries the server to see if this specific dependency version is already known.
    *   `GET /api/v1/dependencies?name=chart.js&version=4.4.3&manager=npm`
4.  **Register New Dependency:** The query returns empty, so the agent registers it. It may perform a web search or use a registry API to find the official documentation URL.
    *   **API Call:** `POST /api/v1/dependencies`
    *   **Example Payload:**
        ```json
        {
          "name": "chart.js",
          "version": "4.4.3",
          "manager": "npm",
          "documentation_url": "https://www.chartjs.org/docs/latest/"
        }
        ```
5.  **Trigger Documentation Ingestion:** Upon successful creation, the server returns the new record with its `id` (e.g., `f6g7h8i9-0005-4005-8005-567890abcdef`). The agent immediately kicks off the server-side ingestion process.
    *   **API Call:** `POST /api/v1/dependencies/f6g7h8i9-0005-4005-8005-567890abcdef/ingest-docs`
    *   **Request Body:** (Empty)
    *   **Outcome:** The server responds with `202 Accepted`. The agent's job is done; the server now asynchronously scrapes, chunks, and embeds the documentation from the provided URL into the `dependency_docs_collection` in ChromaDB.