# Sentient-Brain: Master Architectural Blueprint

*Version 1.0 - Last Updated: 2025-06-21*

## 1. Executive Summary & Mission

This document is the single source of truth for the `sentient-brain` project. Its mission is to build a high-performance, extensible, and observable **Model-Context-Protocol (MCP) Server**. This server will empower next-generation AI agents by providing them with a rich, queryable, and stateful understanding of complex domains, starting with software development codebases.

This blueprint is designed to be self-contained. All architectural decisions, technology choices, and implementation plans are detailed and justified herein, based on official documentation, community best practices, and a deep analysis of exemplar projects.

## 2. The Model-Context-Protocol (MCP) in Practice

`sentient-brain` is not just a server that uses AI; it is a native implementation of the **Model-Context-Protocol (MCP)**, an open standard for AI agent-tool interaction.

### 2.1. What is MCP?

MCP is a JSON-RPC 2.0-based protocol that standardizes how AI agents (Clients) discover and interact with external systems (Servers). It solves the M×N integration problem by creating a universal language, allowing any MCP-compliant agent to use any MCP-compliant tool without bespoke engineering. Our server will function as a specialized **MCP Server**.

### 2.2. How `sentient-brain` Implements MCP

An AI agent (e.g., an IDE-based coding assistant) will connect to our `sentient-brain` server as an MCP Client. The interaction will follow this flow:

1.  **Handshake & Discovery**: The agent connects to our server's MCP endpoint. It calls standard MCP methods like `mcp_list_tools` and `mcp_list_resources`.
2.  **Capability Response**: Our server responds with a manifest of its capabilities:
    *   **Tools (Actions)**: `ingest_repository(url)`, `query_code_graph(cypher)`, `validate_code_snippet(code)`.
    *   **Resources (Data)**: `code_graph_nodes`, `code_graph_relationships`.
3.  **Agent Decision**: The agent's host process (e.g., the IDE plugin) presents these capabilities to the core LLM. When the user asks, "*Which functions use the `Neo4jCodeAnalyzer` class?*", the LLM decides to use our server's tools.
4.  **Tool Invocation**: The agent sends a JSON-RPC request to our server to execute `mcp_call_tool` with the name `query_code_graph` and the appropriate Cypher query as parameters.
5.  **Execution & Response**: Our FastAPI server routes this request to the `RetrievalService`, which executes the query against the Neo4j database and returns the structured result. The agent then uses this data to formulate its answer.

This architecture makes `sentient-brain` a powerful, reusable, and discoverable component in a larger AI ecosystem.

## 3. System Architecture Deep Dive

```mermaid
graph TD
    subgraph AI Agent (MCP Client)
        A[IDE Plugin / Agent Host]
    end

    subgraph Sentient-Brain MCP Server (FastAPI on Docker)
        B(gRPC Gateway) -- JSON-RPC --> C{Service Router}
        C --> D[Ingestion Service]
        C --> E[Retrieval Service]
        C --> F[Code Graph Service]

        F -- uses --> G(AST Parser)
        F -- writes --> H[Neo4j Database]
        D -- triggers --> F

        E -- reads --> H
        E -- uses --> I(Hybrid Search Logic)
        I -- reads --> J[Weaviate Database]
    end

    subgraph Databases
        H
        J
    end

    A -- MCP over HTTP/gRPC --> B
```

*   **gRPC Gateway**: The primary entry point, handling MCP requests.
*   **Ingestion Service**: Orchestrates the process of fetching and processing data (e.g., cloning a Git repo).
*   **Code Graph Service**: The core of our codebase memory. It uses Python's `ast` module to parse source code into an Abstract Syntax Tree and populates the Neo4j database with nodes (files, classes, functions) and relationships (imports, calls).
*   **Retrieval Service**: Exposes query capabilities. It can perform structured queries against the Neo4j graph and will later perform hybrid semantic search against Weaviate.

## 4. Technology Stack & Dependency Justification

This stack is the result of synthesizing the `Archon` dependency analysis with the requirements of our MCP-native architecture.

### Core Framework
*   **fastapi, uvicorn**: **[ADD]** High-performance ASGI framework. The standard for modern Python web services.

### Communication & Agentics
*   **grpcio, grpcio-tools, protobuf**: **[ADD]** Chosen for high-performance, strongly-typed agent-server communication, as inspired by `a2a-python`.
*   **pydantic, pydantic-settings**: **[ADD]** The backbone of our data validation and schema-first design.
*   **pydantic-graph**: **[ADD]** A powerful tool from `Archon` for defining and executing the complex, stateful workflows required for ingestion and multi-step retrieval.

### Databases & Data Handling
*   **neo4j**: **[ADD]** The core of our codebase memory, storing the AST-derived knowledge graph.
*   **weaviate-client**: **[ADD]** For our future document memory layer and hybrid search capabilities.
*   **rank-bm25**: **[ADD]** Essential for implementing effective hybrid search (sparse + dense vectors) in Weaviate.

### LLM & AI Services
*   **google-genai, sentence-transformers, litellm**: **[ADD]** A flexible suite for interacting with Gemini, generating local embeddings via Ollama, and abstracting LLM calls.

### Ingestion & Parsing
*   **playwright, tf-playwright-stealth**: **[ADD]** For robust, stealthy web scraping to build our document memory layer in Phase 2.
*   **beautifulsoup4, html2text**: **[ADD]** Standard tools for processing raw HTML.

### Utilities & Resilience
*   **langchain-community, langchain-core, langchain-text-splitters**: **[ADD]** While we are not using the full LangChain agent framework, its utility modules for tasks like text splitting are best-in-class and battle-tested.
*   **tenacity**: **[ADD]** Critical for resilience. All external calls (to LLMs, databases, etc.) will be wrapped in `tenacity` retry logic.
*   **typer, rich, tqdm**: **[ADD]** For building powerful and user-friendly CLI tools for administration and batch processing.
*   **python-dotenv**: **[ADD]** Standard for managing environment variables.

## 5. Final `requirements.txt`

```
# Main Application Framework
fastapi
uvicorn[standard]

# Communication & Agentics
grpcio
grpcio-tools
protobuf
pydantic-graph

# LLM & AI Services
google-genai
sentence-transformers
litellm

# Data Storage & Search
weaviate-client
neo4j
rank-bm25

# Data Handling & Validation
pydantic
pydantic-settings

# LangChain Utilities (for specific tasks like text splitting)
langchain-community
langchain-core
langchain-text-splitters

# Web/File Ingestion & Parsing
playwright
tf-playwright-stealth
beautifulsoup4
html2text

# Utilities & Resilience
tenacity
typer
rich
tqdm
python-dotenv
```

## 6. Phased Implementation Roadmap

1.  **Environment Setup**: Rebuild the Docker environment with the final `requirements.txt`.
2.  **Service Scaffolding**: Create the initial Python files for our core services.
3.  **Code-to-Graph Pipeline**: Implement the `ast`-based parsing and Neo4j ingestion.
4.  **MCP/gRPC Endpoints**: Expose the pipeline via a discoverable MCP service.
5.  **Test**: Ingest a sample repository and validate the graph.
