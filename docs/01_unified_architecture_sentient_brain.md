# Sentient-Brain: Unified Architecture Blueprint

## 1. Mission

To build a high-performance, extensible, and observable MCP server for advanced codebase and document memory. The server will power next-generation AI agents by providing them with rich, contextual information through a state-of-the-art RAG and knowledge graph pipeline, starting with a primary focus on codebase analysis.

## 2. Core Architectural Decisions

This architecture is a direct synthesis of the best-in-class patterns observed across the `Archon`, `a2a-python`, and `mcp-crawl4ai-rag` repositories.

*   **Primary Framework**: **FastAPI**
    *   *Source*: Common best practice, confirmed in `Archon`.
    *   *Reasoning*: High performance, asynchronous support, and excellent ecosystem integration (Pydantic, OpenTelemetry).

*   **Communication Protocol**: **gRPC**
    *   *Source*: `a2a-python`.
    *   *Reasoning*: Provides a strongly-typed, high-performance, and language-agnostic interface for agent-server communication, crucial for reliability and scalability.

*   **Codebase Knowledge Graph**: **Neo4j + Python `ast` Module**
    *   *Source*: `mcp-crawl4ai-rag`.
    *   *Reasoning*: The `ast` module provides a direct, fast, and accurate way to parse Python code into an Abstract Syntax Tree. Storing this tree in Neo4j creates a powerful, queryable graph of the codebase's structure, enabling advanced analysis and validation without relying on LLMs for parsing.

*   **Document & Semantic Search**: **Weaviate**
    *   *Source*: Initial project plan, validated by hybrid storage patterns.
    *   *Reasoning*: Provides state-of-the-art vector search capabilities, which will be essential for the second phase of development (document memory).

*   **Agentic Logic & Workflows**: **Pydantic-Graph**
    *   *Source*: `Archon`.
    *   *Reasoning*: Offers a modern, Pydantic-native way to define and execute complex, graph-based agentic workflows, which will be critical for orchestrating ingestion and retrieval tasks.

*   **Observability**: **OpenTelemetry**
    *   *Source*: `a2a-python`.
    *   *Reasoning*: The industry standard for distributed tracing. Instrumenting with OpenTelemetry from the start will give us crucial visibility into the performance and behavior of our distributed services.

## 3. Final Technology Stack & `requirements.txt`

Based on the above, the final, consolidated list of primary dependencies is:

*   **Framework**: `fastapi`, `uvicorn`
*   **Communication**: `grpcio`, `grpcio-tools`, `protobuf`
*   **Agentic Engine**: `pydantic-graph` (and its dependencies)
*   **Databases**: `neo4j`, `weaviate-client`
*   **LLM/Embeddings**: `google-genai`, `sentence-transformers`, `litemllm`
*   **Data Handling**: `pydantic`, `pydantic-settings`
*   **Web/File Parsing**: `playwright`, `beautifulsoup4`, `html2text`
*   **Observability**: `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`
*   **Utilities**: `tenacity`, `typer`, `rich`, `python-dotenv`

## 4. Implementation Roadmap (Phase 1: Codebase Memory)

1.  **Environment Setup**: Rebuild the Docker environment with the final `requirements.txt` and ensure all services (FastAPI, Weaviate, Neo4j, Ollama) start correctly.
2.  **Service Scaffolding**: Create the initial Python files for our core services (`grpc_server.py`, `services/neo4j_service.py`, `services/code_graph_service.py`).
3.  **Code-to-Graph Pipeline**: Implement the `ast`-based parsing and Neo4j ingestion logic in `code_graph_service.py`.
4.  **gRPC Endpoints**: Expose the code ingestion and querying functionality via a gRPC service.
5.  **Testing**: Thoroughly test the pipeline by ingesting a sample repository and querying the resulting graph.

This document now serves as the single source of truth for our architecture. All subsequent steps will align with this blueprint.